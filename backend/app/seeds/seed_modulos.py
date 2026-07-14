"""
Seed de modulos del sistema, tipos de documento y permisos base.
Ejecutar despues de la creacion de tablas.
"""
import uuid
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.document_type import ModuloSistema, DocumentoTipo, DocumentoSubtipo, DocumentoEstado
from app.domain.models.rol import Rol
from app.domain.models.permiso import Permiso
from app.domain.models.empresa import Empresa
from app.domain.accounting.models import JournalType


MODULOS = [
    {"codigo": "admin", "nombre": "Administracion General", "icono": "settings", "orden": 1},
    {"codigo": "contabilidad", "nombre": "Contabilidad General", "icono": "book-open", "orden": 2},
    {"codigo": "bancos", "nombre": "Bancos", "icono": "landmark", "orden": 3},
    {"codigo": "cxc", "nombre": "Cuentas por Cobrar", "icono": "credit-card", "orden": 4},
    {"codigo": "cxp", "nombre": "Cuentas por Pagar", "icono": "receipt", "orden": 5},
    {"codigo": "compras", "nombre": "Compras", "icono": "shopping-cart", "orden": 6},
    {"codigo": "facturacion", "nombre": "Facturacion", "icono": "file-text", "orden": 7},
    {"codigo": "inventario", "nombre": "Inventario", "icono": "package", "orden": 8},
    {"codigo": "activos_fijos", "nombre": "Activos Fijos", "icono": "building", "orden": 9},
    {"codigo": "nomina", "nombre": "Nomina", "icono": "users", "orden": 10},
    {"codigo": "presupuestos", "nombre": "Presupuestos", "icono": "bar-chart", "orden": 11},
]

DOCUMENTOS_POR_MODULO = {
    "facturacion": [
        {"codigo": "FAC", "nombre": "Factura", "nombre_corto": "FAC", "genera_asiento": True, "afecta_inventario": True, "afecta_cxc": True},
        {"codigo": "NCR", "nombre": "Nota Credito", "nombre_corto": "NCR", "genera_asiento": True, "afecta_inventario": True, "afecta_cxc": True},
        {"codigo": "NDB", "nombre": "Nota Debito", "nombre_corto": "NDB", "genera_asiento": True, "afecta_inventario": False, "afecta_cxc": True},
        {"codigo": "COT", "nombre": "Cotizacion", "nombre_corto": "COT", "genera_asiento": False, "afecta_inventario": False, "afecta_cxc": False},
    ],
    "compras": [
        {"codigo": "OC", "nombre": "Orden de Compra", "nombre_corto": "OC", "genera_asiento": False, "afecta_inventario": False, "afecta_cxp": False},
        {"codigo": "RECEPCION", "nombre": "Recepcion de Mercancia", "nombre_corto": "REC", "genera_asiento": False, "afecta_inventario": True, "afecta_cxp": False},
        {"codigo": "COMPRA", "nombre": "Factura de Compra", "nombre_corto": "FCP", "genera_asiento": True, "afecta_inventario": True, "afecta_cxp": True},
    ],
    "cxc": [
        {"codigo": "COBRO", "nombre": "Cobro", "nombre_corto": "COB", "genera_asiento": True, "afecta_cxc": True},
        {"codigo": "ANTICIPO_C", "nombre": "Anticipo Cliente", "nombre_corto": "ANT", "genera_asiento": True, "afecta_cxc": True},
        {"codigo": "AJU_CXC", "nombre": "Ajuste CxC", "nombre_corto": "AJU", "genera_asiento": True, "afecta_cxc": True},
    ],
    "cxp": [
        {"codigo": "PAGO", "nombre": "Pago", "nombre_corto": "PAG", "genera_asiento": True, "afecta_cxp": True},
        {"codigo": "RETENCION", "nombre": "Retencion", "nombre_corto": "RET", "genera_asiento": True, "afecta_cxp": True},
        {"codigo": "ANTICIPO_P", "nombre": "Anticipo Proveedor", "nombre_corto": "ANT", "genera_asiento": True, "afecta_cxp": True},
        {"codigo": "AJU_CXP", "nombre": "Ajuste CxP", "nombre_corto": "AJU", "genera_asiento": True, "afecta_cxp": True},
    ],
    "bancos": [
        {"codigo": "DEBITO", "nombre": "Debito Bancario", "nombre_corto": "DB", "genera_asiento": True, "afecta_bancos": True},
        {"codigo": "CREDITO", "nombre": "Credito Bancario", "nombre_corto": "CR", "genera_asiento": True, "afecta_bancos": True},
        {"codigo": "CHEQUE", "nombre": "Cheque", "nombre_corto": "CHQ", "genera_asiento": True, "afecta_bancos": True},
        {"codigo": "TRANSFERENCIA", "nombre": "Transferencia", "nombre_corto": "TRF", "genera_asiento": True, "afecta_bancos": True},
        {"codigo": "MOV_BANCO", "nombre": "Movimiento Bancario Configurable", "nombre_corto": "MB", "genera_asiento": True, "afecta_bancos": True},
    ],
    "inventario": [
        {"codigo": "ENTRADA", "nombre": "Entrada de Inventario", "nombre_corto": "ENT", "genera_asiento": True, "afecta_inventario": True},
        {"codigo": "SALIDA", "nombre": "Salida de Inventario", "nombre_corto": "SAL", "genera_asiento": True, "afecta_inventario": True},
        {"codigo": "SALIDA_INV", "nombre": "Salida de Inventario Configurable", "nombre_corto": "SIN", "genera_asiento": True, "afecta_inventario": True},
        {"codigo": "AJUSTE", "nombre": "Ajuste de Inventario", "nombre_corto": "AJU", "genera_asiento": True, "afecta_inventario": True},
        {"codigo": "TRASLADO", "nombre": "Traslado entre Bodegas", "nombre_corto": "TRAS", "genera_asiento": False, "afecta_inventario": True},
        {"codigo": "CONSUMO", "nombre": "Consumo Propio", "nombre_corto": "CONS", "genera_asiento": True, "afecta_inventario": True},
    ],
    "activos_fijos": [
        {"codigo": "DEPRECIACION", "nombre": "Depreciacion", "nombre_corto": "DEP", "genera_asiento": True},
        {"codigo": "BAJA", "nombre": "Baja de Activo", "nombre_corto": "BAJA", "genera_asiento": True},
        {"codigo": "REVALUACION", "nombre": "Revaluacion", "nombre_corto": "REV", "genera_asiento": True},
    ],
    "nomina": [
        {"codigo": "NOMINA", "nombre": "Nomina", "nombre_corto": "NOM", "genera_asiento": True},
        {"codigo": "PROVISION", "nombre": "Provision", "nombre_corto": "PROV", "genera_asiento": True},
    ],
    "presupuestos": [
        {"codigo": "PRESUPUESTO", "nombre": "Presupuesto", "nombre_corto": "PRE", "genera_asiento": False},
    ],
    "admin": [
        {"codigo": "CONFIG", "nombre": "Configuracion General", "genera_asiento": False},
    ],
}

ACCIONES_PERMISO = ['CREAR', 'LEER', 'ACTUALIZAR', 'ELIMINAR', 'APROBAR', 'CONTABILIZAR', 'ANULAR', 'REVERTIR', 'EXPORTAR', 'IMPRIMIR', 'CONFIGURAR']

PAQUETES_DEFAULT = [
    {"code": "AB", "name": "Activos Biologicos", "module": "activos_fijos", "nature": "AUTOMATIC", "prefijo": "AB", "digitos": 8},
    {"code": "AF", "name": "Activos Fijos", "module": "activos_fijos", "nature": "AUTOMATIC", "prefijo": "AF", "digitos": 8},
    {"code": "AM", "name": "Amortizaciones", "module": "contabilidad", "nature": "AUTOMATIC", "prefijo": "AM", "digitos": 8},
    {"code": "CB", "name": "Control Bancario", "module": "bancos", "nature": "AUTOMATIC", "prefijo": "CB", "digitos": 8},
    {"code": "CC", "name": "Cuentas por Cobrar", "module": "cxc", "nature": "AUTOMATIC", "prefijo": "CC", "digitos": 8},
    {"code": "CG", "name": "Contabilidad General", "module": "contabilidad", "nature": "AUTOMATIC", "prefijo": "CG", "digitos": 8},
    {"code": "CI", "name": "Control de Inventarios", "module": "inventario", "nature": "AUTOMATIC", "prefijo": "CI", "digitos": 8},
    {"code": "CIER", "name": "Asientos de Cierre Anual", "module": "contabilidad", "nature": "AUTOMATIC", "prefijo": "CIER", "digitos": 6},
    {"code": "CN", "name": "Control de Nominas", "module": "nomina", "nature": "AUTOMATIC", "prefijo": "CN", "digitos": 8},
    {"code": "COS", "name": "Distribucion de Costos a Lotes", "module": "inventario", "nature": "AUTOMATIC", "prefijo": "COS", "digitos": 7},
    {"code": "COST", "name": "Costos de Produccion", "module": "inventario", "nature": "AUTOMATIC", "prefijo": "COST", "digitos": 6},
    {"code": "CP", "name": "Cuentas por Pagar", "module": "cxp", "nature": "AUTOMATIC", "prefijo": "CP", "digitos": 8},
    {"code": "DC", "name": "Diferencial Cambiario", "module": "contabilidad", "nature": "AUTOMATIC", "prefijo": "DC", "digitos": 8},
    {"code": "FA", "name": "Facturacion", "module": "facturacion", "nature": "AUTOMATIC", "prefijo": "FA", "digitos": 8},
    {"code": "FI", "name": "Asientos Financieros", "module": "contabilidad", "nature": "AUTOMATIC", "prefijo": "FI", "digitos": 8},
    {"code": "IMP", "name": "Impuestos", "module": "contabilidad", "nature": "AUTOMATIC", "prefijo": "IMP", "digitos": 7},
    {"code": "RH", "name": "Recursos Humanos", "module": "nomina", "nature": "AUTOMATIC", "prefijo": "RH", "digitos": 8},
]


async def seed_modulos(db: AsyncSession, company_id: uuid.UUID):
    """Crea modulos, tipos de documento, y permisos base."""
    modulos_creados = {}

    for mdata in MODULOS:
        existing = await db.execute(select(ModuloSistema).where(ModuloSistema.codigo == mdata["codigo"]))
        if existing.scalar_one_or_none():
            mod = existing.scalar_one()
        else:
            mod = ModuloSistema(**mdata)
            db.add(mod)
            await db.flush()
        modulos_creados[mdata["codigo"]] = mod

    for modulo_codigo, docs in DOCUMENTOS_POR_MODULO.items():
        modulo = modulos_creados.get(modulo_codigo)
        if not modulo:
            continue
        for ddata in docs:
            existing = await db.execute(
                select(DocumentoTipo).where(
                    DocumentoTipo.company_id == company_id,
                    DocumentoTipo.codigo == ddata["codigo"],
                )
            )
            if existing.scalar_one_or_none():
                continue
            doc = DocumentoTipo(
                company_id=company_id,
                modulo_id=modulo.id,
                codigo=ddata["codigo"],
                nombre=ddata["nombre"],
                nombre_corto=ddata.get("nombre_corto", ""),
                genera_asiento=ddata.get("genera_asiento", True),
                afecta_inventario=ddata.get("afecta_inventario", False),
                afecta_cxc=ddata.get("afecta_cxc", False),
                afecta_cxp=ddata.get("afecta_cxp", False),
                afecta_bancos=ddata.get("afecta_bancos", False),
            )
            db.add(doc)
            await db.flush()

    # Crear subtipos para tipos de documento clave
    SUBTIPOS = {
        "FAC": [
            {"codigo": "FAC_CONTADO", "nombre": "Factura de Contado", "nombre_corto": "FAC", "genera_asiento": True, "afecta_inventario": True, "afecta_cxc": True, "calcula_iva": True, "genera_costo_venta": True},
            {"codigo": "FAC_CREDITO", "nombre": "Factura de Credito", "nombre_corto": "FAC", "genera_asiento": True, "afecta_inventario": True, "afecta_cxc": True, "calcula_iva": True, "genera_costo_venta": True},
        ],
        "COMPRA": [
            {"codigo": "COMPRA", "nombre": "Factura de Compra", "nombre_corto": "FCP", "genera_asiento": True, "afecta_inventario": True, "afecta_cxp": True, "calcula_iva": True},
        ],
        "COBRO": [
            {"codigo": "COBRO", "nombre": "Cobro en Efectivo", "nombre_corto": "COB", "genera_asiento": True, "afecta_cxc": True, "afecta_bancos": True, "calcula_iva": False},
        ],
        "PAGO": [
            {"codigo": "PAGO", "nombre": "Pago en Efectivo", "nombre_corto": "PAG", "genera_asiento": True, "afecta_cxp": True, "afecta_bancos": True, "calcula_iva": False},
        ],

    }
    for tipo_codigo, subtipos in SUBTIPOS.items():
        tipo_doc = await db.execute(
            select(DocumentoTipo).where(
                DocumentoTipo.company_id == company_id,
                DocumentoTipo.codigo == tipo_codigo,
            )
        )
        tipo_doc = tipo_doc.scalar_one_or_none()
        if not tipo_doc:
            continue
        for sdata in subtipos:
            existing = await db.execute(
                select(DocumentoSubtipo).where(
                    DocumentoSubtipo.company_id == company_id,
                    DocumentoSubtipo.documento_tipo_id == tipo_doc.id,
                    DocumentoSubtipo.codigo == sdata["codigo"],
                )
            )
            if existing.scalar_one_or_none():
                continue
            sub = DocumentoSubtipo(
                company_id=company_id,
                documento_tipo_id=tipo_doc.id,
                **sdata,
            )
            db.add(sub)
        await db.flush()

    # Crear estados por defecto para cada tipo de documento
    tipos_doc = await db.execute(
        select(DocumentoTipo).where(DocumentoTipo.company_id == company_id)
    )
    for td in tipos_doc.scalars():
        estados_exist = await db.execute(
            select(DocumentoEstado).where(
                DocumentoEstado.documento_tipo_id == td.id,
                DocumentoEstado.codigo == 'BORRADOR',
            )
        )
        if estados_exist.scalar_one_or_none():
            continue
        estados_data = [
            {"codigo": "BORRADOR", "nombre": "Borrador", "es_inicial": True, "orden": 1},
            {"codigo": "PENDIENTE", "nombre": "Pendiente", "orden": 2},
            {"codigo": "APROBADO", "nombre": "Aprobado", "orden": 3},
            {"codigo": "CONTABILIZADO", "nombre": "Contabilizado", "orden": 4},
            {"codigo": "ANULADO", "nombre": "Anulado", "es_final": True, "orden": 5},
        ]
        for edata in estados_data:
            est = DocumentoEstado(
                company_id=company_id,
                documento_tipo_id=td.id,
                **edata,
            )
            db.add(est)
        await db.flush()

    # Crear permisos extendidos
    for modulo_codigo, mod in modulos_creados.items():
        for accion in ACCIONES_PERMISO:
            codigo_permiso = f"{modulo_codigo}.{accion.lower()}"
            existing = await db.execute(
                select(Permiso).where(Permiso.codigo == codigo_permiso)
            )
            if existing.scalar_one_or_none():
                continue
            p = Permiso(
                codigo=codigo_permiso,
                nombre=f"{mod.nombre}: {accion}",
                modulo=modulo_codigo,
                module_id=mod.id,
                action_type=accion,
                scope='ALL',
            )
            db.add(p)
        await db.flush()

    # Crear paquetes (JournalType) por defecto
    for jt_data in PAQUETES_DEFAULT:
        existing = await db.execute(
            select(JournalType).where(
                JournalType.company_id == company_id,
                JournalType.code == jt_data["code"],
            )
        )
        if existing.scalar_one_or_none():
            continue
        jt = JournalType(company_id=company_id, **jt_data)
        db.add(jt)
    await db.flush()

    # Asignar todos los permisos al rol ADMIN
    admin_rol = await db.execute(
        select(Rol).where(Rol.empresa_id == company_id, Rol.nombre == 'ADMIN')
    )
    admin_rol = admin_rol.scalar_one_or_none()
    if admin_rol:
        permisos = await db.execute(select(Permiso))
        for p in permisos.scalars():
            exists = await db.execute(
                text("SELECT 1 FROM rol_permiso WHERE rol_id = :rol_id AND permiso_id = :permiso_id"),
                {"rol_id": admin_rol.id, "permiso_id": p.id},
            )
            if not exists.scalar():
                await db.execute(
                    text("INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (:rol_id, :permiso_id)"),
                    {"rol_id": admin_rol.id, "permiso_id": p.id},
                )
        await db.flush()
