import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean
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
    descuento: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    aplica_iva: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tasa_iva: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    centro_costo_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))
    cuenta_contable_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class OrdenCompra(Base):
    __tablename__ = "orden_compra"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    proveedor_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("proveedor.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_entrega: Mapped[datetime | None] = mapped_column(DateTime)
    bodega_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("bodega.id"))
    condicion_pago_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("condicion_pago.id"))
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    descuento: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    iva: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    retencion_ir: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    moneda_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("moneda.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="EMITIDA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    lineas = relationship("OrdenCompraLinea", backref="orden", lazy="selectin")
