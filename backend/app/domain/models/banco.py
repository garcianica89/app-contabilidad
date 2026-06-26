import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class CuentaBanco(Base):
    __tablename__ = "cuenta_banco"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    banco: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_cuenta: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), default="CORRIENTE")
    moneda_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("moneda.id"), nullable=False)
    saldo: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class MovimientoBanco(Base):
    __tablename__ = "movimiento_banco"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    cuenta_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("cuenta_banco.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    numero_documento: Mapped[str | None] = mapped_column(String(50))
    concepto: Mapped[str] = mapped_column(Text, nullable=False)
    entrada: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    salida: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    saldo: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False)
    asiento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
