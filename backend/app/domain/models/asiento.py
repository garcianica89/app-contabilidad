import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Asiento(Base):
    __tablename__ = "asiento"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    numero: Mapped[int] = mapped_column(nullable=False)
    fecha: Mapped[datetime] = mapped_column(Date, nullable=False)
    periodo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("periodo_contable.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="DIARIO")
    concepto: Mapped[str] = mapped_column(Text, nullable=False)
    origen_modulo: Mapped[str | None] = mapped_column(String(50))
    origen_documento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    creado_por: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("usuario.id"), nullable=False)
    aprobado_por: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    reversado: Mapped[bool] = mapped_column(Boolean, default=False)
    asiento_reversa_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    empresa = relationship("Empresa", backref="asientos")
    periodo = relationship("PeriodoContable", backref="asientos")
    lineas = relationship("AsientoLinea", back_populates="asiento", cascade="all, delete-orphan")


class AsientoLinea(Base):
    __tablename__ = "asiento_linea"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    asiento_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("asiento.id"), nullable=False)
    cuenta_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"), nullable=False)
    centro_costo_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))
    descripcion: Mapped[str | None] = mapped_column(Text)
    debe_local: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    haber_local: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    debe_dolar: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    haber_dolar: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    orden: Mapped[int] = mapped_column(default=0)

    asiento = relationship("Asiento", back_populates="lineas")
    cuenta = relationship("CuentaContable")
