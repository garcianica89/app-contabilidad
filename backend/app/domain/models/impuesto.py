import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, ForeignKey
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Impuesto(Base):
    __tablename__ = "impuesto"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    tasa: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    cuenta_contable_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    empresa = relationship("Empresa")
    cuenta_contable = relationship("CuentaContable")
