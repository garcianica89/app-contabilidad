"""
Seed de configuracion del motor contable.

Crea:
- Account records sincronizados desde CuentaContable
- AccountingEvent para FAC y COMPRA
- JournalTemplate + JournalTemplateLine para generacion de asientos
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.cuenta_contable import CuentaContable
from app.domain.accounting.models import (
    Account, AccountType, AccountingEvent,
    JournalType, JournalTemplate, JournalTemplateLine,
)


ADDITIONAL_ACCOUNTS = [
    {
        "code": "1-1-4-1-01-00-00-0000",
        "name": "IVA Credito Fiscal",
        "tipo": "ACTIVO",
        "level": 5,
        "accepts_entries": True,
    },
    {
        "code": "5-1-1-2-01-00-00-0000",
        "name": "Compras de Mercancias",
        "tipo": "COSTO",
        "level": 5,
        "accepts_entries": True,
    },
    {
        "code": "5-1-2-1-01-00-00-0000",
        "name": "Gastos Sueldos",
        "tipo": "GASTO",
        "level": 5,
        "accepts_entries": True,
    },
    {
        "code": "2-1-1-3-01-00-00-0000",
        "name": "Sueldos por Pagar",
        "tipo": "PASIVO",
        "level": 5,
        "accepts_entries": True,
    },
    {
        "code": "2-1-2-1-03-00-00-0000",
        "name": "Retenciones por Pagar",
        "tipo": "PASIVO",
        "level": 5,
        "accepts_entries": True,
    },
    {
        "code": "5-1-3-1-01-00-00-0000",
        "name": "Gasto Depreciacion",
        "tipo": "GASTO",
        "level": 5,
        "accepts_entries": True,
    },
    {
        "code": "1-1-5-9-01-00-00-0000",
        "name": "Depreciacion Acumulada",
        "tipo": "ACTIVO",
        "level": 5,
        "accepts_entries": True,
    },
]

EVENT_CONFIGS = [
    {
        "code": "FAC",
        "name": "Factura de Venta",
        "module": "facturacion",
        "journal_type_code": "FA",
    },
    {
        "code": "COMPRA",
        "name": "Factura de Compra",
        "module": "compras",
        "journal_type_code": "CP",
    },
    {
        "code": "SALIDA_INV",
        "name": "Salida de Inventario",
        "module": "inventario",
        "journal_type_code": "CI",
    },
    {
        "code": "PAGO",
        "name": "Pago a Proveedor",
        "module": "cxp",
        "journal_type_code": "CP",
    },
    {
        "code": "MOV_BANCO",
        "name": "Movimiento Bancario Configurable",
        "module": "bancos",
        "journal_type_code": "CB",
    },
    {
        "code": "NOMINA",
        "name": "Provision de Nomina",
        "module": "nomina",
        "journal_type_code": "CN",
    },
    {
        "code": "PAGO_NOMINA",
        "name": "Pago de Nomina",
        "module": "nomina",
        "journal_type_code": "CN",
    },
    {
        "code": "DEPRECIACION",
        "name": "Depreciacion de Activo Fijo",
        "module": "activos_fijos",
        "journal_type_code": "AF",
    },
]


# ── Configuracion de cuentas por modulo (ModuleAccountingConfig) ──
# Estos son defaults iniciales; el admin puede cambiarlos via API.
MODULE_ACCOUNTING_CONFIGS = [
    {"module": "facturacion", "concept_code": "FAC_VENTAS",         "concept_name": "Ventas de Mercancias",      "account_code": "4-1-1-1-01-00-00-0000"},
    {"module": "facturacion", "concept_code": "FAC_IVA",            "concept_name": "IVA Debito Fiscal",         "account_code": "2-1-2-1-00-00-0000"},
    {"module": "compras",     "concept_code": "COMPRA_MERCANCIAS",  "concept_name": "Compras de Mercancias",     "account_code": "5-1-1-2-01-00-00-0000"},
    {"module": "compras",     "concept_code": "COMPRA_IVA",         "concept_name": "IVA Credito Fiscal",        "account_code": "1-1-4-1-01-00-00-0000"},
    {"module": "inventario",  "concept_code": "INVENTARIO_MERCANCIAS", "concept_name": "Inventario de Mercancias", "account_code": "1-1-3-1-01-00-00-0000"},
    {"module": "bancos",      "concept_code": "CAJA_BANCO",         "concept_name": "Caja / Banco",              "account_code": "1-1-1-1-01-00-00-0000"},
    {"module": "nomina",      "concept_code": "GASTO_SUELDOS",      "concept_name": "Gastos de Sueldos",         "account_code": "5-1-2-1-01-00-00-0000"},
    {"module": "nomina",      "concept_code": "SUELDOS_PAGAR",      "concept_name": "Sueldos por Pagar",         "account_code": "2-1-1-3-01-00-00-0000"},
    {"module": "nomina",      "concept_code": "RETENCIONES_PAGAR",  "concept_name": "Retenciones por Pagar",     "account_code": "2-1-2-1-03-00-00-0000"},
    {"module": "nomina",      "concept_code": "CAJA_EFECTIVO",      "concept_name": "Caja para nomina",          "account_code": "1-1-1-1-02-00-00-0000"},
    {"module": "activos_fijos", "concept_code": "GASTO_DEPRECIACION",   "concept_name": "Gasto de Depreciacion",    "account_code": "5-1-3-1-01-00-00-0000"},
    {"module": "activos_fijos", "concept_code": "DEPRECIACION_ACUMULADA","concept_name": "Depreciacion Acumulada",  "account_code": "1-1-5-9-01-00-00-0000"},
    {"module": "cxp",         "concept_code": "CXP_CAJA",           "concept_name": "Caja para pagos CxP",       "account_code": "1-1-1-1-02-00-00-0000"},
    {"module": "cxp",         "concept_code": "CXP_BANCO",          "concept_name": "Banco para pagos CxP",      "account_code": "1-1-1-1-01-00-00-0000"},
    {"module": "cxc",         "concept_code": "CXC_CAJA",           "concept_name": "Caja para cobros CxC",      "account_code": "1-1-1-1-02-00-00-0000"},
    {"module": "cxc",         "concept_code": "CXC_BANCO",          "concept_name": "Banco para cobros CxC",     "account_code": "1-1-1-1-01-00-00-0000"},
]


class TemplateLineDef:
    def __init__(self, line_order: int, nature: str, amount_expr: str, desc_expr: str = "",
                 is_mandatory: bool = True,
                 condition_expr: str | None = None,
                 account_source: str = 'PARAM',
                 account_param_concept: str | None = None,
                 account_context_var: str | None = None,
                 invert_in_banking: bool = False):
        self.line_order = line_order
        self.nature = nature
        self.amount_expr = amount_expr
        self.desc_expr = desc_expr
        self.is_mandatory = is_mandatory
        self.condition_expr = condition_expr
        self.account_source = account_source
        self.account_param_concept = account_param_concept
        self.account_context_var = account_context_var
        self.invert_in_banking = invert_in_banking


# ── Templates (sin cuentas hardcodeadas) ──

FAC_TEMPLATE_LINES = [
    TemplateLineDef(
        1, 'DEBIT', '{{total}}', 'Factura #{{numero}}',
        account_source='CONTEXT', account_context_var='cuenta_tercero_id',
    ),
    TemplateLineDef(
        2, 'CREDIT', '{{subtotal - descuento}}', 'Venta de mercancias factura #{{numero}}',
        account_source='PARAM', account_param_concept='FAC_VENTAS',
    ),
    TemplateLineDef(
        3, 'CREDIT', '{{iva}}', 'IVA Debito Fiscal factura #{{numero}}',
        is_mandatory=False, condition_expr='{{iva > 0}}',
        account_source='PARAM', account_param_concept='FAC_IVA',
    ),
]

COMPRA_TEMPLATE_LINES = [
    TemplateLineDef(
        1, 'DEBIT', '{{subtotal - descuento - retencion_ir}}', 'Compra de mercancias factura #{{numero}}',
        account_source='PARAM', account_param_concept='COMPRA_MERCANCIAS',
    ),
    TemplateLineDef(
        2, 'DEBIT', '{{iva}}', 'IVA Credito Fiscal factura #{{numero}}',
        is_mandatory=False, condition_expr='{{iva > 0}}',
        account_source='PARAM', account_param_concept='COMPRA_IVA',
    ),
    TemplateLineDef(
        3, 'CREDIT', '{{total}}', 'Factura #{{numero}}',
        account_source='CONTEXT', account_context_var='cuenta_tercero_id',
    ),
]

MOV_BANCO_TEMPLATE_LINES = [
    TemplateLineDef(
        1, 'DEBIT', '{{monto}}', '{{concepto}}',
        account_source='SUBTYPE',
        invert_in_banking=True,
    ),
    TemplateLineDef(
        2, 'CREDIT', '{{monto}}', '{{concepto}}',
        account_source='PARAM', account_param_concept='CAJA_BANCO',
        invert_in_banking=True,
    ),
]

PAGO_TEMPLATE_LINES = [
    TemplateLineDef(
        1, 'DEBIT', '{{total_factura}}', 'Pago factura #{{numero}}',
        account_source='CONTEXT', account_context_var='cuenta_tercero_id',
    ),
    TemplateLineDef(
        2, 'CREDIT', '{{monto_pagado}}', 'Pago factura #{{numero}}',
        account_source='SUBTYPE',
    ),
]

SALIDA_INV_TEMPLATE_LINES = [
    TemplateLineDef(
        1, 'DEBIT', '{{costo_total}}', '{{motivo}}',
        account_source='SUBTYPE',
    ),
    TemplateLineDef(
        2, 'CREDIT', '{{costo_total}}', 'Inventario - {{motivo}}',
        account_source='PARAM', account_param_concept='INVENTARIO_MERCANCIAS',
    ),
]

NOMINA_TEMPLATE_LINES = [
    TemplateLineDef(
        1, 'DEBIT', '{{total_devengado}}', 'Provision nomina {{periodo_codigo}}',
        account_source='PARAM', account_param_concept='GASTO_SUELDOS',
    ),
    TemplateLineDef(
        2, 'CREDIT', '{{total_neto}}', 'Sueldos por pagar {{periodo_codigo}}',
        account_source='PARAM', account_param_concept='SUELDOS_PAGAR',
    ),
    TemplateLineDef(
        3, 'CREDIT', '{{total_deducciones}}', 'Retenciones por pagar {{periodo_codigo}}',
        is_mandatory=False, condition_expr='{{total_deducciones > 0}}',
        account_source='PARAM', account_param_concept='RETENCIONES_PAGAR',
    ),
]

PAGO_NOMINA_TEMPLATE_LINES = [
    TemplateLineDef(
        1, 'DEBIT', '{{monto}}', 'Pago nomina {{periodo_codigo}}',
        account_source='PARAM', account_param_concept='SUELDOS_PAGAR',
    ),
    TemplateLineDef(
        2, 'CREDIT', '{{monto}}', 'Pago nomina {{periodo_codigo}}',
        account_source='PARAM', account_param_concept='CAJA_EFECTIVO',
    ),
]

DEPRECIACION_TEMPLATE_LINES = [
    TemplateLineDef(
        1, 'DEBIT', '{{monto_depreciacion}}', 'Depreciacion activo {{activo_id}}',
        account_source='PARAM', account_param_concept='GASTO_DEPRECIACION',
    ),
    TemplateLineDef(
        2, 'CREDIT', '{{monto_depreciacion}}', 'Depreciacion acumulada activo {{activo_id}}',
        account_source='PARAM', account_param_concept='DEPRECIACION_ACUMULADA',
    ),
]


async def _get_account_type(db: AsyncSession, tipo: str) -> AccountType | None:
    r = await db.execute(select(AccountType).where(AccountType.code == tipo))
    return r.scalar_one_or_none()


async def seed_accounting(db: AsyncSession, company_id: uuid.UUID):
    """Crea account records, eventos contables y plantillas de asiento."""

    # ── 1. Sincronizar CuentaContable → Account ──
    cuentas = await db.execute(
        select(CuentaContable).where(CuentaContable.empresa_id == company_id)
    )
    for cc in cuentas.scalars():
        existing = await db.execute(
            select(Account).where(
                Account.company_id == company_id,
                Account.code == cc.codigo,
            )
        )
        if existing.scalar_one_or_none():
            continue

        at = await _get_account_type(db, cc.tipo)
        if not at:
            continue

        account = Account(
            company_id=company_id,
            code=cc.codigo,
            name=cc.nombre,
            level=cc.nivel or 1,
            account_type_id=at.id,
            accepts_entries=cc.acepta_datos or False,
            is_active=True,
        )
        db.add(account)

    # ── 2. Crear cuentas adicionales (IVA CF, Retenciones) ──
    for acct_data in ADDITIONAL_ACCOUNTS:
        existing = await db.execute(
            select(Account).where(
                Account.company_id == company_id,
                Account.code == acct_data["code"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        at = await _get_account_type(db, acct_data["tipo"])
        if not at:
            continue

        account = Account(
            company_id=company_id,
            code=acct_data["code"],
            name=acct_data["name"],
            level=acct_data["level"],
            account_type_id=at.id,
            accepts_entries=acct_data["accepts_entries"],
            is_active=True,
        )
        db.add(account)

    await db.flush()

    # ── 3. Crear eventos contables ──
    for evt_cfg in EVENT_CONFIGS:
        existing = await db.execute(
            select(AccountingEvent).where(
                AccountingEvent.company_id == company_id,
                AccountingEvent.code == evt_cfg["code"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        jt = await db.execute(
            select(JournalType).where(
                JournalType.company_id == company_id,
                JournalType.code == evt_cfg["journal_type_code"],
            )
        )
        jt = jt.scalar_one_or_none()
        if not jt:
            continue

        event = AccountingEvent(
            company_id=company_id,
            code=evt_cfg["code"],
            name=evt_cfg["name"],
            module=evt_cfg["module"],
            journal_type_resolution='DIRECT',
            journal_type_id=jt.id,
            is_active=True,
        )
        db.add(event)

    # ── 3b. Seed ModuleAccountingConfig ──
    for cfg in MODULE_ACCOUNTING_CONFIGS:
        existing = await db.execute(
            select(ModuleAccountingConfig).where(
                ModuleAccountingConfig.company_id == company_id,
                ModuleAccountingConfig.module == cfg["module"],
                ModuleAccountingConfig.concept_code == cfg["concept_code"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        acct = await db.execute(
            select(Account).where(
                Account.company_id == company_id,
                Account.code == cfg["account_code"],
            )
        )
        acct = acct.scalar_one_or_none()
        if not acct:
            continue

        rec = ModuleAccountingConfig(
            company_id=company_id,
            module=cfg["module"],
            concept_code=cfg["concept_code"],
            concept_name=cfg["concept_name"],
            account_id=acct.id,
            is_active=True,
        )
        db.add(rec)

    await db.flush()

    # ── 4. Crear plantillas de asiento ──
    template_configs = [
        ("FA", "Plantilla Factura Venta", FAC_TEMPLATE_LINES),
        ("CP", "Plantilla Factura Compra", COMPRA_TEMPLATE_LINES),
        ("CI", "Plantilla Salida Inventario", SALIDA_INV_TEMPLATE_LINES),
        ("CP", "Plantilla Pago Proveedor", PAGO_TEMPLATE_LINES),
        ("CB", "Plantilla Movimiento Bancario", MOV_BANCO_TEMPLATE_LINES),
        ("CN", "Plantilla Provision Nomina", NOMINA_TEMPLATE_LINES),
        ("CN", "Plantilla Pago Nomina", PAGO_NOMINA_TEMPLATE_LINES),
        ("AF", "Plantilla Depreciacion", DEPRECIACION_TEMPLATE_LINES),
    ]

    for jt_code, tpl_name, lines_def in template_configs:
        jt = await db.execute(
            select(JournalType).where(
                JournalType.company_id == company_id,
                JournalType.code == jt_code,
            )
        )
        jt = jt.scalar_one_or_none()
        if not jt:
            continue

        existing = await db.execute(
            select(JournalTemplate).where(
                JournalTemplate.company_id == company_id,
                JournalTemplate.journal_type_id == jt.id,
                JournalTemplate.name == tpl_name,
            )
        )
        if existing.scalar_one_or_none():
            continue

        template = JournalTemplate(
            journal_type_id=jt.id,
            company_id=company_id,
            name=tpl_name,
            priority=0,
            is_active=True,
        )
        db.add(template)

        for line_def in lines_def:
            tpl_line = JournalTemplateLine(
                template_id=template.id,
                line_order=line_def.line_order,
                nature=line_def.nature,
                account_source=line_def.account_source,
                account_code=None,
                account_param_concept=line_def.account_param_concept,
                account_context_var=line_def.account_context_var,
                amount_expression=line_def.amount_expr,
                description_expression=line_def.desc_expr,
                is_mandatory=line_def.is_mandatory,
                condition_expr=line_def.condition_expr,
                invert_in_banking=line_def.invert_in_banking,
            )
            db.add(tpl_line)

    await db.flush()
