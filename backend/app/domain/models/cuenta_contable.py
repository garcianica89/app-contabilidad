import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class CuentaContable(Base):
    __tablename__ = "cuenta_contable"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    nivel: Mapped[int] = mapped_column(nullable=False)
    padre_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"))
    acepta_datos: Mapped[bool] = mapped_column(Boolean, default=False)
    moneda_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("moneda.id"))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    indice: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    empresa = relationship("Empresa", backref="cuentas")
    padre = relationship("CuentaContable", remote_side="CuentaContable.id", backref="hijos")
