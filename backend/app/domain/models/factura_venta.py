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
    aplica_iva: Mapped[bool | None] = mapped_column(Boolean, default=None)
    tasa_iva: Mapped[float | None] = mapped_column(Numeric(5, 2), default=None)
    moneda_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("moneda.id"), nullable=False)
    asiento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))
    estado: Mapped[str] = mapped_column(String(20), default="EMITIDA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    retenciones: Mapped[list["FacturaVentaRetencion"]] = relationship(
        back_populates="factura", cascade="all, delete-orphan"
    )


class FacturaVentaRetencion(Base):
    __tablename__ = "factura_venta_retencion"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    factura_venta_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("factura_venta.id", ondelete="CASCADE"), nullable=False)
    retencion_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("retencion.id", ondelete="CASCADE"), nullable=False)
    base_imponible: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    monto_retenido: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    factura = relationship("FacturaVenta", back_populates="retenciones")
    retencion = relationship("Retencion")


class FacturaVentaLinea(Base):
    __tablename__ = "factura_venta_linea"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    factura_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("factura_venta.id"), nullable=False)
    producto_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("producto.id"), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    descuento: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    aplica_iva: Mapped[bool | None] = mapped_column(Boolean, default=None)
    tasa_iva: Mapped[float | None] = mapped_column(Numeric(5, 2), default=None)
