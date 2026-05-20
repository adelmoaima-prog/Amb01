from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import date
from typing import Optional
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.agenda import Agenda
from app.models.escala import EscalaMedica, AlteracaoEscala
from app.models.especialidade import Especialidade
from app.models.profissional import Profissional
from app.models.consultorio import Consultorio
from app.models.consulta import Consulta
from app.schemas.agenda import (
    AgendaCreate, AgendaUpdate, AgendaResponse,
    EscalaCreate, EscalaUpdate, EscalaResponse,
    AlteracaoEscalaResponse, ImpactoEscala,
)

router = APIRouter(prefix="/agendas", tags=["agendas"])


@router.get("/", response_model=list[AgendaResponse])
async def list_agendas(
    especialidade_id: Optional[str] = Query(None),
    profissional_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    turno: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(
        Agenda,
        Especialidade.nome.label("esp_nome"),
        Profissional.nome.label("prof_nome"),
        Consultorio.numero.label("cons_numero"),
    ).join(Especialidade, Agenda.especialidade_id == Especialidade.id
    ).join(Profissional, Agenda.profissional_id == Profissional.id
    ).outerjoin(Consultorio, Agenda.consultorio_id == Consultorio.id)

    filters = []
    if especialidade_id:
        filters.append(Agenda.especialidade_id == especialidade_id)
    if profissional_id:
        filters.append(Agenda.profissional_id == profissional_id)
    if status:
        filters.append(Agenda.status == status)
    if turno:
        filters.append(Agenda.turno == turno)
    if filters:
        stmt = stmt.where(and_(*filters))

    result = await db.execute(stmt)
    rows = result.all()

    return [
        AgendaResponse(
            id=row.Agenda.id,
            especialidade_id=row.Agenda.especialidade_id,
            profissional_id=row.Agenda.profissional_id,
            consultorio_id=row.Agenda.consultorio_id,
            turno=row.Agenda.turno,
            dia_semana=row.Agenda.dia_semana,
            hora_inicio=row.Agenda.hora_inicio,
            hora_fim=row.Agenda.hora_fim,
            intervalo_minutos=row.Agenda.intervalo_minutos,
            vagas_total=row.Agenda.vagas_total,
            vagas_reserva=row.Agenda.vagas_reserva,
            data_inicio=row.Agenda.data_inicio,
            data_fim=row.Agenda.data_fim,
            observacoes=row.Agenda.observacoes,
            status=row.Agenda.status,
            especialidade_nome=row.esp_nome,
            profissional_nome=row.prof_nome,
            consultorio_numero=row.cons_numero,
        )
        for row in rows
    ]


@router.post("/", response_model=AgendaResponse, status_code=201)
async def create_agenda(
    body: AgendaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agenda = Agenda(**body.model_dump())
    db.add(agenda)
    await db.commit()
    await db.refresh(agenda)
    return AgendaResponse(**body.model_dump(), id=agenda.id, status=agenda.status)


@router.get("/{agenda_id}", response_model=AgendaResponse)
async def get_agenda(
    agenda_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(
        Agenda, Especialidade.nome.label("esp_nome"),
        Profissional.nome.label("prof_nome"),
        Consultorio.numero.label("cons_numero"),
    ).join(Especialidade, Agenda.especialidade_id == Especialidade.id
    ).join(Profissional, Agenda.profissional_id == Profissional.id
    ).outerjoin(Consultorio, Agenda.consultorio_id == Consultorio.id
    ).where(Agenda.id == agenda_id)

    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Agenda não encontrada")

    return AgendaResponse(
        id=row.Agenda.id,
        especialidade_id=row.Agenda.especialidade_id,
        profissional_id=row.Agenda.profissional_id,
        consultorio_id=row.Agenda.consultorio_id,
        turno=row.Agenda.turno,
        dia_semana=row.Agenda.dia_semana,
        hora_inicio=row.Agenda.hora_inicio,
        hora_fim=row.Agenda.hora_fim,
        intervalo_minutos=row.Agenda.intervalo_minutos,
        vagas_total=row.Agenda.vagas_total,
        vagas_reserva=row.Agenda.vagas_reserva,
        data_inicio=row.Agenda.data_inicio,
        data_fim=row.Agenda.data_fim,
        observacoes=row.Agenda.observacoes,
        status=row.Agenda.status,
        especialidade_nome=row.esp_nome,
        profissional_nome=row.prof_nome,
        consultorio_numero=row.cons_numero,
    )


@router.patch("/{agenda_id}", response_model=AgendaResponse)
async def update_agenda(
    agenda_id: uuid.UUID,
    body: AgendaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agenda).where(Agenda.id == agenda_id))
    agenda = result.scalar_one_or_none()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda não encontrada")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agenda, key, value)

    await db.commit()
    await db.refresh(agenda)
    return await get_agenda(agenda_id, db, current_user)


# Escalas
escalas_router = APIRouter(prefix="/escalas", tags=["escalas"])


@router.get("/{agenda_id}/impacto", response_model=ImpactoEscala)
async def get_impacto(
    agenda_id: uuid.UUID,
    data: Optional[date] = Query(None),
    turno: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Agenda, Especialidade.nome.label("esp_nome"))
        .join(Especialidade, Agenda.especialidade_id == Especialidade.id)
        .where(Agenda.id == agenda_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Agenda não encontrada")

    agendados = 0
    if data:
        count_result = await db.execute(
            select(func.count(Consulta.id)).where(
                Consulta.agenda_id == agenda_id,
                func.date(Consulta.data_hora) == data,
                Consulta.status.in_(["agendado", "confirmado"]),
            )
        )
        agendados = count_result.scalar() or 0

    return ImpactoEscala(
        pacientes_agendados=agendados,
        vagas_abertas=row.Agenda.vagas_total - agendados,
        producao_estimada_perdida=agendados,
        especialidade_nome=row.esp_nome,
        data=str(data) if data else "",
        turno=turno or row.Agenda.turno,
    )


@escalas_router.get("/", response_model=list[EscalaResponse])
async def list_escalas(
    data: Optional[date] = Query(None),
    profissional_id: Optional[str] = Query(None),
    especialidade_id: Optional[str] = Query(None),
    mes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(
        EscalaMedica,
        Profissional.nome.label("prof_nome"),
        Especialidade.nome.label("esp_nome"),
    ).join(Profissional, EscalaMedica.profissional_id == Profissional.id
    ).join(Especialidade, Profissional.especialidade_id == Especialidade.id)

    filters = []
    if data:
        filters.append(EscalaMedica.data == data)
    if profissional_id:
        filters.append(EscalaMedica.profissional_id == profissional_id)
    if especialidade_id:
        filters.append(Profissional.especialidade_id == especialidade_id)
    if mes:
        parts = mes.split("-")
        ano, mes_n = int(parts[0]), int(parts[1])
        import calendar as cal
        inicio = date(ano, mes_n, 1)
        fim = date(ano, mes_n, cal.monthrange(ano, mes_n)[1])
        filters.append(EscalaMedica.data >= inicio)
        filters.append(EscalaMedica.data <= fim)
    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.order_by(EscalaMedica.data, EscalaMedica.turno)
    result = await db.execute(stmt)
    rows = result.all()

    return [
        EscalaResponse(
            id=row.EscalaMedica.id,
            profissional_id=row.EscalaMedica.profissional_id,
            agenda_id=row.EscalaMedica.agenda_id,
            data=row.EscalaMedica.data,
            turno=row.EscalaMedica.turno,
            hora_inicio=row.EscalaMedica.hora_inicio,
            hora_fim=row.EscalaMedica.hora_fim,
            status=row.EscalaMedica.status,
            profissional_nome=row.prof_nome,
            especialidade_nome=row.esp_nome,
        )
        for row in rows
    ]


@escalas_router.post("/", response_model=EscalaResponse, status_code=201)
async def create_escala(
    body: EscalaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    escala = EscalaMedica(**body.model_dump())
    db.add(escala)
    await db.commit()
    await db.refresh(escala)
    return EscalaResponse(**body.model_dump(), id=escala.id)


@escalas_router.patch("/{escala_id}", response_model=EscalaResponse)
async def update_escala(
    escala_id: uuid.UUID,
    body: EscalaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(EscalaMedica).where(EscalaMedica.id == escala_id))
    escala = result.scalar_one_or_none()
    if not escala:
        raise HTTPException(status_code=404, detail="Escala não encontrada")

    dados_ant = {
        "status": escala.status,
        "hora_inicio": str(escala.hora_inicio),
        "hora_fim": str(escala.hora_fim),
    }

    justificativa = body.justificativa
    tipo_alt = body.tipo_alteracao or "alteracao"

    update_data = body.model_dump(exclude_unset=True, exclude={"justificativa", "tipo_alteracao"})
    for k, v in update_data.items():
        setattr(escala, k, v)

    if justificativa:
        alteracao = AlteracaoEscala(
            escala_id=escala_id,
            user_id=current_user.id,
            tipo_alteracao=tipo_alt,
            justificativa=justificativa,
            dados_anteriores=dados_ant,
            dados_novos={k: str(v) for k, v in update_data.items()},
        )
        db.add(alteracao)

    await db.commit()
    await db.refresh(escala)
    return EscalaResponse(
        id=escala.id,
        profissional_id=escala.profissional_id,
        agenda_id=escala.agenda_id,
        data=escala.data,
        turno=escala.turno,
        hora_inicio=escala.hora_inicio,
        hora_fim=escala.hora_fim,
        status=escala.status,
    )


@escalas_router.get("/{escala_id}/historico", response_model=list[AlteracaoEscalaResponse])
async def get_historico_escala(
    escala_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(AlteracaoEscala, User.nome.label("user_nome")).join(
        User, AlteracaoEscala.user_id == User.id
    ).where(AlteracaoEscala.escala_id == escala_id).order_by(AlteracaoEscala.data_alteracao.desc())

    result = await db.execute(stmt)
    rows = result.all()

    return [
        AlteracaoEscalaResponse(
            id=row.AlteracaoEscala.id,
            tipo_alteracao=row.AlteracaoEscala.tipo_alteracao,
            justificativa=row.AlteracaoEscala.justificativa,
            pacientes_impactados=row.AlteracaoEscala.pacientes_impactados,
            producao_perdida=row.AlteracaoEscala.producao_perdida,
            data_alteracao=str(row.AlteracaoEscala.data_alteracao),
            user_nome=row.user_nome,
        )
        for row in rows
    ]
