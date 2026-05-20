from pydantic import BaseModel
from typing import Optional
import uuid


class ResumoProducao(BaseModel):
    total_realizadas: int
    consultas_medicas: int
    multiprofissional: int
    procedimentos: int
    exames: int
    primeiras_consultas: int
    retornos: int
    altas: int
    contrarreferencias: int
    em_seguimento: int


class ProducaoPorEspecialidadeDetalhe(BaseModel):
    especialidade_id: uuid.UUID
    especialidade_nome: str
    cor: str
    realizadas: int
    primeiras: int
    retornos: int
    procedimentos: int
    altas: int
    contrarreferencias: int
    meta: int
    percentual_meta: float


class ProducaoPorProfissionalDetalhe(BaseModel):
    profissional_id: uuid.UUID
    profissional_nome: str
    crm: Optional[str]
    especialidade_nome: str
    realizadas: int
    faltas: int
    taxa_falta: float
    primeiras: int
    retornos: int


class TipoConsultaDistribuicao(BaseModel):
    tipo: str
    total: int
    percentual: float


class ComparativoMensal(BaseModel):
    mes_atual: int
    mes_anterior: int
    variacao_percentual: float


class SeguimentoPaciente(BaseModel):
    especialidade_nome: str
    em_seguimento: int
    com_alta: int
    com_contrarreferencia: int
    percentual_alta: float
