from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, case
from datetime import date, datetime
from typing import Optional
import calendar
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.consulta import Consulta, MotivoFalta, ConfirmacaoPresenca
from app.models.especialidade import Especialidade
from app.schemas.absenteismo import (
    ResumoAbsenteismo, AbsenteismoPorEspecialidade, AbsenteismoPorMunicipio,
    AbsenteismoPorDia, AbsenteismoPorTurno, AbsenteismoPorMotivo,
    TendenciaAbsenteismo, RegistrarFaltaRequest,
    ConfirmacaoPresencaCreate, ConfirmacaoPresencaResponse,
)

router = APIRouter(prefix="/absenteismo", tags=["absenteismo"])

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def parse_competencia(competencia: Optional[str]) -> tuple[date, date]:
    if competencia:
        parts = competencia.split("-")
        ano, mes = int(parts[0]), int(parts[1])
    else:
        now = datetime.utcnow()
        ano, mes = now.year, now.month
    inicio = date(ano, mes, 1)
    fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
    return inicio, fim


@router.get("/resumo", response_model=ResumoAbsenteismo)
async def get_resumo(
    competencia: Optional[str] = Query(None),
    especialidade_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inicio, fim = parse_competencia(competencia)

    filters = [
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    ]
    if especialidade_id:
        filters.append(Consulta.especialidade_id == especialidade_id)

    stmt = select(
        Consulta.status, func.count(Consulta.id).label("total")
    ).where(and_(*filters)).group_by(Consulta.status)

    result = await db.execute(stmt)
    counts = {r.status: r.total for r in result.all()}
    faltas = counts.get("falta", 0)
    total = sum(counts.values())
    canceladas = counts.get("cancelado", 0)
    denom = total - canceladas
    taxa = round((faltas / denom * 100) if denom > 0 else 0, 1)

    # Especialidade com maior falta
    esp_stmt = select(
        Especialidade.nome,
        func.count(Consulta.id).label("faltas")
    ).join(Consulta, Consulta.especialidade_id == Especialidade.id
    ).where(and_(Consulta.status == "falta", *filters)
    ).group_by(Especialidade.nome).order_by(func.count(Consulta.id).desc()).limit(1)
    esp_result = await db.execute(esp_stmt)
    esp_row = esp_result.first()

    # Município com maior falta
    mun_stmt = select(
        Consulta.paciente_municipio,
        func.count(Consulta.id).label("faltas")
    ).where(
        and_(Consulta.status == "falta", Consulta.paciente_municipio != None, *filters)
    ).group_by(Consulta.paciente_municipio).order_by(func.count(Consulta.id).desc()).limit(1)
    mun_result = await db.execute(mun_stmt)
    mun_row = mun_result.first()

    # Dia com maior falta
    dia_stmt = select(
        extract("dow", Consulta.data_hora).label("dia"),
        func.count(Consulta.id).label("faltas")
    ).where(and_(Consulta.status == "falta", *filters)
    ).group_by("dia").order_by(func.count(Consulta.id).desc()).limit(1)
    dia_result = await db.execute(dia_stmt)
    dia_row = dia_result.first()

    # Turno com maior falta
    from app.models.agenda import Agenda
    turno_stmt = select(
        Agenda.turno,
        func.count(Consulta.id).label("faltas")
    ).join(Consulta, Consulta.agenda_id == Agenda.id
    ).where(and_(Consulta.status == "falta", *filters)
    ).group_by(Agenda.turno).order_by(func.count(Consulta.id).desc()).limit(1)
    turno_result = await db.execute(turno_stmt)
    turno_row = turno_result.first()

    return ResumoAbsenteismo(
        total_faltas=faltas,
        taxa_absenteismo=taxa,
        especialidade_maior_falta=esp_row.nome if esp_row else "—",
        municipio_maior_falta=mun_row.paciente_municipio if mun_row else "—",
        dia_semana_maior_falta=DIAS_SEMANA[int(dia_row.dia) - 1] if dia_row else "—",
        turno_maior_falta=turno_row.turno if turno_row else "—",
    )


@router.get("/por-especialidade", response_model=list[AbsenteismoPorEspecialidade])
async def get_por_especialidade(
    competencia: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inicio, fim = parse_competencia(competencia)

    stmt = select(
        Especialidade.id,
        Especialidade.nome,
        Especialidade.cor,
        func.count(Consulta.id).label("total"),
        func.count(Consulta.id).filter(Consulta.status == "falta").label("faltas"),
    ).join(Consulta, Consulta.especialidade_id == Especialidade.id
    ).where(
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    ).group_by(Especialidade.id, Especialidade.nome, Especialidade.cor)

    result = await db.execute(stmt)
    return [
        AbsenteismoPorEspecialidade(
            especialidade_id=r.id,
            especialidade_nome=r.nome,
            cor=r.cor or "#3B82F6",
            total_agendadas=r.total or 0,
            total_faltas=r.faltas or 0,
            taxa=round((r.faltas / r.total * 100) if r.total else 0, 1),
        )
        for r in result.all()
    ]


@router.get("/por-municipio", response_model=list[AbsenteismoPorMunicipio])
async def get_por_municipio(
    competencia: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inicio, fim = parse_competencia(competencia)

    stmt = select(
        Consulta.paciente_municipio,
        func.count(Consulta.id).label("total"),
        func.count(Consulta.id).filter(Consulta.status == "falta").label("faltas"),
    ).where(
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
        Consulta.paciente_municipio != None,
    ).group_by(Consulta.paciente_municipio).order_by(func.count(Consulta.id).filter(Consulta.status == "falta").desc())

    result = await db.execute(stmt)
    return [
        AbsenteismoPorMunicipio(
            municipio=r.paciente_municipio or "Não informado",
            total_consultas=r.total or 0,
            total_faltas=r.faltas or 0,
            taxa=round((r.faltas / r.total * 100) if r.total else 0, 1),
        )
        for r in result.all()
    ]


@router.get("/por-dia-semana", response_model=list[AbsenteismoPorDia])
async def get_por_dia(
    competencia: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inicio, fim = parse_competencia(competencia)

    stmt = select(
        extract("dow", Consulta.data_hora).label("dia"),
        func.count(Consulta.id).label("total"),
        func.count(Consulta.id).filter(Consulta.status == "falta").label("faltas"),
    ).where(
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    ).group_by("dia").order_by("dia")

    result = await db.execute(stmt)
    return [
        AbsenteismoPorDia(
            dia_semana=int(r.dia),
            dia_nome=DIAS_SEMANA[int(r.dia) - 1] if 1 <= int(r.dia) <= 7 else "Dom",
            total_faltas=r.faltas or 0,
            taxa=round((r.faltas / r.total * 100) if r.total else 0, 1),
        )
        for r in result.all()
    ]


@router.get("/por-motivo", response_model=list[AbsenteismoPorMotivo])
async def get_por_motivo(
    competencia: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inicio, fim = parse_competencia(competencia)

    total_stmt = select(func.count(Consulta.id)).where(
        Consulta.status == "falta",
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    )
    total_result = await db.execute(total_stmt)
    total_faltas = total_result.scalar() or 1

    stmt = select(
        MotivoFalta.codigo,
        MotivoFalta.descricao,
        MotivoFalta.categoria,
        func.count(Consulta.id).label("total"),
    ).join(Consulta, Consulta.motivo_falta_id == MotivoFalta.id
    ).where(
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    ).group_by(MotivoFalta.codigo, MotivoFalta.descricao, MotivoFalta.categoria
    ).order_by(func.count(Consulta.id).desc())

    result = await db.execute(stmt)
    return [
        AbsenteismoPorMotivo(
            motivo_codigo=r.codigo,
            motivo_descricao=r.descricao,
            categoria=r.categoria,
            total=r.total,
            percentual=round(r.total / total_faltas * 100, 1),
        )
        for r in result.all()
    ]


@router.get("/tendencia", response_model=list[TendenciaAbsenteismo])
async def get_tendencia(
    meses: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    resultado = []

    for i in range(meses - 1, -1, -1):
        mes_ref = now.month - i
        ano_ref = now.year
        while mes_ref <= 0:
            mes_ref += 12
            ano_ref -= 1

        inicio = date(ano_ref, mes_ref, 1)
        fim = date(ano_ref, mes_ref, calendar.monthrange(ano_ref, mes_ref)[1])

        stmt = select(
            Consulta.status, func.count(Consulta.id).label("total")
        ).where(
            func.date(Consulta.data_hora) >= inicio,
            func.date(Consulta.data_hora) <= fim,
        ).group_by(Consulta.status)

        result = await db.execute(stmt)
        counts = {r.status: r.total for r in result.all()}
        faltas = counts.get("falta", 0)
        total = sum(counts.values())
        canceladas = counts.get("cancelado", 0)
        denom = total - canceladas
        taxa = round((faltas / denom * 100) if denom > 0 else 0, 1)

        resultado.append(TendenciaAbsenteismo(
            competencia=f"{ano_ref:04d}-{mes_ref:02d}",
            taxa=taxa,
            total_faltas=faltas,
        ))

    return resultado


@router.post("/registrar-falta")
async def registrar_falta(
    body: RegistrarFaltaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Consulta).where(Consulta.id == body.consulta_id))
    consulta = result.scalar_one_or_none()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    consulta.status = "falta"
    consulta.motivo_falta_id = body.motivo_falta_id
    if body.observacao:
        consulta.observacoes = body.observacao

    await db.commit()
    return {"mensagem": "Falta registrada"}


@router.get("/confirmacoes", response_model=list[ConfirmacaoPresencaResponse])
async def list_confirmacoes(
    status: Optional[str] = Query(None),
    data: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(
        ConfirmacaoPresenca,
        Consulta.paciente_codigo,
        Consulta.data_hora,
        Especialidade.nome.label("esp_nome"),
    ).join(Consulta, ConfirmacaoPresenca.consulta_id == Consulta.id
    ).join(Especialidade, Consulta.especialidade_id == Especialidade.id)

    filters = []
    if status:
        filters.append(ConfirmacaoPresenca.status == status)
    if data:
        filters.append(func.date(Consulta.data_hora) == data)
    if filters:
        stmt = stmt.where(and_(*filters))

    result = await db.execute(stmt)
    rows = result.all()

    return [
        ConfirmacaoPresencaResponse(
            id=row.ConfirmacaoPresenca.id,
            consulta_id=row.ConfirmacaoPresenca.consulta_id,
            canal=row.ConfirmacaoPresenca.canal,
            status=row.ConfirmacaoPresenca.status,
            tentativas=row.ConfirmacaoPresenca.tentativas,
            data_contato=str(row.ConfirmacaoPresenca.data_contato),
            paciente_codigo=row.paciente_codigo,
            especialidade_nome=row.esp_nome,
            data_consulta=str(row.data_hora),
        )
        for row in rows
    ]


@router.post("/confirmacoes", response_model=ConfirmacaoPresencaResponse, status_code=201)
async def create_confirmacao(
    body: ConfirmacaoPresencaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conf = ConfirmacaoPresenca(
        **body.model_dump(),
        user_id=current_user.id,
    )
    db.add(conf)
    await db.commit()
    await db.refresh(conf)
    return ConfirmacaoPresencaResponse(
        id=conf.id,
        consulta_id=conf.consulta_id,
        canal=conf.canal,
        status=conf.status,
        tentativas=conf.tentativas,
        data_contato=str(conf.data_contato),
    )
