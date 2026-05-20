import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ConfiguracaoRelatorio(Base):
    __tablename__ = "configuracoes_relatorio"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    parametros: Mapped[dict] = mapped_column(JSONB, default=dict)
    agendamento: Mapped[str] = mapped_column(String(50), default="manual")
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship("User")
    relatorios: Mapped[list["RelatorioGerado"]] = relationship("RelatorioGerado", back_populates="configuracao")


class RelatorioGerado(Base):
    __tablename__ = "relatorios_gerados"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    configuracao_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("configuracoes_relatorio.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    periodo_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    periodo_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    parametros: Mapped[dict] = mapped_column(JSONB, default=dict)
    arquivo_pdf: Mapped[str | None] = mapped_column(Text, nullable=True)
    arquivo_csv: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pendente")
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finalizado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    configuracao: Mapped["ConfiguracaoRelatorio | None"] = relationship("ConfiguracaoRelatorio", back_populates="relatorios")
    user: Mapped["User"] = relationship("User")
