import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TipoCambioHist(Base):
    __tablename__ = "tipo_cambio_hist"
    __table_args__ = (
        UniqueConstraint("empresa_id", "moneda_id", "fecha", name="uq_tipo_cambio_hist"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    moneda_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("moneda.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tasa_compra: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    tasa_venta: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    empresa = relationship("Empresa")
    moneda = relationship("Moneda")
