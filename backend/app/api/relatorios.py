from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import os
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.relatorio import RelatorioGerado, ConfiguracaoRelatorio
from app.schemas.relatorio import (
    GerarRelatorioRequest, RelatorioGeradoResponse,
    ConfiguracaoRelatorioCreate, ConfiguracaoRelatorioResponse,
)
from app.config import settings

router = APIRouter(prefix="/relatorios", tags=["relatorios"])


async def _gerar_relatorio_task(relatorio_id: str, parametros: dict, db_url: str):
    """Background task to generate report files."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    import csv
    import io

    engine = create_async_engine(db_url)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        result = await session.execute(select(RelatorioGerado).where(RelatorioGerado.id == relatorio_id))
        rel = result.scalar_one_or_none()
        if not rel:
            return

        try:
            rel.status = "processando"
            await session.commit()

            os.makedirs(settings.REPORTS_DIR, exist_ok=True)

            pdf_path = os.path.join(settings.REPORTS_DIR, f"{relatorio_id}.pdf")
            csv_path = os.path.join(settings.REPORTS_DIR, f"{relatorio_id}.csv")

            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            title = Paragraph(f"<b>HUC Ambulatorial — {parametros.get('tipo', 'Relatório').replace('_', ' ').title()}</b>", styles["Title"])
            elements.append(title)
            elements.append(Spacer(1, 12))

            periodo = Paragraph(f"Período: {parametros.get('periodo_inicio', '')} a {parametros.get('periodo_fim', '')}", styles["Normal"])
            elements.append(periodo)
            elements.append(Spacer(1, 12))

            gerado = Paragraph(f"Gerado em: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}", styles["Normal"])
            elements.append(gerado)
            elements.append(Spacer(1, 24))

            note = Paragraph("Relatório gerado pelo Sistema de Inteligência Ambulatorial — HUC. Dados anonimizados para fins acadêmicos/gerenciais.", styles["Normal"])
            elements.append(note)

            doc.build(elements)

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["tipo", "periodo_inicio", "periodo_fim", "gerado_em"])
                writer.writerow([
                    parametros.get("tipo", ""),
                    parametros.get("periodo_inicio", ""),
                    parametros.get("periodo_fim", ""),
                    datetime.utcnow().isoformat(),
                ])

            rel.arquivo_pdf = pdf_path
            rel.arquivo_csv = csv_path
            rel.status = "pronto"
            rel.finalizado_at = datetime.utcnow()
            await session.commit()

        except Exception as e:
            rel.status = "erro"
            await session.commit()

    await engine.dispose()


@router.post("/gerar", response_model=RelatorioGeradoResponse, status_code=202)
async def gerar_relatorio(
    body: GerarRelatorioRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rel = RelatorioGerado(
        tipo=body.tipo,
        periodo_inicio=body.periodo_inicio,
        periodo_fim=body.periodo_fim,
        parametros={
            "tipo": body.tipo,
            "periodo_inicio": str(body.periodo_inicio),
            "periodo_fim": str(body.periodo_fim),
            "especialidade_id": str(body.especialidade_id) if body.especialidade_id else None,
            **body.parametros,
        },
        status="pendente",
        user_id=current_user.id,
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)

    background_tasks.add_task(
        _gerar_relatorio_task,
        str(rel.id),
        rel.parametros,
        settings.DATABASE_URL,
    )

    return RelatorioGeradoResponse(
        id=rel.id,
        tipo=rel.tipo,
        status=rel.status,
        periodo_inicio=rel.periodo_inicio,
        periodo_fim=rel.periodo_fim,
        arquivo_pdf=None,
        arquivo_csv=None,
        created_at=str(rel.created_at),
        finalizado_at=None,
        user_nome=current_user.nome,
    )


@router.get("/gerados", response_model=list[RelatorioGeradoResponse])
async def list_relatorios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(RelatorioGerado, User.nome.label("user_nome")).join(
        User, RelatorioGerado.user_id == User.id
    ).order_by(RelatorioGerado.created_at.desc())

    result = await db.execute(stmt)
    rows = result.all()

    return [
        RelatorioGeradoResponse(
            id=r.RelatorioGerado.id,
            tipo=r.RelatorioGerado.tipo,
            status=r.RelatorioGerado.status,
            periodo_inicio=r.RelatorioGerado.periodo_inicio,
            periodo_fim=r.RelatorioGerado.periodo_fim,
            arquivo_pdf=f"/api/relatorios/gerados/{r.RelatorioGerado.id}/download/pdf" if r.RelatorioGerado.arquivo_pdf else None,
            arquivo_csv=f"/api/relatorios/gerados/{r.RelatorioGerado.id}/download/csv" if r.RelatorioGerado.arquivo_csv else None,
            created_at=str(r.RelatorioGerado.created_at),
            finalizado_at=str(r.RelatorioGerado.finalizado_at) if r.RelatorioGerado.finalizado_at else None,
            user_nome=r.user_nome,
        )
        for r in rows
    ]


@router.get("/gerados/{relatorio_id}", response_model=RelatorioGeradoResponse)
async def get_relatorio(
    relatorio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RelatorioGerado, User.nome.label("user_nome"))
        .join(User, RelatorioGerado.user_id == User.id)
        .where(RelatorioGerado.id == relatorio_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    return RelatorioGeradoResponse(
        id=row.RelatorioGerado.id,
        tipo=row.RelatorioGerado.tipo,
        status=row.RelatorioGerado.status,
        periodo_inicio=row.RelatorioGerado.periodo_inicio,
        periodo_fim=row.RelatorioGerado.periodo_fim,
        arquivo_pdf=f"/api/relatorios/gerados/{row.RelatorioGerado.id}/download/pdf" if row.RelatorioGerado.arquivo_pdf else None,
        arquivo_csv=f"/api/relatorios/gerados/{row.RelatorioGerado.id}/download/csv" if row.RelatorioGerado.arquivo_csv else None,
        created_at=str(row.RelatorioGerado.created_at),
        finalizado_at=str(row.RelatorioGerado.finalizado_at) if row.RelatorioGerado.finalizado_at else None,
        user_nome=row.user_nome,
    )


@router.get("/gerados/{relatorio_id}/download/pdf")
async def download_pdf(
    relatorio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RelatorioGerado).where(RelatorioGerado.id == relatorio_id))
    rel = result.scalar_one_or_none()
    if not rel or not rel.arquivo_pdf or not os.path.exists(rel.arquivo_pdf):
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado")
    return FileResponse(rel.arquivo_pdf, media_type="application/pdf", filename=f"relatorio_{relatorio_id}.pdf")


@router.get("/gerados/{relatorio_id}/download/csv")
async def download_csv(
    relatorio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RelatorioGerado).where(RelatorioGerado.id == relatorio_id))
    rel = result.scalar_one_or_none()
    if not rel or not rel.arquivo_csv or not os.path.exists(rel.arquivo_csv):
        raise HTTPException(status_code=404, detail="Arquivo CSV não encontrado")
    return FileResponse(rel.arquivo_csv, media_type="text/csv", filename=f"relatorio_{relatorio_id}.csv")


@router.post("/configuracoes", response_model=ConfiguracaoRelatorioResponse, status_code=201)
async def create_config(
    body: ConfiguracaoRelatorioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = ConfiguracaoRelatorio(**body.model_dump(), user_id=current_user.id)
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return ConfiguracaoRelatorioResponse(
        **body.model_dump(),
        id=config.id,
        created_at=str(config.created_at),
    )


@router.get("/configuracoes", response_model=list[ConfiguracaoRelatorioResponse])
async def list_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ConfiguracaoRelatorio).order_by(ConfiguracaoRelatorio.created_at.desc()))
    configs = result.scalars().all()
    return [
        ConfiguracaoRelatorioResponse(
            id=c.id,
            nome=c.nome,
            tipo=c.tipo,
            parametros=c.parametros,
            agendamento=c.agendamento,
            created_at=str(c.created_at),
        )
        for c in configs
    ]
