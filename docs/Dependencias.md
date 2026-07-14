# Mapa de Dependencias

## Dependencias entre Módulos

```
                    ┌──────────────────────┐
                    │  ADMINISTRACIÓN GRAL  │ ← No depende de nadie
                    │  (Empresas/Usuarios/  │
                    │   Roles/Permisos)     │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼───┐   ┌───────▼───────┐   ┌────▼───────┐
     │ CONTABILIDAD│   │  INVENTARIO   │   │ PRESUPUESTOS│
     │ (Cuentas/   │   │  (Productos/  │   │ (Presup/CC) │
     │  Asientos)  │   │   Categorías) │   └─────────────
     └────────┬───┘   └───────┬───────┘
              │                │
              └────┬───────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
┌────▼────┐ ┌─────▼─────┐ ┌────▼────┐
│  CxC    │ │  BANCOS/  │ │ ACTIVOS │
│ (Cobros)│ │  CAJA     │ │  FIJOS  │
│ (Ventas)│ │ (Tesorería)│ │         │
└────┬────┘ └─────┬─────┘ └────┬────┘
     │             │             │
┌────▼────┐ ┌─────▼─────┐ ┌────▼────┐
│  CxP    │ │COMPRAS/OC │ │ NÓMINA  │
│ (Pagos) │ │           │ │         │
└─────────┘ └───────────┘ └─────────┘
                   │
          ┌────────▼────────┐
          │    REPORTES/BI  │ ← Depende de todos
          │  (Dashboard,    │
          │   Estados Fin.) │
          └─────────────────┘
```

## Servicios Compartidos

| Servicio | Usado por | Propósito |
|----------|-----------|-----------|
| `DocumentEngine` | CxC, CxP, (futuro: todos) | Pipeline central de procesamiento |
| `AccountingEngine` | Caja, Bancos, Activos Fijos, Nómina, CxC, CxP | Generación de asientos contables |
| `TemplateEngine` | AccountingEngine | Generación de líneas desde plantillas |
| `ExpressionEvaluator` | TemplateEngine, RuleEngine | Evaluación de expresiones |
| `RuleEngine` | DocumentEngine, WorkflowEngine | Reglas de negocio |
| `WorkflowEngine` | DocumentEngine | Transiciones de estado |
| `AsientoService` | Endpoints legacy | CRUD de asientos (legacy) |
| `AuditoriaService` | AsientoService, (potencial: todos) | Log de auditoría |
| `NumeracionService` | (potencial: todos) | Correlativos automáticos |
| `ReporteService` | Reportes endpoints | Estados financieros |

## Código Duplicado

### 1. Dualidad CxC / CxP
Los servicios `CxcService` y `CxpService` son casi idénticos:
- `crear_factura()` ↔ `crear_factura_compra()` — misma lógica, cambia modelo y document_type
- `estado_cuenta_cliente()` ↔ `estado_cuenta_proveedor()` — misma lógica, cambia modelo
- `antiguedad_saldos()` — misma lógica, cambia tabla

### 2. Dualidad de Modelos de Cuentas
Tres representaciones de cuentas contables:
- `cuenta_contable.py` → `cuenta_contable` (legacy)
- `accounting/models.py:Account` → `account` (nuevo core)
- `erp/models_cg.py:CuentaContable` → `cuenta_contable` (ERP heredado)

### 3. Dualidad de Motores Contables
Tres formas de crear asientos:
- `AsientoService.crear_asiento()` — legacy
- `AccountingEngine.generate_from_document()` — nuevo (template-based)
- `erp/accounting_engine.py` — ERP heredado

### 4. Estados de UI en Frontend
El patrón Loading/Empty/Data está duplicado en cada una de las 30 páginas. Los componentes `Skeleton` y `Empty` existen solo como funciones inline dentro de `ConfiguracionPage.tsx`, no como componentes compartidos.

### 5. Formularios CRUD
Cada página implementa su propio formulario de creación/edición con el mismo patrón de markup, sin un componente `Form` reutilizable.

## Código Reutilizable

### Backend
- **DocumentEngine**: Pipeline extensible para cualquier tipo de documento
- **AccountingEngine**: Motor de contabilización desacoplado del módulo de negocio
- **TemplateEngine**: Plantillas configurables para generación de asientos
- **RuleEngine**: Motor de reglas genérico (usable por cualquier módulo)
- **WorkflowEngine**: Motor de estados/transiciones genérico
- **ExpressionEvaluator**: Evaluador de expresiones en contexto
- **AuditoriaService**: Log de cambios genérico
- **require_permission()**: Decorator/dependencia de autorización genérico

### Frontend
- **DataTable**: Tabla genérica con columnas configurables
- **KPICard**: Tarjeta de métrica reutilizable
- **ChartCard**: Wrapper de gráficos reutilizable
- **PeriodFilter**: Selector de período reutilizable
- **api.ts**: Cliente API centralizado
- **useApi.ts**: Hook genérico de data fetching

## Ciclos de Dependencia Potenciales

No se detectaron ciclos de dependencia evidentes. La arquitectura es mayormente en árbol con Contabilidad como nodo central.

## Dependencias Externas (Shared)

- **Moneda**: Usado por CxC, CxP, Bancos, Caja, Contabilidad
- **PeriodoContable**: Usado por Asientos, Cierre, Reportes
- **CentroCosto**: Usado por Asientos, Presupuestos
- **Tercero**: Catálogo unificado de clientes/proveedores/empleados
- **Numeracion**: Usado por facturación, compras, bancos
- **CondicionPago**: Usado por CxC, CxP
- **Impuesto**: Usado por CxC, CxP
