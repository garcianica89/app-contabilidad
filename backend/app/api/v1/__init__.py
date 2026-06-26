from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, empresas, usuarios, roles, cuentas, productos,
    clientes, proveedores, asientos, caja, reportes, cxc, cxp,
    bi, periodos,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticacion"])
api_router.include_router(empresas.router, prefix="/empresas", tags=["Empresas"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
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
