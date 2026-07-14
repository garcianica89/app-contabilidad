# Plan Maestro de Implementacion — ERP Contabilidad BI

> Fecha: 2026-07-01
> Versión: 1.0
> Estado: Borrador para aprobacion
> Referencia: ERP de referenciaERP 7.00 (benchmark funcional)

---

## 0. Resumen Ejecutivo

### Estado Actual vs Objetivo

| Dimension | Actual | Objetivo |
|-----------|--------|----------|
| Catalogo Cuentas | Semilla de 32 cuentas hardcodeadas | Vacio al inicio, configurable, jerarquias ilimitadas |
| Parametrizacion Contable | Cuentas en `constants.py` | `module_accounting_config` configurable por modulo |
| CxC | Servicio con reglas en codigo | Subtipos de documento configurables + motor plantillas |
| CxP | Servicio con reglas en codigo | Subtipos de documento configurables + motor plantillas |
| Numeracion | `SELECT max+1` con race condition | Sistema de series con `FOR UPDATE` |
| Asientos | `AsientoService` con reglas en codigo | `TemplateEngine` con reglas en base de datos |
| Administracion General | Inexistente | Nucleo completo con empresas, sucursales, roles, permisos, bitacora |
| Contabilidad General | Parcial (asientos basicos) | Motor completo: diario, mayor, auxiliares, cierres, NIIF |
| CxC/CxP | Facturacion basica | Subtipos, retenciones, mora, antiguedad, estados de cuenta |
| Control Bancario | Solo cuentas bancarias | Conciliacion, cheques, transferencias, caja chica |
| Activos Fijos | CRUD basico | Depreciacion (3 metodos), revaluacion, baja, mejora |
| Inventarios | Costeo promedio | Costeo FIFO, UEPS, ajustes, traspasos, bodegas multiples |
| Nomina | Inexistente | INSS, IR, aguinaldo, vacaciones, prestaciones |
| Reportes | 3 estados basicos | Estados financieros, libros, analisis, exportacion |

---

## 1. Analisis de Brecha Funcional por Modulo

### 1.1 Administracion General

**Documento ERP de referencia Identificado:**
- Admin. del Sistema completo con:
  - Usuarios / Grupos / Autenticacion
  - Tablas: Paises, Monedas, Tipos de Cambio, Denominaciones, Condiciones de Pago, Codigos de Impuesto
  - Retenciones, Tipos de Anulacion, Formatos
  - Bodegas, Unidades, Aduanas, Agentes Aduanales
  - Consecutivos NCF, Regimenes, Modelo Retenciones
  - Purga de Datos Historicos, Bitacora de Procesos
  - Compañias, Periodos Contables, Opciones Configurables
  - Campos Configurables, Hooks, Estructuras, Diccionario de Datos

**Brecha:**
- [ ] No existe CRUD de Paises
- [ ] No existe CRUD de Denominaciones (billetes/monedas)
- [ ] No existen Grupos de Usuarios (solo roles)
- [ ] No existe Bitacora de Procesos (solo auditoria de datos)
- [ ] No existen Consecutivos NCF (facturacion fiscal)
- [ ] No existen Regimenes / Modelo Retenciones
- [ ] No existe Purga de Datos / Preferencias / Bloqueos
- [ ] No existe Diccionario de Datos / Estructuras configurables

### 1.2 Contabilidad General

**Documento ERP de referencia Identificado:**
- Tipos de Transacciones Contables (journal_type)
- Asignacion Centro-Cuenta
- Cuenta Doble Asiento
- Reportes Contables
- Tipo de Diferido
- Parametros del Modulo

**Brecha:**
- [ ] `journal_type` no existe (junto con template engine)
- [ ] `journal_template` + `journal_template_line` no existen
- [ ] `module_accounting_config` no existe (reemplaza constants.py)
- [ ] No existe Asignacion Centro-Cuenta
- [ ] No existen Diferidos (amortizaciones diferidas)
- [ ] Catálogo actual usa `cuenta_contable` fijo (debe migrar a `account` configurable)
- [ ] No existe importador de catalogo desde Excel/CSV
- [ ] No existe cierre anual / reapertura
- [ ] No existen asientos de provision / ajuste / recurrente

### 1.3 Cuentas por Cobrar

**Documento ERP de referencia Identificado:**
- Subtipos de Documento (FAC, NCR, NDB, REC, ANT, AJU, INT, CAS, REV)
- Tipos de Retenciones
- Parametros del Modulo
- Consulta General / Corporativa de Documentos
- Estados de Cuenta, Saldos por Cuenta, General de Cuentas
- Proyeccion/Analisis de Vencimiento, Antiguedad
- Intereses de Mora, Dias Promedio de Atraso
- Generacion de Asientos
- Cargador de Direcciones

**Brecha:**
- [ ] `cxc_document_subtype` no existe
- [ ] No hay Cargador de Direcciones (batch import)
- [ ] No hay Intereses de Mora automatizados
- [ ] No hay Dias Promedio de Atraso (KPI)
- [ ] Analisis de Antiguedad existe pero basico
- [ ] No hay Consulta Corporativa (multi-empresa)
- [ ] No hay Reportes por Moneda
- [ ] NO existe `generacion_asientos` automatica por subtipo
- [x] Existe: antiguedad, estados de cuenta basicos

### 1.4 Cuentas por Pagar

**Documento ERP de referencia Identificado:**
- Subtipos de Documento (FAC, NCR, NDB, PAG, ANT, RET, AJU)
- Tipos de Retenciones
- Parametros del Modulo
- Listado por Aplicacion / Aplicaciones
- Pago de Retenciones
- Diferencias Cambiarias
- Generacion de Facturas de Compras
- Ajuste mensual retencion en la fuente
- Codigo de ingreso, Tipos de cuenta
- Documento CxP: Tipo Doc, Subtipo, Fecha, Rige, T-Contable, Vence, Numero, Aplicacion, Monto, Moneda, Condiciones de Pago

**Brecha:**
- [ ] `cxp_document_subtype` no existe
- [ ] No existe modulo de Aplicacion de Pagos
- [ ] No existen Diferencias Cambiarias por tipo de cambio
- [ ] No existe Pago de Retenciones a DGI
- [ ] No existe Ajuste mensual retencion en la fuente
- [ ] No existen Codigos de Ingreso / Tipos de Cuenta
- [ ] No hay Cargador de Direcciones
- [ ] Generacion de Asientos por subtipo no existe
- [x] Existe: CRUD basico facturas, ordenes compra, antiguedad

---

## 2. Arquitectura Objetivo

### 2.1 Principios Rectores

1. **Modulos independientes** — Cada modulo con su propia estructura, APIs y UI
2. **Cero cuentas hardcodeadas** — Todo via `module_accounting_config`
3. **Motor de eventos contables** — Ningun modulo sabe contabilizar; generan eventos
4. **Subtipos configurables** — Comportamiento completo definido en datos
5. **Numeracion por series** — Cada documento usa `numeracion` con correlativo + serie
6. **Catalogo vacio al inicio** — El usuario carga su propio plan de cuentas
7. **Migracion no destructiva** — Strangler Fig: tablas nuevas coexisten, migracion gradual

### 2.2 Modulos y Dependencias

```
Fase 1: Fundacion
    Administracion General (nucleo)
    └── Empresas, Sucursales, Usuarios, Roles, Permisos, Bitacora

Fase 2: Framework Contable
    Estructura Catalogo (company_account_structure)
    └── Catalogo Cuentas (account) + Importador
    └── Account Type / Financial / Tax / IFRS Classifications
    └── Parametrizacion por modulo (module_accounting_config)

Fase 3: Motor Contable
    Tipos de Asiento (journal_type)
    └── Plantillas (journal_template + lines)
    └── Template Engine + Expression Evaluator
    └── Asientos manuales / Diario / Mayor / Auxiliares

Fase 4: Cuentas por Cobrar (independiente)
    Subtipos CxC + Parametros
    └── Facturacion → Motor Contable (evento)
    └── Estados de Cuenta / Antiguedad / Mora

Fase 5: Cuentas por Pagar (independiente)
    Subtipos CxP + Parametros
    └── Compras → Motor Contable (evento)
    └── Aplicacion Pagos / Retenciones / Diferencias Cambiarias

Fase 6: Inventarios (independiente)
    Bodegas / Costeo / Kardex
    └── Conexion con Compras y Ventas

Fase 7: Control Bancario (independiente)
    Caja / Bancos / Conciliacion / Cheques

Fase 8: Activos Fijos (independiente)
    Depreciacion / Revaluacion / Baja / Mejora

Fase 9: Nomina (independiente)
    Empleados / INSS / IR / Aguinaldo / Vacaciones

Fase 10: Reportes (transversal)
    Estados Financieros / Libros / Analisis / Exportacion
```

### 2.3 Flujo del Motor de Eventos Contables

```
┌─────────────────────────────────────────────────────────────────┐
│                        MODULO DE NEGOCIO                        │
│  (Ventas, Compras, Inventario, Nomina, Activos, Bancos, Caja)  │
│                                                                 │
│  1. Registra documento (factura, nomina, compra, etc.)         │
│  2. Genera Evento Contable con contexto completo               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EVENTO CONTABLE                             │
│  {                                                              │
│    empresa_id, documento_id, tipo, subtipo_id,                  │
│    fecha, numero, monto, moneda, tipo_cambio,                   │
│    cliente/proveedor, lineas, impuestos, retenciones...         │
│  }                                                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MOTOR DE PLANTILLAS                          │
│                                                                 │
│  1. Resolver journal_type desde:                                │
│     - subtipo_documento.journal_type_id (si existe)             │
│     - O por reglas de negocio (tipo_pago, modulo, etc.)        │
│                                                                 │
│  2. Buscar templates activos para ese journal_type              │
│     ordenados por prioridad                                     │
│                                                                 │
│  3. Evaluar condiciones del template                            │
│     - Si cumple → evaluar cada linea                            │
│     - Si no → siguiente template                                │
│                                                                 │
│  4. Para cada linea del template ganador:                      │
│     - Resolver cuenta (FIXED/PARAM/CONTEXT/SUBTYPE)            │
│     - Evaluar expresion de monto                               │
│     - Evaluar expresion de descripcion                         │
│     - Evaluar condicion de inclusion                           │
│                                                                 │
│  5. Validar partida doble (Sum Debe = Sum Haber)               │
│                                                                 │
│  6. Enviar al Journal Engine                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      JOURNAL ENGINE                             │
│                                                                 │
│  1. Validar periodo abierto                                     │
│  2. Asignar numero de asiento (correlativo x periodo)           │
│  3. Crear asiento + lineas en BD                               │
│  4. Actualizar tabla de movimientos por cuenta                 │
│  5. Registrar en auditoria                                     │
│  6. Publicar evento de asiento creado                          │
│                                                                 │
│  RETORNA: asiento_id, numero_asiento                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Fases de Implementacion

### FASE 1: Fundacion — Administracion General (Semana 1-2)

**Objetivo:** Nucleo del ERP con seguridad, configuracion y administracion.

**Backend:**
- [ ] CRUD Paises (`pais` table)
- [ ] CRUD Sucursales (`sucursal` table)
- [ ] CRUD Grupos de Usuarios (`grupo_usuario` table)
- [ ] CRUD Denominaciones (`denominacion` table)
- [ ] CRUD Bodegas (`bodega` table)
- [ ] CRUD Unidades de Medida (`unidad_medida` table)
- [ ] CRUD Regimenes / Modelo Retenciones
- [ ] CRUD Consecutivos NCF (para facturacion fiscal futura)
- [ ] Bitacora de Procesos (`bitacora_proceso` table)
- [ ] Purga de Datos / Bloqueos / Preferencias
- [ ] Diccionario de Datos / Estructuras / Hooks

**Frontend:**
- [ ] Pagina de Administracion General con sub-modulos
- [ ] Grilla de usuarios con grupos
- [ ] Mantenimiento de tablas (paises, monedas, bodegas, etc.)

**Migracion:**
- [ ] Tablas nuevas coexisten con actuales
- [ ] Seed de tablas base

### FASE 2: Reingenieria del Catalogo de Cuentas (Semana 3-4)

**Objetivo:** Reemplazar catalogo fijo por estructura configurable.

**Backend:**
- [ ] Crear `company_account_structure` (niveles, longitud, separador)
- [ ] Crear `account_type` (seed: ACTIVO, PASIVO, PATRIMONIO, INGRESO, COSTO, GASTO)
- [ ] Crear `financial_classification` (seed: CORRIENTE, NO_CORRIENTE, etc.)
- [ ] Crear `tax_classification` (seed: GRAVADO, EXENTO, EXCLUIDO)
- [ ] Crear `ifrs_classification` (seed: NIIF para PYME)
- [ ] Crear `account` (reemplaza `cuenta_contable`)
- [ ] Importador de Catalogo desde Excel/CSV (preview, validate, import)
- [ ] Sincronizador bidireccional `cuenta_contable` ↔ `account` (strangler fig)
- [ ] Crear `module_accounting_config` (parametrizacion por modulo)

**Frontend:**
- [ ] Pagina de Estructura del Catalogo (configurar niveles)
- [ ] Pagina de Catalogo de Cuentas con arbol jerarquico
- [ ] Pagina de Importacion de Catalogo (drag & drop Excel)
- [ ] Pantalla de Parametrizacion Contable por Modulo

**Reglas:**
- [ ] Validacion de jerarquia (cuenta con hijos no acepta asientos)
- [ ] Herencia de clasificaciones (hijo hereda del padre)
- [ ] Restriccion por moneda
- [ ] Dimensiones obligatorias (centro costo, etc.)

### FASE 3: Motor Contable — Tipos de Asiento y Plantillas (Semana 5-7)

**Objetivo:** Motor universal de generacion de asientos basado en plantillas.

**Backend:**
- [ ] Crear `journal_type` (tabla de tipos de asiento)
- [ ] Crear `journal_template` (plantillas con condiciones)
- [ ] Crear `journal_template_line` (lineas con resolucion de cuentas)
- [ ] Implementar `ExpressionEvaluator` (mini-lenguaje `{{}}` con `sum/if`)
- [ ] Implementar `TemplateEngine` (orquestador completo)
- [ ] Implementar `JournalEngine` (creacion de asientos)
- [ ] Asientos manuales (usando el nuevo motor)
- [ ] Validacion de partida doble
- [ ] Cierre mensual + cierre anual + reapertura
- [ ] Asientos de provision / ajuste / recurrente
- [ ] Diferidos (amortizaciones)

**Frontend:**
- [ ] Pagina de Tipos de Asiento
- [ ] Pagina de Plantillas (con editor de lineas)
- [ ] Editor de expresiones con preview
- [ ] Pagina de Asientos Manuales
- [ ] Reportes: Diario General, Mayor General, Auxiliares

**Feature Flag:**
- [ ] `NEW_ACCOUNTING_ENGINE`: `INACTIVE` → `VALIDATION` → `ACTIVE`

### FASE 4: Cuentas por Cobrar (Semana 8-9)

**Objetivo:** CxC configurable con subtipos, parametros y motor de eventos.

**Backend:**
- [ ] Crear `cxc_document_subtype` (tabla de subtipos)
- [ ] Seed de subtipos: FAC, NCR, NDB, REC, ANT, AJU, INT, CAS, REV
- [ ] Parametros del modulo CxC
- [ ] Refactorizar Facturacion para usar subtipos
- [ ] Conectar con TemplateEngine (evento → asiento)
- [ ] Intereses de Mora (calculo automatico)
- [ ] Dias Promedio de Atraso (KPI)
- [ ] Estados de Cuenta con detalle de aplicaciones
- [ ] Analisis de Antiguedad mejorado
- [ ] Reportes por Moneda
- [ ] Consulta Corporativa (multi-empresa)

**Frontend:**
- [ ] Pagina de Administracion CxC (subtipos, parametros)
- [ ] Pagina de Consulta General de Documentos
- [ ] Pagina de Estados de Cuenta
- [ ] Pagina de Analisis de Vencimiento / Antiguedad

### FASE 5: Cuentas por Pagar (Semana 10-11)

**Objetivo:** CxP configurable con aplicacion de pagos, retenciones y diferencial cambiario.

**Backend:**
- [ ] Crear `cxp_document_subtype` (tabla de subtipos)
- [ ] Seed de subtipos: FAC, NCR, NDB, PAG, ANT, RET, AJU
- [ ] Parametros del modulo CxP
- [ ] Refactorizar Compras para usar subtipos
- [ ] Conectar con TemplateEngine (evento → asiento)
- [ ] Aplicacion de Pagos (aplicar pagos a facturas)
- [ ] Pago de Retenciones (generacion de declaracion)
- [ ] Diferencias Cambiarias (por fluctuacion de tipo de cambio)
- [ ] Ajuste mensual retencion en la fuente
- [ ] Codigos de Ingreso / Tipos de Cuenta
- [ ] Cargador de Direcciones (import batch)

**Frontend:**
- [ ] Pagina de Administracion CxP (subtipos, parametros)
- [ ] Pagina de Documentos CxP con detalle completo
- [ ] Pagina de Aplicacion de Pagos
- [ ] Pagina de Retenciones
- [ ] Pagina de Diferencias Cambiarias

### FASE 6: Inventarios (Semana 12-13)

**Objetivo:** Inventario completo con bodegas multiples y metodos de costeo.

**Backend:**
- [ ] CRUD Bodegas
- [ ] Metodos de Costeo: Promedio, FIFO, UEPS (configurable por producto)
- [ ] Traspasos entre bodegas
- [ ] Ajustes de inventario (sobrantes/faltantes)
- [ ] Conteo fisico con ajuste automatico
- [ ] Costeo de importaciones (liquidacion)

**Frontend:**
- [ ] Pagina de Inventario con filtro por bodega
- [ ] Reporte de existencias con costo
- [ ] Pagina de Traspasos
- [ ] Pagina de Conteo Fisico

### FASE 7: Control Bancario (Semana 14-15)

**Objetivo:** Caja, bancos, cheques, conciliacion.

**Backend:**
- [ ] Arqueo de Caja
- [ ] Caja Chica (fondo fijo)
- [ ] Cheques Emitidos / Recibidos / Reversados
- [ ] Transferencias entre cuentas
- [ ] Conciliacion Bancaria (cruce automatico)
- [ ] Notas de Debito/Credito bancarias

**Frontend:**
- [ ] Pagina de Caja (apertura, arqueo, cierre)
- [ ] Pagina de Cheques
- [ ] Pagina de Conciliacion Bancaria

### FASE 8: Activos Fijos (Semana 16)

**Objetivo:** Activos fijos con metodos de depreciacion y eventos contables.

**Backend:**
- [ ] Conectar ActivoFijoService con TemplateEngine
- [ ] Revaluacion de Activos
- [ ] Mejoras / Capitalizacion
- [ ] Depreciacion por componentes

**Frontend:**
- [ ] Mejoras a pagina existente

### FASE 9: Nomina (Semana 17-18)

**Objetivo:** Nomina completa con INSS, IR, aguinaldo, vacaciones.

**Backend:**
- [ ] Calculo de INSS Patronal/Laboral (reglas Nicaragua)
- [ ] Calculo de IR (tabla progresiva)
- [ ] Aguinaldo (decimo tercer mes)
- [ ] Vacaciones / Prestaciones
- [ ] Integracion con TemplateEngine

**Frontend:**
- [ ] Pagina de Calculo de Nomina
- [ ] Pagina de Configuracion de Deducciones

### FASE 10: Reportes y Cierre (Semana 19-20)

**Objetivo:** Reporteria completa y cierre del ciclo.

- [ ] Balance General configurable por niveles
- [ ] Estado de Resultados
- [ ] Flujo de Efectivo (metodo directo e indirecto)
- [ ] Estado de Cambios en el Patrimonio
- [ ] Diario General + Mayor General + Auxiliares
- [ ] Exportacion a Excel y PDF
- [ ] Dashboard con KPIs

---

## 4. Tablas del Sistema (Diseno Final)

### 4.1 Administracion General

| Tabla | Descripcion | Estado |
|-------|-------------|--------|
| `empresa` | Empresa / Compañia | Existe |
| `sucursal` | Sucursales por empresa | **Nueva** |
| `usuario` | Usuarios del sistema | Existe |
| `grupo_usuario` | Grupos de usuarios | **Nueva** |
| `rol` | Roles del sistema | Existe |
| `permiso` | Permisos individuales | Existe |
| `rol_permiso` | Asignacion rol-permiso | Existe |
| `pais` | Catalogo de paises | **Nueva** |
| `moneda` | Monedas | Existe |
| `tipo_cambio` | Tipos de cambio historicos | Existe |
| `denominacion` | Denominaciones de billetes/monedas | **Nueva** |
| `condicion_pago` | Condiciones de pago | Existe |
| `impuesto` | Codigos de impuesto | Existe |
| `retencion` | Definicion de retenciones | **Nueva** |
| `bodega` | Bodegas / almacenes | **Nueva** |
| `unidad_medida` | Unidades de medida | **Nueva** |
| `periodo_contable` | Periodos contables | Existe |
| `bitacora_proceso` | Bitacora de procesos automaticos | **Nueva** |
| `auditoria` | Auditoria de cambios en datos | Existe |

### 4.2 Contabilidad

| Tabla | Descripcion | Estado |
|-------|-------------|--------|
| `company_account_structure` | Estructura de codigo contable | **Nueva** |
| `account_type` | Clasificacion base (ACTIVO, PASIVO...) | **Nueva** |
| `financial_classification` | Clasificacion financiera | **Nueva** |
| `tax_classification` | Clasificacion fiscal | **Nueva** |
| `ifrs_classification` | Clasificacion NIIF | **Nueva** |
| `account` | Catalogo de cuentas (nuevo) | **Nueva** |
| `cuenta_contable` | Catalogo de cuentas (viejo) | Deprecar |
| `module_accounting_config` | Parametrizacion contable por modulo | **Nueva** |
| `journal_type` | Tipos de asiento | **Nueva** |
| `journal_template` | Plantillas de asiento | **Nueva** |
| `journal_template_line` | Lineas de plantilla | **Nueva** |
| `asiento` | Asientos contables | Existe |
| `asiento_linea` | Lineas de asiento | Existe |
| `centro_costo` | Centros de costo | Existe |

### 4.3 CxC / CxP

| Tabla | Descripcion | Estado |
|-------|-------------|--------|
| `cxc_document_subtype` | Subtipos CxC | **Nueva** |
| `cxp_document_subtype` | Subtipos CxP | **Nueva** |
| `cliente` | Clientes | Existe |
| `proveedor` | Proveedores | Existe |
| `factura_venta` | Facturas de venta | Existe |
| `factura_compra` | Facturas de compra | Existe |
| `orden_compra` | Ordenes de compra | Existe |
| `numeracion` | Series y correlativos | Existe |

### 4.4 Otros Modulos

| Tabla | Descripcion | Estado |
|-------|-------------|--------|
| `producto` | Productos | Existe |
| `categoria` | Categorias de productos | Existe |
| `kardex_movimiento` | Movimientos de inventario | **Nueva** |
| `cuenta_banco` | Cuentas bancarias | Existe |
| `movimiento_banco` | Movimientos bancarios | Existe |
| `caja` | Cajas | **Nueva** |
| `activo_fijo` | Activos fijos | Existe |
| `empleado` | Empleados | Existe |
| `nomina_periodo` | Periodos de nomina | Existe |
| `nomina_detalle` | Detalle de nomina | Existe |

---

## 5. ADRs Requeridos

| ADR | Titulo | Estado |
|-----|--------|--------|
| ADR-001 | Arquitectura General del Sistema | Aprobado |
| ADR-002 | Reingenieria del Nucleo Contable | **Pendiente** |
| ADR-003 | Estrategia de Migracion Strangler Fig | **Pendiente** |
| ADR-004 | Motor de Expresiones y Seguridad | **Pendiente** |
| ADR-005 | API Versionado y Contratos | **Pendiente** |
| ADR-006 | Manejo de Multiempresa y Sucursales | **Pendiente** |
| ADR-007 | Estrategia de Caché y Performance | **Pendiente** |
| ADR-008 | Despliegue y DevOps | **Pendiente** |

---

## 6. Lineamientos para la Implementacion

### 6.1 Lo que NO debe cambiar

- Stack tecnologico (FastAPI + React + PostgreSQL)
- UUID como PKs
- API versionada `/api/v1/`
- Estructura de capas (endpoint → service → repository)
- Autenticacion JWT
- TypeScript estricto en frontend

### 6.2 Lo que DEBE cambiar

- `constants.py` → `module_accounting_config`
- `cuenta_contable` → `account`
- Logica de asientos en servicios → `TemplateEngine`
- Numeracion por `SELECT max+1` → `numeracion` con `FOR UPDATE`
- Reglas de IVA/Retenciones en codigo → Subtipos configurables

### 6.3 Prioridades

1. **No romper el sistema actual** — Cada fase debe mantener compatibilidad
2. **Primero tablas, luego logica** — Crear estructura de datos antes de refactorizar servicios
3. **Feature flags para todo** — Poder activar/desactivar el nuevo motor
4. **Validacion paralela** — Ambos motores corren simultaneamente en validacion
5. **Pruebas automatizadas** — Cada template debe tener test de integracion

---

## 7. Proxima Accion

Este plan maestro requiere tu aprobacion antes de proceder.

Puntos a decidir:

1. **¿Apruebas la estructura de 10 fases propuesta?**
2. **¿Quieres comenzar con Fase 1 (Fundacion) o Fase 2 (Catalogo) primero?**
   - Fase 1: Administracion General (paises, bodegas, grupos, etc.)
   - Fase 2: Reingenieria del Catalogo de Cuentas (mas critico pero mas complejo)
3. **¿Confirmas catalogo vacio al inicio (sin seed de cuentas)?**
4. **¿Apruebas el diseno del motor de plantillas con mini-lenguaje `{{}}`?**
5. **¿Quieres revisar y aprobar ADR-002 antes de comenzar?**
