from pydantic import BaseModel
from typing import Optional
import uuid


class ResumoCapacidade(BaseModel):
    consultorios_total: int
    consultorios_ativos: int
    consultorios_ocupados: int
    consultorios_ociosos: int
    taxa_ocupacao: float
    profissionais_escalados: int
    profissionais_disponiveis: int


class ConsultorioStatus(BaseModel):
    id: uuid.UUID
    numero: str
    nome: Optional[str]
    andar: int
    tipo: str
    status: str  # "ocupado", "ocioso", "disponivel", "manutencao"
    turno_atual: Optional[str]
    profissional_atual: Optional[str]
    especialidade_atual: Optional[str]
    vagas_ofertadas: int
    vagas_ocupadas: int


class OcupacaoPorTurno(BaseModel):
    turno: str
    consultorios_disponiveis: int
    consultorios_ocupados: int
    vagas_ofertadas: int
    vagas_ocupadas: int
    taxa_ocupacao: float


class EquipeEscalada(BaseModel):
    data: str
    turno: str
    medicos: int
    enfermeiros: int
    tecnicos: int
    recepcionistas: int
    total_equipe: int
    capacidade_maxima: int


class SimulacaoCapacidade(BaseModel):
    nova_especialidade: str
    vagas_solicitadas: int
    turno: str
    consultorios_disponiveis: int
    consultorio_sugerido: Optional[str]
    viavel: bool
    impacto_taxa_ocupacao: float
    requer_nova_equipe: bool
