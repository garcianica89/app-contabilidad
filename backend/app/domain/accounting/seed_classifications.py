from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.accounting.models import (
    AccountType,
    FinancialClassification,
    TaxClassification,
    IfrsClassification,
)


ACCOUNT_TYPES = [
    {"code": "ACTIVO", "name": "Activo", "nature": "DEUDORA", "financial_statement": "BALANCE", "display_order": 1, "is_system": True},
    {"code": "PASIVO", "name": "Pasivo", "nature": "ACREEDORA", "financial_statement": "BALANCE", "display_order": 2, "is_system": True},
    {"code": "PATRIMONIO", "name": "Patrimonio", "nature": "ACREEDORA", "financial_statement": "BALANCE", "display_order": 3, "is_system": True},
    {"code": "INGRESO", "name": "Ingresos", "nature": "ACREEDORA", "financial_statement": "INCOME", "display_order": 4, "is_system": True},
    {"code": "COSTO", "name": "Costos", "nature": "DEUDORA", "financial_statement": "INCOME", "display_order": 5, "is_system": True},
    {"code": "GASTO", "name": "Gastos", "nature": "DEUDORA", "financial_statement": "INCOME", "display_order": 6, "is_system": True},
    {"code": "ORDEN_DEUD", "name": "Cuentas Orden Deudora", "nature": "DEUDORA", "financial_statement": "ORDER", "display_order": 7, "is_system": True},
    {"code": "ORDEN_ACRE", "name": "Cuentas Orden Acreedora", "nature": "ACREEDORA", "financial_statement": "ORDER", "display_order": 8, "is_system": True},
]

FINANCIAL_CLASSIFICATIONS = [
    {"code": "CORRIENTE", "name": "Corriente", "type": "BALANCE", "display_order": 1},
    {"code": "NO_CORRIENTE", "name": "No Corriente", "type": "BALANCE", "display_order": 2},
    {"code": "OTRO_ACTIVO", "name": "Otros Activos", "type": "BALANCE", "display_order": 3},
    {"code": "PASIVO_CORRIENTE", "name": "Pasivo Corriente", "type": "BALANCE", "display_order": 4},
    {"code": "PASIVO_NO_CORRIENTE", "name": "Pasivo No Corriente", "type": "BALANCE", "display_order": 5},
    {"code": "CAPITAL", "name": "Capital", "type": "BALANCE", "display_order": 6},
    {"code": "RESERVAS", "name": "Reservas", "type": "BALANCE", "display_order": 7},
    {"code": "RESULTADOS", "name": "Resultados", "type": "BALANCE", "display_order": 8},
    {"code": "OPERACIONALES", "name": "Operacionales", "type": "INCOME", "display_order": 9},
    {"code": "NO_OPERACIONALES", "name": "No Operacionales", "type": "INCOME", "display_order": 10},
    {"code": "EXTRAORDINARIOS", "name": "Extraordinarios", "type": "INCOME", "display_order": 11},
]

TAX_CLASSIFICATIONS = [
    {"code": "GRAVADO", "name": "Gravado"},
    {"code": "EXENTO", "name": "Exento"},
    {"code": "EXCLUIDO", "name": "Excluido"},
    {"code": "NO_APLICA", "name": "No Aplica"},
]

IFRS_CLASSIFICATIONS = [
    {"code": "EFECTIVO", "name": "Efectivo y Equivalentes", "ifrs_standard": "NIIF_PYME"},
    {"code": "CLIENTES", "name": "Cuentas por Cobrar", "ifrs_standard": "NIIF_PYME"},
    {"code": "INVENTARIOS", "name": "Inventarios", "ifrs_standard": "NIIF_PYME"},
    {"code": "PROPIEDADES", "name": "Propiedades, Planta y Equipo", "ifrs_standard": "NIIF_PYME"},
    {"code": "INTANGIBLES", "name": "Activos Intangibles", "ifrs_standard": "NIIF_PYME"},
    {"code": "PROVEEDORES", "name": "Cuentas por Pagar", "ifrs_standard": "NIIF_PYME"},
    {"code": "PASIVOS_FIN", "name": "Pasivos Financieros", "ifrs_standard": "NIIF_PYME"},
    {"code": "PATRIMONIO", "name": "Patrimonio", "ifrs_standard": "NIIF_PYME"},
    {"code": "INGRESOS_ORD", "name": "Ingresos de Actividades Ordinarias", "ifrs_standard": "NIIF_PYME"},
    {"code": "COSTOS_VENTA", "name": "Costo de Ventas", "ifrs_standard": "NIIF_PYME"},
    {"code": "GASTOS_ADMIN", "name": "Gastos de Administración", "ifrs_standard": "NIIF_PYME"},
    {"code": "GASTOS_VENTA", "name": "Gastos de Venta", "ifrs_standard": "NIIF_PYME"},
    {"code": "GASTOS_FIN", "name": "Gastos Financieros", "ifrs_standard": "NIIF_PYME"},
    {"code": "IMPUESTO", "name": "Impuesto a la Renta", "ifrs_standard": "NIIF_PYME"},
]


async def seed_classifications(db: AsyncSession):
    for data in ACCOUNT_TYPES:
        existing = await db.execute(select(AccountType).where(AccountType.code == data["code"]))
        if existing.scalar_one_or_none():
            continue
        db.add(AccountType(**data))

    for data in FINANCIAL_CLASSIFICATIONS:
        existing = await db.execute(select(FinancialClassification).where(FinancialClassification.code == data["code"]))
        if existing.scalar_one_or_none():
            continue
        db.add(FinancialClassification(**data))

    for data in TAX_CLASSIFICATIONS:
        existing = await db.execute(select(TaxClassification).where(TaxClassification.code == data["code"]))
        if existing.scalar_one_or_none():
            continue
        db.add(TaxClassification(**data))

    for data in IFRS_CLASSIFICATIONS:
        existing = await db.execute(select(IfrsClassification).where(IfrsClassification.code == data["code"]))
        if existing.scalar_one_or_none():
            continue
        db.add(IfrsClassification(**data))

    await db.flush()
