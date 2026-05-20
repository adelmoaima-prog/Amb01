from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.especialidade import Especialidade
from app.models.profissional import Profissional
from app.models.consultorio import Consultorio
from app.models.consulta import MotivoFalta

router = APIRouter(prefix="/recursos", tags=["recursos"])


@router.get("/especialidades")
async def list_especialidades(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Especialidade).where(Especialidade.ativa == True).order_by(Especialidade.nome)
    )
    return [
        {"id": str(e.id), "nome": e.nome, "sigla": e.sigla, "cor": e.cor, "meta_mensal": e.meta_mensal}
        for e in result.scalars().all()
    ]


@router.get("/profissionais")
async def list_profissionais(
    especialidade_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Profissional, Especialidade.nome.label("esp_nome")).join(
        Especialidade, Profissional.especialidade_id == Especialidade.id
    ).where(Profissional.ativo == True)
    if especialidade_id:
        stmt = stmt.where(Profissional.especialidade_id == especialidade_id)
    stmt = stmt.order_by(Profissional.nome)
    result = await db.execute(stmt)
    return [
        {
            "id": str(row.Profissional.id),
            "nome": row.Profissional.nome,
            "crm": row.Profissional.crm,
            "tipo": row.Profissional.tipo,
            "especialidade_id": str(row.Profissional.especialidade_id),
            "especialidade_nome": row.esp_nome,
            "turno_preferencial": row.Profissional.turno_preferencial,
        }
        for row in result.all()
    ]


@router.get("/consultorios")
async def list_consultorios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Consultorio).where(Consultorio.ativo == True).order_by(Consultorio.andar, Consultorio.numero)
    )
    return [
        {"id": str(c.id), "numero": c.numero, "nome": c.nome, "andar": c.andar, "tipo": c.tipo}
        for c in result.scalars().all()
    ]


@router.get("/motivos-falta")
async def list_motivos_falta(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MotivoFalta).where(MotivoFalta.ativo == True).order_by(MotivoFalta.codigo)
    )
    return [
        {"id": str(m.id), "codigo": m.codigo, "descricao": m.descricao, "categoria": m.categoria}
        for m in result.scalars().all()
    ]
