import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Numeric, Date, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class AccountType(Base):
    __tablename__ = "account_type"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nature: Mapped[str] = mapped_column(String(10), nullable=False)
    financial_statement: Mapped[str | None] = mapped_column(String(30))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)


class FinancialClassification(Base):
    __tablename__ = "financial_classification"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class TaxClassification(Base):
    __tablename__ = "tax_classification"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class IfrsClassification(Base):
    __tablename__ = "ifrs_classification"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ifrs_standard: Mapped[str | None] = mapped_column(String(20))


class CompanyAccountStructure(Base):
    __tablename__ = "company_account_structure"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    digit_length: Mapped[int] = mapped_column(Integer, nullable=False)
    separator: Mapped[str] = mapped_column(String(5), default="-")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Account(Base):
    __tablename__ = "account"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    account_type_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("account_type.id"), nullable=False)
    accepts_entries: Mapped[bool] = mapped_column(Boolean, default=False)
    is_control_account: Mapped[bool] = mapped_column(Boolean, default=False)
    is_auxiliary: Mapped[bool] = mapped_column(Boolean, default=False)
    currency_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("moneda.id"))
    requires_cost_center: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_dimension_2: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_dimension_3: Mapped[bool] = mapped_column(Boolean, default=False)
    financial_classification_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("financial_classification.id"))
    tax_classification_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("tax_classification.id"))
    ifrs_classification_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("ifrs_classification.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    observations: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))

    parent = relationship("Account", remote_side="Account.id", backref="children")
    account_type = relationship("AccountType")
    financial_classification = relationship("FinancialClassification")
    tax_classification = relationship("TaxClassification")
    ifrs_classification = relationship("IfrsClassification")


class ModuleAccountingConfig(Base):
    __tablename__ = "module_accounting_config"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    concept_code: Mapped[str] = mapped_column(String(100), nullable=False)
    concept_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("account.id"), nullable=False)
    auxiliary_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))

    account = relationship("Account", foreign_keys=[account_id], overlaps="auxiliary_account")
    auxiliary_account = relationship("Account", foreign_keys=[auxiliary_account_id], overlaps="account")


class JournalType(Base):
    __tablename__ = "journal_type"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str | None] = mapped_column(String(50))
    nature: Mapped[str] = mapped_column(String(20), nullable=False)
    affects_inventory: Mapped[bool] = mapped_column(Boolean, default=False)
    affects_receivable: Mapped[bool] = mapped_column(Boolean, default=False)
    affects_payable: Mapped[bool] = mapped_column(Boolean, default=False)
    affects_cash: Mapped[bool] = mapped_column(Boolean, default=False)
    affects_bank: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_max_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Numeracion de asientos por paquete
    prefijo: Mapped[str | None] = mapped_column(String(10), default='CG')
    digitos: Mapped[int] = mapped_column(Integer, default=8)
    correlativo_actual: Mapped[int] = mapped_column(Integer, default=0)


class JournalTemplate(Base):
    __tablename__ = "journal_template"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    journal_type_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("journal_type.id"), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    condition_expr: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    journal_type = relationship("JournalType", backref="templates")
    lines = relationship("JournalTemplateLine", back_populates="template", cascade="all, delete-orphan")


class JournalTemplateLine(Base):
    __tablename__ = "journal_template_line"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("journal_template.id"), nullable=False)
    line_order: Mapped[int] = mapped_column(Integer, nullable=False)
    nature: Mapped[str] = mapped_column(String(10), nullable=False)
    account_source: Mapped[str] = mapped_column(String(50), nullable=False)
    account_code: Mapped[str | None] = mapped_column(String(50))
    account_param_concept: Mapped[str | None] = mapped_column(String(100))
    account_context_var: Mapped[str | None] = mapped_column(String(100))
    amount_expression: Mapped[str] = mapped_column(Text, nullable=False)
    description_expression: Mapped[str | None] = mapped_column(Text)
    cost_center_source: Mapped[str] = mapped_column(String(50), default="SUBTYPE")
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))
    cost_center_context_var: Mapped[str | None] = mapped_column(String(100))
    condition_expr: Mapped[str | None] = mapped_column(Text)
    invert_in_banking: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    template = relationship("JournalTemplate", back_populates="lines")


class CxcDocumentSubtype(Base):
    __tablename__ = "cxc_document_subtype"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(20))
    serie: Mapped[str | None] = mapped_column(String(10))
    uses_numeracion: Mapped[bool] = mapped_column(Boolean, default=True)
    numeracion_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("numeracion.id"))
    afecta_saldo: Mapped[bool] = mapped_column(Boolean, default=True)
    permite_saldo_negativo: Mapped[bool] = mapped_column(Boolean, default=False)
    genera_asiento: Mapped[bool] = mapped_column(Boolean, default=True)
    journal_type_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("journal_type.id"))
    journal_template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("journal_template.id"))
    cuenta_principal_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_impuestos_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_descuentos_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_intereses_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_mora_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_puente_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cost_center_default_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))
    requiere_aprobacion: Mapped[bool] = mapped_column(Boolean, default=False)
    permite_reversion: Mapped[bool] = mapped_column(Boolean, default=True)
    max_dias_reversion: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    observations: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))

    journal_type = relationship("JournalType", foreign_keys=[journal_type_id])
    journal_template = relationship("JournalTemplate", foreign_keys=[journal_template_id])


class Numeracion(Base):
    __tablename__ = "numeracion"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    sucursal_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("sucursal.id"))
    serie: Mapped[str] = mapped_column(String(10), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String(30), nullable=False)
    mascara: Mapped[str] = mapped_column(String(50), default='{SERIE}-{NUMERO}')
    prefijo: Mapped[str | None] = mapped_column(String(20))
    sufijo: Mapped[str | None] = mapped_column(String(20))
    correlativo_actual: Mapped[int] = mapped_column(Integer, default=0)
    digitos: Mapped[int] = mapped_column(Integer, default=6)
    reinicio: Mapped[str] = mapped_column(String(20), default='NUNCA')
    numeracion_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    permite_reserva: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class CxpDocumentSubtype(Base):
    __tablename__ = "cxp_document_subtype"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(20))
    serie: Mapped[str | None] = mapped_column(String(10))
    uses_numeracion: Mapped[bool] = mapped_column(Boolean, default=True)
    numeracion_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("numeracion.id"))
    afecta_saldo: Mapped[bool] = mapped_column(Boolean, default=True)
    permite_saldo_negativo: Mapped[bool] = mapped_column(Boolean, default=False)
    genera_asiento: Mapped[bool] = mapped_column(Boolean, default=True)
    journal_type_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("journal_type.id"))
    journal_template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("journal_template.id"))
    cuenta_principal_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_impuestos_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_descuentos_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_retencion_iva_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_retencion_ir_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_puente_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cost_center_default_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("centro_costo.id"))
    requiere_aprobacion: Mapped[bool] = mapped_column(Boolean, default=False)
    permite_reversion: Mapped[bool] = mapped_column(Boolean, default=True)
    max_dias_reversion: Mapped[int | None] = mapped_column(Integer)
    afecta_inventario: Mapped[bool] = mapped_column(Boolean, default=False)
    afecta_costo_promedio: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    observations: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))

    journal_type = relationship("JournalType", foreign_keys=[journal_type_id])
    journal_template = relationship("JournalTemplate", foreign_keys=[journal_template_id])


class AccountingEvent(Base):
    __tablename__ = "accounting_event"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)

    journal_type_resolution: Mapped[str] = mapped_column(String(20), default='DIRECT')
    journal_type_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("journal_type.id"))
    journal_type_rule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("accounting_rule.id"))
    journal_type_param_key: Mapped[str | None] = mapped_column(String(100))

    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    observaciones: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    journal_type = relationship("JournalType", foreign_keys=[journal_type_id])


class AccountingRule(Base):
    __tablename__ = "accounting_rule"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    module: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[int] = mapped_column(default=0)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition_expression: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CierreMensual(Base):
    """Cierre mensual — control de cierre de periodos."""
    __tablename__ = "cierre_mensual"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    periodo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("periodo_contable.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default='ABIERTO')
    cerrado_por: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    cerrado_en: Mapped[datetime | None] = mapped_column(DateTime)
    reabierto_por: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    reabierto_en: Mapped[datetime | None] = mapped_column(DateTime)
    observaciones: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CierreFiscal(Base):
    """Cierre fiscal — cierre anual de ejercicio."""
    __tablename__ = "cierre_fiscal"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    ejercicio_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("ejercicio_fiscal.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default='EN_PROCESO')

    resultado_ejercicio: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    cuenta_resultado_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))
    cuenta_utilidad_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("account.id"))

    asiento_cierre_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))
    asiento_apertura_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("asiento.id"))

    cerrado_por: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    cerrado_en: Mapped[datetime | None] = mapped_column(DateTime)
    observaciones: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AccountingRuleLog(Base):
    __tablename__ = "accounting_rule_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("accounting_rule.id"), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(50))
    document_id: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    context_summary: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    execution_time_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
