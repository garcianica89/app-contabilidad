# Módulos del ERP — Estado por Módulo

## Leyenda
- ✅ **Funcional**: Endpoints + Servicios + Página Frontend completos
- ⚠️ **Parcial**: Funcionalidad básica, faltan features
- 🗂️ **Solo Backend**: API existe, Frontend no tiene página
- 🖥️ **Solo Frontend**: Página existe pero API limitada
- 🔲 **No implementado**: No existe código funcional

---

## 1. ADMINISTRACIÓN GENERAL

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Empresas | ✅ Funcional | CRUD básico (3 endpoints). Página frontend con grid. Sin auth (endpoints públicos). |
| Usuarios | ✅ Funcional | CRUD + asignación de roles. Página frontend completa. |
| Roles | ✅ Funcional | CRUD + asignación de permisos con árbol. Página frontend completa. |
| Permisos | ✅ Funcional | Seed automático por módulo. Verificación RBAC real. |
| Módulos | ✅ Funcional | CRUD de módulos del sistema, tipos documento, subtipos. |
| Workflow | ⚠️ Parcial | Motor funcional (WorkflowEngine con transiciones, aprobaciones, historial). Sin integración real con documentos. |
| Auditoría | ⚠️ Parcial | Modelo `Auditoria` existe. `AuditoriaService` tiene `log()` y `log_asiento()`. Sin endpoints públicos ni UI. |
| Sucursales | 🗂️ Solo Backend | Modelo creado. Sin endpoints CRUD ni UI. |
| Feature Flags | 🗂️ Solo Backend | Modelo creado. Sin uso real. |

**Entidades**: Empresa, Usuario, Rol, Permiso, ModuloSistema, DocumentoTipo, DocumentoSubtipo, Sucursal, FeatureFlag, WfWorkflow, WfStatus, WfTransition, Auditoria

**Depende de**: Nada (módulo base)
**Dependen de él**: Todos los módulos

---

## 2. CONTABILIDAD GENERAL

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Catálogo Cuentas | ✅ Funcional | CRUD completo + árbol jerárquico. Página frontend con vista de árbol. |
| Asientos | ✅ Funcional | Creación, listado, obtención, reversión. Validación partida doble, período cerrado. |
| Tipos de Asiento | ✅ Funcional | CRUD de JournalType con prefijo/dígitos/correlativo. |
| Plantillas | ✅ Funcional | CRUD de JournalTemplate con líneas configurables. |
| Períodos | ✅ Funcional | CRUD de períodos contables. |
| Ejercicios | ✅ Funcional | CRUD de ejercicios fiscales. |
| Cierre Mensual | ✅ Funcional | Creación, reapertura. Endpoints + página frontend. |
| Cierre Fiscal | ✅ Funcional | Creación. Endpoints + página frontend. |
| Centros de Costo | ✅ Funcional | CRUD jerárquico. |
| AccountingEngine | ✅ Funcional | Motor template-based con resolución DIRECT/SUBTYPE/RULE/PARAM. |
| TemplateEngine | ✅ Funcional | Generación de líneas de asiento desde plantillas configurables. |
| ExpressionEvaluator | ✅ Funcional | Evaluación de expresiones en contexto. |
| RuleEngine | ⚠️ Parcial | Evaluación de condiciones, acciones BLOCK/WARN/APPROVAL. No implementado SET_FIELD. |
| Mayorización | 🗂️ Solo Backend | Modelos ERP heredado para mayor. Sin endpoint dedicado. |

**Entidades**: CuentaContable, Account, AccountType, FinancialClassification, TaxClassification, IfrsClassification, Asiento, AsientoLinea, PeriodoContable, EjercicioFiscal, CentroCosto, JournalType, JournalTemplate, JournalTemplateLine, AccountingEvent, AccountingRule, CierreMensual, CierreFiscal

**Depende de**: Administración General (Empresa)
**Dependen de él**: Todos los módulos transaccionales (CxC, CxP, Bancos, Caja, Activos Fijos, Nómina)

---

## 3. CUENTAS POR COBRAR (CxC)

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Clientes | ✅ Funcional | CRUD completo. Página frontend completa. |
| Facturación | ⚠️ Parcial | Creación de facturas via DocumentEngine. Listado. Sin nota crédito/débito. Sin estados de cuenta avanzados. |
| Antigüedad | ✅ Funcional | Reporte de antigüedad de saldos. Dashboard + página dedicada. |
| Estado Cuenta | ⚠️ Parcial | Endpoint existe. Sin UI dedicada. |
| Cobros | ⚠️ Parcial | Endpoint via DocumentEngine. Sin página frontend. |
| CxcService | ✅ Funcional | crear_factura, estado_cuenta, antigüedad. Integrado con DocumentEngine. |

**Entidades**: Cliente, FacturaVenta, FacturaVentaLinea
**Depende de**: Contabilidad General (cuentas, asientos), Administración General
**Dependen de él**: Reportes (Dashboard, Antigüedad)

---

## 4. CUENTAS POR PAGAR (CxP)

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Proveedores | ✅ Funcional | CRUD completo. Página frontend completa. |
| Compras (Facturas) | ⚠️ Parcial | Creación via DocumentEngine + CxpService. Listado. |
| Órdenes de Compra | ✅ Funcional | CRUD + aprobar/anular. Página frontend con pestañas. |
| Retenciones | ✅ Funcional | CRUD de retenciones (IR, IVA). |
| Antigüedad | ✅ Funcional | Reporte de antigüedad. Dashboard + página dedicada. |
| Estado Cuenta | ⚠️ Parcial | Endpoint existe. Sin UI dedicada. |
| Pagos | ⚠️ Parcial | Endpoint via DocumentEngine. Sin página frontend. |

**Entidades**: Proveedor, FacturaCompra, FacturaCompraLinea, OrdenCompra, OrdenCompraLinea, Retencion
**Depende de**: Contabilidad General, Administración General
**Dependen de él**: Reportes

---

## 5. BANCOS / TESORERÍA

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Cuentas Bancarias | ✅ Funcional | CRUD completo. |
| Movimientos Bancarios | ✅ Funcional | Registro + listado. Genera asiento via AccountingEngine. |
| Conciliación Bancaria | ⚠️ Parcial | Creación, cierre, conciliación de partidas. Página frontend. |
| Caja General | ✅ Funcional | CRUD de cajas. Movimientos con generación de asiento. |
| Cheques | 🗂️ Solo Backend | Modelo en ERP heredado CB. Sin endpoints. |

**Entidades**: CuentaBanco, MovimientoBanco, ConciliacionBancaria, ConciliacionDetalle, Caja, MovimientoCaja, ArqueoCaja
**Depende de**: Contabilidad General (asientos), Administración General
**Dependen de él**: Reportes

---

## 6. INVENTARIO

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Productos | ✅ Funcional | CRUD completo + kardex. Página frontend. |
| Categorías | ✅ Funcional | CRUD. Página frontend (CategoriasPage). |
| Bodegas | 🗂️ Solo Backend | Modelo creado. Sin endpoints. |
| Unidades de Medida | 🗂️ Solo Backend | Modelo creado. Sin endpoints. |
| Kardex | ✅ Funcional | Endpoint de kardex por producto. |
| Costeo | 🗂️ Solo Backend | CostEngine en ERP heredado. Sin integración real. |

**Entidades**: Producto, Categoria, Bodega, UnidadMedida
**Depende de**: Administración General
**Dependen de él**: Facturación, Compras, Reportes

---

## 7. ACTIVOS FIJOS

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Categorías de Activo | ✅ Funcional | CRUD con vida útil y método depreciación default. |
| Activos Fijos | ✅ Funcional | CRUD completo. Depreciación. Dar de baja. Página frontend completa (452 líneas). |
| Depreciación | ✅ Funcional | Líneas de depreciación. |
| Integración Contable | ✅ Funcional | Depreciación genera asiento via AccountingEngine. |

**Entidades**: CategoriaActivo, ActivoFijo, DepreciacionLinea
**Depende de**: Contabilidad General (asientos), Administración General
**Dependen de él**: Reportes

---

## 8. RRHH / NÓMINA

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Empleados | ✅ Funcional | CRUD completo + cargos + departamentos. Página frontend. |
| Nómina | ✅ Funcional | Períodos, procesamiento, pago. Configuración (INSS, IR). Página frontend. |
| Integración Contable | ✅ Funcional | Nómina genera asiento via AccountingEngine. |

**Entidades**: Empleado, Cargo, Departamento, NominaConfig, NominaPeriodo, NominaDetalle
**Depende de**: Contabilidad General (asientos), Administración General
**Dependen de él**: Reportes

---

## 9. PRESUPUESTOS

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Presupuestos | ✅ Funcional | CRUD + aprobación. Partidas presupuestarias. Ejecución. Página frontend. |
| Centros de Costo | ✅ Funcional | CRUD jerárquico (compartido con Contabilidad). |

**Entidades**: PresupuestoCabecera, PresupuestoDetalle, PresupuestoEjecucion, CentroCosto
**Depende de**: Administración General
**Dependen de él**: Reportes

---

## 10. REPORTES / BI

| Componente | Estado | Detalle |
|-----------|--------|---------|
| Dashboard | ✅ Funcional | KPIs, ventas por mes, ingresos vs gastos, top clientes, antigüedad CxC, movimientos recientes. |
| Balance General | ✅ Funcional | Endpoint + página frontend. |
| Estado Resultados | ✅ Funcional | Endpoint + página frontend. |
| Flujo de Efectivo | ✅ Funcional | Endpoint + página frontend. |
| Balance Comprobación | ✅ Funcional | Endpoint existe. |
| Mayor General | ✅ Funcional | Endpoint existe. |
| Antigüedad CxC | ✅ Funcional | Endpoint + página frontend. |
| Antigüedad CxP | ✅ Funcional | Endpoint + página frontend. |

**Entidades**: Depende de todas las entidades transaccionales
**Depende de**: Todos los módulos transaccionales

---

## 11. HERRAMIENTAS

| Componente | Estado | Detalle |
|-----------|--------|---------|
| OCR | ⚠️ Parcial | Endpoints + página frontend. Funcionalidad básica. |
| IA | ⚠️ Parcial | Endpoints + página frontend. Análisis básico. |
| Document Engine | ✅ Funcional | Pipeline completo: validación, numeración, workflow, rules, accounting, inventario, CxC/CxP. |
| Rule Engine | ⚠️ Parcial | Evaluación de reglas funcional. Sin UI de administración. |

---

## 12. ERP HEREDADO (DUPLICADO)

| Módulo | Estado | Detalle |
|--------|--------|---------|
| CG (Contabilidad) | ✅ Funcional | Endpoints CRUD + árbol cuentas + balance comprobación. |
| CI (Inventario) | ✅ Funcional | Endpoints CRUD + existencias + transacciones + costeo. |
| FA (Facturación) | 🗂️ Solo Backend | Endpoints creados. Sin frontend. |
| CO (Compras) | 🗂️ Solo Backend | Endpoints creados. Sin frontend. |
| CC (CxC) | 🗂️ Solo Backend | Endpoints creados. Sin frontend. |
| AF (Activos Fijos) | 🗂️ Solo Backend | Endpoints creados. Sin frontend. |
| CB (Tesorería) | 🗂️ Solo Backend | Endpoints creados. Sin frontend. |
| RH (Nómina) | 🗂️ Solo Backend | Endpoints creados. Sin frontend. |
| PE (Pedidos) | 🗂️ Solo Backend | Endpoints creados. Sin frontend. |

**Nota**: Este track ERP heredado es una duplicación paralela. Crea sus propias tablas, sus propios endpoints y sus propios engines. No está integrado con el track principal.
