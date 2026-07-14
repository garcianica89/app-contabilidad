# Plan Maestro de Implementacion v2.0
## ERP Contabilidad BI — Arquitectura Enterprise

> **Version:** 2.0
> **Fecha:** 2026-07-01
> **Estado:** Borrador para aprobacion
> **Clasificacion:** CONFIDENCIAL — Chief ERP Architect
> **Benchmark funcional:** ERP de referencia 7.00
> **Benchmark arquitectonico:** ERP Enterprise moderno (20+ anos de evolucion)

---

## Indice

1. [Filosofia Arquitectonica](#1-filosofia-arquitectonica)
2. [Bounded Contexts](#2-bounded-contexts)
3. [Motor Contable — Centro del ERP](#3-motor-contable--centro-del-erp)
4. [ERP Metadata](#4-erp-metadata)
5. [Motor de Configuracion Contable](#5-motor-de-configuracion-contable)
6. [Motor de Workflow](#6-motor-de-workflow)
7. [Motor de Reglas (Rule Engine)](#7-motor-de-reglas-rule-engine)
8. [Motor de Numeraciones](#8-motor-de-numeraciones)
9. [Seguridad Empresarial (RBAC++ + SoD)](#9-seguridad-empresarial-rbac--sod)
10. [Multiempresa Real](#10-multiempresa-real)
11. [Dimensiones Contables](#11-dimensiones-contables)
12. [Catalogo de Cuentas](#12-catalogo-de-cuentas)
13. [Parametrizacion por Modulo](#13-parametrizacion-por-modulo)
14. [Cuentas por Cobrar / Pagar](#14-cuentas-por-cobrar--pagar)
15. [Reporting Layer (BI)](#15-reporting-layer-bi)
16. [API Publica](#16-api-publica)
17. [Localizaciones](#17-localizaciones)
18. [Roadmap Detallado por Fases](#18-roadmap-detallado-por-fases)
19. [Diagramas de Arquitectura](#19-diagramas-de-arquitectura)
20. [Modelo Entidad-Relacion de Alto Nivel](#20-modelo-entidad-relacion-de-alto-nivel)
21. [ADRs](#21-adrs)
22. [Criterios de Exito](#22-criterios-de-exito)

---

## 1. Filosofia Arquitectonica

### 1.1 Principios Fundamentales

```
1.  EL MOTOR CONTABLE ES EL CENTRO
    Ningun modulo de negocio sabe contabilizar.
    Solo publican eventos. El motor contable resuelve todo.

2.  CONFIGURACION > CODIGO
    Toda regla de negocio, parametro contable, workflow,
    y comportamiento debe ser configurable desde datos.

3.  MODULOS INDEPENDIENTES
    Cada bounded context es autonomo. Comunicacion
    exclusivamente por eventos asincronos.

4.  CERO CUENTAS HARDCODEADAS
    Ninguna cuenta contable vive en el codigo fuente.
    Todo sale de tablas de configuracion.

5.  CATALOGO VACIO AL INICIO
    El sistema se instala sin cuentas. Solo estructura.
    El usuario carga su plan de cuentas.

6.  MIGRACION NO DESTRUCTIVA
    Strangler Fig: nuevas capacidades coexisten con las
    existentes hasta su reemplazo completo.

7.  AUDITORIA POR DEFECTO
    Toda operacion critica queda registrada con
    usuario, fecha, valor anterior, valor nuevo.

8.  DISENO PARA 20 ANOS
    Escalabilidad horizontal, tablas particionables,
    indices preparados para cientos de empresas,
    API versionada, localizaciones desde el dia 1.
```

### 1.2 Stack Tecnologico (extendido)

```
┌──────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                           │
│  React 18 + TypeScript + TailwindCSS + PWA                       │
│  TanStack Query + Table + React Hook Form + Recharts             │
│  ShadCN/ui como libreria de componentes base                     │
├──────────────────────────────────────────────────────────────────┤
│                     API GATEWAY / BFF                            │
│  FastAPI + Pydantic v2 + OpenAPI                                 │
│  Rate limiting, versionado, autenticacion JWT                    │
├──────────────────────────────────────────────────────────────────┤
│                     APPLICATION LAYER                            │
│  Command/Query pattern (CQRS ligero)                             │
│  Servicios de aplicacion por bounded context                     │
│  Workflow Engine | Rule Engine | Template Engine                 │
├──────────────────────────────────────────────────────────────────┤
│                     DOMAIN LAYER                                 │
│  Entidades + Value Objects + Eventos de Dominio                  │
│  Reglas de negocio encapsuladas                                  │
├──────────────────────────────────────────────────────────────────┤
│                     INFRASTRUCTURE LAYER                         │
│  PostgreSQL 16+ (Neon.tech)                                      │
│  Redis (caché, colas, sesiones)                                  │
│  SQLAlchemy 2.x (async) + Alembic                                │
│  Materialized Views + Read Models para reporting                 │
├──────────────────────────────────────────────────────────────────┤
│                     EVENT BUS (futuro)                            │
│  RabbitMQ / NATS / Redis Streams                                 │
│  Event sourcing para auditoria                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Bounded Contexts

### 2.1 Mapa de Contextos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ERP METADATA                                      │
│  Define la estructura del sistema: modulos, documentos, tipos, workflows,   │
│  menus, permisos, parametros, hooks, extensiones                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  ADMIN       │ │  CONTABILIDAD│ │   CxC        │ │   CxP        │ │  INVENTARIOS │
│  GENERAL     │ │  GENERAL     │ │              │ │              │ │              │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ Empresas     │ │ Motor        │ │ Facturacion  │ │ Compras      │ │ Productos    │
│ Sucursales   │ │ Contable     │ │ Cobros       │ │ Pagos        │ │ Bodegas      │
│ Usuarios     │ │ Catalogo     │ │ Antiguedad   │ │ Retenciones  │ │ Kardex       │
│ Roles/Permis │ │ Asientos     │ │ Estados Cta  │ │ Diferencial  │ │ Costeo       │
│ Numeraciones │ │ Cierres      │ │ Mora         │ │ Cambiario    │ │ Ajustes      │
│ Parametros   │ │ Reportes     │ │              │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  BANCOS      │ │  ACTIVOS     │ │   NOMINA     │ │  REPORTES    │ │  API PUBLICA │
│              │ │  FIJOS       │ │              │ │  (BI)        │ │              │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ Cuentas      │ │ Depreciacion │ │ Empleados    │ │ Dashboards   │ │ REST         │
│ Conciliacion │ │ Revaluacion  │ │ Calculo      │ │ Read Models  │ │ GraphQL      │
│ Cheques      │ │ Baja         │ │ INSS/IR      │ │ KPI          │ │ Webhooks     │
│ Caja         │ │ Mejora       │ │ Aguinaldo    │ │ Exportacion  │ │ POS          │
│ Caja Chica   │ │              │ │ Vacaciones   │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           MOTOR DE WORKFLOW                                 │
│  Estados, transiciones, aprobaciones, firmas, reversiones                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           MOTOR DE REGLAS                                   │
│  Reglas de negocio configurables: crediticio, aprobaciones, alertas         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOCALIZACIONES                                     │
│  Impuestos, retenciones, calendarios fiscales, normativas por pais          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Comunicacion entre Contextos

```
┌──────────────┐       Evento de Negocio       ┌──────────────────┐
│  VENTAS      │ ──────────────────────────────▶│  MOTOR CONTABLE  │
│  (publica)   │                                │  (subscribe)     │
└──────────────┘                                │                  │
                                                │  1. Resolver     │
┌──────────────┐       Evento de Negocio       │     journal_type │
│  COMPRAS     │ ──────────────────────────────▶│  2. Evaluar      │
│  (publica)   │                                │     templates    │
└──────────────┘                                │  3. Resolver     │
                                                │     cuentas      │
┌──────────────┐       Evento de Negocio       │  4. Crear        │
│  INVENTARIO  │ ──────────────────────────────▶│     asiento      │
│  (publica)   │                                │  5. Publicar     │
└──────────────┘                                │     evento       │
                                                └──────────────────┘
┌──────────────┐       Evento de Negocio              │
│  NOMINA      │ ──────────────────────────────▶       │
│  (publica)   │                                       │
└──────────────┘                                       ▼
                                              ┌──────────────────┐
┌──────────────┐       Evento de Negocio     │  WORKFLOW ENGINE │
│  ACTIVOS     │ ──────────────────────────────▶  (evaluate      │
│  FIJOS       │                              │   transitions)  │
└──────────────┘                              └──────────────────┘
                                                      │
┌──────────────┐       Evento de Negocio              ▼
│  BANCOS      │ ──────────────────────────────▶┌──────────────────┐
│  (publica)   │                                │   RULE ENGINE    │
└──────────────┘                                │  (evaluate       │
                                                │   conditions)    │
┌──────────────┐       Evento de Negocio       └──────────────────┘
│  CxC/CxP     │ ──────────────────────────────▶
│  (publica)   │
└──────────────┘
```

---

## 3. Motor Contable — Centro del ERP

### 3.1 Arquitectura del Flujo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVENTO DE NEGOCIO                                   │
│                                                                             │
│  {                                                                          │
│    "event_type": "VENTA_EMITIDA",                                           │
│    "module": "sales",                                                       │
│    "document_type": "FAC",                                                  │
│    "document_subtype_id": "uuid",                                           │
│    "document_id": "uuid",                                                   │
│    "number": "A-000123",                                                    │
│    "date": "2026-07-01",                                                    │
│    "company_id": "uuid",                                                    │
│    "currency_id": "uuid",                                                   │
│    "exchange_rate": 1.0,                                                    │
│    "amounts": { "subtotal": 1000, "iva": 150, "total": 1150 },             │
│    "parties": { "customer_id": "uuid", "customer_name": "..." },           │
│    "dimensions": { "cost_center_id": "uuid", "project_id": "uuid" },       │
│    "lines": [ { "product_id": "uuid", "qty": 2, "price": 500 } ],          │
│    "metadata": { "origin": "POS-01", "user_id": "uuid" }                   │
│  }                                                                          │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ACCOUNTING EVENT RESOLVER                              │
│                                                                             │
│  1. Buscar en `accounting_event` por event_type + module                   │
│     └── Si no existe → error: evento no configurado                        │
│                                                                             │
│  2. Del accounting_event obtener:                                           │
│     - journal_type_id (o regla de resolucion)                              │
│     - parametros requeridos del contexto                                    │
│     - condiciones de validacion previa                                      │
│                                                                             │
│  3. Validar que el periodo contable este abierto                           │
│  4. Validar que el documento no este duplicado (idempotencia)              │
│  5. Enriquecer contexto con parametros del modulo                          │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JOURNAL TYPE RESOLVER                             │
│                                                                             │
│  Estrategia de resolucion (configurable por evento):                        │
│                                                                             │
│  1. DIRECT: journal_type_id fijo en accounting_event                        │
│  2. SUBTYPE: lookup en cxc/cxp_document_subtype.journal_type_id            │
│  3. RULE: evaluar regla en Rule Engine                                     │
│     (ej: si tipo_pago == CONTADO → VENTA_CONT, si no → VENTA_CRED)        │
│  4. PARAM: lookup en accounting_parameter_value                            │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TEMPLATE ENGINE                                    │
│                                                                             │
│  1. Cargar templates activos para el journal_type, ordenados por prioridad │
│  2. Evaluar condicion de cada template (accounting_condition)              │
│     └── Si cumple → seleccionar este template                              │
│     └── Si no → siguiente template                                          │
│  3. Para cada linea del template:                                           │
│     a. Evaluar condicion de la linea (opcional)                            │
│     b. Resolver cuenta:                                                     │
│        - FIXED: account_code literal                                       │
│        - PARAM: lookup en accounting_parameter_value                       │
│        - CONTEXT: variable del evento                                      │
│        - SUBTYPE: lookup en documento_subtype                              │
│        - RULE: evaluar regla para resolver cuenta                          │
│     c. Evaluar expresion de monto (ExpressionEvaluator)                    │
│     d. Evaluar expresion de descripcion                                    │
│     e. Resolver dimensiones (centro costo, proyecto, etc.)                 │
│  4. Si linea es mandatory y condicion falla → descartar template           │
│  5. Si ninguna linea producida → buscar siguiente template                  │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JOURNAL ENGINE (ESCRITOR)                         │
│                                                                             │
│  1. Validar partida doble: SUM(debe) = SUM(haber)                         │
│  2. Si no cuadra → error (bug de configuracion, no del modulo)             │
│  3. Asignar numero de asiento:                                             │
│     - Llamar a NumeracionEngine para correlativo por periodo               │
│  4. Crear asiento + lineas en BD (transaccion)                             │
│  5. Actualizar tabla de movimientos por cuenta (saldos)                    │
│  6. Registrar en bitacora de procesos                                      │
│  7. Publicar evento: ASIENTO_CONTABILIZADO                                 │
│     - WorkflowEngine evalua si hay transicion de estado                    │
│     - RuleEngine evalua reglas post-contabilizacion                        │
│  8. Retornar: { asiento_id, numero_asiento }                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Tablas del Motor Contable

```sql
-- accounting_event: define que eventos de negocio generan contabilizacion
CREATE TABLE accounting_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    code VARCHAR(50) NOT NULL,        -- 'VENTA_EMITIDA', 'COMPRA_REGISTRADA'
    name VARCHAR(200) NOT NULL,
    module VARCHAR(50) NOT NULL,      -- 'sales', 'purchasing', etc.
    document_type VARCHAR(20),        -- 'FAC', 'NCR', etc. (opcional)
    document_subtype_id UUID REFERENCES cxc_document_subtype(id),
     -- Opcional: si el evento es especifico de un subtipo

    -- Resolucion de journal_type
    journal_type_resolution VARCHAR(20) NOT NULL DEFAULT 'DIRECT'
        CHECK (journal_type_resolution IN ('DIRECT', 'SUBTYPE', 'RULE', 'PARAM')),
    journal_type_id UUID REFERENCES journal_type(id),
     -- Usado cuando resolution = 'DIRECT'

    journal_type_rule_id UUID REFERENCES accounting_rule(id),
     -- Usado cuando resolution = 'RULE'

    journal_type_param_key VARCHAR(100),
     -- Usado cuando resolution = 'PARAM'

    -- Control
    requires_approval BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    observations TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, code)
);

-- journal_type: tipos de asiento contable
CREATE TABLE journal_type (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    code VARCHAR(20) NOT NULL,         -- 'VENTA_CONT', 'VENTA_CRED', 'COMPRA_NAC'
    name VARCHAR(100) NOT NULL,
    module VARCHAR(50),
    nature VARCHAR(20) NOT NULL
        CHECK (nature IN ('AUTOMATIC', 'MANUAL', 'RECURRING')),
    affects_inventory BOOLEAN DEFAULT FALSE,
    affects_receivable BOOLEAN DEFAULT FALSE,
    affects_payable BOOLEAN DEFAULT FALSE,
    affects_cash BOOLEAN DEFAULT FALSE,
    affects_bank BOOLEAN DEFAULT FALSE,
    requires_approval BOOLEAN DEFAULT FALSE,
    approval_max_amount DECIMAL(14,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, code)
);

-- journal_template: plantillas de asiento
CREATE TABLE journal_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_type_id UUID NOT NULL REFERENCES journal_type(id),
    company_id UUID NOT NULL REFERENCES company(id),
    name VARCHAR(100) NOT NULL,
    priority INT DEFAULT 0,
    condition_expression TEXT,
     -- Expresion: "{{tipo_pago}} == 'CONTADO'"
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(journal_type_id, company_id, name)
);

-- journal_template_line: lineas de plantilla
CREATE TABLE journal_template_line (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES journal_template(id),
    line_order INT NOT NULL,
    nature VARCHAR(10) NOT NULL CHECK (nature IN ('DEBIT', 'CREDIT')),

    -- Resolucion de cuenta
    account_source VARCHAR(20) NOT NULL
        CHECK (account_source IN ('FIXED', 'PARAM', 'CONTEXT', 'SUBTYPE', 'RULE')),
    account_code VARCHAR(50),                  -- FIXED
    account_param_key VARCHAR(100),             -- PARAM: concepto en accounting_parameter
    account_context_var VARCHAR(100),           -- CONTEXT: {{cuenta_ventas}}
    account_rule_id UUID REFERENCES accounting_rule(id), -- RULE

    -- Monto
    amount_expression TEXT NOT NULL,
     -- "{{total}}", "{{subtotal - descuento}}", "{{iva}}"

    -- Descripcion
    description_expression TEXT,
     -- "Venta {{numero}}", "{{cliente_nombre}}"

    -- Dimensiones
    cost_center_source VARCHAR(20) DEFAULT 'FROM_TRANSACTION'
        CHECK (cost_center_source IN ('FIXED', 'CONTEXT', 'SUBTYPE', 'FROM_TRANSACTION', 'RULE')),
    cost_center_id UUID REFERENCES cost_center(id),

    -- Condicion de inclusion
    condition_expression TEXT,
     -- "{{iva}} > 0", NULL = siempre

    is_mandatory BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.3 ExpressionEvaluator

```python
"""
Evaluador de expresiones aritmeticas SIN usar eval().

Variables:    {{nombre_variable}}
Operadores:   +, -, *, /, (, ), ==, !=, >, <, >=, <=, and, or, not
Funciones:    sum(array, field), if(cond, then, else), round(val, dec)
              abs(val), min(array), max(array), count(array)

Ejemplos:
  "{{total}}"
  "{{subtotal - descuento}}"
  "{{total * 0.15}}"
  "{{if(iva > 0, iva, 0)}}"
  "{{sum(lineas, 'subtotal')}}"
  "{{if(antiguedad_dias > 90, monto * 0.02, 0)}}"

Implementacion:
  - Tokenizer → Shunting-yard → AST → Decimal evaluator
  - Contexto tipado (Decimal, str, bool, list[dict])
  - Cache de expresiones compiladas (LRU)
"""
```

---

## 4. ERP Metadata

### 4.1 Proposito

Modulo que define la estructura funcional completa del ERP.
Todo lo que puede hacerse en el sistema se define aqui.

### 4.2 Tablas

```sql
-- Modulos del sistema
CREATE TABLE erp_module (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    parent_module_id UUID REFERENCES erp_module(id),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documentos del sistema (factura, orden compra, nomina, etc.)
CREATE TABLE erp_document_type (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES erp_module(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    short_name VARCHAR(20),
    icon VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(module_id, code)
);

-- Subtipos de documento
CREATE TABLE erp_document_subtype (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type_id UUID NOT NULL REFERENCES erp_document_type(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),

    -- Referencia a tablas especificas de cada modulo
    -- (ej: cxc_document_subtype, cxp_document_subtype)
    -- Usando pattern: tablas polimorficas o FK opcionales
    cxc_subtype_id UUID REFERENCES cxc_document_subtype(id),
    cxp_subtype_id UUID REFERENCES cxp_document_subtype(id),

    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(document_type_id, code)
);

-- Estados de documentos (workflow)
CREATE TABLE erp_document_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type_id UUID NOT NULL REFERENCES erp_document_type(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    is_initial BOOLEAN DEFAULT FALSE,
    is_final BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    UNIQUE(document_type_id, code)
);

-- Eventos de negocio
CREATE TABLE erp_business_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES erp_module(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    UNIQUE(module_id, code)
);

-- Acciones permitidas por documento/estado
CREATE TABLE erp_action (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT
);

-- Hooks / Extension points
CREATE TABLE erp_hook (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    module_id UUID REFERENCES erp_module(id),
    event_type VARCHAR(50), -- 'PRE_CREATE', 'POST_CREATE', 'PRE_UPDATE', etc.
    handler_type VARCHAR(50), -- 'PYTHON', 'HTTP', 'RULE'
    handler_config JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Favoritos
CREATE TABLE erp_favorite (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES usuario(id),
    entity_type VARCHAR(50),
    entity_id UUID,
    label VARCHAR(200),
    url VARCHAR(500),
    display_order INT DEFAULT 0,
    UNIQUE(user_id, entity_type, entity_id)
);
```

### 4.3 Seeds de Modulos y Documentos

```
Modulos:
  ADMIN          Administracion General
  ACCOUNTING     Contabilidad General
  CXC            Cuentas por Cobrar
  CXP            Cuentas por Pagar
  BANKING        Control Bancario
  INVENTORY      Inventarios
  FIXED_ASSETS   Activos Fijos
  PAYROLL        Gestion Nomina
  REPORTING      Reportes
  METADATA       ERP Metadata

Documentos por modulo (ejemplos):
  CXC:       FAC (Factura), NCR (Nota Credito), NDB (Nota Debito),
             REC (Recibo), ANT (Anticipo), AJU (Ajuste), INT (Interes),
             CAS (Castigo), REV (Reversion)
  CXP:       FAC (Factura), NCR (Nota Credito), NDB (Nota Debito),
             PAG (Pago), ANT (Anticipo), RET (Retencion), AJU (Ajuste)
  INVENTORY: ING (Ingreso), SAL (Salida), AJU (Ajuste), TRA (Traslado),
             CON (Conteo), PRO (Produccion)
  BANKING:   DEP (Deposito), CHE (Cheque), TRA (Transferencia),
             NDB (Nota Debito), NCR (Nota Credito)
```

---

## 5. Motor de Configuracion Contable

### 5.1 Estructura

Reemplaza el `module_accounting_config` por un motor completo.

```sql
-- Modulos contables
CREATE TABLE accounting_module (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT
    -- Seed: sales, purchasing, inventory, cash, bank,
    --       fixed_assets, payroll, cxc, cxp, budget, reconciliation
);

-- Grupos de parametros (para organizar la UI)
CREATE TABLE accounting_parameter_group (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES accounting_module(id),
    code VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    display_order INT DEFAULT 0,
    UNIQUE(module_id, code)
);

-- Definicion de parametros contables
CREATE TABLE accounting_parameter (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES accounting_module(id),
    group_id UUID REFERENCES accounting_parameter_group(id),
    code VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    data_type VARCHAR(50) NOT NULL
        CHECK (data_type IN ('ACCOUNT', 'COST_CENTER', 'BOOLEAN',
               'STRING', 'NUMERIC', 'PERCENTAGE', 'DIMENSION')),
    is_required BOOLEAN DEFAULT FALSE,
    validation_rule_id UUID REFERENCES accounting_rule(id),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(module_id, code)
);

-- Valores de parametros (por empresa)
CREATE TABLE accounting_parameter_value (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    parameter_id UUID NOT NULL REFERENCES accounting_parameter(id),
    value_account_id UUID REFERENCES account(id),
    value_cost_center_id UUID REFERENCES cost_center(id),
    value_string VARCHAR(500),
    value_numeric DECIMAL(14,2),
    value_boolean BOOLEAN,
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    updated_by UUID REFERENCES usuario(id),
    UNIQUE(company_id, parameter_id, valid_from)
);
```

### 5.2 Conceptos por Modulo (herencia de diseno previo)

| Modulo | Conceptos Clave |
|--------|----------------|
| Ventas | VENTAS_CONTADO, VENTAS_CREDITO, IVA_DEBITO, DESCUENTOS_VENTA, CXC_CLIENTES, ANTICIPO_CLIENTES |
| Compras | COMPRAS_NAC, COMPRAS_IMP, IVA_CREDITO, RETENCION_IR, RETENCION_IVA, CXP_PROVEEDORES, ANTICIPO_PROV |
| Inventario | INVENTARIO_MERCANCIAS, COSTO_VENTAS, AJUSTE_POSITIVO, AJUSTE_NEGATIVO |
| Caja | CAJA_GENERAL, CAJA_CHICA, INGRESOS_VARIOS, EGRESOS_VARIOS |
| Bancos | BANCO_CUENTA, COMISIONES, INTERESES, CHEQUES_EMITIDOS |
| Activos Fijos | ACTIVO_FIJO, DEPRECIACION_ACUM, GASTO_DEPRECIACION, BAJA_ACTIVO |
| Nomina | SUELDOS, HORAS_EXTRAS, AGUINALDO, VACACIONES, INSS_PATRONAL, INSS_LABORAL, IR_EMPLEADOS |
| CxC | CXC_CLIENTES_NAC, CXC_CLIENTES_EXT, CXC_DUDOSO_COBRO |
| CxP | CXP_PROVEEDORES_NAC, CXP_PROVEEDORES_EXT |

---

## 6. Motor de Workflow

### 6.1 Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            WORKFLOW ENGINE                                  │
│                                                                             │
│  Cada documento tiene un estado actual.                                     │
│  Las transiciones estan definidas en tablas de configuracion.               │
│  Cada transicion puede requerir: aprobacion, reglas, firmas.                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Ejemplo de workflow para Factura de Venta:

    ┌──────────┐
    │ BORRADOR │
    └────┬─────┘
         │ emitir
         ▼
    ┌──────────┐    ┌──────────────┐
    │ PENDIENTE│───▶│  APROBACION  │  (si requiere_aprobacion)
    └────┬─────┘    └──────┬───────┘
         │ aprobar         │ rechazar
         ▼                 ▼
    ┌──────────┐    ┌──────────┐
    │ APROBADA │    │ RECHAZADA│
    └────┬─────┘    └──────────┘
         │ contabilizar
         ▼
    ┌──────────────┐
    │ CONTABILIZADA│
    └──────┬───────┘
           │ cobrar (parcial/total)
           ▼
    ┌──────────┐
    │  PAGADA  │
    └────┬─────┘
         │ anular
         ▼
    ┌──────────┐
    │  ANULADA │
    └──────────┘
```

### 6.2 Tablas

```sql
-- Workflows por tipo de documento
CREATE TABLE wf_workflow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    document_type_id UUID NOT NULL REFERENCES erp_document_type(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(company_id, document_type_id, code)
);

-- Estados del workflow
CREATE TABLE wf_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES wf_workflow(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    is_initial BOOLEAN DEFAULT FALSE,
    is_final BOOLEAN DEFAULT FALSE,
    requires_approval BOOLEAN DEFAULT FALSE,
    requires_signature BOOLEAN DEFAULT FALSE,
    notify_on_enter BOOLEAN DEFAULT FALSE,
    UNIQUE(workflow_id, code)
);

-- Transiciones entre estados
CREATE TABLE wf_transition (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES wf_workflow(id),
    from_status_id UUID NOT NULL REFERENCES wf_status(id),
    to_status_id UUID NOT NULL REFERENCES wf_status(id),
    action_code VARCHAR(50) NOT NULL,
     -- 'EMITIR', 'APROBAR', 'RECHAZAR', 'CONTABILIZAR', 'ANULAR'
    name VARCHAR(200) NOT NULL,

    -- Control
    requires_comment BOOLEAN DEFAULT FALSE,
    requires_approval BOOLEAN DEFAULT FALSE,
    approval_count INT DEFAULT 1,
     -- Numero de aprobaciones requeridas

    -- Reglas
    condition_rule_id UUID REFERENCES accounting_rule(id),
     -- Regla opcional que debe cumplirse para permitir transicion

    -- Reversion
    is_reversion BOOLEAN DEFAULT FALSE,
    -- TRUE = esta transicion revierte el documento a su estado anterior
    reversion_target_status_id UUID REFERENCES wf_status(id),
    -- NULL = estado anterior inmediato

    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(workflow_id, from_status_id, action_code)
);

-- Historial de estados por documento
CREATE TABLE wf_document_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type_id UUID NOT NULL REFERENCES erp_document_type(id),
    document_id UUID NOT NULL,
    from_status_id UUID REFERENCES wf_status(id),
    to_status_id UUID NOT NULL REFERENCES wf_status(id),
    transition_id UUID REFERENCES wf_transition(id),
    user_id UUID NOT NULL REFERENCES usuario(id),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Aprobaciones pendientes
CREATE TABLE wf_pending_approval (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type_id UUID NOT NULL REFERENCES erp_document_type(id),
    document_id UUID NOT NULL,
    transition_id UUID NOT NULL REFERENCES wf_transition(id),
    requested_by UUID NOT NULL REFERENCES usuario(id),
    approved_by UUID REFERENCES usuario(id),
    status VARCHAR(20) DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);
```

---

## 7. Motor de Reglas (Rule Engine)

### 7.1 Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RULE ENGINE                                      │
│                                                                             │
│  Motor independiente que evalua condiciones y ejecuta acciones.             │
│  Utilizado por: Workflow Engine, Template Engine, Security, Alertas.        │
│                                                                             │
│  Ejemplos de reglas:                                                        │
│  - Si cliente.saldo > cliente.limite_credito → bloquear venta              │
│  - Si monto > 10000 → requiere aprobacion                                   │
│  - Si proveedor.tipo == 'EXTRANJERO' → retencion_ir = 15%                  │
│  - Si producto.stock < producto.stock_minimo → alerta de reorden            │
│  - Si factura.antiguedad_dias > 90 → calcular interes_mora                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Tablas

```sql
-- Reglas
CREATE TABLE accounting_rule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    code VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    module VARCHAR(50),
    -- 'sales', 'purchasing', 'all', etc.

    priority INT DEFAULT 0,
    rule_type VARCHAR(50) NOT NULL
        CHECK (rule_type IN ('VALIDATION', 'APPROVAL', 'CALCULATION',
               'TRANSFORMATION', 'ALERT', 'SECURITY')),

    -- Condicion (cuando se evalua la regla)
    condition_expression TEXT NOT NULL,
    -- "{{cliente.saldo_actual + monto}} > {{cliente.limite_credito}}"

    -- Accion (que hacer si la condicion se cumple)
    action_type VARCHAR(50) NOT NULL
        CHECK (action_type IN ('BLOCK', 'WARN', 'APPROVAL_REQUIRED',
               'SET_VALUE', 'CALCULATE', 'NOTIFY', 'TRANSITION')),
    action_config JSONB,
    -- Ej: { "message": "Cliente excede limite de credito",
    --       "severity": "ERROR",
    --       "approval_required": true }

    error_message VARCHAR(500),
     -- Mensaje de error si la regla falla

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, code)
);

-- Variables de contexto disponibles para las reglas
CREATE TABLE accounting_variable (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    data_type VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL
        CHECK (source_type IN ('CONTEXT', 'ENTITY', 'PARAMETER',
               'CALCULATED', 'SYSTEM')),
    source_expression TEXT,
     -- Si source_type = 'CALCULATED', la expresion para calcularla
    is_active BOOLEAN DEFAULT TRUE
);

-- Condiciones reutilizables
CREATE TABLE accounting_condition (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    expression TEXT NOT NULL,
    -- "{{monto_total}} > {{parametro:monto_maximo_sin_aprobacion}}"
    is_active BOOLEAN DEFAULT TRUE
);

-- Log de ejecucion de reglas
CREATE TABLE accounting_rule_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES accounting_rule(id),
    document_type VARCHAR(50),
    document_id UUID,
    context_summary JSONB,
    result VARCHAR(20) NOT NULL
        CHECK (result IN ('PASS', 'FAIL', 'ERROR', 'BLOCKED')),
    error_message TEXT,
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 8. Motor de Numeraciones

### 8.1 Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NUMERACION ENGINE                                   │
│                                                                             │
│  Servicio centralizado e independiente.                                     │
│  Todo documento que requiera numero lo solicita aqui.                       │
│                                                                             │
│  Soporta:                                                                   │
│  - Series (A, B, C, F, etc.)                                               │
│  - Prefijos/Sufijos estaticos y dinamicos (ano, mes, sucursal)            │
│  - Empresa + Sucursal                                                        │
│  - Reinicio anual/mensual                                                   │
│  - Numeracion manual o automatica                                           │
│  - Reserva de numeros (para workflows multi-paso)                          │
│  - Consecutivos paralelos (varios documentos comparten serie)              │
│  - Mascara configurable                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Ejemplos de mascaras:
  "{SERIE}-{NUMERO}"            → "A-000001"
  "{SERIE}{SUCURSAL}-{NUMERO}"  → "M01-000001"
  "{ANO}-{MES}-{NUMERO}"        → "2026-07-000001"
  "FAC-{NUMERO}"                → "FAC-000001"
```

### 8.2 Tablas (extendidas sobre `numeracion` existente)

```sql
-- Se extiende la tabla numeracion existente
-- (los campos nuevos se agregan como opcionales para compatibilidad)

ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS
    sucursal_id UUID REFERENCES sucursal(id);

ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS
    prefijo VARCHAR(20);               -- Prefijo estatico

ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS
    sufijo VARCHAR(20);                -- Sufijo estatico

ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS
    mask VARCHAR(100) DEFAULT '{SERIE}-{NUMERO}';
    -- Mascara completa

ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS
    reinicio VARCHAR(20) DEFAULT 'NUNCA'
        CHECK (reinicio IN ('NUNCA', 'ANUAL', 'MENSUAL'));

ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS
    digitos INT DEFAULT 6;
    -- Cantidad de digitos del numero

ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS
    numeracion_manual BOOLEAN DEFAULT FALSE;
    -- TRUE = el usuario ingresa el numero manualmente

ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS
    permite_reserva BOOLEAN DEFAULT FALSE;
    -- TRUE = permite reservar numeros antes de usarlos

-- Reserva de numeros
CREATE TABLE numeracion_reserva (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numeracion_id UUID NOT NULL REFERENCES numeracion(id),
    numero INT NOT NULL,
    reservado_por UUID NOT NULL REFERENCES usuario(id),
    documento_tipo VARCHAR(50),
    documento_id UUID,
    estado VARCHAR(20) DEFAULT 'RESERVADO'
        CHECK (estado IN ('RESERVADO', 'CONFIRMADO', 'LIBERADO')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(numeracion_id, numero, estado)
);
```

---

## 9. Seguridad Empresarial (RBAC++ + SoD)

### 9.1 Modelo de Permisos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SEGURIDAD EMPRESARIAL                               │
│                                                                             │
│  Usuario ──── Tiene ──── Rol(es) ──── Tiene ──── Permiso(s)                │
│                                                    │                       │
│                          ┌─────────────────────────┼─────────────────┐     │
│                          ▼                         ▼                 ▼     │
│                    ┌──────────┐            ┌──────────────┐  ┌──────────┐  │
│                    │ MODULO   │            │  ACCION      │  │ ALCANCE  │  │
│                    │          │            │              │  │          │  │
│                    │ sales    │            │ create       │  │ company  │  │
│                    │ cxc      │            │ read         │  │ branch   │  │
│                    │ accounting│           │ update       │  │ all      │  │
│                    │ payroll  │            │ delete       │  │ own      │  │
│                    │ reports  │            │ approve      │  │          │  │
│                    │ admin    │            │ reverse      │  │          │  │
│                    │ ...      │            │ export       │  │          │  │
│                    └──────────┘            │ import       │  └──────────┘  │
│                                            │ close        │               │
│                                            │ reopen       │               │
│                                            │ ...          │               │
│                                            └──────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Tablas (extendidas)

```sql
-- Permisos detallados (extension de permiso existente)
ALTER TABLE permiso ADD COLUMN IF NOT EXISTS
    module_id UUID REFERENCES erp_module(id);

ALTER TABLE permiso ADD COLUMN IF NOT EXISTS
    action_type VARCHAR(50);       -- 'CREATE', 'READ', 'UPDATE', 'DELETE',
                                    -- 'APPROVE', 'REVERSE', 'EXPORT', 'IMPORT',
                                    -- 'CLOSE', 'REOPEN', 'PRINT', 'CONFIGURE'

ALTER TABLE permiso ADD COLUMN IF NOT EXISTS
    scope VARCHAR(20) DEFAULT 'ALL'
        CHECK (scope IN ('ALL', 'COMPANY', 'BRANCH', 'OWN'));

-- Restricciones SoD (Segregation of Duties)
CREATE TABLE sod_restriction (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Permisos que no pueden coexistir en un mismo rol
CREATE TABLE sod_conflict (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restriction_id UUID NOT NULL REFERENCES sod_restriction(id),
    permiso_a_id UUID NOT NULL REFERENCES permiso(id),
    permiso_b_id UUID NOT NULL REFERENCES permiso(id),
    UNIQUE(restriction_id, permiso_a_id, permiso_b_id)
);
```

### 9.3 Permisos por Modulo (seed)

| Modulo | Acciones |
|--------|----------|
| admin | user.*, role.*, company.*, branch.*, parameter.* |
| accounting | account.*, journal.*, template.*, close.*, reopen.* |
| cxc | document.*, payment.*, reverse.*, interest.*, castigo.* |
| cxp | document.*, payment.*, retention.*, reverse.* |
| inventory | product.*, adjustment.*, transfer.*, count.* |
| banking | account.*, transaction.*, reconcile.*, check.* |
| fixed_assets | asset.*, depreciate.*, revalue.*, dispose.* |
| payroll | employee.*, process.*, pay.*, config.* |
| reports | view.*, export.*, print.* |
| metadata | module.*, document_type.*, workflow.*, hook.* |

---

## 10. Multiempresa Real

### 10.1 Estrategia de Aislamiento

```
Nivel 1 — LOGICO (actual)
  - Toda tabla tiene company_id
  - Todos los queries filtran por company_id
  - Indices compuestos (company_id, ...)

Nivel 2 — ESQUEMA (futuro, cuando supere ~100 empresas)
  - Un esquema por empresa en la misma base de datos
  - Mismos nombres de tablas, datos separados
  - PostgreSQL schemas: company_001.tables, company_002.tables

Nivel 3 — BASE DE DATOS (futuro, >500 empresas)
  - Base de datos por empresa o grupo de empresas
  - Connection pooling por shard
  - Routing en capa de aplicacion
```

### 10.2 Politicas

```sql
-- Cache de configuracion por empresa
-- Redis: company:{id}:config:{key}

-- Particionamiento futuro (preparado desde ahora):
-- Tablas grandes (asiento_linea, kardex_movimiento, wf_document_history)
--   PARTITION BY LIST (company_id)

-- Todas las consultas CRITICAS deben incluir company_id
-- NO EXISTS (SELECT 1 FROM asiento WHERE ...) sin company_id

-- Auditoria incluye company_id siempre
```

---

## 11. Dimensiones Contables

### 11.1 Modelo

```sql
-- Definicion de dimensiones por empresa
CREATE TABLE accounting_dimension (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(company_id, code)
);

-- Valores de cada dimension
CREATE TABLE accounting_dimension_value (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension_id UUID NOT NULL REFERENCES accounting_dimension(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    parent_id UUID REFERENCES accounting_dimension_value(id),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(dimension_id, code)
);

-- Asignacion de dimensiones a cuentas
-- (la cuenta requiere X dimension obligatoria)
ALTER TABLE account ADD COLUMN IF NOT EXISTS
    dimension_requirements JSONB;
-- Ej: {"cost_center": true, "project": false, "department": true}
```

### 11.2 Dimensiones Predefinidas (Seed)

```
CENTRO_COSTO   Centro de Costo     (jerarquico)
PROYECTO       Proyecto            (jerarquico)
DEPARTAMENTO   Departamento        (simple)
SUCURSAL       Sucursal            (simple)
UNIDAD_NEG     Unidad de Negocio   (jerarquico)
MARCA          Marca               (simple)
CANAL          Canal de Venta      (simple)
REGION         Region              (jerarquico)
```

---

## 12. Catalogo de Cuentas

### 12.1 Diseno (heredado de ADR-002, validado)

Se mantiene el diseno aprobado de ADR-002:

1. `company_account_structure` — niveles, longitud, separador
2. `account_type` — ACTIVO, PASIVO, PATRIMONIO, INGRESO, COSTO, GASTO (+ ORDEN)
3. `financial_classification` — CORRIENTE, NO_CORRIENTE, etc.
4. `tax_classification` — GRAVADO, EXENTO, EXCLUIDO
5. `ifrs_classification` — NIIF para PYME
6. `account` — catalogo con jerarquia, validates, clasificaciones

### 12.2 Reglas de Negocio (reafirmadas)

```
1. Catalogo completamente VACIO al inicio del sistema
2. NO se crea ninguna cuenta automaticamente
3. Unicamente se seedean: account_type, financial_classification,
   tax_classification, ifrs_classification, company_account_structure
4. El usuario carga su catalogo mediante importador Excel/CSV
5. La estructura de codigo es configurable por empresa
6. Cuenta de movimiento (accepts_entries=true) ≠ cuenta de agrupacion
7. Clasificaciones hereditarias (hijo hereda del padre si no especifica)
8. Dimensiones obligatorias configurables por cuenta
```

---

## 13. Parametrizacion por Modulo

### 13.1 Pantallas de Configuracion

Cada modulo tendra su propia pantalla de parametrizacion contable,
leyendo y escribiendo en `accounting_parameter` + `accounting_parameter_value`.

| Modulo | Parametros |
|--------|------------|
| Ventas | Cuenta Clientes, Cuenta Ventas Contado, Cuenta Ventas Credito, IVA Debito, Descuentos, Devoluciones, Anticipos |
| Compras | Cuenta Proveedores, Compras Nacionales, Compras Importacion, IVA Credito, Retencion IR, Retencion IVA, Anticipos |
| Inventario | Cuenta Inventario, Costo Ventas, Ajuste Positivo, Ajuste Negativo, Diferencia Inventario |
| Caja | Caja General, Caja Chica, Ingresos Varios, Egresos Varios, Transferencias |
| Bancos | Cuenta Bancaria, Comisiones, Intereses, Cheques Emitidos, Diferencias Conciliacion |
| Activos Fijos | Activo Fijo, Depreciacion Acumulada, Gasto Depreciacion, Baja Activo, Revaluacion, Mejora |
| Nomina | Sueldos, Horas Extras, Aguinaldo, Vacaciones, INSS Patronal, INSS Laboral, IR Empleados, Prestaciones, Prestamos, Anticipos |
| CxC | CxC Clientes Nacionales, CxC Clientes Extranjeros, CxC Dudoso Cobro |
| CxP | CxP Proveedores Nacionales, CxP Proveedores Extranjeros |

---

## 14. Cuentas por Cobrar / Pagar

### 14.1 Subtipos de Documento (diseno de ADR-002, validado)

Se mantiene el diseno de subtipos con las tablas:
- `cxc_document_subtype`
- `cxp_document_subtype`

Cada subtipo configura:
- Serie, Consecutivo (via NumeracionEngine)
- Evento Contable (via accounting_event)
- Tipo de Asiento y Plantilla
- Cuentas (principal, impuestos, descuentos, intereses, mora, puente)
- Centro de costo y dimensiones
- Reglas (via RuleEngine)
- Comportamiento (aprobacion, reversion, anulacion)

### 14.2 Subtipos CxC

| Codigo | Nombre | Afecta Saldo | Genera Asiento |
|--------|--------|-------------|----------------|
| FAC | Factura | SI | SI |
| NCR | Nota Credito | SI | SI |
| NDB | Nota Debito | SI | SI |
| REC | Recibo de Cobro | SI | NO |
| ANT | Anticipo | SI | SI |
| AJU | Ajuste | SI | SI |
| INT | Interes | SI | SI |
| CAS | Castigo | SI | SI |
| REV | Reversion | SI | SI |

### 14.3 Subtipos CxP

| Codigo | Nombre | Afecta Saldo | Genera Asiento | Afecta Inventario |
|--------|--------|-------------|----------------|-------------------|
| FAC | Factura Proveedor | SI | SI | SI |
| NCR | Nota Credito | SI | SI | SI |
| NDB | Nota Debito | SI | SI | NO |
| PAG | Pago | SI | NO | NO |
| ANT | Anticipo | SI | SI | NO |
| RET | Retencion | SI | SI | NO |
| AJU | Ajuste | SI | SI | NO |

---

## 15. Reporting Layer (BI)

### 15.1 Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REPORTING LAYER (BI)                                │
│                                                                             │
│  Capa independiente que NO escribe en tablas transaccionales.               │
│  Solo LEE datos procesados.                                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────┐                            │
│  │         READ MODELS (Vistas Materializadas)  │                            │
│  │                                             │                            │
│  │  vw_balance_general                         │                            │
│  │  vw_estado_resultados                       │                            │
│  │  vw_flujo_efectivo                          │                            │
│  │  vw_antiguedad_cxc                          │                            │
│  │  vw_antiguedad_cxp                          │                            │
│  │  vw_mayor_general                           │                            │
│  │  vw_diario_general                          │                            │
│  │  vw_kardex_valorizado                       │                            │
│  │  vw_rotacion_inventario                     │                            │
│  │  vw_vencimiento_cartera                     │                            │
│  │  vw_costo_ventas_producto                   │                            │
│  │  vw_analisis_depreciacion                   │                            │
│  │  vw_nomina_acumulada                        │                            │
│  │  vw_presupuesto_vs_real                     │                            │
│  │                                             │                            │
│  └─────────────────────────────────────────────┘                            │
│                          │                                                  │
│                          ▼                                                  │
│  ┌─────────────────────────────────────────────┐                            │
│  │         KPI DASHBOARDS                       │                            │
│  │                                             │                            │
│  │  - Utilidad Bruta / Neta                    │                            │
│  │  - Rotacion de Cartera (DPA)                │                            │
│  │  - Rotacion de Inventario                   │                            │
│  │  - Ciclo de Conversion de Efectivo          │                            │
│  │  - Dias Promedio de Atraso (CxC)           │                            │
│  │  - Porcentaje de Cumplimiento Presupuesto   │                            │
│  │  - EBITDA                                   │                            │
│  │  - Razones Financieras (liquidez,           │                            │
│  │    endeudamiento, rentabilidad)             │                            │
│  │                                             │                            │
│  └─────────────────────────────────────────────┘                            │
│                          │                                                  │
│                          ▼                                                  │
│  ┌─────────────────────────────────────────────┐                            │
│  │         EXPORTACION                          │                            │
│  │                                             │                            │
│  │  - Excel (openpyxl)                         │                            │
│  │  - PDF (ReportLab / WeasyPrint)             │                            │
│  │  - CSV                                      │                            │
│  │  - JSON (API)                               │                            │
│  │                                             │                            │
│  └─────────────────────────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.2 Materialized Views (Refresh Periodico)

```sql
-- Ejemplo: vista materializada de balance general
CREATE MATERIALIZED VIEW vw_balance_general AS
SELECT
    a.company_id,
    a.periodo_id,
    a.fecha,
    cc.codigo AS cuenta_codigo,
    cc.nombre AS cuenta_nombre,
    cc.tipo AS cuenta_tipo,
    SUM(al.debe_local - al.haber_local) AS saldo_local,
    SUM(al.debe_dolar - al.haber_dolar) AS saldo_dolar
FROM asiento a
JOIN asiento_linea al ON al.asiento_id = a.id
JOIN account cc ON cc.id = al.cuenta_id
WHERE a.estado != 'ANULADO'
  AND cc.account_type_id IN ('ACTIVO', 'PASIVO', 'PATRIMONIO')
GROUP BY a.company_id, a.periodo_id, a.fecha, cc.codigo, cc.nombre, cc.tipo
WITH DATA;

CREATE UNIQUE INDEX idx_vw_balance_unique
    ON vw_balance_general(company_id, periodo_id, cuenta_codigo);
```

---

## 16. API Publica

### 16.1 Roadmap de API

```
Fase 1 (actual) — API Interna
  - /api/v1/* para frontend web
  - Autenticacion JWT
  - Documentacion OpenAPI

Fase 2 — API Publica Restringida
  - /api/public/v1/* endpoints seleccionados
  - API Keys para integraciones
  - Rate limiting (100 req/min)
  - Webhooks para eventos

Fase 3 — API Publica Completa
  - /api/public/v1/* todos los modulos
  - GraphQL endpoint para consultas flexibles
  - POS (Point of Sale) API
  - Mobile API
  - eCommerce API
  - Facturacion Electronica API
  - Banking Integration API

Fase 4 — Marketplace
  - Plugin system via hooks
  - Extension API
  - Custom workflows via API
```

---

## 17. Localizaciones

### 17.1 Modelo

```sql
-- Localizaciones por pais
CREATE TABLE localization_country (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(3) NOT NULL UNIQUE,     -- 'NIC', 'CRI', 'GTM', 'SLV', 'HND'
    name VARCHAR(200) NOT NULL,
    currency_code VARCHAR(3) NOT NULL,   -- 'NIO', 'CRC', 'GTQ', etc.
    language VARCHAR(10) DEFAULT 'es',
    date_format VARCHAR(20) DEFAULT 'DD/MM/YYYY',
    decimal_separator VARCHAR(5) DEFAULT '.',
    thousand_separator VARCHAR(5) DEFAULT ','
);

-- Configuracion fiscal por pais
CREATE TABLE localization_tax_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code VARCHAR(3) NOT NULL REFERENCES localization_country(code),
    tax_type VARCHAR(50) NOT NULL,       -- 'IVA', 'ITBMS', 'VAT', 'GST'
    code VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    rate DECIMAL(5,2) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    valid_from DATE,
    valid_to DATE,
    UNIQUE(country_code, code, valid_from)
);

-- Retenciones por pais
CREATE TABLE localization_withholding_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code VARCHAR(3) NOT NULL REFERENCES localization_country(code),
    withholding_type VARCHAR(50) NOT NULL, -- 'IR', 'IVA', 'ITF'
    code VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    rate DECIMAL(5,2),
    rate_type VARCHAR(20) DEFAULT 'PERCENTAGE'
        CHECK (rate_type IN ('PERCENTAGE', 'FIXED_AMOUNT', 'TABLE')),
    min_amount DECIMAL(14,2),
    max_amount DECIMAL(14,2),
    applies_to VARCHAR(20) DEFAULT 'ALL'
        CHECK (applies_to IN ('ALL', 'NATIONAL', 'FOREIGN', 'SPECIAL')),
    valid_from DATE,
    valid_to DATE,
    UNIQUE(country_code, code, valid_from)
);

-- Calendario fiscal por pais
CREATE TABLE localization_fiscal_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code VARCHAR(3) NOT NULL REFERENCES localization_country(code),
    year INT NOT NULL,
    month INT NOT NULL,
    due_date DATE NOT NULL,
    obligation_type VARCHAR(100) NOT NULL,
    description TEXT,
    UNIQUE(country_code, year, month, obligation_type)
);
```

### 17.2 Nicaragua (Seed inicial)

```
Pais: NIC
Moneda: NIO (Cordoba)
Simbolo: C$
Impuesto: IVA 15% (tasa general)
Retenciones:
  - IR 2% (proveedores nacionales)
  - IR 15% (proveedores extranjeros)
  - IVA 100% (retencion total del IVA en compras)
  - ITF 0.25% (impuesto a cheques/transferencias)
Formato: DD/MM/YYYY
Separador: . decimal, , miles
```

---

## 18. Roadmap Detallado por Fases

### FASE 1 — Fundacion Empresarial (Semanas 1-4)

**Objetivo:** Nucleo del ERP con metadatos, seguridad, numeraciones, workflows y reglas.

**Componentes:**
- Administracion General (paises, sucursales, bodegas, unidades, grupos)
- ERP Metadata (modulos, documentos, tipos, estados, acciones)
- Motor de Numeraciones
- RBAC avanzado + SoD
- Motor de Workflow (tablas + logica base)
- Motor de Reglas (tablas + evaluador basico)

**Backend:**
- [ ] Models: erp_module, erp_document_type, erp_document_status, erp_action
- [ ] Models: sucursal, pais, bodega, unidad_medida, denominacion
- [ ] Models: grupo_usuario, permiso_extendido, sod_*
- [ ] Models: wf_workflow, wf_status, wf_transition, wf_document_history, wf_pending_approval
- [ ] Models: accounting_rule, accounting_condition, accounting_variable, accounting_rule_log
- [ ] Extension de numeracion (mask, reinicio, reserva, prefijo/sufijo)
- [ ] CRUDs para todas las tablas nuevas
- [ ] Seeds de modulos, documentos, acciones base

**Frontend:**
- [ ] Pagina de Administracion General con submodulos
- [ ] Pagina de Roles con permisos detallados (matriz modulo x accion)
- [ ] Pagina de Workflow Designer (visual)
- [ ] Pagina de Reglas de Negocio
- [ ] Pagina de Numeraciones con mascara configurable

**Pruebas:**
- [ ] Tests de creacion de empresa + sucursales
- [ ] Tests de RBAC (usuario sin permiso no puede acceder)
- [ ] Tests de workflow (transiciones, aprobaciones)
- [ ] Tests de numeracion (series, reinicio, concurrencia)

---

### FASE 2 — Motor Contable (Semanas 5-8)

**Objetivo:** Centro del ERP — motor de eventos, plantillas, configuracion.

**Componentes:**
- Motor de Configuracion Contable
- Motor de Eventos Contables
- Motor de Plantillas (TemplateEngine)
- ExpressionEvaluator
- JournalEngine

**Backend:**
- [ ] Models: accounting_module, accounting_parameter_group, accounting_parameter, accounting_parameter_value
- [ ] Models: accounting_event, journal_type, journal_template, journal_template_line
- [ ] Implementar ExpressionEvaluator (tokenizer, AST, Decimal evaluator)
- [ ] Implementar TemplateEngine (resolucion, evaluacion, lineas)
- [ ] Implementar JournalEngine (validacion, numeracion, escritura)
- [ ] Implementar EventResolver (conexion evento → journal_type)
- [ ] Seeds de modulos contables y parametros base

**Frontend:**
- [ ] Pagina de Eventos Contables
- [ ] Pagina de Tipos de Asiento
- [ ] Pagina de Plantillas con editor de lineas + preview
- [ ] Pagina de Configuracion Contable por Modulo
- [ ] Editor de expresiones con validacion en vivo

**Feature Flag:**
- [ ] `NEW_ACCOUNTING_ENGINE` en tabla `parametro`
- [ ] INACTIVE → VALIDATION (ambos motores) → ACTIVE

**Pruebas:**
- [ ] Tests de cada funcion del ExpressionEvaluator
- [ ] Tests de resolucion de cuentas (FIXED, PARAM, CONTEXT, SUBTYPE, RULE)
- [ ] Tests de partida doble
- [ ] Tests de validacion paralela (motor viejo vs nuevo)

---

### FASE 3 — Catalogo de Cuentas (Semanas 9-10)

**Objetivo:** Catalogo configurable vacio + importador.

**Backend:**
- [ ] Models: company_account_structure, account_type, financial_classification, tax_classification, ifrs_classification
- [ ] Models: account, accounting_dimension, accounting_dimension_value
- [ ] Importador de Catalogo (preview, validate, bulk insert)
- [ ] Sincronizador cuenta_contable ↔ account (strangler fig)

**Frontend:**
- [ ] Pagina de Estructura del Catalogo
- [ ] Pagina de Catalogo en arbol (jerarquia visual)
- [ ] Modal de creacion/edicion de cuenta con clasificaciones
- [ ] Pagina de Importacion (drag & drop Excel, preview, confirmar)

**Migracion:**
- [ ] Migrar 32 cuentas actuales de cuenta_contable a account
- [ ] Crear company_account_structure para mantener codigo actual
- [ ] Poblar module_accounting_config con valores actuales de constants.py

---

### FASE 4 — Cuentas por Cobrar (Semanas 11-12)

**Backend:**
- [ ] Models: cxc_document_subtype
- [ ] Refactorizar Facturacion para usar subtipos + accounting_event
- [ ] Conectar con TemplateEngine (evento → asiento)
- [ ] Intereses de Mora (calculo automatico configurable)
- [ ] Dias Promedio de Atraso
- [ ] Estados de Cuenta con detalle de aplicaciones
- [ ] Analisis de Antiguedad mejorado (rangos configurables)
- [ ] Reportes por Moneda

**Frontend:**
- [ ] Pagina de Administracion CxC (subtipos, parametros, reglas)
- [ ] Consulta General de Documentos con filtros
- [ ] Estados de Cuenta por cliente
- [ ] Analisis de Vencimiento / Antiguedad

---

### FASE 5 — Cuentas por Pagar (Semanas 13-14)

**Backend:**
- [ ] Models: cxp_document_subtype
- [ ] Refactorizar Compras para usar subtipos + accounting_event
- [ ] Conectar con TemplateEngine
- [ ] Aplicacion de Pagos (aplicar multiples facturas)
- [ ] Pago de Retenciones (reporte DGI)
- [ ] Diferencias Cambiarias (por fluctuacion TC)
- [ ] Ajuste mensual retencion en la fuente

**Frontend:**
- [ ] Pagina de Administracion CxP
- [ ] Documentos CxP con detalle completo
- [ ] Aplicacion de Pagos
- [ ] Retenciones

---

### FASE 6 — Inventarios (Semanas 15-16)

- [ ] Metodos de Costeo: Promedio, FIFO, UEPS
- [ ] Traspasos entre bodegas
- [ ] Conteo Fisico con ajuste automatico
- [ ] Costeo de Importaciones (liquidacion)
- [ ] Reportes: existencias valorizadas, rotacion, kardex

---

### FASE 7 — Control Bancario (Semanas 17-18)

- [ ] Caja General (apertura, arqueo, cierre)
- [ ] Caja Chica (fondo fijo)
- [ ] Cheques Emitidos / Recibidos / Reversados
- [ ] Transferencias entre cuentas
- [ ] Conciliacion Bancaria (cruce automatico)

---

### FASE 8 — Activos Fijos (Semana 19)

- [ ] Conexion con TemplateEngine
- [ ] Revaluacion de Activos
- [ ] Mejoras / Capitalizacion
- [ ] Depreciacion por componentes

---

### FASE 9 — Nomina (Semanas 20-21)

- [ ] Calculo INSS Patronal/Laboral
- [ ] Calculo IR (tabla progresiva)
- [ ] Aguinaldo (decimo tercer mes)
- [ ] Vacaciones / Prestaciones
- [ ] Integracion con TemplateEngine

---

### FASE 10 — BI y Reportes (Semanas 22-24)

- [ ] Vistas materializadas para todos los modulos
- [ ] Estados Financieros (Balance, ER, Flujo, Cambios Patrimonio)
- [ ] Libros Contables (Diario, Mayor, Auxiliares)
- [ ] Dashboard con KPIs
- [ ] Exportacion Excel / PDF
- [ ] OCR (captura de facturas)
- [ ] IA (analisis predictivo)
- [ ] API Publica (primera version)
- [ ] Localizaciones (Nicaragua + preparacion para otros paises)

---

## 19. Diagramas de Arquitectura

### 19.1 Bounded Contexts

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              CORE DOMAIN                                   │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │    MOTOR CONTABLE   │  │   MOTOR WORKFLOW    │  │    MOTOR REGLAS     │ │
│  │                     │  │                     │  │                     │ │
│  │  accounting_event   │  │  wf_workflow        │  │  accounting_rule    │ │
│  │  journal_type       │  │  wf_status          │  │  accounting_cond    │ │
│  │  journal_template   │  │  wf_transition      │  │  accounting_var     │ │
│  │  journal_line       │  │  wf_history         │  │  rule_log           │ │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘ │
│             │                        │                        │            │
└─────────────┼────────────────────────┼────────────────────────┼────────────┘
              │                        │                        │
┌─────────────┼────────────────────────┼────────────────────────┼────────────┐
│             │        SUPPORTING DOMAINS                       │            │
│             │                                                 │            │
│  ┌──────────▼──────────┐  ┌──────────▼──────────┐            │            │
│  │  ERP METADATA       │  │  NUMERACION ENGINE  │            │            │
│  │  erp_module         │  │  numeracion         │            │            │
│  │  erp_document_type  │  │  numeracion_reserva │            │            │
│  │  erp_status         │  │                     │            │            │
│  │  erp_hook           │  └─────────────────────┘            │            │
│  └─────────────────────┘                                     │            │
│                                                               │            │
│  ┌─────────────────────┐  ┌─────────────────────┐            │            │
│  │  CONFIG CONTABLE    │  │  SEGURIDAD          │            │            │
│  │  accounting_module  │  │  permiso_ext        │            │            │
│  │  accounting_param   │  │  sod_restriction    │            │            │
│  │  accounting_value   │  │  sod_conflict       │            │            │
│  └─────────────────────┘  └─────────────────────┘            │            │
│                                                               │            │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                          GENERIC SUBDOMAINS                                │
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  CxC         │ │  CxP        │ │  INVENTARIO │ │  BANCOS     │          │
│  │  Facturacion │ │  Compras    │ │  Productos  │ │  Cuentas    │          │
│  │  Cobros      │ │  Pagos      │ │  Bodegas    │ │  Conciliac  │          │
│  │  Antiguedad  │ │  Retenciones│ │  Costeo     │ │  Cheques    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  ACTIVOS    │ │  NOMINA     │ │  REPORTES   │ │  LOCALIZAC  │          │
│  │  Depreciac  │ │  Empleados  │ │  Read Models│ │  Paises     │          │
│  │  Revaluac   │ │  Calculo    │ │  KPI        │ │  Impuestos  │          │
│  │  Bajas      │ │  INSS/IR    │ │  Dashboards │ │  Calendar   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 19.2 Flujo del Motor Contable (detallado)

```
EVENTO DE NEGOCIO
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCOUNTING_EVENT_RESOLVER                                                   │
│                                                                             │
│  valida:                                                                    │
│  ├── ¿El evento existe en accounting_event?                                 │
│  ├── ¿El periodo esta abierto?                                              │
│  ├── ¿El documento es valido? (no duplicado)                                │
│  └── ¿Las validaciones previas pasan? (RuleEngine.check)                    │
│                                                                             │
│  resuelve journal_type:                                                     │
│  ├── DIRECT → journal_type_id del evento                                    │
│  ├── SUBTYPE → del documento_subtype.journal_type_id                        │
│  ├── RULE → RuleEngine.evaluate(rule_id, context)                           │
│  └── PARAM → accounting_parameter_value                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TEMPLATE ENGINE                                                             │
│                                                                             │
│  templates = journal_template.by_journal_type(journal_type_id)              │
│  templates.sort(priority DESC)                                              │
│                                                                             │
│  for template in templates:                                                 │
│      if template.condition:                                                 │
│          if not ExpressionEvaluator.eval(template.condition, context):      │
│              continue  → siguiente template                                 │
│                                                                             │
│      lines = []                                                             │
│      for line in template.lines:                                            │
│          if line.condition:                                                 │
│              if not ExpressionEvaluator.eval(line.condition, context):       │
│                  if line.is_mandatory: break → next template                │
│                  else: continue → siguiente linea                            │
│                                                                             │
│          account_id = resolve_account(line, context)                         │
│          amount = ExpressionEvaluator.eval(line.amount_expression, context) │
│          description = render_description(line, context)                     │
│          cost_center_id = resolve_cost_center(line, context)                 │
│                                                                             │
│          lines.append({line.nature, account_id, amount, description,        │
│                        cost_center_id, dimensions})                          │
│                                                                             │
│      if sum(debits) == sum(credits):                                        │
│          return lines  → envio a JournalEngine                               │
│                                                                             │
│  raise NoTemplateMatchedError()                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ JOURNAL ENGINE                                                              │
│                                                                             │
│  numero = NumeracionEngine.next("ASIENTO", periodo_id)                      │
│                                                                             │
│  asiento = Asiento(empresa_id, periodo_id, numero, fecha,                   │
│                    journal_type_id, conceptos,                               │
│                    document_id, document_type,                               │
│                    created_by)                                               │
│                                                                             │
│  for line in lines:                                                        │
│      AsientoLinea(asiento_id, cuenta_id, debe, haber,                       │
│                   descripcion, centro_costo, dimensiones)                    │
│                                                                             │
│  db.session.add(asiento)                                                    │
│  db.session.add_all(lineas)                                                 │
│                                                                             │
│  update_saldos_cuentas(asiento)                                             │
│  registro_bitacora(asiento)                                                 │
│                                                                             │
│  db.session.commit()                                                        │
│                                                                             │
│  event_bus.publish(AsientoCreado(asiento_id, numero, documento_id))         │
│  WorkflowEngine.evaluate(documento, 'CONTABILIZAR')                         │
│  RuleEngine.evaluate_post(asiento)                                          │
│                                                                             │
│  return asiento                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 19.3 Diagrama de Motor de Reglas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RULE ENGINE                                      │
│                                                                             │
│  Punto de entrada unico: RuleEngine.evaluate(rules, context)                │
│                                                                             │
│  Flujo:                                                                     │
│                                                                             │
│  1. Cargar reglas activas                                                  │
│     └── Filtro por: company_id, module, rule_type                          │
│  2. Ordenar por priority DESC                                               │
│  3. Para cada regla:                                                        │
│     ├── Evaluar condition_expression con ExpressionEvaluator                │
│     ├── Si cumple:                                                          │
│     │   ├── Ejecutar action_type:                                           │
│     │   │   ├── BLOCK           → retornar error                           │
│     │   │   ├── WARN            → agregar warning a lista                   │
│     │   │   ├── APPROVAL_REQ    → crear wf_pending_approval                 │
│     │   │   ├── SET_VALUE       → modificar valor en contexto               │
│     │   │   ├── CALCULATE       → ejecutar formula y guardar                │
│     │   │   ├── NOTIFY          → enviar notificacion                       │
│     │   │   └── TRANSITION      → ejecutar transicion de workflow           │
│     │   └── Registrar en accounting_rule_log                                │
│     └── Si no cumple: continuar                                             │
│                                                                             │
│  Retorna: { warnings: [], errors: [], blocks: [], approvals: [] }          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Contexto disponible para las reglas:
{
  "document": { tipo, numero, fecha, monto, ... },
  "customer": { id, nombre, saldo, limite_credito, ... },
  "supplier": { id, nombre, tipo, aplica_iva, tasa_iva, ... },
  "product": { id, codigo, stock, costo, precio, ... },
  "account": { id, codigo, saldo, ... },
  "user": { id, nombre, roles, ... },
  "company": { id, nombre, pais, moneda, ... },
  "params": { "param_key": value, ... },
  "system": { "fecha": "2026-07-01", "periodo": "2026-07", ... }
}
```

---

## 20. Modelo Entidad-Relacion de Alto Nivel

```
ERP METADATA
  erp_module ──── N erp_document_type ──── N erp_document_subtype
       │                                        │
       │                                        └── cxc_subtype_id → cxc_document_subtype
       │                                        └── cxp_subtype_id → cxp_document_subtype
       │
       └─── N erp_business_event
       └─── N erp_hook
       └─── N erp_action

SEGURIDAD
  usuario ──── N grupo_usuario
  usuario ──── N usuario_rol ──── N rol ──── N rol_permiso ──── N permiso
       │                                              │
       │                                              └── module_id → erp_module
       │                                              └── action_type
       │                                              └── scope
       └─── N sod_restriction ──── N sod_conflict

ADMINISTRACION
  empresa ──── N sucursal
  empresa ──── N moneda ──── N tipo_cambio
  empresa ──── N pais
  empresa ──── N bodega
  empresa ──── N unidad_medida
  empresa ──── N denominacion
  empresa ──── N periodo_contable
  empresa ──── N numeracion ──── N numeracion_reserva
  empresa ──── N parametro

MOTOR CONTABLE
  empresa ──── N accounting_module ──── N accounting_parameter_group ──── N accounting_parameter ──── N accounting_parameter_value
  empresa ──── N accounting_event ──── N journal_type ──── N journal_template ──── N journal_template_line
  empresa ──── N accounting_rule ──── N accounting_rule_log
  empresa ──── N accounting_condition
  empresa ──── N accounting_variable

CATALOGO CUENTAS
  empresa ──── N company_account_structure
  empresa ──── N account_type
  empresa ──── N financial_classification
  empresa ──── N tax_classification
  empresa ──── N ifrs_classification
  empresa ──── N account ──── N account (parent)
  empresa ──── N accounting_dimension ──── N accounting_dimension_value

ASIENTOS
  empresa ──── N asiento ──── N asiento_linea ──── N account
       │                        │
       │                        └── dimension_id → accounting_dimension_value
       │                        └── centro_costo_id → centro_costo
       └── journal_type_id → journal_type

WORKFLOW
  empresa ──── N wf_workflow ──── N wf_status
       │              │               │
       │              └── N wf_transition
       │                      ├── from_status_id → wf_status
       │                      └── to_status_id → wf_status
       │
       └── N wf_document_history
       └── N wf_pending_approval

LOCALIZACIONES
  localization_country ──── N localization_tax_config
       │                       
       └─── N localization_withholding_config
       └─── N localization_fiscal_calendar
```

---

## 21. ADRs

### ADR-002: Reingenieria del Nucleo Contable (v2)

**Estado:** Pendiente de aprobacion

**Decision:** Reemplazar el sistema contable actual (cuentas hardcodeadas +
logica en servicios) por un Motor Contable basado en eventos, plantillas
configurables y resolucion dinamica de cuentas.

**Design Docs:** `docs/architecture/002-accounting-core-reengineering.md`,
Plan Maestro v2.0 secciones 3, 4, 5, 6, 7

**Consecuencias:**
- Positivas: cero cuentas en codigo, parametrizacion completa,
  modulos desacoplados, facil auditoria, extensible
- Negativas: mayor complejidad inicial, requiere UI de configuracion,
  migracion gradual (strangler fig)
- Riesgos: performance de evaluacion de expresiones (mitigado con cache LRU),
  curva de aprendizaje para contadores (mitigado con UI intuitiva)

### ADR-003: Estrategia de Migracion Strangler Fig

**Estado:** Pendiente de aprobacion

**Decision:** Las nuevas tablas coexisten con las actuales. Implementar
feature flag `NEW_ACCOUNTING_ENGINE` con estados:
INACTIVE → VALIDATION (ambos, comparar resultados) → ACTIVE

### ADR-004: Motor de Expresiones

**Estado:** Pendiente de aprobacion

**Decision:** Mini-lenguaje con {{variables}}, operadores aritmeticos/logicos,
funciones sum/if/round/abs. Implementacion con Tokenizer + Shunting-yard + AST.
Expresiones compiladas cacheadas (LRU). Sin uso de eval().

### ADR-005: API Versionado

**Estado:** Pendiente de aprobacion

**Decision:** /api/v1/ para API interna. /api/public/v1/ para API publica (Fase 10).
OpenAPI como contrato. Versionado semantico.

### ADR-006: Multiempresa

**Estado:** Pendiente de aprobacion

**Decision:** Aislamiento logico por company_id (actual). Preparado para
aislamiento por esquema (futuro). Indices siempre con company_id como
primer campo. Cache por empresa en Redis.

### ADR-007: Reporting Layer

**Estado:** Pendiente de aprobacion

**Decision:** Vistas materializadas como read models. Refresh periodico.
No queries directas a tablas transaccionales para reportes pesados.
Capa separada con su propio esquema de base de datos (rw_).

### ADR-008: Localizaciones

**Estado:** Pendiente de aprobacion

**Decision:** Tablas separadas por pais. Nicaragua como primera localizacion.
Impuestos, retenciones, calendarios fiscales en datos, no en codigo.
Preparado para nuevos paises sin modificar el sistema.

---

## 22. Criterios de Exito

### 22.1 Tecnicos

- [ ] 0 cuentas hardcodeadas en el codigo fuente
- [ ] 100% de los asientos generados por el TemplateEngine
- [ ] Feature flag puede conmutar entre motores sin downtime
- [ ] Todos los modulos publican eventos, ninguno conoce cuentas
- [ ] Cobertura de tests > 80%
- [ ] Tiempo de respuesta API < 200ms (p95)
- [ ] Tiempo de generacion de asiento < 500ms
- [ ] Build frontend sin errores de TypeScript

### 22.2 Funcionales

- [ ] Contador puede configurar parametros contables sin programar
- [ ] Contador puede crear workflows sin programar
- [ ] Contador puede definir reglas de negocio sin programar
- [ ] Contador puede cargar catalogo de cuentas desde Excel
- [ ] Administrador puede crear modulos, documentos y estados nuevos
- [ ] Auditor puede revisar todas las operaciones en bitacora

### 22.3 De Negocio

- [ ] Usuario puede migrar desde ERP de referencia sin perdida de funcionalidad
- [ ] Sistema soporta empresas con estructura multi-sucursal
- [ ] Sistema soporta operaciones multi-moneda
- [ ] Sistema soporta Nicaragua + preparado para otros paises
- [ ] Sistema puede operar 20+ anos sin cambios arquitectonicos mayores

---

## Apendice A: Tablas Existentes vs Nuevas (Resumen)

| Tabla | Estado | Modulo |
|-------|--------|--------|
| empresa | Existente | Admin |
| sucursal | **Nueva** | Admin |
| usuario | Existente | Admin |
| grupo_usuario | **Nueva** | Admin |
| rol | Existente | Admin |
| permiso | Extender | Admin |
| usuario_rol | Existente | Admin |
| rol_permiso | Existente | Admin |
| sod_restriction | **Nueva** | Admin |
| sod_conflict | **Nueva** | Admin |
| pais | **Nueva** | Admin |
| moneda | Existente | Admin |
| tipo_cambio | Existente | Admin |
| denominacion | **Nueva** | Admin |
| condicion_pago | Existente | Admin |
| impuesto | Existente | Admin |
| retencion | **Nueva** | Admin |
| bodega | **Nueva** | Admin |
| unidad_medida | **Nueva** | Admin |
| periodo_contable | Existente | Admin |
| numeracion | Extender | Admin |
| numeracion_reserva | **Nueva** | Admin |
| parametro | Existente | Admin |
| bitacora_proceso | **Nueva** | Admin |
| auditoria | Existente | Admin |

| erp_module | **Nueva** | Metadata |
| erp_document_type | **Nueva** | Metadata |
| erp_document_subtype | **Nueva** | Metadata |
| erp_document_status | **Nueva** | Metadata |
| erp_business_event | **Nueva** | Metadata |
| erp_action | **Nueva** | Metadata |
| erp_hook | **Nueva** | Metadata |
| erp_favorite | **Nueva** | Metadata |

| company_account_structure | **Nueva** | Contabilidad |
| account_type | **Nueva** | Contabilidad |
| financial_classification | **Nueva** | Contabilidad |
| tax_classification | **Nueva** | Contabilidad |
| ifrs_classification | **Nueva** | Contabilidad |
| account | **Nueva** | Contabilidad |
| cuenta_contable | Deprecar | Contabilidad |
| accounting_dimension | **Nueva** | Contabilidad |
| accounting_dimension_value | **Nueva** | Contabilidad |

| accounting_module | **Nueva** | Motor Contable |
| accounting_parameter_group | **Nueva** | Motor Contable |
| accounting_parameter | **Nueva** | Motor Contable |
| accounting_parameter_value | **Nueva** | Motor Contable |
| accounting_event | **Nueva** | Motor Contable |
| journal_type | **Nueva** | Motor Contable |
| journal_template | **Nueva** | Motor Contable |
| journal_template_line | **Nueva** | Motor Contable |
| accounting_rule | **Nueva** | Motor Contable |
| accounting_condition | **Nueva** | Motor Contable |
| accounting_variable | **Nueva** | Motor Contable |
| accounting_rule_log | **Nueva** | Motor Contable |

| asiento | Existente | Motor Contable |
| asiento_linea | Existente | Motor Contable |
| centro_costo | Existente | Contabilidad |

| wf_workflow | **Nueva** | Workflow |
| wf_status | **Nueva** | Workflow |
| wf_transition | **Nueva** | Workflow |
| wf_document_history | **Nueva** | Workflow |
| wf_pending_approval | **Nueva** | Workflow |

| cxc_document_subtype | **Nueva** | CxC |
| cxp_document_subtype | **Nueva** | CxP |
| cliente | Existente | CxC |
| proveedor | Existente | CxP |
| factura_venta | Existente | CxC |
| factura_compra | Existente | CxP |
| orden_compra | Existente | CxP |

| localization_country | **Nueva** | Localizacion |
| localization_tax_config | **Nueva** | Localizacion |
| localization_withholding_config | **Nueva** | Localizacion |
| localization_fiscal_calendar | **Nueva** | Localizacion |

| producto | Existente | Inventario |
| categoria | Existente | Inventario |
| kardex_movimiento | Existente | Inventario |

| cuenta_banco | Existente | Bancos |
| movimiento_banco | Existente | Bancos |

| activo_fijo | Existente | Activos |
| empleado | Existente | Nomina |
| nomina_periodo | Existente | Nomina |
| nomina_detalle | Existente | Nomina |

---

## Apendice B: Glosario

| Termino | Definicion |
|---------|------------|
| Evento de Negocio | Accion en un modulo (emitir factura, registrar compra) |
| Evento Contable | Representacion del evento lista para contabilizar |
| Journal Type | Tipo de asiento (VENTA_CONT, COMPRA_NAC) |
| Template | Plantilla que define como generar un asiento |
| Template Line | Linea individual de la plantilla (debe/haber, cuenta, monto) |
| Expression | Formula calculada: "{{total * 0.15}}" |
| Rule | Regla de negocio configurable con condicion + accion |
| Workflow | Maquina de estados para documentos |
| Dimension | Eje analitico: centro costo, proyecto, departamento |
| Subtipo | Variante de documento con comportamiento propio |
| Serie | Prefijo alfabetico para numeracion (A, B, F) |
| Mascara | Formato del numero: "{SERIE}-{NUMERO}" |
| Strangler Fig | Patron de migracion donde nuevo codigo coexiste con viejo |
| SoD | Segregation of Duties: separacion de roles incompatibles |
| Read Model | Vista optimizada para lectura (materializada) |
| Bounded Context | Limite explicito de un dominio dentro del ERP |
