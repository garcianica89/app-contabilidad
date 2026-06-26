import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Producto(Base):
    __tablename__ = "producto"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(50))
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("categoria.id"))
    unidad_medida: Mapped[str] = mapped_column(String(20), default="UNIDAD")
    costo_promedio: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    precio_venta: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    moneda_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("moneda.id"))
    stock_actual: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    stock_minimo: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class KardexMovimiento(Base):
    __tablename__ = "kardex_movimiento"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    producto_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("producto.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo_documento: Mapped[str | None] = mapped_column(String(20))
    documento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    costo_unitario: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    costo_total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    saldo_cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    saldo_costo_promedio: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    saldo_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
