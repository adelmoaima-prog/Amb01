from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from datetime import date, datetime
from typing import Optional
import calendar

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.consulta import Consulta
from app.models.meta import MetaContratual
from app.models.especialidade import Especialidade
from app.models.profissional import Profissional
from app.schemas.dashboard import (
    KPIResumo, ProducaoPorEspecialidade, ProducaoPorProfissional,
    HistoricoMensal, Alerta, PrevisaoFechamento
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def parse_competencia(competencia: Optional[str]) -> tuple[int, int]:
    if competencia:
        parts = competencia.split("-")
        return int(parts[0]), int(parts[1])
    now = datetime.utcnow()
    return now.year, now.month


@router.get("/resumo", response_model=KPIResumo)
async def get_resumo(
    competencia: Optional[str] = Query(None, description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ano, mes = parse_competencia(competencia)
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)

    stmt = select(
        Consulta.status,
        func.count(Consulta.id).label("total")
    ).where(
        and_(
            func.date(Consulta.data_hora) >= inicio,
            func.date(Consulta.data_hora) <= fim,
        )
    ).group_by(Consulta.status)

    result = await db.execute(stmt)
    rows = result.all()
    counts = {r.status: r.total for r in rows}

    agendadas = sum(counts.values())
    realizadas = counts.get("realizado", 0)
    faltas = counts.get("falta", 0)
    canceladas = counts.get("cancelado", 0)

    denominator = agendadas - canceladas
    taxa_abs = round((faltas / denominator * 100) if denominator > 0 else 0, 1)

    meta_result = await db.execute(
        select(func.sum(MetaContratual.meta_consultas))
        .where(MetaContratual.competencia == inicio, MetaContratual.especialidade_id == None)
    )
    meta_global = meta_result.scalar() or 0

    if not meta_global:
        meta_result2 = await db.execute(
            select(func.sum(MetaContratual.meta_consultas))
            .where(MetaContratual.competencia == inicio)
        )
        meta_global = meta_result2.scalar() or 0

    taxa_meta = round((realizadas / meta_global * 100) if meta_global > 0 else 0, 1)

    today = datetime.utcnow().date()
    if today.year == ano and today.month == mes:
        dias_passados = today.day
        dias_totais = ultimo_dia
        media_diaria = realizadas / dias_passados if dias_passados > 0 else 0
        previsao = int(media_diaria * dias_totais)
    else:
        previsao = realizadas

    if taxa_meta >= 90:
        risco = "ok"
    elif taxa_meta >= 70:
        risco = "atencao"
    else:
        risco = "critico"

    return KPIResumo(
        total_agendadas=agendadas,
        total_realizadas=realizadas,
        total_faltas=faltas,
        total_canceladas=canceladas,
        taxa_absenteismo=taxa_abs,
        taxa_cumprimento_meta=taxa_meta,
        meta_mensal=int(meta_global),
        previsao_mes=previsao,
        risco_meta=risco,
    )


@router.get("/producao-especialidade", response_model=list[ProducaoPorEspecialidade])
async def get_producao_especialidade(
    competencia: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ano, mes = parse_competencia(competencia)
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)

    stmt = select(
        Especialidade.id,
        Especialidade.nome,
        Especialidade.cor,
        func.count(Consulta.id).filter(Consulta.status == "realizado").label("realizadas"),
    ).outerjoin(
        Consulta, and_(
            Consulta.especialidade_id == Especialidade.id,
            func.date(Consulta.data_hora) >= inicio,
            func.date(Consulta.data_hora) <= fim,
        )
    ).where(Especialidade.ativa == True).group_by(Especialidade.id, Especialidade.nome, Especialidade.cor)

    result = await db.execute(stmt)
    rows = result.all()

    meta_stmt = select(MetaContratual.especialidade_id, MetaContratual.meta_consultas).where(
        MetaContratual.competencia == inicio
    )
    meta_result = await db.execute(meta_stmt)
    metas = {str(r.especialidade_id): r.meta_consultas for r in meta_result.all()}

    output = []
    for r in rows:
        meta = metas.get(str(r.id), 0)
        pct = round((r.realizadas / meta * 100) if meta > 0 else 0, 1)
        output.append(ProducaoPorEspecialidade(
            especialidade_id=r.id,
            especialidade_nome=r.nome,
            especialidade_cor=r.cor or "#3B82F6",
            realizadas=r.realizadas or 0,
            meta=meta,
            percentual_meta=pct,
        ))

    return sorted(output, key=lambda x: x.realizadas, reverse=True)


@router.get("/producao-profissional", response_model=list[ProducaoPorProfissional])
async def get_producao_profissional(
    competencia: Optional[str] = Query(None),
    especialidade_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ano, mes = parse_competencia(competencia)
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)

    filters = [
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    ]
    if especialidade_id:
        filters.append(Consulta.especialidade_id == especialidade_id)

    stmt = select(
        Profissional.id,
        Profissional.nome,
        Especialidade.nome.label("especialidade_nome"),
        func.count(Consulta.id).filter(Consulta.status == "realizado").label("realizadas"),
        func.count(Consulta.id).filter(Consulta.status == "falta").label("faltas"),
    ).join(Consulta, Consulta.profissional_id == Profissional.id).join(
        Especialidade, Profissional.especialidade_id == Especialidade.id
    ).where(and_(*filters)).group_by(Profissional.id, Profissional.nome, Especialidade.nome)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        ProducaoPorProfissional(
            profissional_id=r.id,
            profissional_nome=r.nome,
            especialidade_nome=r.especialidade_nome,
            realizadas=r.realizadas or 0,
            faltas=r.faltas or 0,
        )
        for r in rows
    ]


@router.get("/historico-mensal", response_model=list[HistoricoMensal])
async def get_historico_mensal(
    meses: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    resultado = []

    for i in range(meses - 1, -1, -1):
        mes_ref = mes = now.month - i
        ano_ref = now.year
        while mes_ref <= 0:
            mes_ref += 12
            ano_ref -= 1

        inicio = date(ano_ref, mes_ref, 1)
        ultimo_dia = calendar.monthrange(ano_ref, mes_ref)[1]
        fim = date(ano_ref, mes_ref, ultimo_dia)

        stmt = select(
            Consulta.status, func.count(Consulta.id).label("total")
        ).where(
            func.date(Consulta.data_hora) >= inicio,
            func.date(Consulta.data_hora) <= fim,
        ).group_by(Consulta.status)

        result = await db.execute(stmt)
        counts = {r.status: r.total for r in result.all()}

        agendadas = sum(counts.values())
        realizadas = counts.get("realizado", 0)
        faltas = counts.get("falta", 0)
        denom = agendadas - counts.get("cancelado", 0)
        taxa = round((faltas / denom * 100) if denom > 0 else 0, 1)

        resultado.append(HistoricoMensal(
            competencia=f"{ano_ref:04d}-{mes_ref:02d}",
            realizadas=realizadas,
            agendadas=agendadas,
            faltas=faltas,
            taxa_absenteismo=taxa,
        ))

    return resultado


@router.get("/alertas", response_model=list[Alerta])
async def get_alertas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    inicio = date(now.year, now.month, 1)
    ultimo_dia = calendar.monthrange(now.year, now.month)[1]
    fim = date(now.year, now.month, ultimo_dia)

    alertas = []

    # Check absenteeism by specialty
    stmt = select(
        Especialidade.nome,
        func.count(Consulta.id).filter(Consulta.status == "falta").label("faltas"),
        func.count(Consulta.id).label("total"),
    ).join(Consulta, Consulta.especialidade_id == Especialidade.id).where(
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= fim,
    ).group_by(Especialidade.nome)

    result = await db.execute(stmt)
    for r in result.all():
        taxa = (r.faltas / r.total * 100) if r.total > 0 else 0
        if taxa > 30:
            alertas.append(Alerta(
                id=f"abs_{r.nome}",
                tipo="critico",
                titulo=f"Absenteísmo crítico — {r.nome}",
                descricao=f"Taxa de {taxa:.1f}% em {r.nome}. Acima do limite de 30%.",
                modulo="absenteismo",
            ))
        elif taxa > 20:
            alertas.append(Alerta(
                id=f"abs_atencao_{r.nome}",
                tipo="atencao",
                titulo=f"Absenteísmo elevado — {r.nome}",
                descricao=f"Taxa de {taxa:.1f}% em {r.nome}.",
                modulo="absenteismo",
            ))

    # Check meta compliance
    meta_stmt = select(
        Especialidade.nome,
        MetaContratual.meta_consultas,
        func.count(Consulta.id).filter(Consulta.status == "realizado").label("realizadas"),
    ).join(MetaContratual, MetaContratual.especialidade_id == Especialidade.id).outerjoin(
        Consulta, and_(
            Consulta.especialidade_id == Especialidade.id,
            func.date(Consulta.data_hora) >= inicio,
            func.date(Consulta.data_hora) <= fim,
        )
    ).where(MetaContratual.competencia == inicio).group_by(Especialidade.nome, MetaContratual.meta_consultas)

    meta_result = await db.execute(meta_stmt)
    today = now.date()
    dias_passados = today.day
    dias_totais = ultimo_dia
    fracao_mes = dias_passados / dias_totais

    for r in meta_result.all():
        if r.meta_consultas <= 0:
            continue
        meta_esperada_hoje = r.meta_consultas * fracao_mes
        pct_real = (r.realizadas / meta_esperada_hoje * 100) if meta_esperada_hoje > 0 else 100
        if pct_real < 70:
            alertas.append(Alerta(
                id=f"meta_{r.nome}",
                tipo="critico",
                titulo=f"Risco de meta — {r.nome}",
                descricao=f"Produção em {pct_real:.0f}% do esperado para a data. Meta: {r.meta_consultas} consultas.",
                modulo="painel",
            ))

    return alertas


@router.get("/previsao-fechamento", response_model=PrevisaoFechamento)
async def get_previsao(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    inicio = date(now.year, now.month, 1)
    ultimo_dia = calendar.monthrange(now.year, now.month)[1]
    fim = date(now.year, now.month, ultimo_dia)
    today = now.date()

    stmt = select(func.count(Consulta.id)).where(
        Consulta.status == "realizado",
        func.date(Consulta.data_hora) >= inicio,
        func.date(Consulta.data_hora) <= today,
    )
    result = await db.execute(stmt)
    realizadas = result.scalar() or 0

    meta_result = await db.execute(
        select(func.sum(MetaContratual.meta_consultas)).where(MetaContratual.competencia == inicio)
    )
    meta = int(meta_result.scalar() or 0)

    dias_passados = today.day
    dias_totais = ultimo_dia
    dias_restantes = dias_totais - dias_passados
    media_diaria = realizadas / dias_passados if dias_passados > 0 else 0
    previsao = int(realizadas + media_diaria * dias_restantes)
    pct = round((previsao / meta * 100) if meta > 0 else 0, 1)

    return PrevisaoFechamento(
        realizadas_ate_hoje=realizadas,
        meta_mensal=meta,
        dias_uteis_total=dias_totais,
        dias_uteis_restantes=dias_restantes,
        media_diaria=round(media_diaria, 1),
        previsao_final=previsao,
        percentual_projetado=pct,
        suficiente=pct >= 90,
    )
