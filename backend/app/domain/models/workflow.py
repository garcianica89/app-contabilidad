import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class WfWorkflow(Base):
    """Workflow: define estados y transiciones para un tipo de documento."""
    __tablename__ = "wf_workflow"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    documento_tipo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("documento_tipo.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class WfStatus(Base):
    """Estado dentro de un workflow."""
    __tablename__ = "wf_status"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("wf_workflow.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    es_inicial: Mapped[bool] = mapped_column(Boolean, default=False)
    es_final: Mapped[bool] = mapped_column(Boolean, default=False)
    requiere_aprobacion: Mapped[bool] = mapped_column(Boolean, default=False)
    requiere_firma: Mapped[bool] = mapped_column(Boolean, default=False)
    notificar_al_entrar: Mapped[bool] = mapped_column(Boolean, default=False)


class WfTransition(Base):
    """Transicion entre estados de workflow."""
    __tablename__ = "wf_transition"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("wf_workflow.id"), nullable=False)
    from_status_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("wf_status.id"), nullable=False)
    to_status_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("wf_status.id"), nullable=False)
    action_code: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    requiere_comentario: Mapped[bool] = mapped_column(Boolean, default=False)
    requiere_aprobacion: Mapped[bool] = mapped_column(Boolean, default=False)
    cantidad_aprobaciones: Mapped[int] = mapped_column(Integer, default=1)
    condition_rule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("accounting_rule.id"))
    es_reversion: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WfDocumentHistory(Base):
    """Historial de estados por documento."""
    __tablename__ = "wf_document_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    documento_tipo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("documento_tipo.id"), nullable=False)
    documento_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    from_status_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("wf_status.id"))
    to_status_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("wf_status.id"), nullable=False)
    transition_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("wf_transition.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("usuario.id"), nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class WfPendingApproval(Base):
    """Aprobaciones pendientes."""
    __tablename__ = "wf_pending_approval"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    documento_tipo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("documento_tipo.id"), nullable=False)
    documento_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    transition_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("wf_transition.id"), nullable=False)
    solicitado_por: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("usuario.id"), nullable=False)
    aprobado_por: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    estado: Mapped[str] = mapped_column(String(20), default='PENDIENTE')
    comentario: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
