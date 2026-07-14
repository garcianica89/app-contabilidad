import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base

# Import for Relationship type hint
from app.domain.models.retencion import Retencion


class Proveedor(Base):
    __tablename__ = "proveedor"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(20))
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    ruc: Mapped[str | None] = mapped_column(String(20))
    direccion: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100))
    saldo: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    plazo_credito: Mapped[int] = mapped_column(default=30)
    aplica_iva: Mapped[bool] = mapped_column(Boolean, default=True)
    tasa_iva: Mapped[float] = mapped_column(Numeric(5, 2), default=15.00)
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("categoria_proveedor.id"))
    tipo_fiscal: Mapped[str] = mapped_column(String(20), default='NORMAL')
    sujeto_retenciones: Mapped[bool] = mapped_column(Boolean, default=True)
    activo: Mapped[bool] = mapped_column(default=True)
    retenciones: Mapped[list["Retencion"]] = relationship(
        secondary="proveedor_retencion",
        backref="proveedores",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
