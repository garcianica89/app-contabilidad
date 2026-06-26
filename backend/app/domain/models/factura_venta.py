import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class FacturaVenta(Base):
    __tablename__ = "factura_venta"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("cliente.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_vencimiento: Mapped[datetime | None] = mapped_column(DateTime)
    tipo: Mapped[str] = mapped_column(String(20), default="CONTADO")
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    descuento: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    iva: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    moneda_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("moneda.id"), nullable=False)
    asiento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))
    estado: Mapped[str] = mapped_column(String(20), default="EMITIDA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class FacturaVentaLinea(Base):
    __tablename__ = "factura_venta_linea"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    factura_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("factura_venta.id"), nullable=False)
    producto_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("producto.id"), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    descuento: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
