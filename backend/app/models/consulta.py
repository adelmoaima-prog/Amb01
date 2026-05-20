import uuid
from datetime import datetime, time
from sqlalchemy import String, Boolean, DateTime, Time, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MotivoFalta(Base):
    __tablename__ = "motivos_falta"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), default="outros")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    consultas: Mapped[list["Consulta"]] = relationship("Consulta", back_populates="motivo_falta")


class Consulta(Base):
    __tablename__ = "consultas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agenda_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agendas.id"), nullable=True)
    profissional_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=False)
    especialidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("especialidades.id"), nullable=False)
    consultorio_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("consultorios.id"), nullable=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tipo_consulta: Mapped[str] = mapped_column(String(50), default="primeira_consulta")
    tipo_atendimento: Mapped[str] = mapped_column(String(50), default="medico")
    paciente_codigo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    paciente_municipio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    paciente_idade_faixa: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="agendado")
    motivo_falta_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("motivos_falta.id"), nullable=True)
    hora_chegada: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_entrada: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_saida: Mapped[time | None] = mapped_column(Time, nullable=True)
    foi_alta: Mapped[bool] = mapped_column(Boolean, default=False)
    foi_contrarreferencia: Mapped[bool] = mapped_column(Boolean, default=False)
    em_seguimento: Mapped[bool] = mapped_column(Boolean, default=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    agenda: Mapped["Agenda | None"] = relationship("Agenda", back_populates="consultas")
    profissional: Mapped["Profissional"] = relationship("Profissional", back_populates="consultas")
    especialidade: Mapped["Especialidade"] = relationship("Especialidade", back_populates="consultas")
    consultorio: Mapped["Consultorio | None"] = relationship("Consultorio")
    motivo_falta: Mapped["MotivoFalta | None"] = relationship("MotivoFalta", back_populates="consultas")
    confirmacoes: Mapped[list["ConfirmacaoPresenca"]] = relationship("ConfirmacaoPresenca", back_populates="consulta")


class ConfirmacaoPresenca(Base):
    __tablename__ = "confirmacoes_presenca"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consulta_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("consultas.id"), nullable=False)
    canal: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    tentativas: Mapped[int] = mapped_column(Integer, default=1)
    data_contato: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    consulta: Mapped["Consulta"] = relationship("Consulta", back_populates="confirmacoes")
