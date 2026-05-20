from pydantic import BaseModel
from typing import Optional
import uuid


class ResumoAbsenteismo(BaseModel):
    total_faltas: int
    taxa_absenteismo: float
    especialidade_maior_falta: str
    municipio_maior_falta: str
    dia_semana_maior_falta: str
    turno_maior_falta: str


class AbsenteismoPorEspecialidade(BaseModel):
    especialidade_id: uuid.UUID
    especialidade_nome: str
    cor: str
    total_agendadas: int
    total_faltas: int
    taxa: float


class AbsenteismoPorMunicipio(BaseModel):
    municipio: str
    total_consultas: int
    total_faltas: int
    taxa: float


class AbsenteismoPorDia(BaseModel):
    dia_semana: int
    dia_nome: str
    total_faltas: int
    taxa: float


class AbsenteismoPorTurno(BaseModel):
    turno: str
    total_faltas: int
    taxa: float


class AbsenteismoPorMotivo(BaseModel):
    motivo_codigo: str
    motivo_descricao: str
    categoria: str
    total: int
    percentual: float


class TendenciaAbsenteismo(BaseModel):
    competencia: str
    taxa: float
    total_faltas: int


class RegistrarFaltaRequest(BaseModel):
    consulta_id: uuid.UUID
    motivo_falta_id: uuid.UUID
    observacao: Optional[str] = None


class ConfirmacaoPresencaCreate(BaseModel):
    consulta_id: uuid.UUID
    canal: str
    status: str
    tentativas: int = 1
    observacao: Optional[str] = None


class ConfirmacaoPresencaResponse(BaseModel):
    id: uuid.UUID
    consulta_id: uuid.UUID
    canal: str
    status: str
    tentativas: int
    data_contato: str
    paciente_codigo: Optional[str] = None
    especialidade_nome: Optional[str] = None
    data_consulta: Optional[str] = None

    class Config:
        from_attributes = True
