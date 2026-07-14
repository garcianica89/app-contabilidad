# Base de Datos — Análisis Técnico

## Motor
- PostgreSQL 16+ (Neon.tech serverless cloud)
- Driver: asyncpg (conexión asíncrona)
- ORM: SQLAlchemy 2.0+ (asíncrono)

## Migraciones (Alembic)

16 migraciones en total, desde `0001_initial` hasta `0016_create_erp_tables`:

| Migración | Tablas Creadas | Propósito |
|-----------|---------------|-----------|
| 0001 | ~25 tablas | Schema inicial (usuarios, roles, empresas, cuentas, asientos, etc.) |
| 0002 | tipo_cambio_hist, condicion_pago | Tipos de cambio y condiciones de pago |
| 0003 | — (solo índices) | Índices críticos en columnas frecuentes |
| 0004 | account_type, account, journal_type, journal_template, etc. | Core contable nuevo (14 tablas) |
| 0005 | impuesto | Tabla de impuestos |
| 0006 | conciliacion_bancaria, conciliacion_detalle | Conciliación bancaria |
| 0007 | categoria_activo, activo_fijo, depreciacion_linea | Activos fijos |
| 0008 | empleado, cargo, departamento | Empleados |
| 0009 | nomina_config, nomina_periodo, nomina_detalle | Nómina |
| 0010 | presupuesto_cabecera, presupuesto_detalle, presupuesto_ejecucion | Presupuestos |
| 0011 | — | OCR (no se pudo verificar) |
| 0012 | — | IA (no se pudo verificar) |
| 0013 | — (ALTER TABLE) | Fix: asiento.numero integer→varchar(30), columnas nuevas |
| 0014 | cierre_mensual, cierre_fiscal | Cierres contables + columnas en documento_subtipo |
| 0015 | — (ALTER TABLE) | prefijo, digitos, correlativo_actual en journal_type |
| 0016 | 32 tablas (10 módulos) | Tablas ERP heredado (CG, CI, FA, CO, CC, AF, CB, RH, PE) |

**Patrón de migraciones**: 
- Todas las migraciones recientes (0013-0016) usan `op.execute()` con SQL crudo
- Usan `CREATE TABLE IF NOT EXISTS` para idempotencia
- Las alteraciones de columna usan `DO $$ ... EXCEPTION WHEN duplicate_column THEN NULL;`

## Modelo de Datos Actual

### Modelos Principales (~42 tablas en `domain/models/`)

#### Seguridad y Configuración
- `empresa` — Compañías/empresas
- `usuario` — Usuarios del sistema
- `rol` — Roles de usuario
- `permiso` — Permisos individuales
- `usuario_rol` — Asignación usuario→rol (M:N)
- `rol_permiso` — Asignación rol→permiso (M:N)
- `modulo_sistema` — Módulos del ERP (11 registros seed)
- `documento_tipo` — Tipos de documento por módulo
- `documento_subtipo` — Subtipos de documento (configuración contable)
- `documento_estado` — Estados posibles

#### Contabilidad General
- `periodo_contable` — Períodos contables (mensuales)
- `ejercicio_fiscal` — Ejercicios anuales
- `cuenta_contable` — Catálogo de cuentas (jerárquico, 8 niveles)
- `asiento` — Asientos contables (cabecera)
- `asiento_linea` — Líneas de asiento (partida doble)
- `centro_costo` — Centros de costo (jerárquico)

#### Core Contable (nuevo)
- `account` — Cuentas contables (nuevo modelo, coexiste con cuenta_contable)
- `account_type` — Tipos de cuenta (ACTIVO, PASIVO, etc.)
- `financial_classification` — Clasificación financiera
- `tax_classification` — Clasificación fiscal
- `ifrs_classification` — Clasificación IFRS
- `company_account_structure` — Estructura de niveles por empresa
- `journal_type` — Tipos de asiento/paquetes (17 seed)
- `journal_template` — Plantillas de asientos
- `journal_template_line` — Líneas de plantilla
- `module_accounting_config` — Configuración contable por módulo
- `accounting_event` — Eventos contables
- `accounting_rule` — Reglas contables
- `accounting_rule_log` — Log de ejecución de reglas
- `cxc_document_subtype` — Subtipos de documento CxC + cuentas
- `cxp_document_subtype` — Subtipos de documento CxP + cuentas
- `numeracion` — Correlativos por serie/tipo

#### CxC / Facturación
- `cliente` — Clientes
- `factura_venta` — Facturas de venta
- `factura_venta_linea` — Líneas de factura

#### CxP / Compras
- `proveedor` — Proveedores
- `factura_compra` — Facturas de compra
- `factura_compra_linea` — Líneas de factura
- `orden_compra` — Órdenes de compra
- `orden_compra_linea` — Líneas de OC
- `retencion` — Retenciones (IR, IVA)

#### Inventario
- `producto` — Productos
- `categoria` — Categorías de producto
- `unidad_medida` — Unidades de medida
- `bodega` — Bodegas/almacenes

#### Bancos / Tesorería
- `cuenta_banco` — Cuentas bancarias
- `movimiento_banco` — Movimientos bancarios
- `conciliacion_bancaria` — Conciliaciones
- `conciliacion_detalle` — Partidas conciliadas
- `caja` — Cajas (efectivo)
- `movimiento_caja` — Movimientos de caja
- `arqueo_caja` — Arqueos de caja

#### Activos Fijos
- `categoria_activo` — Categorías de activo
- `activo_fijo` — Activos fijos
- `depreciacion_linea` — Líneas de depreciación

#### RRHH / Nómina
- `empleado` — Empleados
- `cargo` — Cargos/puestos
- `departamento` — Departamentos
- `nomina_config` — Configuración de nómina
- `nomina_periodo` — Períodos de nómina
- `nomina_detalle` — Detalle de nómina por empleado

#### Otros
- `moneda` — Monedas (NIO, USD)
- `tipo_cambio_hist` — Historial de tipos de cambio
- `condicion_pago` — Condiciones de pago
- `impuesto` — Impuestos (IVA, etc.)
- `parametro` — Parámetros del sistema
- `tercero` — Catálogo único de terceros
- `sucursal` — Sucursales
- `presupuesto_cabecera` — Presupuestos
- `presupuesto_detalle` — Partidas presupuestarias
- `presupuesto_ejecucion` — Ejecución presupuestaria
- `feature_flag` — Feature flags
- `wf_workflow` — Workflows
- `wf_status` — Estados de workflow
- `wf_transition` — Transiciones
- `wf_document_history` — Historial de documentos
- `wf_pending_approval` — Aprobaciones pendientes
- `auditoria` — Auditoría de cambios
- `cierre_mensual` — Cierres mensuales
- `cierre_fiscal` — Cierres fiscales
- `ocr_documento` — Documentos OCR
- `analisis_ia` — Análisis de IA

### Modelos ERP heredado (~32 tablas en `domain/erp/`)
Migración 0016 crea tablas con prefijo de módulo: `cg_cuenta_contable`, `ci_articulo`, `fa_cliente`, `co_proveedor`, etc. (nombres sin prefijo real en BD). Todos incluyen columnas de auditoría ERP heredado.

## Relaciones Clave

```
Empresa ──┬── Usuario
          ├── Rol ── Permiso
          ├── PeriodoContable ── Asiento ── AsientoLinea ── Account
          ├── CuentaContable (jerárquico, padre→hijos)
          ├── Cliente ── FacturaVenta ── FacturaVentaLinea
          ├── Proveedor ── FacturaCompra ── FacturaCompraLinea
          ├── Producto
          ├── CuentaBanco ── MovimientoBanco
          ├── Caja ── MovimientoCaja
          └── Moneda (local)
```

## Llaves Primarias
- **Todas las tablas**: UUID v4 como PK (`id`)
- Generadas en aplicación con `uuid.uuid4()`
- Las tablas ERP heredado también usan UUID

## Índices
- Migración 0003 añadió índices críticos
- Foreign keys tienen índices implícitos (PostgreSQL)
- Algunas columnas tienen `unique=True` (username, email, ruc, codigo)

## Normalización
- Mayormente 3NF (Tercera Forma Normal)
- Algunas tablas tienen redundancia controlada (saldo_actual en caja, costo_promedio en producto)
- La tabla `account` tiene desnormalización controlada (financial_classification, tax_classification, ifrs_classification como FK directas)

## Dualidad de Modelos
Existen **dos sistemas de cuentas contables**:
1. `cuenta_contable` (legacy) — tabla original con estructura jerárquica simple
2. `account` (nuevo) — tabla con clasificaciones IFRS/fiscal/financiera

Y **tres sistemas de asientos**:
1. `asiento` + `asiento_linea` (legacy)
2. `asiento_de_diario` + `diario` (ERP heredado CG)
3. `mayor` (ERP heredado, mayorización)
