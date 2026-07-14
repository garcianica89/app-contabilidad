# Backend — Análisis Técnico

## Estructura General

```
backend/
├── app/
│   ├── main.py               # Punto de entrada FastAPI + lifespan + SPA serving
│   ├── seed.py               # Seed inicial (datos demo)
│   ├── seed_nuevos_modulos.py # Seed complementario
│   ├── api/
│   │   ├── deps.py            # Dependencias: get_current_user, require_permission
│   │   └── v1/
│   │       ├── __init__.py    # Registro de 47 routers
│   │       └── endpoints/     # 51 archivos de endpoints
│   ├── core/
│   │   ├── config.py          # Settings (env vars)
│   │   ├── database.py        # Engine async + session factory
│   │   ├── security.py        # JWT + bcrypt
│   │   └── logging_config.py  # JSON logger
│   ├── domain/
│   │   ├── models/            # 42 modelos SQLAlchemy (entidades)
│   │   ├── accounting/        # 14 modelos + clasificaciones
│   │   ├── erp/               # 32 modelos ERP heredado (10 módulos)
│   │   └── schemas/           # Pydantic DTOs (compartido)
│   ├── service/               # Lógica de negocio
│   │   ├── accounting/        # AccountingEngine, TemplateEngine, ExpressionEvaluator
│   │   ├── document_engine/   # DocumentEngine (pipeline central)
│   │   └── erp/               # AccountingEngine + CostEngine (ERP heredado)
│   ├── repository/            # Patrón repositorio (solo accounting)
│   ├── modules/               # Módulos hook (audit/, notifications/ — vacíos)
│   └── seeds/
├── alembic/                   # Migraciones (16 versiones)
├── tests/                     # Tests unitarios (7 archivos)
├── requirements.txt
├── alembic.ini
├── pytest.ini
└── Dockerfile
```

## API Endpoints (51 routers, ~47 prefixos)

| Prefixo | Archivo | Tags | Módulo |
|---------|---------|------|--------|
| `/api/v1/auth` | auth.py | Autenticacion | Core |
| `/api/v1/empresas` | empresas.py | Empresas | Core |
| `/api/v1/usuarios` | usuarios.py | Usuarios | Core |
| `/api/v1/roles` | roles.py | Roles | Core |
| `/api/v1/permisos` | permisos.py | Permisos | Core |
| `/api/v1/terceros` | terceros.py | Terceros | Core |
| `/api/v1/cuentas` | cuentas.py | Cuentas Contables | Contabilidad |
| `/api/v1/asientos` | asientos.py | Asientos | Contabilidad |
| `/api/v1/periodos` | periodos.py | Periodos | Contabilidad |
| `/api/v1/tipos-asiento` | tipos_asiento.py | Tipos de Asiento | Contabilidad |
| `/api/v1/plantillas` | plantillas.py | Plantillas | Contabilidad |
| `/api/v1/cierre` | cierre.py | Cierre Contable | Contabilidad |
| `/api/v1/ejercicios` | ejercicios.py | Ejercicios Fiscales | Contabilidad |
| `/api/v1/cuentas-por-cobrar` | cxc.py | Cuentas por Cobrar | CxC |
| `/api/v1/cuentas-por-pagar` | cxp.py | Cuentas por Pagar | CxP |
| `/api/v1/clientes` | clientes.py | Clientes | CxC |
| `/api/v1/proveedores` | proveedores.py | Proveedores | CxP |
| `/api/v1/productos` | productos.py | Productos | Inventario |
| `/api/v1/caja` | caja.py | Caja | Tesorería |
| `/api/v1/bancos` | bancos.py | Bancos | Tesorería |
| `/api/v1/conciliaciones` | conciliaciones.py | Conciliaciones | Tesorería |
| `/api/v1/activos-fijos` | activos_fijos.py | Activos Fijos | AF |
| `/api/v1/empleados` | empleados.py | Empleados | RRHH |
| `/api/v1/nomina` | nomina.py | Nomina | RRHH |
| `/api/v1/ordenes-compra` | ordenes_compra.py | Ordenes de Compra | Compras |
| `/api/v1/presupuestos` | presupuestos.py | Presupuestos | Planificación |
| `/api/v1/reportes` | reportes.py | Reportes | Reportes |
| `/api/v1/bi` | bi.py | Business Intelligence | BI |
| `/api/v1/monedas` | monedas.py | Monedas | Configuración |
| `/api/v1/tipos-cambio` | tipos_cambio.py | Tipos de Cambio | Configuración |
| `/api/v1/condiciones-pago` | condiciones_pago.py | Condiciones de Pago | Configuración |
| `/api/v1/impuestos` | impuestos.py | Impuestos | Configuración |
| `/api/v1/parametros` | parametros.py | Parametros | Configuración |
| `/api/v1/numeraciones` | numeraciones.py | Numeraciones | Configuración |
| `/api/v1/ia` | ia.py | Inteligencia Artificial | IA |
| `/api/v1/ocr` | ocr.py | OCR | OCR |
| `/api/v1/modulos` | modulos.py | Modulos del Sistema | Core |
| `/api/v1/workflow` | workflow.py | Workflow | Core |
| `/api/v1/retenciones` | retenciones.py | Retenciones | CxP |
| `/api/v1/document-engine` | document_engine.py | Document Engine | Core |
| `/api/v1/erp/cg` | erp_cg.py | ERP Contabilidad General | ERP heredado |
| `/api/v1/erp/ci` | erp_ci.py | ERP Inventario | ERP heredado |
| `/api/v1/erp/fa` | erp_fa.py | ERP Facturacion | ERP heredado |
| `/api/v1/erp/co` | erp_co.py | ERP Compras | ERP heredado |
| `/api/v1/erp/cc` | erp_cc.py | ERP Cuentas por Cobrar | ERP heredado |
| `/api/v1/erp/af` | erp_af.py | ERP Activos Fijos | ERP heredado |
| `/api/v1/erp/cb` | erp_cb.py | ERP Tesoreria | ERP heredado |
| `/api/v1/erp/rh` | erp_rh.py | ERP Nominas | ERP heredado |
| `/api/v1/erp/pe` | erp_pe.py | ERP Pedidos y Presupuestos | ERP heredado |

## Autenticación y Autorización

### Autenticación
- **Método**: JWT (Bearer token)
- **Algoritmo**: HS256
- **Expiración**: 480 minutos (8 horas)
- **Flujo**: `POST /auth/login` → JWT → `Authorization: Bearer <token>`
- **Dependencia**: `get_current_user()` decodifica token y busca usuario en BD

### Autorización
- **Sistema**: RBAC (Role-Based Access Control)
- **Entidades**: Usuario → Rol → Permiso (many-to-many)
- **Verificación**: `require_permission("CONFIG_VER")` o `require_permission("config.ver")`
- **Soporte dual**: Formato antiguo (`CONFIG_VER`) y nuevo (`config.leer`)
- **Mapeo automático**: `ver→leer`, `editar→actualizar`
- **Permisos por módulo+acción**: `modulo = "config", action_type = "LEER"`
- **Permiso por defecto**: `scope = 'ALL'`

### Seguridad
- **CORS**: Orígenes configurados (localhost, Vercel, Railway)
- **Password hashing**: bcrypt
- **Token en localStorage**: Almacenado en cliente

## Manejo de Errores
- HTTPExceptions estándar de FastAPI
- Excepciones personalizadas: `PartidaDobleError`, `PeriodoCerradoError`, `CuentaNoValidaError`
- Errores de servicio mapeados a 400 con mensaje descriptivo
- Sin middleware global de errores

## Logging
- Formato JSON estructurado
- Logger principal: `app_contabilidad`
- Niveles: INFO por defecto, WARNING para uvicorn/sqlalchemy
- Función helper: `get_logger(name)`

## Patrones Detectados

### Dualidad de Modelos
Existen 3 representaciones diferentes para cuentas contables:
1. `domain/models/cuenta_contable.py` (tabla `cuenta_contable`) — modelo legacy
2. `domain/accounting/models.py:Account` (tabla `account`) — nuevo core contable
3. `domain/erp/models_cg.py:CuentaContable` (tabla `cuenta_contable` en schema ERP heredado) — clon ERP heredado

### Dualidad de Motores Contables
1. `service/asiento_service.py` — servicio legacy de asientos
2. `service/accounting/accounting_engine.py` — nuevo motor (template-based)
3. `service/erp/accounting_engine.py` — clon ERP heredado

### Mezcla de Estilos
- Algunos endpoints escriben SQL directo (crud simple)
- Otros delegan en servicios (lógica compleja)
- CxC/CxP usan DocumentEngine para creación, pero SQL directo para consultas
