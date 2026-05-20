from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, datetime
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.consultorio import Consultorio
from app.models.capacidade import CapacidadeTurno
from app.models.escala import EscalaMedica
from app.models.profissional import Profissional
from app.models.especialidade import Especialidade
from app.schemas.capacidade import (
    ResumoCapacidade, ConsultorioStatus, OcupacaoPorTurno,
    EquipeEscalada, SimulacaoCapacidade,
)

router = APIRouter(prefix="/capacidade", tags=["capacidade"])


@router.get("/resumo", response_model=ResumoCapacidade)
async def get_resumo(
    data: Optional[date] = Query(None),
    turno: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ref_date = data or datetime.utcnow().date()

    total_cons_result = await db.execute(select(func.count(Consultorio.id)).where(Consultorio.ativo == True))
    total_cons = total_cons_result.scalar() or 0

    filters = [CapacidadeTurno.data == ref_date]
    if turno:
        filters.append(CapacidadeTurno.turno == turno)

    cap_stmt = select(
        func.count(CapacidadeTurno.id).label("total"),
        func.count(CapacidadeTurno.id).filter(CapacidadeTurno.status_sala == "ocupada").label("ocupados"),
        func.count(CapacidadeTurno.id).filter(CapacidadeTurno.status_sala == "ociosa").label("ociosos"),
    ).where(and_(*filters))

    cap_result = await db.execute(cap_stmt)
    cap = cap_result.first()

    prof_stmt = select(func.count(EscalaMedica.id)).where(
        EscalaMedica.data == ref_date,
        EscalaMedica.status == "confirmado",
    )
    if turno:
        prof_stmt = prof_stmt.where(EscalaMedica.turno == turno)
    prof_result = await db.execute(prof_stmt)
    prof_escalados = prof_result.scalar() or 0

    ocupados = cap.ocupados or 0
    ociosos = cap.ociosos or 0
    taxa = round((ocupados / total_cons * 100) if total_cons > 0 else 0, 1)

    return ResumoCapacidade(
        consultorios_total=total_cons,
        consultorios_ativos=total_cons,
        consultorios_ocupados=ocupados,
        consultorios_ociosos=ociosos,
        taxa_ocupacao=taxa,
        profissionais_escalados=prof_escalados,
        profissionais_disponiveis=prof_escalados,
    )


@router.get("/consultorios", response_model=list[ConsultorioStatus])
async def get_consultorios(
    data: Optional[date] = Query(None),
    turno: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ref_date = data or datetime.utcnow().date()

    stmt = select(Consultorio).where(Consultorio.ativo == True).order_by(Consultorio.andar, Consultorio.numero)
    result = await db.execute(stmt)
    consultorios = result.scalars().all()

    cap_filters = [CapacidadeTurno.data == ref_date]
    if turno:
        cap_filters.append(CapacidadeTurno.turno == turno)

    cap_stmt = select(CapacidadeTurno).where(and_(*cap_filters))
    cap_result = await db.execute(cap_stmt)
    caps = {str(c.consultorio_id): c for c in cap_result.scalars().all()}

    output = []
    for c in consultorios:
        cap = caps.get(str(c.id))
        status = cap.status_sala if cap else "disponivel"
        output.append(ConsultorioStatus(
            id=c.id,
            numero=c.numero,
            nome=c.nome,
            andar=c.andar,
            tipo=c.tipo,
            status=status,
            turno_atual=turno,
            profissional_atual=None,
            especialidade_atual=None,
            vagas_ofertadas=cap.vagas_ofertadas if cap else 0,
            vagas_ocupadas=cap.vagas_ocupadas if cap else 0,
        ))

    return output


@router.get("/por-turno", response_model=list[OcupacaoPorTurno])
async def get_por_turno(
    data: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ref_date = data or datetime.utcnow().date()

    stmt = select(
        CapacidadeTurno.turno,
        func.count(CapacidadeTurno.id).label("total"),
        func.count(CapacidadeTurno.id).filter(CapacidadeTurno.status_sala == "ocupada").label("ocupados"),
        func.sum(CapacidadeTurno.vagas_ofertadas).label("vagas_ofertadas"),
        func.sum(CapacidadeTurno.vagas_ocupadas).label("vagas_ocupadas"),
    ).where(CapacidadeTurno.data == ref_date
    ).group_by(CapacidadeTurno.turno)

    result = await db.execute(stmt)
    return [
        OcupacaoPorTurno(
            turno=r.turno,
            consultorios_disponiveis=r.total or 0,
            consultorios_ocupados=r.ocupados or 0,
            vagas_ofertadas=int(r.vagas_ofertadas or 0),
            vagas_ocupadas=int(r.vagas_ocupadas or 0),
            taxa_ocupacao=round((r.ocupados / r.total * 100) if r.total else 0, 1),
        )
        for r in result.all()
    ]


@router.get("/equipe", response_model=list[EquipeEscalada])
async def get_equipe(
    data: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ref_date = data or datetime.utcnow().date()

    stmt = select(
        EscalaMedica.turno,
        func.count(EscalaMedica.id).filter(Profissional.tipo == "medico").label("medicos"),
        func.count(EscalaMedica.id).filter(Profissional.tipo == "enfermeiro").label("enfermeiros"),
        func.count(EscalaMedica.id).filter(Profissional.tipo == "tecnico_enfermagem").label("tecnicos"),
        func.count(EscalaMedica.id).label("total"),
    ).join(Profissional, EscalaMedica.profissional_id == Profissional.id
    ).where(
        EscalaMedica.data == ref_date,
        EscalaMedica.status == "confirmado",
    ).group_by(EscalaMedica.turno)

    result = await db.execute(stmt)
    return [
        EquipeEscalada(
            data=str(ref_date),
            turno=r.turno,
            medicos=r.medicos or 0,
            enfermeiros=r.enfermeiros or 0,
            tecnicos=r.tecnicos or 0,
            recepcionistas=2,
            total_equipe=r.total or 0,
            capacidade_maxima=(r.medicos or 0) * 8,
        )
        for r in result.all()
    ]


@router.get("/simulacao", response_model=SimulacaoCapacidade)
async def get_simulacao(
    nova_especialidade: str = Query(...),
    vagas: int = Query(..., ge=1),
    turno: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = datetime.utcnow().date()

    total_cons_result = await db.execute(select(func.count(Consultorio.id)).where(Consultorio.ativo == True))
    total_cons = total_cons_result.scalar() or 0

    cap_stmt = select(func.count(CapacidadeTurno.id)).where(
        CapacidadeTurno.data == today,
        CapacidadeTurno.turno == turno,
        CapacidadeTurno.status_sala == "ocupada",
    )
    cap_result = await db.execute(cap_stmt)
    ocupados = cap_result.scalar() or 0
    disponiveis = total_cons - ocupados

    nova_taxa = round(((ocupados + 1) / total_cons * 100) if total_cons > 0 else 0, 1)

    return SimulacaoCapacidade(
        nova_especialidade=nova_especialidade,
        vagas_solicitadas=vagas,
        turno=turno,
        consultorios_disponiveis=disponiveis,
        consultorio_sugerido=f"Sala {disponiveis + 101}" if disponiveis > 0 else None,
        viavel=disponiveis > 0,
        impacto_taxa_ocupacao=nova_taxa,
        requer_nova_equipe=vagas > 8,
    )
