from pydantic import BaseModel
from typing import Optional, Any
from datetime import date
import uuid


class GerarRelatorioRequest(BaseModel):
    tipo: str
    periodo_inicio: date
    periodo_fim: date
    especialidade_id: Optional[uuid.UUID] = None
    profissional_id: Optional[uuid.UUID] = None
    formato: str = "pdf"
    parametros: dict = {}


class RelatorioGeradoResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    status: str
    periodo_inicio: Optional[date]
    periodo_fim: Optional[date]
    arquivo_pdf: Optional[str]
    arquivo_csv: Optional[str]
    created_at: str
    finalizado_at: Optional[str]
    user_nome: Optional[str]

    class Config:
        from_attributes = True


class ConfiguracaoRelatorioCreate(BaseModel):
    nome: str
    tipo: str
    parametros: dict = {}
    agendamento: str = "manual"


class ConfiguracaoRelatorioResponse(ConfiguracaoRelatorioCreate):
    id: uuid.UUID
    created_at: str

    class Config:
        from_attributes = True
