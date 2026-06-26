import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Permiso(Base):
    __tablename__ = "permiso"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    modulo: Mapped[str] = mapped_column(String(50), nullable=False)

    roles = relationship("Rol", secondary="rol_permiso", back_populates="permisos")
