import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid
from app.core.database import Base


class PresupuestoCabecera(Base):
    __tablename__ = "presupuesto_cabecera"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    ejercicio_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("ejercicio_fiscal.id"), nullable=False)
    centro_costo_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))
    moneda_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("moneda.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), default='OPERATIVO')
    estado: Mapped[str] = mapped_column(String(20), default='BORRADOR')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PresupuestoDetalle(Base):
    __tablename__ = "presupuesto_detalle"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    presupuesto_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("presupuesto_cabecera.id"), nullable=False)
    cuenta_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("account.id"), nullable=False)
    mes_01: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_02: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_03: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_04: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_05: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_06: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_07: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_08: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_09: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_10: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_11: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    mes_12: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)


class PresupuestoEjecucion(Base):
    __tablename__ = "presupuesto_ejecucion"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    presupuesto_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("presupuesto_cabecera.id"), nullable=False)
    cuenta_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("account.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    presupuestado: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    ejecutado: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    variacion: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    porcentaje_ejecucion: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
