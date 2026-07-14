import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class CategoriaActivo(Base):
    __tablename__ = "categoria_activo"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    vida_util_default: Mapped[int | None] = mapped_column(Numeric(3, 0))
    metodo_depreciacion_default: Mapped[str | None] = mapped_column(String(20))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    activos = relationship("ActivoFijo", back_populates="categoria")


class ActivoFijo(Base):
    __tablename__ = "activo_fijo"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    categoria_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("categoria_activo.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    fecha_adquisicion: Mapped[date] = mapped_column(Date, nullable=False)
    costo_adquisicion: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    valor_residual: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    vida_util_anos: Mapped[int] = mapped_column(Numeric(3, 0), nullable=False)
    metodo_depreciacion: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO")
    valor_libros: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    depreciacion_acumulada: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    fecha_baja: Mapped[date | None] = mapped_column(Date)
    motivo_baja: Mapped[str | None] = mapped_column(Text)
    cuenta_contable_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"))
    cuenta_depreciacion_gasto_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"))
    cuenta_depreciacion_acumulada_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"))
    cuenta_baja_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"))
    ubicacion: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    categoria = relationship("CategoriaActivo", back_populates="activos")
    depreciaciones = relationship("DepreciacionLinea", back_populates="activo", cascade="all, delete-orphan")


class DepreciacionLinea(Base):
    __tablename__ = "depreciacion_linea"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    activo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("activo_fijo.id"), nullable=False)
    periodo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("periodo_contable.id"), nullable=False)
    fecha_depreciacion: Mapped[date] = mapped_column(Date, nullable=False)
    monto_depreciacion: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    depreciacion_acumulada: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    valor_libros_despues: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    activo = relationship("ActivoFijo", back_populates="depreciaciones")
    periodo = relationship("PeriodoContable")
