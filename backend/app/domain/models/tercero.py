import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Numeric, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Tercero(Base):
    """
    Catalogo UNICO de terceros.
    Reemplaza las tablas cliente, proveedor, empleado.

    Un mismo tercero puede tener multiples roles:
    - es_cliente
    - es_proveedor
    - es_empleado
    - es_transportista
    - es_banco
    - etc.
    """
    __tablename__ = "tercero"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)

    tipo_documento: Mapped[str] = mapped_column(String(10), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(30), nullable=False)
    nombre_legal: Mapped[str] = mapped_column(String(300), nullable=False)
    nombre_comercial: Mapped[str | None] = mapped_column(String(300))
    direccion: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(200))
    ciudad: Mapped[str | None] = mapped_column(String(100))
    pais: Mapped[str | None] = mapped_column(String(100))

    # Roles
    es_cliente: Mapped[bool] = mapped_column(Boolean, default=False)
    es_proveedor: Mapped[bool] = mapped_column(Boolean, default=False)
    es_empleado: Mapped[bool] = mapped_column(Boolean, default=False)
    es_transportista: Mapped[bool] = mapped_column(Boolean, default=False)
    es_banco: Mapped[bool] = mapped_column(Boolean, default=False)

    # Datos de cliente
    limite_credito: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    condicion_pago_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("condicion_pago.id"))
    lista_precio: Mapped[str | None] = mapped_column(String(20), default='GENERAL')
    cobrador_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    dias_gracia: Mapped[int] = mapped_column(Integer, default=0)

    # Datos de proveedor
    tipo_proveedor: Mapped[str] = mapped_column(String(20), default='NACIONAL')
    aplica_iva: Mapped[bool] = mapped_column(Boolean, default=True)
    tasa_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=15.00)
    plazo_entrega: Mapped[int] = mapped_column(Integer, default=0)

    # Datos de empleado
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    fecha_ingreso: Mapped[date | None] = mapped_column(Date)
    salario_base: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    tipo_contrato: Mapped[str | None] = mapped_column(String(50))
    departamento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("departamento.id"))

    # Control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    empresa = relationship("Empresa", backref="terceros")
    condicion_pago = relationship("CondicionPago", foreign_keys=[condicion_pago_id])

    __table_args__ = (
        {"schema": None},
    )
