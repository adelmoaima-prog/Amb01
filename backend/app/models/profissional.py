import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Profissional(Base):
    __tablename__ = "profissionais"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cpf_enc: Mapped[str | None] = mapped_column(String(500), nullable=True)
    crm: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    conselho_numero: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tipo: Mapped[str] = mapped_column(String(50), default="medico")
    especialidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("especialidades.id"), nullable=False)
    carga_horaria: Mapped[int] = mapped_column(Integer, default=20)
    turno_preferencial: Mapped[str] = mapped_column(String(20), default="manha")
    municipio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    especialidade: Mapped["Especialidade"] = relationship("Especialidade", back_populates="profissionais")
    agendas: Mapped[list["Agenda"]] = relationship("Agenda", back_populates="profissional")
    escalas: Mapped[list["EscalaMedica"]] = relationship("EscalaMedica", back_populates="profissional", foreign_keys="EscalaMedica.profissional_id")
    consultas: Mapped[list["Consulta"]] = relationship("Consulta", back_populates="profissional")
