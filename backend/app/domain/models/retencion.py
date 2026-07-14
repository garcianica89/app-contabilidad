import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid
from app.core.database import Base


class Retencion(Base):
    """
    Retenciones configurables.
    Gestionadas exclusivamente desde Cuentas por Pagar.

    Cada tipo de retencion tiene:
    - Codigo, nombre, porcentaje
    - Cuenta contable
    - Vigencia
    - Aplica a (NACIONAL, EXTRANJERO, AMBOS)
    - Monto minimo
    """
    __tablename__ = "retencion"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)

    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    aplica_a: Mapped[str] = mapped_column(String(20), default='NACIONAL')
    monto_minimo: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    cuenta_retencion_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_pagar_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_cobrar_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    centro_costo_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))

    base_imponible: Mapped[str] = mapped_column(String(20), default='SUBTOTAL')
    prioridad: Mapped[int] = mapped_column(default=10)
    redondeo: Mapped[int] = mapped_column(default=2)
    naturaleza: Mapped[str] = mapped_column(String(10), default='CREDITO')

    vigencia_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigencia_hasta: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
