# Informe Ejecutivo — Auditoría Técnica

> **Proyecto**: App Contabilidad ERP
> **Fecha**: Julio 2026
> **Auditor**: Arquitecto Principal de Software
> **Propósito**: Conocer el sistema antes de proponer cambios

---

## 1. Resumen General del Proyecto

ERP contable full-stack con 3 canales de acceso (web SPA, mobile PWA, desktop Electron). Orientado a empresas Nicaragüenses, con moneda dual (NIO/USD) y cumplimiento fiscal local (INSS, IR, IVA). Construido sobre PostgreSQL (Neon.tech cloud) con backend FastAPI asíncrono y frontend React + TailwindCSS.

**Origen**: Inspirado en ERP heredado (benchmark funcional declarado). Comenzó como dashboard BI y evolucionó a ERP completo.

---

## 2. Estado Actual del ERP

### Qué funciona bien (producción-ready):
- ✅ Autenticación JWT + RBAC con permisos reales
- ✅ Contabilidad General (catálogo, asientos, períodos, cierres)
- ✅ CxC / CxP (facturación, antigüedad, estado cuenta)
- ✅ Bancos / Caja (movimientos con generación de asientos)
- ✅ Activos Fijos (depreciación, bajas)
- ✅ Nómina (períodos, procesamiento, pago)
- ✅ Inventario (productos, categorías, kardex)
- ✅ Órdenes de Compra
- ✅ Presupuestos
- ✅ Reportes financieros (Balance General, ER, Flujo Efectivo)
- ✅ Dashboard BI con KPIs y gráficos
- ✅ DocumentEngine (pipeline central)
- ✅ AccountingEngine (motor de contabilización template-based)

### Qué existe pero incompleto:
- ⚠️ Workflow (motor funcional, sin integración real)
- ⚠️ Conciliación Bancaria (funcionalidad básica, sin UI completa)
- ⚠️ OCR / IA (endpoints + páginas, funcionalidad básica)
- ⚠️ Cobros / Pagos (endpoints vía DocumentEngine, sin UI dedicada)
- ⚠️ Sucursales / Bodegas (modelos creados, sin endpoints ni UI)
- ⚠️ Retenciones (CRUD completo, sin integración real en facturación)

### Qué no existe:
- 🔲 Módulo de Importaciones
- 🔲 Módulo de Producción
- 🔲 Módulo de Puntos de Venta (POS)
- 🔲 Módulo de CRM
- 🔲 Módulo de Contratos
- 🔲 Dashboard de RRHH
- 🔲 Reportes personalizables
- 🔲 Notificaciones en tiempo real
- 🔲 Auditoría de cambios (solo log de asientos)

---

## 3. Arquitectura Encontrada

### Tipo: Arquitectura de Capas (Layered Architecture)
```
API Layer (endpoints FastAPI)
    ↓
Service Layer (lógica de negocio)
    ↓
Domain Layer (modelos SQLAlchemy)
    ↓
Database Layer (PostgreSQL)
```

### No es:
- ❌ No es Clean Architecture (no hay separación de puertos/adaptadores)
- ❌ No es DDD (no hay bounded contexts, aggregates, value objects)
- ❌ No es Microservicios (monolito backend)
- ❌ No es CQRS (mismos modelos para lectura/escritura)
- ❌ No usa Repository Pattern (solo existe un repositorio real)

### Estilo:
- **Backend**: Monolito modular por carpetas
- **Frontend**: SPA tradicional por páginas
- **Base de datos**: Tablas por módulo, UUIDs, sin schema separation

---

## 4. Fortalezas

1. **DocumentEngine**: Pipeline centralizado que unifica el procesamiento de todos los documentos del ERP. Conceptualmente correcto y extensible.

2. **AccountingEngine**: Motor de contabilización template-based. Las plantillas de asientos son configurables (vía BD), no hardcodeadas. Esto permite adaptación contable sin código.

3. **RBAC real**: Permisos verificados contra BD real (usuario→rol→permiso). Soporte dual de formatos (legacy y nuevo). Mapeo automático de acciones.

4. **Numeración por paquete**: JournalType maneja prefijo, dígitos y correlativo para asientos. Formato `{PREFIJO}{CORRELATIVO}`.

5. **Moneda dual**: Toda transacción registra montos en moneda local y USD, con tipo de cambio histórico.

6. **Cobertura funcional**: 11 módulos funcionales, ~80 endpoints API, 30 páginas frontend. Cobertura sólida para una PYME.

7. **Generación automática de asientos**: Caja, Bancos, Activos Fijos, Nómina, CxC y CxP generan asientos automáticamente a través del AccountingEngine.

8. **Tests unitarios**: 7 archivos de test con mocks asíncronos.

9. **Idempotencia en migraciones**: Todas las migraciones recientes son idempotentes (CREATE IF NOT EXISTS).

---

## 5. Debilidades

1. **Dualidad de modelos**: Existen 3 sistemas paralelos para cuentas contables y asientos (legacy, nuevo core, clon ERP heredado). Esto duplica lógica y confunde.

2. **Mezcla de estilos en endpoints**: Algunos endpoints usan servicios, otros hacen SQL directo en el handler. No hay consistencia.

3. **Sin inyección de dependencias**: Los servicios se instancian manualmente en cada endpoint. No hay contenedor DI.

4. **Sin estado global en frontend**: Cada página maneja su estado local. Sin Context, Redux, ni caché. Las llamadas API se repiten en cada montaje.

5. **Sin tests frontend**: Cero archivos de test en el frontend.

6. **TypeScript subutilizado**: Uso extensivo de `any[]`. Las respuestas de API no están tipadas.

7. **Manejo de errores inconsistente**: Algunas páginas tragan errores silenciosamente (`catch {}`). Otras usan `alert()`. No hay manejo global.

8. **Componentes Skeleton/Empty duplicados**: El patrón de 3 estados (loading/empty/data) se repite inline en cada página. No hay componentes compartidos.

9. **CategoriasPage usa fetch directo**: Única página que no usa el objeto `api` centralizado.

10. **Sin lazy loading**: Las 30 páginas se importan estáticamente en App.tsx.

---

## 6. Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Descripción |
|--------|-------------|---------|-------------|
| **Dualidad de motores contables** | Alta | Alto | Tres formas de crear asientos pueden producir inconsistencias contables. |
| **Track ERP heredado paralelo** | Media | Alto | 32 tablas + 9 routers duplicados sin integración con el sistema principal. Riesgo de divergencia. |
| **Token en localStorage** | Media | Alto | Vulnerable a XSS. Sin refresh tokens. Sin httpOnly cookies. |
| **Sin migraciones automáticas** | Baja | Medio | Base.metadata.create_all() en startup + migraciones manuales puede causar desincronización. |
| **Sin backup/restore** | Desconocido | Alto | No se encontró configuración de backups. Dependencia total de Neon.tech. |
| **Sin límites de paginación** | Baja | Medio | Algunos endpoints no tienen límite de resultados (ej: listar_asientos sin max). |
| **features/ vacías** | Alta | Medio | 7 carpetas de features creadas pero vacías. Indican arquitectura soñada vs implementada. |
| **Monolito sin separación** | Baja | Medio | El backend es un monolito. Escalar requiere dividir. |
| **Sin monitoreo** | Alta | Medio | No se encontró logging estructurado en producción ni métricas. |

---

## 7. Componentes Críticos

Estos componentes NO DEBEN modificarse sin entender su funcionamiento completo:

1. **`service/document_engine/engine.py`** (517 líneas) — Pipeline central. Todos los documentos pasan por aquí. Es el corazón del ERP.

2. **`service/accounting/accounting_engine.py`** (268 líneas) — Motor de contabilización. Genera asientos desde contexto de documentos.

3. **`service/accounting/template_engine.py`** (228 líneas) — Genera líneas de asiento desde plantillas configurables. Lógica compleja de resolución de cuentas.

4. **`service/asiento_service.py`** (244 líneas) — Servicio legacy de asientos. Aún usado por endpoints directos.

5. **`api/deps.py`** (127 líneas) — Sistema de autorización RBAC. La función `require_permission()` es crítica para seguridad.

6. **`app/seed.py`** (301 líneas) — Seed inicial. Crea empresa demo, plan de cuentas, monedas, períodos, etc.

7. **`app/domain/accounting/models.py`** (369 líneas) — 14 modelos del core contable. Incluye JournalType, JournalTemplate, AccountingEvent, AccountingRule, CierreMensual, CierreFiscal.

---

## 8. Código Duplicado

### Prioridad Alta

| Duplicación | Archivos | Líneas Aprox |
|-------------|----------|-------------|
| CxcService ↔ CxpService | `service/cxc_service.py` ↔ `service/cxp_service.py` | ~170 c/u (~80% duplicado) |
| account ↔ cuenta_contable ↔ erp CuentaContable | 3 modelos diferentes | ~30 c/u |
| AccountingEngine (principal) ↔ AccountingEngine (erp) | 2 motores | ~250 c/u |
| AsientoService.crear_asiento ↔ AccountingEngine._create_entry | 2 formas de crear asientos | ~100 c/u |

### Prioridad Media

| Duplicación | Descripción |
|-------------|-------------|
| Estados Loading/Empty en 30 páginas | Skeleton y Empty states duplicados inline |
| Formularios CRUD | Mismo patrón de formulario en cada página |
| Filtros de búsqueda | Mismo patrón de search/filter en cada página |

---

## 9. Posibles Cuellos de Botella

1. **DocumentEngine como bottleneck**: Todos los documentos pasan por un solo pipeline. Si falla, nada funciona. Sin colas ni procesamiento asíncrono.

2. **AccountingEngine sin transacciones distribuidas**: El motor crea asientos pero no hay rollback coordinado si falla un paso posterior.

3. **Sin caché**: El dashboard BI ejecuta consultas pesadas (UNION de factura_venta + factura_compra, SUM agrupados por mes) en cada carga.

4. **Consultas sin índices**: Algunas consultas en el dashboard usan `text()` con joins múltiples sin verificar cobertura de índices.

5. **Crecimiento de asientos_linea**: La tabla crece linealmente con cada transacción. Sin particionamiento ni archivado planeado.

6. **Sin paginación en listados**: Endpoints como GET /asientos/ podrían devolver miles de registros.

---

## 10. Aspectos a Revisar Antes de Continuar

### Críticos

1. **Resolver la dualidad de modelos contables**: Decidir si se migra a `account` + `AccountingEngine` o se mantiene `cuenta_contable` + `AsientoService`. Mantener ambos es insostenible.

2. **Decidir qué hacer con el track ERP heredado**: 32 tablas paralelas, 9 routers, 2 motores. ¿Es una migración futura? ¿Un experimento? ¿Código muerto? Hay que definirlo.

3. **Centralizar la creación de asientos**: Hoy hay 3 caminos para crear un asiento. Debe haber UNO solo (idealmente AccountingEngine).

### Importantes

4. **Agregar estado global al frontend**: Context API o Zustand para compartir sesión, empresa activa, período seleccionado.

5. **Tipar las respuestas de API**: Reemplazar `any[]` con interfaces fuertes. Hay ~80 métodos en api.ts que devuelven `any`.

6. **Estandarizar el manejo de errores**: Unificar el patrón de errores en frontend (toast/snackbar en vez de alert o silencio).

7. **Extraer componentes compartidos**: Skeleton, Empty, FormField, ConfirmDialog como componentes reutilizables.

8. **Agregar lazy loading**: React.lazy + Suspense para las rutas del frontend.

### Técnicos

9. **Implementar refresh tokens**: El token JWT de 8 horas sin refresh es un riesgo de seguridad.

10. **Agregar tests de integración**: La carpeta `tests/integration/` está vacía. Sin tests que verifiquen el pipeline completo.

11. **Revisar indexing**: Analizar las consultas lentas (especialmente dashboard y reportes) y agregar índices compuestos donde falten.

12. **Documentar la decisión arquitectónica**: El proyecto tiene 3 arquitecturas superpuestas (legacy, nueva, ERP heredado). Sin documentación que explique por qué.

### Nota Final

El proyecto tiene una base sólida: un motor contable configurable, un pipeline de documentos centralizado, y cobertura funcional amplia. Sin embargo, arrastra decisiones arquitectónicas tempranas (dualidad de modelos, mezcla de estilos) que deben resolverse antes de agregar más funcionalidad. La prioridad debe ser consolidar lo existente, no expandir.
