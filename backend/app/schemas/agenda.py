from pydantic import BaseModel
from typing import Optional
from datetime import date, time
import uuid


class AgendaBase(BaseModel):
    especialidade_id: uuid.UUID
    profissional_id: uuid.UUID
    consultorio_id: Optional[uuid.UUID] = None
    turno: str
    dia_semana: int
    hora_inicio: time
    hora_fim: time
    intervalo_minutos: int = 30
    vagas_total: int
    vagas_reserva: int = 0
    data_inicio: date
    data_fim: Optional[date] = None
    observacoes: Optional[str] = None


class AgendaCreate(AgendaBase):
    pass


class AgendaUpdate(BaseModel):
    status: Optional[str] = None
    vagas_total: Optional[int] = None
    consultorio_id: Optional[uuid.UUID] = None
    observacoes: Optional[str] = None


class AgendaResponse(AgendaBase):
    id: uuid.UUID
    status: str
    especialidade_nome: Optional[str] = None
    profissional_nome: Optional[str] = None
    consultorio_numero: Optional[str] = None

    class Config:
        from_attributes = True


class EscalaBase(BaseModel):
    profissional_id: uuid.UUID
    agenda_id: Optional[uuid.UUID] = None
    data: date
    turno: str
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None
    status: str = "confirmado"


class EscalaCreate(EscalaBase):
    pass


class EscalaUpdate(BaseModel):
    status: Optional[str] = None
    substituto_id: Optional[uuid.UUID] = None
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None
    justificativa: Optional[str] = None
    tipo_alteracao: Optional[str] = None


class EscalaResponse(EscalaBase):
    id: uuid.UUID
    profissional_nome: Optional[str] = None
    especialidade_nome: Optional[str] = None
    substituto_nome: Optional[str] = None
    num_alteracoes: int = 0

    class Config:
        from_attributes = True


class AlteracaoEscalaResponse(BaseModel):
    id: uuid.UUID
    tipo_alteracao: str
    justificativa: str
    pacientes_impactados: int
    producao_perdida: int
    data_alteracao: str
    user_nome: Optional[str] = None

    class Config:
        from_attributes = True


class ImpactoEscala(BaseModel):
    pacientes_agendados: int
    vagas_abertas: int
    producao_estimada_perdida: int
    especialidade_nome: str
    data: str
    turno: str
