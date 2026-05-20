import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Integer, Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MetaContratual(Base):
    __tablename__ = "metas_contratuais"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    especialidade_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("especialidades.id"), nullable=True)
    competencia: Mapped[date] = mapped_column(Date, nullable=False)
    meta_consultas: Mapped[int] = mapped_column(Integer, default=0)
    meta_procedimentos: Mapped[int] = mapped_column(Integer, default=0)
    meta_exames: Mapped[int] = mapped_column(Integer, default=0)
    meta_multiprofissional: Mapped[int] = mapped_column(Integer, default=0)
    valor_por_consulta: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("especialidade_id", "competencia"),)

    especialidade: Mapped["Especialidade | None"] = relationship("Especialidade", back_populates="metas")


class ProducaoMensal(Base):
    __tablename__ = "producao_mensal"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    especialidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("especialidades.id"), nullable=False)
    profissional_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=True)
    competencia: Mapped[date] = mapped_column(Date, nullable=False)
    consultas_realizadas: Mapped[int] = mapped_column(Integer, default=0)
    primeiras_consultas: Mapped[int] = mapped_column(Integer, default=0)
    retornos: Mapped[int] = mapped_column(Integer, default=0)
    procedimentos: Mapped[int] = mapped_column(Integer, default=0)
    exames: Mapped[int] = mapped_column(Integer, default=0)
    multiprofissional: Mapped[int] = mapped_column(Integer, default=0)
    altas: Mapped[int] = mapped_column(Integer, default=0)
    contrarreferencias: Mapped[int] = mapped_column(Integer, default=0)
    faltas: Mapped[int] = mapped_column(Integer, default=0)
    cancelamentos: Mapped[int] = mapped_column(Integer, default=0)
    pacientes_seguimento: Mapped[int] = mapped_column(Integer, default=0)

    especialidade: Mapped["Especialidade"] = relationship("Especialidade")
    profissional: Mapped["Profissional | None"] = relationship("Profissional")
