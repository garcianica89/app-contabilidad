import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class OrdenCompraLinea(Base):
    __tablename__ = "orden_compra_linea"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    orden_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("orden_compra.id"), nullable=False)
    producto_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("producto.id"), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class OrdenCompra(Base):
    __tablename__ = "orden_compra"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    proveedor_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("proveedor.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_entrega: Mapped[datetime | None] = mapped_column(DateTime)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    iva: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    moneda_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("moneda.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="EMITIDA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
