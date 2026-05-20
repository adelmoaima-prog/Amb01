from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, datetime
from typing import Optional
import calendar

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.consulta import Consulta
from app.models.especialidade import Especialidade
from app.models.profissional import Profissional
from app.models.meta import MetaContratual
from app.schemas.producao import (
    ResumoProducao, ProducaoPorEspecialidadeDetalhe,
    ProducaoPorProfissionalDetalhe, TipoConsultaDistribuicao,
    ComparativoMensal, SeguimentoPaciente,
)

router = APIRouter(prefix="/producao", tags=["producao"])


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


@router.get("/resumo", response_model=ResumoProducao)
async def get_resumo(
    competencia: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inicio, fim = parse_competencia(competencia)

    base = and_(
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
        Consulta.status == "realizado",
    )

    stmt = select(
        func.count(Consulta.id).label("total"),
        func.count(Consulta.id).filter(Consulta.tipo_atendimento == "medico").label("medicas"),
        func.count(Consulta.id).filter(Consulta.tipo_atendimento == "multiprofissional").label("multi"),
        func.count(Consulta.id).filter(Consulta.tipo_atendimento == "procedimento").label("proced"),
        func.count(Consulta.id).filter(Consulta.tipo_atendimento == "exame").label("exames"),
        func.count(Consulta.id).filter(Consulta.tipo_consulta == "primeira_consulta").label("primeiras"),
        func.count(Consulta.id).filter(Consulta.tipo_consulta == "retorno").label("retornos"),
        func.count(Consulta.id).filter(Consulta.foi_alta == True).label("altas"),
        func.count(Consulta.id).filter(Consulta.foi_contrarreferencia == True).label("contrarrefs"),
        func.count(Consulta.id).filter(Consulta.em_seguimento == True).label("seguimento"),
    ).where(base)

    result = await db.execute(stmt)
    r = result.first()

    return ResumoProducao(
        total_realizadas=r.total or 0,
        consultas_medicas=r.medicas or 0,
        multiprofissional=r.multi or 0,
        procedimentos=r.proced or 0,
        exames=r.exames or 0,
        primeiras_consultas=r.primeiras or 0,
        retornos=r.retornos or 0,
        altas=r.altas or 0,
        contrarreferencias=r.contrarrefs or 0,
        em_seguimento=r.seguimento or 0,
    )


@router.get("/por-especialidade", response_model=list[ProducaoPorEspecialidadeDetalhe])
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
        func.count(Consulta.id).filter(Consulta.status == "realizado").label("realizadas"),
        func.count(Consulta.id).filter(and_(Consulta.status == "realizado", Consulta.tipo_consulta == "primeira_consulta")).label("primeiras"),
        func.count(Consulta.id).filter(and_(Consulta.status == "realizado", Consulta.tipo_consulta == "retorno")).label("retornos"),
        func.count(Consulta.id).filter(and_(Consulta.status == "realizado", Consulta.tipo_atendimento == "procedimento")).label("proced"),
        func.count(Consulta.id).filter(and_(Consulta.status == "realizado", Consulta.foi_alta == True)).label("altas"),
        func.count(Consulta.id).filter(and_(Consulta.status == "realizado", Consulta.foi_contrarreferencia == True)).label("contrarrefs"),
    ).outerjoin(
        Consulta, and_(
            Consulta.especialidade_id == Especialidade.id,
            func.date(Consulta.data_hora) >= inicio,
            func.date(Consulta.data_hora) <= fim,
        )
    ).where(Especialidade.ativa == True
    ).group_by(Especialidade.id, Especialidade.nome, Especialidade.cor)

    result = await db.execute(stmt)
    rows = result.all()

    meta_stmt = select(MetaContratual.especialidade_id, MetaContratual.meta_consultas).where(
        MetaContratual.competencia == inicio
    )
    meta_result = await db.execute(meta_stmt)
    metas = {str(r.especialidade_id): r.meta_consultas for r in meta_result.all()}

    return [
        ProducaoPorEspecialidadeDetalhe(
            especialidade_id=r.id,
            especialidade_nome=r.nome,
            cor=r.cor or "#3B82F6",
            realizadas=r.realizadas or 0,
            primeiras=r.primeiras or 0,
            retornos=r.retornos or 0,
            procedimentos=r.proced or 0,
            altas=r.altas or 0,
            contrarreferencias=r.contrarrefs or 0,
            meta=metas.get(str(r.id), 0),
            percentual_meta=round((r.realizadas or 0) / metas.get(str(r.id), 1) * 100 if metas.get(str(r.id), 0) > 0 else 0, 1),
        )
        for r in rows
    ]


@router.get("/por-profissional", response_model=list[ProducaoPorProfissionalDetalhe])
async def get_por_profissional(
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
        filters.append(Profissional.especialidade_id == especialidade_id)

    stmt = select(
        Profissional.id,
        Profissional.nome,
        Profissional.crm,
        Especialidade.nome.label("esp_nome"),
        func.count(Consulta.id).filter(Consulta.status == "realizado").label("realizadas"),
        func.count(Consulta.id).filter(Consulta.status == "falta").label("faltas"),
        func.count(Consulta.id).filter(and_(Consulta.status == "realizado", Consulta.tipo_consulta == "primeira_consulta")).label("primeiras"),
        func.count(Consulta.id).filter(and_(Consulta.status == "realizado", Consulta.tipo_consulta == "retorno")).label("retornos"),
    ).join(Consulta, Consulta.profissional_id == Profissional.id
    ).join(Especialidade, Profissional.especialidade_id == Especialidade.id
    ).where(and_(*filters)
    ).group_by(Profissional.id, Profissional.nome, Profissional.crm, Especialidade.nome
    ).order_by(func.count(Consulta.id).filter(Consulta.status == "realizado").desc())

    result = await db.execute(stmt)
    return [
        ProducaoPorProfissionalDetalhe(
            profissional_id=r.id,
            profissional_nome=r.nome,
            crm=r.crm,
            especialidade_nome=r.esp_nome,
            realizadas=r.realizadas or 0,
            faltas=r.faltas or 0,
            taxa_falta=round((r.faltas / (r.realizadas + r.faltas) * 100) if (r.realizadas + r.faltas) > 0 else 0, 1),
            primeiras=r.primeiras or 0,
            retornos=r.retornos or 0,
        )
        for r in result.all()
    ]


@router.get("/tipos-consulta", response_model=list[TipoConsultaDistribuicao])
async def get_tipos(
    competencia: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inicio, fim = parse_competencia(competencia)

    total_stmt = select(func.count(Consulta.id)).where(
        Consulta.status == "realizado",
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    )
    total_r = await db.execute(total_stmt)
    total = total_r.scalar() or 1

    stmt = select(
        Consulta.tipo_consulta,
        func.count(Consulta.id).label("total"),
    ).where(
        Consulta.status == "realizado",
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    ).group_by(Consulta.tipo_consulta)

    result = await db.execute(stmt)
    return [
        TipoConsultaDistribuicao(
            tipo=r.tipo_consulta,
            total=r.total,
            percentual=round(r.total / total * 100, 1),
        )
        for r in result.all()
    ]


@router.get("/seguimento", response_model=list[SeguimentoPaciente])
async def get_seguimento(
    especialidade_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(
        Especialidade.nome,
        func.count(Consulta.id).filter(Consulta.em_seguimento == True).label("seguimento"),
        func.count(Consulta.id).filter(Consulta.foi_alta == True).label("altas"),
        func.count(Consulta.id).filter(Consulta.foi_contrarreferencia == True).label("contrarrefs"),
    ).join(Consulta, Consulta.especialidade_id == Especialidade.id
    ).where(Consulta.status == "realizado")

    if especialidade_id:
        stmt = stmt.where(Consulta.especialidade_id == especialidade_id)

    stmt = stmt.group_by(Especialidade.nome)
    result = await db.execute(stmt)

    return [
        SeguimentoPaciente(
            especialidade_nome=r.nome,
            em_seguimento=r.seguimento or 0,
            com_alta=r.altas or 0,
            com_contrarreferencia=r.contrarrefs or 0,
            percentual_alta=round(r.altas / (r.seguimento + r.altas + r.contrarrefs) * 100 if (r.seguimento + r.altas + r.contrarrefs) > 0 else 0, 1),
        )
        for r in result.all()
    ]
