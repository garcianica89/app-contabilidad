# App Contabilidad - Guia para Agentes AI

## Stack
- **Backend**: FastAPI + SQLAlchemy 2.x + asyncpg (PostgreSQL en Neon.tech)
- **Frontend**: React 18 + Vite + TailwindCSS + Recharts + PWA
- **Desktop**: Electron (wrapper alrededor del frontend web)
- **Database**: PostgreSQL 16+ (Neon.tech cloud)

## Comandos

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Build Frontend + Copiar a Backend
```bash
cd frontend && npm run build
rm -rf ../backend/static && cp -r dist ../backend/static
```

### Desktop (Electron)
```bash
cd electron
npm install
npm run dev  # Desarrollo (conecta a localhost:5173)
npm run build:win  # Empaquetar para Windows
```

### Base de Datos
- **URL actual**: `postgresql+asyncpg://neondb_owner:npg_3cY0yoMxnfah@ep-red-lab-atfxoamb-pooler.c-9.us-east-1.aws.neon.tech/neondb`
- **Host**: Neon.tech (serverless PostgreSQL)
- **Credenciales en**: `backend/.env`

### Docker (produccion en la nube)
```bash
docker compose up backend -d  # Solo backend (usa Neon.tech)
```

## Arquitectura

```
┌─────────────────────────┐     ┌──────────────────┐
│   Desktop (Electron)    │     │   Mobile (PWA)   │
│   Windows App           │     │   Android/iOS    │
└──────────┬──────────────┘     └────────┬─────────┘
           │                             │
           └──────────┬──────────────────┘
                      │ HTTP/JSON
              ┌───────▼────────┐
              │  FastAPI (cloud)│
              │  Railway/Fly   │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │  PostgreSQL    │
              │  (Neon.tech)   │
              └────────────────┘
```

## Usuarios Seed
- **Usuario**: `rgarcia` / `exrgarcia` (admin)
- **Empresa**: Tuckler Beauty (Nicaragua, C$)

## Endpoints Principales
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/bi/dashboard` - Dashboard KPIs
- `GET /api/v1/reportes/*` - Reportes financieros
- `POST /api/v1/asientos` - Crear asientos contables
- `POST /api/v1/cuentas-por-cobrar/facturas` - Facturas de venta

## Correcciones Frontend (Build Fixes)
- Agregado `src/lucide-react.d.ts` - declaraciones de tipos para todos los iconos usados (lucide-react v0.441.0 no incluye .d.ts)
- `src/services/api.ts` - agregados ~80 metodos faltantes para todos los modulos (activos fijos, cuentas contables, tipos asiento, plantillas, conciliacion, parametros, monedas, tipos de cambio, condiciones pago, impuestos, empleados, nomina, OCR, IA, presupuestos, roles/permisos, ordenes compra, facturas compra, numeraciones, categorias)
- Corregidas firmas de `getAnalisisIA(tipo?)` y `getEmpleados(params?)` para aceptar filtros opcionales

## Alembic Migrations
- Migraciones existentes en `backend/alembic/versions/` (0001-0022 aplicadas)
- Para aplicar migraciones pendientes: `cd backend && PYTHONPATH=. alembic upgrade head`
- Nota: Usar `op.execute('CREATE ... IF NOT EXISTS')` para idempotencia en PostgreSQL
- `asiento.numero` es `varchar(30)` en BD (migracion 0013 aplicada)
- El directorio `alembic/` en backend tiene un `__init__.py` que shadowea el package real; se recomienda borrarlo (`rm alembic/__init__.py`)

## Session Actual (Jul 2026)
**Ultima sesion**: RBAC completo con permisos directos por usuario + entidad, PermissionContext frontend, sidebar gating, fix payload asignacion rol:

### Sistema RBAC (Jul 2026)
- **Migration 0030** aplicada: tabla `usuario_permiso` con FK usuario/permiso + entity_type/entity_id opcionales + allow
- **Migration 0029** aplicada: CHECK constraints `chk_asiento_linea_debe_haber`, `chk_asiento_linea_non_negative`
- **Permiso model**: nuevos campos `empresa_id`, `is_system`
- **UsuarioPermiso model**: `usuario_id`, `permiso_id`, `entity_type` (NULL=global), `entity_id`, `allow`, `created_at`
- **`permission_service.py`**: `user_has_perm()` — unifica rol + directo + entity-scoped + deny override; `get_user_permissions()` — retorna lista de codigos
- **`deps.py`**: `require_permission` reescrito con `user_has_perm()`; nuevo `require_entity_permission(codigo, entity_type)` para scoping
- **`permisos.py` endpoint**: rutas nuevas — `GET /mis-permisos`, `GET /mis-permisos/entidad/{type}/{id}`, `GET /usuario/{id}/permisos`, `POST /usuario/{id}/permisos` (asignar con scoping), `DELETE /usuario/{id}/permisos/{up_id}`
- **Fix `asignarPermisosRol`**: payload cambiado de `["uuid"]` a `{"permiso_ids":["uuid"]}` para coincidir con backend Pydantic
- **Fix `BancosPage` moneda hardcodeada** — ahora carga monedas desde API (`getMonedas()`), selector dinamico
- **Fix `cierre.py` SQL ambiguo**: alias `account a` → `acct`; `_calcular_resultado_ejercicio` ahora filtra por fecha
- **`PermissionContext.tsx`**: proveedor React que carga permisos al login, expone `has()`, `hasAny()`, `hasAll()`
- **`Can.tsx`**: componente de gating — `<Can permiso="inventario_ver"><Button/></Can>`
- **`Sidebar.tsx`**: cada `MenuItem` tiene `permiso?` opcional; sidebar filtra dinamicamente items/grupos basado en permisos del usuario
- **`PermisosUsuariosPage.tsx`**: frontend completo — lista usuarios a la izquierda, permisos agrupados por modulo a la derecha, toggle on/off con feedback visual
- **Metodos `api.ts`**: `misPermisos()`, `misPermisosEntidad()`, `getPermisosUsuario()`, `asignarPermisoUsuario()`, `eliminarPermisoUsuario()`
- **Ruta `/permisos`**: en sidebar bajo "Administracion General" como "Permisos Usuario"

### Arquitectura de Permisos
- `rol_permiso` + `usuario_permiso` coexisten: ambos se consultan en `user_has_perm()`
- `allow=false` en `usuario_permiso` sirve como denegacion explicita que overridea rol
- `entity_type` + `entity_id` permiten scoping a nivel de instancia (ej. permiso `asientos_ver` sobre asiento X)
- Sidebar y componentes deben usar `usePermissions().has(codigo)` para gating UI
- Backend usa `require_permission(codigo)` o `require_entity_permission(codigo, entity_type)` en Depends
- Permisos actualmente seeded con `is_system=true` en seed_modulos; permisos custom pueden crearse sin flag system

### MOV_BANCO + Bancos Configurables (Jul 2026)
- **DocumentoTipo `MOV_BANCO`** añadido a modulo bancos (seed_modulos) — convive con DEBITO/CREDITO/CHEQUE/TRANSFERENCIA existentes
- **MOV_BANCO AccountingEvent + Template**: "Plantilla Movimiento Bancario" (CB) con lineas DEBIT SUBTYPE + CREDIT FIXED (1-1-1-1-01-00-00-0000), ambas con invert_in_banking=True
- **DocumentEngine._get_module()**: añadido MOV_BANCO → bancos
- **TemplateEngine._get_subtype_account()**: handler para MOV_BANCO (cuenta_principal_id)
- **Endpoint `POST /bancos/movimientos-configurables`**: procesa via DocumentEngine con MOV_BANCO + subtype_code, genera asiento contable
- **BancosPage frontend**: nuevo formulario "Mov. Configurable" con selector de subtipos MOV_BANCO (desde API), cuenta, fecha, tipo, monto, concepto, no. documento

### OrdenCompra + Compras (Jul 2026)
- **Migración 0022**: Añade `bodega_id`, `condicion_pago_id`, `descuento`, `retencion_ir` a `orden_compra`; `descuento`, `aplica_iva`, `tasa_iva` a `orden_compra_linea`
- **OrdenCompra model**: nuevos campos + `lineas` relationship (selectin loading)
- **Endpoint `/ordenes-compra`**: schemas Pydantic completos (Create con lineas + Response con lineas), soporta todos los nuevos campos
- **Frontend ComprasPage**: formulario OC con selector de bodega, condicion pago, descuento %, retencion IR, checkbox IVA + tasa por linea
- **Frontend ComprasPage**: formulario FacturaCompra con selector de orden de compra (solo ordenes APROBADAS)
- **Flujo**: OrdenCompra (EMITIDA→APROBADA→ANULADA) + FacturaCompra → DocumentEngine → Inventario (via `_update_inventory`) + CxP (via `_update_cxp`) + Contabilidad (via `_generate_entry`)
- **Seed COMPRA** config: `afecta_inventario: True`, `afecta_cxp: True`, `genera_asiento: True`

### Retenciones + Proveedor Fiscal (Jul 2026)
- **Retencion** model: `codigo`, `nombre`, `tipo` (IR/IVA/MUNICIPAL/OTRO), `porcentaje`, `aplica_a`, `monto_minimo`, `base_imponible` (SUBTOTAL/TOTAL/MONTO), `prioridad`, `redondeo`, `naturaleza` (DEBITO/CREDITO), `cuenta_retencion_id`, `cuenta_pagar_id`, `cuenta_cobrar_id`, `centro_costo_id`, `vigencia_desde/hasta` (migración 0020-0021)
- **Proveedor** model: `tipo_fiscal` (NORMAL/EXENTO/EXONERADO/AGENTE_RETENEDOR), `sujeto_retenciones`, `retenciones` M2M via `proveedor_retencion`
- **RetencionesPage**: CRUD completo con todos los campos contables, filtro, toggle activo
- **ProveedoresPage**: selectores de tipo_fiscal, sujeto_retenciones, pills de retenciones activas
- **Nota**: Retenciones NO se aplican al crear factura — se aplican en modulo CxP al procesar pagos

### IVA por Línea + Descuento por Línea (Jul 2026)
- **FacturaVentaLinea** y **FacturaCompraLinea**: `aplica_iva`, `tasa_iva` (migración 0019)
- **Frontend FacturacionPage**: cada línea tiene checkbox IVA + tasa % + descuento %; IVA calculado sobre neto (precio - descuento)
- **ComprasPage**: IVA por línea en facturas (checkbox + tasa %); descuento a nivel documento
- **CxpService/CxcService**: forwardean `aplica_iva`/`tasa_iva` por línea al DocumentEngine

### DocumentEngine (Jul 2026)
- `_load_config()` lee config desde DocumentoTipo/Subtipo en BD
- `DocumentConfig` tiene `cuenta_descuentos_id`, `cuenta_costo_venta_id`, `cost_center_default_id`
- Pipeline completo: Validate → LoadConfig → Pre-process → Numeracion → Workflow → Rules → Accounting → Cost of Sale → Inventory → CxC/CxP → Banking → Post-process
- **COMPRA** type: `_update_inventory()` añade stock + recalcula costo promedio ponderado; `_update_cxp()` crea FacturaCompra

### Salidas de Inventario Configurables (SALIDA_INV) (Jul 2026)
- **DocumentoTipo `SALIDA_INV`** con subtipos configurables (NO hardcodeados en seed)
- Subtipos se crean dinamicamente por el admin via `POST /api/v1/configuracion-documento/subtipos` o desde el mismo frontend SalidasInventarioPage
- Cada subtipo parametrizable con `cuenta_principal_id` (cuenta de gasto/pérdida contable) via configuracion-documento
- **Seed**: solo se crea el DocumentoTipo SALIDA_INV en modulo inventario, sin subtipos predefinidos
- **AccountingEvent**: `SALIDA_INV` linked to JournalType `CI` (Control de Inventarios)
- **Template**: "Plantilla Salida Inventario" con DEBIT → account_source='SUBTYPE' (resuelve cuenta desde subtipo.cuenta_principal_id) y CREDIT → account_source='FIXED' (Inventario 1-1-3-1-01-00-00-0000), ambos con `{{costo_total}}`
- **TemplateEngine._get_subtype_account()**: añadido handler para SALIDA_INV
- **DocumentEngine._get_module()**: añadido SALIDA_INV → inventario
- **Endpoint `/api/v1/inventario/salidas`**: POST (crea via DocumentEngine → inventario + contabilidad), GET (lista desde Asiento.documento_tipo='SALIDA_INV'), GET /{documento_id}
- **Frontend SalidasInventarioPage**: formulario con fecha, selector dinámico de subtipos (desde API), boton inline para crear subtipo nuevo, bodega, motivo, lineas de producto + cantidad (costo desde costo_promedio), tabla de listado
- **Ruta**: `/salidas-inventario` en sidebar bajo Inventarios

### Nuevos Endpoints
- **`/api/v1/bodegas`**: endpoint GET listar bodegas activas por empresa
- **`/api/v1/inventario/salidas`**: CRUD salidas de inventario configurables
- **`/api/v1/configuracion-documento/subtipos`**: GET (listar subtipos por tipo_codigo) + POST (crear subtipo nuevo)
- **Configuracion-documento endpoint**: expone `cuenta_descuentos_id`, `cuenta_principal_id`, `cuenta_impuestos_id`, `cuenta_retencion_id`, `cost_center_default_id`

### Backend fixes
- `alembic/__init__.py` eliminado porque shadowea el package `alembic` real (causa `ModuleNotFoundError: No module named 'alembic.config'`)

## Notas Importantes
- Los modelos SQLAlchemy usan `Uuid()` (compatible PostgreSQL/SQLite)
- El frontend tiene PWA configurado con `vite-plugin-pwa`
- El build del frontend se copia a `backend/static/` para produccion
- Todos los clientes (desktop, mobile, web) usan la misma API cloud
- Migración 0017 añade columnas IVA a proveedor y producto (aplica tras `alembic upgrade head`)
- Migración 0019 añade flags de configuración a documento_subtipo + IVA por línea a factura_compra/venta_linea
- Migración 0020 añade centro_costo_id a retencion + tabla proveedor_retencion
- Migración 0027 añade ultimo_numero a documento_subtipo + subtipo_id/numero_subtipo a movimiento_banco

## Cargador de Movimientos Bancarios (Jul 2026)
- **Módulo nuevo**: `backend/app/service/cargador_service.py` — parsea Excel/CSV/OFX, detecta columnas automáticamente, resuelve subtipos por código
- **Columnas Excel requeridas**: `fecha`, `concepto`, `monto`; opcionales: `referencia`, `saldo`, `subtipo_codigo`, `tipo`
- **Clasificador automático**: `backend/app/service/clasificador_service.py` — matching contra facturas CxP/CxC pendientes por monto ± fecha, reglas por keyword
- **Numeración por subtipo**: cada `DocumentoSubtipo` tiene `ultimo_numero`; al importar, si el movimiento tiene `subtipo_codigo`, se asigna `numero_subtipo` correlativo
- **Endpoint `/api/v1/cargador/`**:
  - `POST /preview` — subir archivo (multipart), devuelve movimientos parseados + detección de duplicados
  - `POST /clasificar` — sugiere módulo CxP/CxC/BANCO para cada movimiento
  - `POST /importar` — confirma importación, crea MovimientoBanco + conciliación + vincula facturas
  - `POST /auto-match` — sugiere pares LIBRO↔ESTADO en conciliación por monto+fecha
  - `POST /auto-match/aplicar` — confirma matches sugeridos
  - `POST /ajustes` — crea asiento de ajuste por diferencias (comisiones, intereses)
  - `GET /movimientos-sin-clasificar` — lista movimientos sin clasificar
  - `POST /vincular-partida` — vincula partida a factura CxP/CxC
- **Frontend `CargadorMovimientosPage.tsx`**: ruta `/cargador-movimientos` en sidebar bajo "Control Bancario"
  - Step 1: seleccionar cuenta + archivo (Excel/CSV/OFX)
  - Step 2: preview con tabla (fecha, concepto, subtipo, monto, clasificación, confianza)
  - Step 3: resultado de importación (movimientos creados, conciliaciones, vinculaciones)
  - Clasificación automática con indicador de confianza (verde ≥80%, amarillo ≥50%, gris)
- **Migration 0027**: `documento_subtipo.ultimo_numero` (Integer, default 0), `movimiento_banco.subtipo_id` (FK), `movimiento_banco.numero_subtipo` (Integer)
