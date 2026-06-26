import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Numeric, UniqueConstraint
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CondicionPago(Base):
    __tablename__ = "condicion_pago"
    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="uq_condicion_pago_empresa_codigo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    dias_neto: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    descuento_contado: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    empresa = relationship("Empresa")
