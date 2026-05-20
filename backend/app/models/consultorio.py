import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Consultorio(Base):
    __tablename__ = "consultorios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    andar: Mapped[int] = mapped_column(Integer, default=1)
    bloco: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tipo: Mapped[str] = mapped_column(String(50), default="consultorio")
    equipamentos: Mapped[list] = mapped_column(JSONB, default=list)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    agendas: Mapped[list["Agenda"]] = relationship("Agenda", back_populates="consultorio")
    capacidade_turnos: Mapped[list["CapacidadeTurno"]] = relationship("CapacidadeTurno", back_populates="consultorio")
