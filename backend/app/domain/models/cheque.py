import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Chequera(Base):
    """Talonario / chequera — controla rangos de números de cheques por cuenta bancaria."""
    __tablename__ = "chequera"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    cuenta_bancaria_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("cuenta_banco.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_inicio: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_fin: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_actual: Mapped[int] = mapped_column(Integer, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    cuenta = relationship("CuentaBanco", backref="chequeras")


class Cheque(Base):
    """Cheque emitido — wrapping the existing `cheque` table from migration 0016."""
    __tablename__ = "cheque"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    chequera_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("chequera.id"))
    numero: Mapped[str] = mapped_column(String(30), nullable=False, comment="Operational cheque number (printed)")
    numero_contable: Mapped[str | None] = mapped_column(String(30), comment="Accounting sequential reference")
    cuenta_bancaria_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("cuenta_banco.id"), nullable=False)
    pagadero_a: Mapped[str] = mapped_column(String(200), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    monto_local: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    monto_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tipo: Mapped[str] = mapped_column(String(20), default='CHEQUE')
    metodo_pago: Mapped[str | None] = mapped_column(String(30))
    referencia: Mapped[str | None] = mapped_column(String(50))
    concepto: Mapped[str | None] = mapped_column(String(200))
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default='EMITIDO')
    proveedor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("proveedor.id"))
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cliente.id"))
    asiento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))
    movimiento_banco_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("movimiento_banco.id"))
    impreso: Mapped[bool] = mapped_column(Boolean, default=False)
    veces_impreso: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    empresa = relationship("Empresa")
    cuenta = relationship("CuentaBanco", backref="cheques")
    chequera = relationship("Chequera", backref="cheques")
    proveedor = relationship("Proveedor")
    cliente = relationship("Cliente")


class ChequeFormato(Base):
    """Formato de impresión de cheques — coordenadas X/Y, fuentes, márgenes.
    
    Cada campo se posiciona de forma absoluta sobre el stock de cheque preimpreso.
    Coordenadas en milímetros desde el borde superior izquierdo.
    """
    __tablename__ = "cheque_formato"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, default='Default')
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    # Dimensiones del cheque en mm
    ancho_mm: Mapped[float] = mapped_column(Numeric(6, 1), default=216.0)    # 8.5 pulgadas
    alto_mm: Mapped[float] = mapped_column(Numeric(6, 1), default=89.0)      # 3.5 pulgadas

    # Campos con posición X/Y en mm
    campo_fecha_x: Mapped[float] = mapped_column(Numeric(6, 1), default=130.0)
    campo_fecha_y: Mapped[float] = mapped_column(Numeric(6, 1), default=14.0)
    campo_fecha_formato: Mapped[str] = mapped_column(String(20), default='DD/MM/YYYY')

    campo_pagadero_x: Mapped[float] = mapped_column(Numeric(6, 1), default=25.0)
    campo_pagadero_y: Mapped[float] = mapped_column(Numeric(6, 1), default=28.0)

    campo_monto_num_x: Mapped[float] = mapped_column(Numeric(6, 1), default=130.0)
    campo_monto_num_y: Mapped[float] = mapped_column(Numeric(6, 1), default=28.0)

    campo_monto_letras_x: Mapped[float] = mapped_column(Numeric(6, 1), default=25.0)
    campo_monto_letras_y: Mapped[float] = mapped_column(Numeric(6, 1), default=42.0)

    campo_concepto_x: Mapped[float] = mapped_column(Numeric(6, 1), default=25.0)
    campo_concepto_y: Mapped[float] = mapped_column(Numeric(6, 1), default=56.0)

    campo_firma_x: Mapped[float] = mapped_column(Numeric(6, 1), default=25.0)
    campo_firma_y: Mapped[float] = mapped_column(Numeric(6, 1), default=72.0)

    # Fuente
    fuente_nombre: Mapped[str] = mapped_column(String(50), default='Courier New')
    fuente_tamano: Mapped[int] = mapped_column(Integer, default=11)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
