import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Especialidade(Base):
    __tablename__ = "especialidades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sigla: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    cor: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    meta_mensal: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    profissionais: Mapped[list["Profissional"]] = relationship("Profissional", back_populates="especialidade")
    agendas: Mapped[list["Agenda"]] = relationship("Agenda", back_populates="especialidade")
    consultas: Mapped[list["Consulta"]] = relationship("Consulta", back_populates="especialidade")
    metas: Mapped[list["MetaContratual"]] = relationship("MetaContratual", back_populates="especialidade")
