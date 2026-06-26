import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class CentroCosto(Base):
    __tablename__ = "centro_costo"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    padre_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
