import uuid
from datetime import datetime, date, time
from sqlalchemy import String, Boolean, DateTime, Integer, Date, Time, ForeignKey, Text, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Agenda(Base):
    __tablename__ = "agendas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    especialidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("especialidades.id"), nullable=False)
    profissional_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=False)
    consultorio_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("consultorios.id"), nullable=True)
    turno: Mapped[str] = mapped_column(String(20), nullable=False)
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[time] = mapped_column(Time, nullable=False)
    intervalo_minutos: Mapped[int] = mapped_column(Integer, default=30)
    vagas_total: Mapped[int] = mapped_column(Integer, nullable=False)
    vagas_reserva: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="aberta")
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    especialidade: Mapped["Especialidade"] = relationship("Especialidade", back_populates="agendas")
    profissional: Mapped["Profissional"] = relationship("Profissional", back_populates="agendas")
    consultorio: Mapped["Consultorio | None"] = relationship("Consultorio", back_populates="agendas")
    escalas: Mapped[list["EscalaMedica"]] = relationship("EscalaMedica", back_populates="agenda")
    consultas: Mapped[list["Consulta"]] = relationship("Consulta", back_populates="agenda")
