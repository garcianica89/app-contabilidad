import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class NominaConfig(Base):
    __tablename__ = "nomina_config"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    salario_minimo: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    inss_patronal_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.225)
    inss_laboral_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.07)
    ir_tramos: Mapped[dict | None] = mapped_column(JSON)
    aguinaldo_dias: Mapped[int] = mapped_column(Numeric(3, 0), default=30)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class NominaPeriodo(Base):
    __tablename__ = "nomina_periodo"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_pago: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="BORRADOR")
    total_devengado: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_deducciones: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_neto: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    asiento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    detalles = relationship("NominaDetalle", back_populates="periodo", cascade="all, delete-orphan")


class NominaDetalle(Base):
    __tablename__ = "nomina_detalle"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    nomina_periodo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("nomina_periodo.id"), nullable=False)
    empleado_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empleado.id"), nullable=False)
    dias_trabajados: Mapped[int] = mapped_column(Numeric(3, 0), default=30)
    salario_base: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    horas_extra: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    bonos: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    comisiones: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_devengado: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    inss_laboral: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    ir: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    otras_deducciones: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_deducciones: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    neto: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    periodo = relationship("NominaPeriodo", back_populates="detalles")
    empleado = relationship("Empleado")
