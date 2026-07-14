import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Permiso(Base):
    __tablename__ = "permiso"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    modulo: Mapped[str] = mapped_column(String(50), nullable=False)

    module_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("modulo_sistema.id"))
    action_type: Mapped[str | None] = mapped_column(String(50))
    scope: Mapped[str | None] = mapped_column(String(20), default='ALL')
    empresa_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("empresa.id"))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    roles = relationship("Rol", secondary="rol_permiso", back_populates="permisos")


class UsuarioPermiso(Base):
    __tablename__ = "usuario_permiso"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    permiso_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("permiso.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    allow: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
