import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class ModuloSistema(Base):
    """
    Modulos del ERP.
    Seed: admin, contabilidad, bancos, cxc, cxp, compras,
          facturacion, inventario, activos_fijos, nomina, presupuestos
    """
    __tablename__ = "modulo_sistema"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    icono: Mapped[str | None] = mapped_column(String(50))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DocumentoTipo(Base):
    """
    Tipos de documento del ERP.
    Cada modulo tiene sus tipos.
    Ej: facturacion → FAC, NCR, NDB
        compras   → OC, RECEPCION
        bancos    → DEBITO, CREDITO, CHEQUE, TRANSFERENCIA
    """
    __tablename__ = "documento_tipo"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    modulo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("modulo_sistema.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    nombre_corto: Mapped[str | None] = mapped_column(String(10))

    # Comportamiento por defecto
    genera_asiento: Mapped[bool] = mapped_column(Boolean, default=True)
    afecta_inventario: Mapped[bool] = mapped_column(Boolean, default=False)
    afecta_cxc: Mapped[bool] = mapped_column(Boolean, default=False)
    afecta_cxp: Mapped[bool] = mapped_column(Boolean, default=False)
    afecta_bancos: Mapped[bool] = mapped_column(Boolean, default=False)

    # Workflow por defecto
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("wf_workflow.id"))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    empresa = relationship("Empresa")
    modulo = relationship("ModuloSistema")
    subtipos = relationship("DocumentoSubtipo", back_populates="documento_tipo", cascade="all, delete-orphan")

    __table_args__ = ({"schema": None})


class DocumentoSubtipo(Base):
    """
    Subtipos de documento.
    TODO documento tiene subtipos.

    El subtipo define:
    - Cuentas contables
    - Comportamiento
    - Workflow
    - Aprobaciones
    - Validaciones
    - Impuestos
    - Retenciones
    - Numeracion

    Ejemplo para Bancos:
    - DEBITO_COMISION    (comision bancaria)
    - DEBITO_IMPUESTO    (impuesto bancario)
    - CREDITO_DEPOSITO   (deposito)
    - CHEQUE_EMITIDO     (cheque)
    """
    __tablename__ = "documento_subtipo"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    documento_tipo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("documento_tipo.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(30), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    nombre_corto: Mapped[str | None] = mapped_column(String(10))

    # Numeracion
    numeracion_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("numeracion.id"))

    # Evento contable
    accounting_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("accounting_event.id"))

    # Comportamiento
    genera_asiento: Mapped[bool] = mapped_column(Boolean, default=True)
    afecta_inventario: Mapped[bool] = mapped_column(Boolean, default=False)
    afecta_cxc: Mapped[bool] = mapped_column(Boolean, default=False)
    afecta_cxp: Mapped[bool] = mapped_column(Boolean, default=False)
    afecta_bancos: Mapped[bool] = mapped_column(Boolean, default=False)
    afecta_saldo: Mapped[bool] = mapped_column(Boolean, default=True)
    permite_saldo_negativo: Mapped[bool] = mapped_column(Boolean, default=False)

    # Reversion
    permite_reversion: Mapped[bool] = mapped_column(Boolean, default=True)
    max_dias_reversion: Mapped[int | None] = mapped_column(Integer)

    # Aprobacion
    requiere_aprobacion: Mapped[bool] = mapped_column(Boolean, default=False)
    cantidad_aprobaciones: Mapped[int] = mapped_column(Integer, default=1)

    # Workflow
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("wf_workflow.id"))

    # Reglas
    validation_rule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("accounting_rule.id"))

    # Referencia directa a JournalType y Template (desde subtipo)
    journal_type_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("journal_type.id"))
    journal_template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("journal_template.id"))

    # Comportamiento extendido
    calcula_iva: Mapped[bool] = mapped_column(Boolean, default=True)
    aplica_retenciones: Mapped[bool] = mapped_column(Boolean, default=False)
    genera_costo_venta: Mapped[bool] = mapped_column(Boolean, default=False)
    requiere_centros_costo: Mapped[bool] = mapped_column(Boolean, default=False)

    # Cuentas contables (desde subtipo)
    cuenta_principal_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_contrapartida_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_impuestos_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_descuentos_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_intereses_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_retencion_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_retencion_iva_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_retencion_ir_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_mora_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_puente_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_costo_venta_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))

    # Centro costo por defecto
    cost_center_default_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))

    # Control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    observaciones: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Numeracion por subtipo (auto-increment)
    ultimo_numero: Mapped[int] = mapped_column(Integer, default=0)

    empresa = relationship("Empresa")
    documento_tipo = relationship("DocumentoTipo", back_populates="subtipos")

    __table_args__ = ({"schema": None})


class DocumentoEstado(Base):
    """
    Estados posibles para documentos.
    Cada tipo de documento puede tener sus propios estados.
    """
    __tablename__ = "documento_estado"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    documento_tipo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("documento_tipo.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    es_inicial: Mapped[bool] = mapped_column(Boolean, default=False)
    es_final: Mapped[bool] = mapped_column(Boolean, default=False)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    empresa = relationship("Empresa")
    documento_tipo = relationship("DocumentoTipo")

    __table_args__ = ({"schema": None})
