from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, empresas, usuarios, roles, cuentas, productos,
    clientes, proveedores, asientos, caja, reportes, cxc, cxp,
    bi, periodos, bancos, numeraciones, monedas, tipos_cambio,
    condiciones_pago, impuestos, parametros, permisos,
    activos_fijos, empleados, nomina, presupuestos, ordenes_compra,
    conciliaciones, plantillas, tipos_asiento, ia, ocr,
    terceros, modulos, workflow, retenciones, document_engine,
    cierre,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticacion"])
api_router.include_router(empresas.router, prefix="/empresas", tags=["Empresas"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permisos.router, prefix="/permisos", tags=["Permisos"])
api_router.include_router(terceros.router, prefix="/terceros", tags=["Terceros"])
api_router.include_router(cuentas.router, prefix="/cuentas", tags=["Cuentas Contables"])
api_router.include_router(productos.router, prefix="/productos", tags=["Productos"])
api_router.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
api_router.include_router(proveedores.router, prefix="/proveedores", tags=["Proveedores"])
api_router.include_router(asientos.router, prefix="/asientos", tags=["Asientos"])
api_router.include_router(caja.router, prefix="/caja", tags=["Caja"])
api_router.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])
api_router.include_router(cxc.router, prefix="/cuentas-por-cobrar", tags=["Cuentas por Cobrar"])
api_router.include_router(cxp.router, prefix="/cuentas-por-pagar", tags=["Cuentas por Pagar"])
api_router.include_router(bi.router, prefix="/bi", tags=["Business Intelligence"])
api_router.include_router(periodos.router, prefix="/periodos", tags=["Periodos"])
api_router.include_router(bancos.router, prefix="/bancos", tags=["Bancos"])
api_router.include_router(numeraciones.router, prefix="/numeraciones", tags=["Numeraciones"])
api_router.include_router(monedas.router, prefix="/monedas", tags=["Monedas"])
api_router.include_router(tipos_cambio.router, prefix="/tipos-cambio", tags=["Tipos de Cambio"])
api_router.include_router(condiciones_pago.router, prefix="/condiciones-pago", tags=["Condiciones de Pago"])
api_router.include_router(impuestos.router, prefix="/impuestos", tags=["Impuestos"])
api_router.include_router(parametros.router, prefix="/parametros", tags=["Parametros"])
api_router.include_router(activos_fijos.router, prefix="/activos-fijos", tags=["Activos Fijos"])
api_router.include_router(empleados.router, prefix="/empleados", tags=["Empleados"])
api_router.include_router(nomina.router, prefix="/nomina", tags=["Nomina"])
api_router.include_router(presupuestos.router, prefix="/presupuestos", tags=["Presupuestos"])
api_router.include_router(ordenes_compra.router, prefix="/ordenes-compra", tags=["Ordenes de Compra"])
api_router.include_router(conciliaciones.router, prefix="/conciliaciones", tags=["Conciliaciones"])
api_router.include_router(plantillas.router, prefix="/plantillas", tags=["Plantillas"])
api_router.include_router(tipos_asiento.router, prefix="/tipos-asiento", tags=["Tipos de Asiento"])
api_router.include_router(ia.router, prefix="/ia", tags=["Inteligencia Artificial"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
api_router.include_router(modulos.router, prefix="/modulos", tags=["Modulos del Sistema"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["Workflow"])
api_router.include_router(retenciones.router, prefix="/retenciones", tags=["Retenciones"])
api_router.include_router(document_engine.router, prefix="/document-engine", tags=["Document Engine"])
api_router.include_router(cierre.router, prefix="/cierre", tags=["Cierre Contable"])
