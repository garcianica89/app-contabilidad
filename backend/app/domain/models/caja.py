import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Caja(Base):
    __tablename__ = "caja"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), default="Caja General")
    moneda_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("moneda.id"), nullable=False)
    saldo_actual: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class MovimientoCaja(Base):
    __tablename__ = "movimiento_caja"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    caja_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("caja.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    concepto: Mapped[str] = mapped_column(Text, nullable=False)
    entrada: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    salida: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    saldo: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    referencia_id: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    asiento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ArqueoCaja(Base):
    __tablename__ = "arqueo_caja"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    caja_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("caja.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    saldo_esperado: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    saldo_real: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    diferencia: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    observaciones: Mapped[str | None] = mapped_column(Text)
    realizado_por: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("usuario.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
