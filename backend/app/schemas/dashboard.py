from pydantic import BaseModel
from typing import Optional
import uuid


class KPIResumo(BaseModel):
    total_agendadas: int
    total_realizadas: int
    total_faltas: int
    total_canceladas: int
    taxa_absenteismo: float
    taxa_cumprimento_meta: float
    meta_mensal: int
    previsao_mes: int
    risco_meta: str  # "ok", "atencao", "critico"


class ProducaoPorEspecialidade(BaseModel):
    especialidade_id: uuid.UUID
    especialidade_nome: str
    especialidade_cor: str
    realizadas: int
    meta: int
    percentual_meta: float


class ProducaoPorProfissional(BaseModel):
    profissional_id: uuid.UUID
    profissional_nome: str
    especialidade_nome: str
    realizadas: int
    faltas: int


class HistoricoMensal(BaseModel):
    competencia: str
    realizadas: int
    agendadas: int
    faltas: int
    taxa_absenteismo: float


class Alerta(BaseModel):
    id: str
    tipo: str  # "critico", "atencao", "info"
    titulo: str
    descricao: str
    modulo: str


class PrevisaoFechamento(BaseModel):
    realizadas_ate_hoje: int
    meta_mensal: int
    dias_uteis_total: int
    dias_uteis_restantes: int
    media_diaria: float
    previsao_final: int
    percentual_projetado: float
    suficiente: bool
