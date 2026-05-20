import uuid
from datetime import datetime, date, time
from sqlalchemy import String, Boolean, DateTime, Date, Time, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EscalaMedica(Base):
    __tablename__ = "escala_medica"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profissional_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=False)
    agenda_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agendas.id"), nullable=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    turno: Mapped[str] = mapped_column(String(20), nullable=False)
    hora_inicio: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_fim: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="confirmado")
    substituto_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    profissional: Mapped["Profissional"] = relationship("Profissional", back_populates="escalas", foreign_keys=[profissional_id])
    substituto: Mapped["Profissional | None"] = relationship("Profissional", foreign_keys=[substituto_id])
    agenda: Mapped["Agenda | None"] = relationship("Agenda", back_populates="escalas")
    alteracoes: Mapped[list["AlteracaoEscala"]] = relationship("AlteracaoEscala", back_populates="escala")


class AlteracaoEscala(Base):
    __tablename__ = "alteracoes_escala"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escala_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("escala_medica.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tipo_alteracao: Mapped[str] = mapped_column(String(50), nullable=False)
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    pacientes_impactados: Mapped[int] = mapped_column(Integer, default=0)
    producao_perdida: Mapped[int] = mapped_column(Integer, default=0)
    data_alteracao: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    dados_anteriores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dados_novos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    escala: Mapped["EscalaMedica"] = relationship("EscalaMedica", back_populates="alteracoes")
    user: Mapped["User"] = relationship("User")
