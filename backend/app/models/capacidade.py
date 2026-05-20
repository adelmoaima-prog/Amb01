import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Integer, Date, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CapacidadeTurno(Base):
    __tablename__ = "capacidade_turnos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    turno: Mapped[str] = mapped_column(String(20), nullable=False)
    consultorio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("consultorios.id"), nullable=False)
    agenda_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agendas.id"), nullable=True)
    profissional_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=True)
    vagas_ofertadas: Mapped[int] = mapped_column(Integer, default=0)
    vagas_ocupadas: Mapped[int] = mapped_column(Integer, default=0)
    status_sala: Mapped[str] = mapped_column(String(30), default="disponivel")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("data", "turno", "consultorio_id"),)

    consultorio: Mapped["Consultorio"] = relationship("Consultorio", back_populates="capacidade_turnos")
    agenda: Mapped["Agenda | None"] = relationship("Agenda")
    profissional: Mapped["Profissional | None"] = relationship("Profissional")
