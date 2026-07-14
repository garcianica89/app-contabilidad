import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class ConciliacionBancaria(Base):
    __tablename__ = "conciliacion_bancaria"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    cuenta_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("cuenta_banco.id"), nullable=False)
    periodo_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("periodo_contable.id"))
    fecha_inicio: Mapped[date | None] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    saldo_inicial_banco: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    saldo_final_banco: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    saldo_inicial_libro: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    saldo_final_libro: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    diferencia: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE")
    observaciones: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    cerrada_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # TEMPORAL = en progreso, EN_FIRME = conciliacion cerrada definitiva
    # PENDIENTE = recien creada


class PartidaConciliacion(Base):
    __tablename__ = "partida_conciliacion"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    conciliacion_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("conciliacion_bancaria.id"), nullable=False)
    movimiento_banco_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("movimiento_banco.id", ondelete="SET NULL"))
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # LIBRO (sistema) or BANCO (banco)
    concepto: Mapped[str] = mapped_column(Text, nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(50))
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    monto: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False)
    observacion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
