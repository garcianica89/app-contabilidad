# Arquitectura Final ERP v3.0

> **Version:** 3.0
> **Fecha:** 2026-07-01
> **Estado:** Aprobado para implementacion
> **Clasificacion:** CONFIDENCIAL — Arquitectura definitiva
> **Benchmark funcional:** ERP de referencia 7.00

---

## Indice

1. [Estructura de Modulos](#1-estructura-de-modulos)
2. [Bounded Contexts y Diagrama](#2-bounded-contexts-y-diagrama)
3. [Administracion General](#3-administracion-general)
4. [Motor Contable (Centro del ERP)](#4-motor-contable-centro-del-erp)
5. [Catalogos Compartidos](#5-catalogos-compartidos)
6. [Flujo de Inventario](#6-flujo-de-inventario)
7. [Flujo de Compras](#7-flujo-de-compras)
8. [Flujo de Facturacion](#8-flujo-de-facturacion)
9. [Flujo de Cuentas por Pagar y Retenciones](#9-flujo-de-cuentas-por-pagar-y-retenciones)
10. [Flujo de Generacion de Asientos](#10-flujo-de-generacion-de-asientos)
11. [Tablas Nuevas y Modificadas](#11-tablas-nuevas-y-modificadas)
12. [Mejoras Aplicadas](#12-mejoras-aplicadas)
13. [Riesgos Identificados](#13-riesgos-identificados)
14. [Roadmap de Implementacion por Fases](#14-roadmap-de-implementacion-por-fases)
15. [Proximos Pasos](#15-proximos-pasos)

---

## 1. Estructura de Modulos

### 1.1 Los 11 Modulos del ERP

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       SISTEMA ERP — 11 MODULOS                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ADMINISTRACION GENERAL                                                  │
│     Usuarios | Roles | Permisos | Empresas | Sucursales                     │
│     Monedas | Tipos de Cambio | Centros de Costo                           │
│     Periodos | Ejercicios | Auditoria | Bitacora                           │
│     Configuracion General | Parametrizacion centralizada                   │
│                                                                             │
│  2. CONTABILIDAD GENERAL                                                    │
│     Motor Contable | Catalogo de Cuentas | Asientos                         │
│     Cierres | Balanza | Diario | Mayor | Estados Financieros               │
│     Reportes: Diario, Mayor, Balanza, Balance General, ER, Flujo Efectivo  │
│                                                                             │
│  3. BANCOS                                                                  │
│     Cuentas Bancarias | Movimientos | Conciliacion Bancaria                 │
│     Cheques Emitidos/Recibidos | Transferencias                            │
│     Caja General | Caja Chica                                              │
│     Reportes: Movimientos, Conciliacion, Saldos                            │
│                                                                             │
│  4. CUENTAS POR COBRAR                                                     │
│     Administracion de Cartera | Cobros | Antiguedad de Saldos              │
│     Estados de Cuenta | Intereses | Castigos                               │
│     Reportes: Antiguedad, Estado de Cuenta, Mora                           │
│                                                                             │
│  5. CUENTAS POR PAGAR                                                      │
│     Administracion de Pasivo | Pagos | Retenciones                         │
│     Vencimientos | Antiguedad                                              │
│     Reportes: Vencimientos, Retenciones, Antiguedad                        │
│                                                                             │
│  6. COMPRAS                                                                │
│     Ordenes de Compra | Entrada de Inventario                              │
│     Proveedores (compartidos con CxP)                                      │
│     Reportes: Compras por proveedor, por producto                          │
│                                                                             │
│  7. FACTURACION                                                            │
│     Facturas | Notas Credito | Notas Debito                                │
│     Clientes (compartidos con CxC)                                         │
│     Reportes: Ventas, Impuestos, Clientes                                  │
│                                                                             │
│  8. INVENTARIO                                                             │
│     Productos | Bodegas | Kardex | Costeo                                  │
│     Ajustes | Traslados | Conteo Fisico                                    │
│     Reportes: Kardex, Existencias, Valorizacion, Rotacion                  │
│                                                                             │
│  9. ACTIVOS FIJOS                                                          │
│     Depreciacion | Revaluacion | Bajas | Mejoras                           │
│     Reportes: Depreciacion, Analisis de Activos                            │
│                                                                             │
│ 10. NOMINA                                                                 │
│     Empleados | Calculo INSS/IR | Aguinaldo                                │
│     Vacaciones | Prestaciones | Provisiones                                │
│     Reportes: Nominas, INSS, IR, Vacaciones                                │
│                                                                             │
│ 11. PRESUPUESTOS                                                           │
│     Presupuesto vs Real | Proyecciones                                     │
│     Reportes: Comparativos, Desviaciones                                   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Principios de Diseno

```
1. MOTOR CONTABLE ES EL CENTRO
   Ningun modulo de negocio sabe contabilizar.
   Solo publican eventos. El motor contable resuelve todo.

2. CONFIGURACION > CODIGO
   Toda regla de negocio, parametro contable, workflow
   y comportamiento debe ser configurable desde datos.

3. MODULOS INDEPENDIENTES
   Cada modulo es autonomo. Comunicacion exclusivamente
   por eventos asincronos via Bus de Eventos interno.

4. CATALOGO UNICO DE TERCEROS
   Cliente, Proveedor y Empleado comparten tabla base
   'tercero' con roles. Sin duplicacion de datos.

5. CODIGO UNICO DE PRODUCTO
   Compras, Facturacion e Inventario usan el mismo
   catalogo de productos. Sin duplicidad de codigos.

6. CERO CUENTAS HARDCODEADAS
   Ninguna cuenta contable vive en el codigo fuente.
   Todo sale de tablas de configuracion.

7. CATALOGO VACIO AL INICIO
   El sistema se instala sin cuentas. Solo estructura.
   El usuario carga su plan de cuentas.

8. NUMERACION CONFIGURABLE
   Por empresa, sucursal, serie, mascara, reinicio.

9. REPORTES POR MODULO
   Cada modulo contiene sus propios reportes.
   No existe un modulo independiente de Reportes.

10. AUDITORIA POR DEFECTO
    Toda operacion critica queda registrada con
    usuario, fecha, valor anterior, valor nuevo.

11. DISENO PARA 20 ANOS
    Escalabilidad horizontal, tablas particionables,
    indices preparados, API versionada, localizaciones
    desde el dia 1.
```

---

## 2. Bounded Contexts y Diagrama

### 2.1 Mapa de Contextos Actualizado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CORE DOMAIN                                          │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        MOTOR CONTABLE                                 │   │
│  │                                                                        │   │
│  │  Accounting Event → Journal Type → Template Engine → Journal Engine   │   │
│  │  ExpressionEvaluator | Rule Engine | Numeracion Engine                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      SUPPORTING DOMAINS                                      │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │ ADMIN GENERAL    │  │ CONTABILIDAD     │  │ BANCOS           │           │
│  │                  │  │                  │  │                  │           │
│  │ Usuarios/Roles   │  │ Catalogo Cuentas │  │ Cuentas Bcos     │           │
│  │ Empresas/Sucurs  │  │ Asientos/Cierres │  │ Movimientos      │           │
│  │ Monedas/TC       │  │ Balanza/Mayor    │  │ Conciliacion     │           │
│  │ Centros Costo    │  │ Estados Finan    │  │ Cheques/Caja     │           │
│  │ Periodos/Ejerc   │  │ Reportes propios │  │ Reportes propios │           │
│  │ Configuracion    │  └──────────────────┘  └──────────────────┘           │
│  └──────────────────┘                                                       │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │ CXC              │  │ CXP              │  │ COMPRAS          │           │
│  │                  │  │                  │  │                  │           │
│  │ Cartera          │  │ Pasivo           │  │ Ordenes Compra   │           │
│  │ Cobros           │  │ Pagos            │  │ Entrada Invent   │           │
│  │ Antiguedad       │  │ Retenciones      │  │ Proveedores      │           │
│  │ Estados Cta      │  │ Vencimientos     │  │ Reportes propios │           │
│  │ Reportes propios │  │ Reportes propios │  └──────────────────┘           │
│  └──────────────────┘  └──────────────────┘                                  │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │ FACTURACION      │  │ INVENTARIO       │  │ ACTIVOS FIJOS    │           │
│  │                  │  │                  │  │                  │           │
│  │ Facturas Electr  │  │ Productos        │  │ Depreciacion     │           │
│  │ Notas Cred/Deb   │  │ Bodegas/Kardex   │  │ Revaluacion      │           │
│  │ Clientes         │  │ Costeo           │  │ Bajas/Mejoras    │           │
│  │ Reportes propios │  │ Ajustes/Traslados│  │ Reportes propios │           │
│  └──────────────────┘  │ Conteo Fisico    │  └──────────────────┘           │
│                        │ Reportes propios │                                  │
│                        └──────────────────┘                                  │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                                 │
│  │ NOMINA           │  │ PRESUPUESTOS     │                                 │
│  │                  │  │                  │                                 │
│  │ Empleados        │  │ Presupuesto      │                                 │
│  │ Calculo INSS/IR  │  │ Vs Real          │                                 │
│  │ Aguinaldo/Vacac  │  │ Proyecciones     │                                 │
│  │ Prestaciones     │  │ Reportes propios │                                 │
│  │ Reportes propios │  └──────────────────┘                                 │
│  └──────────────────┘                                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Comunicacion entre Modulos

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ COMPRAS  │  │FACTURAC. │  │INVENTARIO│  ────  Catalogos Compartidos:
└─────┬────┘  └────┬─────┘  └────┬─────┘            Producto (unico)
      │            │             │                  Tercero (unico)
      │   Eventos  │   Eventos   │   Eventos
      │   de       │   de        │   de
      │   Negocio  │   Negocio   │   Negocio
      ▼            ▼             ▼
┌─────────────────────────────────────────────────┐
│               BUS DE EVENTOS INTERNO             │
│                                                  │
│  Suscriben:                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ MOTOR    │ │ WORKFLOW │ │ RULE     │        │
│  │ CONTABLE │ │ ENGINE   │ │ ENGINE   │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────┘
      │            │             │
      ▼            ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│  CxC     │  │   CxP    │  │ BANCOS   │
│  (Cobros)│  │  (Pagos) │  │(Concil.) │
└──────────┘  └──────────┘  └──────────┘
```

---

## 3. Administracion General

### 3.1 Componentes

```
ADMINISTRACION GENERAL
│
├── Seguridad
│   ├── Usuarios (login, JWT, 2FA)
│   ├── Roles (RBAC)
│   ├── Permisos (Modulo × Accion × Alcance)
│   ├── SoD (Segregation of Duties)
│   └── Auditoria de accesos
│
├── Estructura
│   ├── Empresas (multiempresa)
│   ├── Sucursales (por empresa)
│   ├── Bodegas (por sucursal)
│   ├── Departamentos
│   └── Unidades de Medida
│
├── Financiero
│   ├── Monedas
│   ├── Tipos de Cambio
│   ├── Centros de Costo
│   ├── Periodos Contables
│   └── Ejercicios Fiscales
│
├── Catalogos Base
│   ├── Terceros (unico: cliente/proveedor/empleado)
│   ├── Productos (unico: compartido modulos)
│   ├── Condiciones de Pago
│   └── Denominaciones (efectivo)
│
├── Configuracion General
│   ├── Parametros del Sistema
│   ├── Preferencias por Empresa
│   └── Feature Flags
│
├── Numeraciones
│   ├── Series por Empresa/Sucursal
│   ├── Mascaras configurables
│   ├── Reinicio (NUNCA, ANUAL, MENSUAL)
│   └── Reserva de numeros
│
├── Monitoreo
│   ├── Bitacora de Procesos
│   ├── Auditoria de Cambios
│   └── Logs del Sistema
│
└── Workflows y Reglas
    ├── Workflow Designer
    └── Rule Engine (condiciones + acciones)
```

### 3.2 Modelo de Permisos

```
Permiso = { Modulo, Accion, Alcance }

Modulos:   admin, contabilidad, bancos, cxc, cxp, compras,
           facturacion, inventario, activos_fijos, nomina,
           presupuestos

Acciones:  crear, leer, actualizar, eliminar, aprobar,
           contabilizar, anular, revertir, exportar, imprimir,
           configurar

Alcance:   ALL (todo el sistema), COMPANY (su empresa),
           BRANCH (su sucursal), OWN (solo sus registros)

Ejemplo:
  "facturacion.contabilizar" + alcance "COMPANY"
  → Usuario puede contabilizar facturas de su empresa
```

### 3.3 Tabla Unificada de Terceros

```sql
-- TERCERO UNICO: reemplaza cliente, proveedor y empleado separados
CREATE TABLE tercero (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(20) NOT NULL,
    tipo_documento VARCHAR(10) NOT NULL,  -- 'RUC', 'CEDULA', 'PASAPORTE'
    numero_documento VARCHAR(30) NOT NULL,
    nombre_legal VARCHAR(300) NOT NULL,
    nombre_comercial VARCHAR(300),
    direccion TEXT,
    telefono VARCHAR(50),
    email VARCHAR(200),
    ciudad VARCHAR(100),
    pais_id UUID REFERENCES localization_country(id),

    -- Roles del tercero (puede tener multiples)
    es_cliente BOOLEAN DEFAULT FALSE,
    es_proveedor BOOLEAN DEFAULT FALSE,
    es_empleado BOOLEAN DEFAULT FALSE,

    -- Datos de cliente (si es_cliente)
    limite_credito DECIMAL(14,2),
    condicion_pago_id UUID REFERENCES condicion_pago(id),
    lista_precio VARCHAR(20) DEFAULT 'GENERAL',
    cobrador_id UUID,
    dias_gracia INT DEFAULT 0,

    -- Datos de proveedor (si es_proveedor)
    tipo_proveedor VARCHAR(20) DEFAULT 'NACIONAL', -- NACIONAL, EXTRANJERO
    aplica_iva BOOLEAN DEFAULT TRUE,
    tasa_iva DECIMAL(5,2) DEFAULT 15.00,
    plazo_entrega INT DEFAULT 0,

    -- Datos de empleado (si es_empleado)
    fecha_nacimiento DATE,
    fecha_ingreso DATE,
    salario_base DECIMAL(14,2),
    tipo_contrato VARCHAR(50),
    departamento_id UUID,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(company_id, codigo),
    UNIQUE(company_id, tipo_documento, numero_documento)
);
```

---

## 4. Motor Contable (Centro del ERP)

### 4.1 Arquitectura del Flujo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVENTO DE NEGOCIO                                   │
│                                                                             │
│  {                                                                          │
│    "event_type": "FACTURA_EMITIDA",                                         │
│    "module": "facturacion",                                                  │
│    "document_type": "FAC",                                                   │
│    "document_id": "uuid",                                                    │
│    "number": "A-000123",                                                     │
│    "date": "2026-07-01",                                                     │
│    "company_id": "uuid",                                                     │
│    "currency_id": "uuid",                                                    │
│    "exchange_rate": 1.0,                                                     │
│    "amounts": { "subtotal": 1000, "iva": 150, "total": 1150 },             │
│    "parties": { "tercero_id": "uuid", "tercero_nombre": "..." },           │
│    "dimensions": { "cost_center_id": "uuid" },                               │
│    "lines": [ { "product_id": "uuid", "qty": 2, "price": 500 } ],          │
│    "metadata": { "origin": "POS-01", "user_id": "uuid" }                   │
│  }                                                                          │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ACCOUNTING ENGINE (SERVICIO CENTRAL)                   │
│                                                                             │
│  1. Buscar en accounting_event por event_type + module                     │
│     └── Si no existe → error: evento no configurado                        │
│                                                                             │
│  2. Validar periodo contable abierto                                        │
│  3. Validar idempotencia (documento no duplicado)                          │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PLANTILLA CONTABLE (TEMPLATE ENGINE)                    │
│                                                                             │
│  1. Resolver journal_type segun configuracion del evento                   │
│  2. Cargar plantilla activa para el journal_type                           │
│  3. Evaluar expresiones de cada linea:                                     │
│     - Resolver cuenta (FIXED, PARAM, CONTEXT, RULE)                        │
│     - Evaluar monto (ExpressionEvaluator)                                  │
│     - Evaluar descripcion                                                   │
│     - Resolver dimensiones                                                  │
│  4. Generar lineas Debe/Haber                                               │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VALIDACION                                              │
│                                                                             │
│  1. Validar partida doble: SUM(debe) = SUM(haber)                         │
│  2. Validar cuentas existentes y activas                                   │
│  3. Validar periodo abierto                                                │
│  4. Aplicar reglas de negocio (Rule Engine)                                │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      GENERACION DE ASIENTO (JOURNAL ENGINE)                 │
│                                                                             │
│  1. Asignar numero de asiento (NumeracionEngine)                           │
│  2. Crear asiento + lineas en BD                                           │
│  3. Actualizar saldos de cuentas                                           │
│  4. Registrar en bitacora                                                   │
│  5. Publicar evento ASIENTO_CONTABILIZADO                                  │
│  6. Evaluar workflow (transiciones)                                        │
│                                                                             │
│  Retorna: { asiento_id, numero_asiento }                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Eventos Contables a Configurar

| Evento | Modulo | Descripcion |
|--------|--------|-------------|
| COMPRA_REGISTRADA | compras | Compra registrada con entrada a inventario |
| ENTRADA_INVENTARIO | inventario | Entrada por compra, ajuste positivo |
| FACTURA_EMITIDA | facturacion | Factura de venta emitida |
| SALIDA_INVENTARIO | inventario | Salida por factura, consumo, ajuste |
| COBRO_RECIBIDO | cxc | Cobro aplicado a factura |
| PAGO_REALIZADO | cxp | Pago aplicado a factura |
| RETENCION_APLICADA | cxp | Retencion aplicada en pago |
| AJUSTE_POSITIVO | inventario | Ajuste positivo de inventario |
| AJUSTE_NEGATIVO | inventario | Ajuste negativo de inventario |
| CONSUMO_PROPIO | inventario | Consumo interno de productos |
| TRASLADO_BODEGA | inventario | Traslado entre bodegas |
| REVERSION_DOCUMENTO | varios | Reversion de cualquier documento |
| DEPRECIACION_CONTABILIZADA | activos_fijos | Depreciacion del periodo |
| NOMINA_CONTABILIZADA | nomina | Nomina procesada |
| CIERRE_PERIODO | contabilidad | Cierre contable del periodo |

---

## 5. Catalogos Compartidos

### 5.1 Producto Unico

```sql
-- Catalogo unico de productos
-- Usado por: Compras, Facturacion, Inventario
CREATE TABLE producto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(300) NOT NULL,
    descripcion TEXT,
    categoria_id UUID REFERENCES categoria(id),
    unidad_medida_id UUID REFERENCES unidad_medida(id),

    -- Control de inventario
    tipo_producto VARCHAR(50) DEFAULT 'INVENTARIABLE'
        CHECK (tipo_producto IN ('INVENTARIABLE', 'SERVICIO', 'CONSUMO', 'ACTIVO')),
    metodo_costeo VARCHAR(20) DEFAULT 'PROMEDIO'
        CHECK (metodo_costeo IN ('PROMEDIO', 'FIFO', 'LIFO')),
    stock_minimo DECIMAL(14,4) DEFAULT 0,
    stock_maximo DECIMAL(14,4),
   允许_existencias_negativas BOOLEAN DEFAULT FALSE,

    -- Precios
    precio_compra DECIMAL(14,4),
    precio_venta DECIMAL(14,4),
    tasa_iva DECIMAL(5,2) DEFAULT 15.00,
    exento BOOLEAN DEFAULT FALSE,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(company_id, codigo)
);
```

### 5.2 Comportamiento por Modulo

| Operacion | Modulo | Efecto en Inventario |
|-----------|--------|---------------------|
| Crear/Editar producto | Administracion General | Define catalogo |
| Orden de Compra | Compras | No afecta (solo cuando se recibe) |
| Recepcion OC | Compras | Entrada fisica + contable |
| Factura de Venta | Facturacion | Salida fisica + contable |
| Ajuste Positivo | Inventario | Entrada |
| Ajuste Negativo | Inventario | Salida |
| Traslado | Inventario | Salida bodega A → Entrada bodega B |
| Consumo Propio | Inventario | Salida (gasto) |
| Conteo Fisico | Inventario | Ajuste automatico por diferencia |

---

## 6. Flujo de Inventario

### 6.1 Entrada de Inventario por Compra

```
Usuario                        Sistema
  │                              │
  ├─ Registra Orden de Compra ──▶│
  │                              ├─ Estado: BORRADOR
  │                              │
  ├─ Aprueba Orden de Compra ──▶│
  │                              ├─ Estado: APROBADA
  │                              │
  ├─ Recibe Mercancia ─────────▶│
  │                              ├─ Crear Entrada de Inventario
  │                              │  ┌──────────────────────┐
  │                              │  │ Inventario    Debe   │
  │                              │  │ IVA Credito   Debe   │
  │                              │  │ CxP           Haber  │
  │                              │  └──────────────────────┘
  │                              ├─ Publicar: ENTRADA_INVENTARIO
  │                              ├─ Actualizar Kardex
  │                              ├─ Estado: COMPLETADA
  │                              │
  ├─ Recibe Factura Proveedor ──▶│
  │                              ├─ Coincidir con Entrada
  │                              ├─ Validar montos
  │                              └─ Estado: FACTURADA
```

### 6.2 Salida de Inventario por Facturacion

```
Usuario                        Sistema
  │                              │
  ├─ Emite Factura de Venta ───▶│
  │                              ├─ Validar existencias (si aplica)
  │                              ├─ Calcular costo (segun metodo)
  │                              ├─ Crear Salida de Inventario
  │                              │  ┌─────────────────────────┐
  │                              │  │ Costo de Ventas   Debe │
  │                              │  │ Inventario        Haber│
  │                              │  └─────────────────────────┘
  │                              ├─ Publicar: SALIDA_INVENTARIO
  │                              ├─ Actualizar Kardex
  │                              ├─ Publicar: FACTURA_EMITIDA
  │                              └─ Estado: CONTABILIZADA
```

### 6.3 Salida por Consumo Propio

```
┌───────────────────────────────────────┐
│ CONSUMO PROPIO                        │
├───────────────────────────────────────┤
│ Inventario (Salida)                   │
│   ┌──────────────────────────────┐   │
│   │ Gasto/Consumo Interno  Debe │   │
│   │ Inventario             Haber│   │
│   └──────────────────────────────┘   │
│                                       │
│ Cuenta configurable por parametro:    │
│   accounting_parameter_value          │
│   ├── module: inventory               │
│   ├── code: CONSUMO_PROPIO_CUENTA    │
│   └── value_account_id: 5-1-01-001   │
└───────────────────────────────────────┘
```

### 6.4 Reglas Criticas de Inventario

```
REGLA                    DESCRIPCION
─────────────────────────────────────────────────────────────
1. Existencias Negativas  No permitir (salvo config explicita
                          producto.allow_existencias_negativas)

2. Costeo                Segun metodo configurado por producto:
                          PROMEDIO, FIFO, LIFO

3. Traslados              NO afectan resultados
                          Solo cambian ubicacion

4. Ajustes                Cuentas configurables por parametro:
                           AJUSTE_POSITIVO_CUENTA
                           AJUSTE_NEGATIVO_CUENTA

5. Anulaciones            Revertir movimientos inventario
                           Y asientos contables asociados

6. Kardex Inmutable       Una vez registrado, NO se modifica
                           Solo asientos de reversión

7. Costo en Factura       Usar costo vigente al momento de la
                           salida, no el precio de venta
─────────────────────────────────────────────────────────────
```

---

## 7. Flujo de Compras

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE COMPRAS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐                                                      │
│  │ REQUISIC │──▶ Aprueba ──▶ ┌──────────┐                         │
│  │ ION      │                │   OC     │──▶ Aprueba OC           │
│  └──────────┘                └────┬─────┘                         │
│                                   │                                │
│                                   ▼                                │
│                          ┌────────────────┐                       │
│                          │ RECEPCION       │──▶ Entrada Inventario │
│                          │ DE MERCANCIA    │    ┌──────────────┐   │
│                          └────────┬───────┘    │ Invent Debe  │   │
│                                   │             │ IVA Debe     │   │
│                                   ▼             │ CxP Haber    │   │
│                          ┌────────────────┐    └──────────────┘   │
│                          │ FACTURA        │──▶ Coincidir con      │
│                          │ PROVEEDOR      │     Recepcion         │
│                          └────────┬───────┘                      │
│                                   │                               │
│                                   ▼                               │
│                          ┌────────────────┐                       │
│                          │ CxP            │──▶ Pago + Retenciones │
│                          │ GESTION PAGO   │                       │
│                          └────────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Flujo de Facturacion

```
┌─────────────────────────────────────────────────────────────────────┐
│                       FLUJO DE FACTURACION                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐                                                      │
│  │ COTIZAC  │──▶ Aprueba ──▶ ┌──────────┐                        │
│  │ ION      │                │ FACTURA  │──▶ Emitir               │
│  └──────────┘                └────┬─────┘                        │
│                                   │                                │
│                                   ▼                                │
│                          ┌────────────────┐                       │
│                          │ SALIDA         │──▶ Costo de Ventas    │
│                          │ INVENTARIO     │    ┌──────────────┐   │
│                          └────────┬───────┘    │ CV Debe      │   │
│                                   │             │ Invent Haber │   │
│                                   ▼             └──────────────┘   │
│                          ┌────────────────┐                       │
│                          │ MOTOR          │──▶ Asiento Contable   │
│                          │ CONTABLE       │    ┌──────────────┐   │
│                          └────────┬───────┘    │ CxC Debe     │   │
│                                   │             │ Ventas Haber │   │
│                                   ▼             │ IVA Haber    │   │
│                          ┌────────────────┐    └──────────────┘   │
│                          │ CxC            │──▶ Gestion de Cobro   │
│                          │ CARTERA        │                       │
│                          └────────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Flujo de Cuentas por Pagar y Retenciones

### 9.1 Flujo de Pagos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE CXP + RETENCIONES                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Factura Proveedor (desde Compras)                                  │
│         │                                                           │
│         ▼                                                           │
│  ┌────────────────┐                                                 │
│  │ CxP: FACTURA   │──▶ Vencimiento programado                      │
│  │ REGISTRADA     │                                                 │
│  └────────┬───────┘                                                 │
│           │                                                         │
│           ▼                                                         │
│  ┌────────────────┐                                                 │
│  │ SELECCIONAR    │──▶ Elegir facturas a pagar                     │
│  │ DOCUMENTOS     │──▶ Calcular monto total                        │
│  └────────┬───────┘                                                 │
│           │                                                         │
│           ▼                                                         │
│  ┌────────────────┐                                                 │
│  │ APLICAR        │──▶ Si aplica: seleccionar tipo retencion       │
│  │ RETENCION      │    ┌──────────────────────────────────────┐   │
│  │                │    │ RET-IR-2   (IR 2%)                   │   │
│  │                │    │ RET-IVA-100 (IVA 100%)                │   │
│  │                │    │ RET-ITF-025 (ITF 0.25%)               │   │
│  │                │    └──────────────────────────────────────┘   │
│  └────────┬───────┘                                                 │
│           │                                                         │
│           ▼                                                         │
│  ┌────────────────┐                                                 │
│  │ REGISTRAR      │──▶ Asiento contable:                           │
│  │ PAGO           │    ┌──────────────────────────────┐           │
│  │                │    │ CxP                    Debe  │           │
│  │                │    │ Retencion por Pagar    Haber │           │
│  │                │    │ Banco                   Haber │           │
│  │                │    └──────────────────────────────┘           │
│  └────────────────┘                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Tabla de Retenciones

```sql
-- Retenciones configurables (gestionadas desde CxP)
CREATE TABLE retencion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(20) NOT NULL,          -- 'RET-IR-2', 'RET-IVA-100'
    nombre VARCHAR(200) NOT NULL,         -- 'Retencion IR 2%'
    descripcion TEXT,
    tipo VARCHAR(20) NOT NULL             -- 'IR', 'IVA', 'ITF', 'OTRO'
        CHECK (tipo IN ('IR', 'IVA', 'ITF', 'OTRO')),
    porcentaje DECIMAL(5,2) NOT NULL,     -- 2.00, 100.00, 0.25
    aplica_a VARCHAR(20) DEFAULT 'NACIONAL'
        CHECK (aplica_a IN ('NACIONAL', 'EXTRANJERO', 'AMBOS')),
    monto_minimo DECIMAL(14,2),           -- Monto minimo para aplicar
    cuenta_retencion_id UUID REFERENCES account(id),
         -- Cuenta contable: "Retencion por Pagar"
    vigencia_desde DATE NOT NULL,
    vigencia_hasta DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, codigo, vigencia_desde)
);
```

### 9.3 Asiento de Retencion

```
Al aplicar retencion en un pago:

  ┌────────────────────────────────┐
  │  Cuentas Por Pagar      Debe  │  (Total factura - retencion)
  │  Retencion por Pagar    Haber │  (Monto retenido)
  │  Banco                  Haber │  (Neto pagado)
  └────────────────────────────────┘

  La cuenta "Retencion por Pagar" se obtiene de:
    retencion.cuenta_retencion_id

  La cuenta "Cuentas Por Pagar" se obtiene de:
    accounting_parameter_value
    ├── module: cxp
    ├── code: CXP_PROVEEDORES
    └── value_account_id: 2-1-01-001

  La cuenta "Banco" se obtiene de:
    cuenta_banco.cuenta_contable_id
```

---

## 10. Flujo de Generacion de Asientos

### 10.1 Flujo Obligatorio

```
TODO asiento debe seguir este flujo. Ningun modulo puede
insertar asientos directamente en la base de datos.

┌─────────────────────────────────────────────────────────────────────┐
│                   FLUJO OBLIGATORIO DE ASIENTOS                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. DOCUMENTO                                                       │
│     Cualquier modulo crea/modifica un documento                    │
│     Ej: Factura emitida, Compra registrada                         │
│         │                                                           │
│         ▼                                                           │
│  2. ACCOUNTING ENGINE                                               │
│     Servicio central que recibe el evento                          │
│     Valida: periodo, idempotencia, reglas                          │
│         │                                                           │
│         ▼                                                           │
│  3. PLANTILLA CONTABLE                                              │
│     TemplateEngine resuelve lineas Debe/Haber                      │
│     Cuentas desde parametros, no hardcodeadas                      │
│     Montos desde ExpressionEvaluator                               │
│         │                                                           │
│         ▼                                                           │
│  4. VALIDACION                                                     │
│     Partida doble: SUM(Debe) = SUM(Haber)                         │
│     Cuentas activas, periodo abierto                               │
│     Reglas de negocio (Rule Engine)                                │
│         │                                                           │
│         ▼                                                           │
│  5. GENERACION DE ASIENTO                                          │
│     JournalEngine escribe en BD                                    │
│     Numeracion por periodo                                          │
│     Actualiza saldos                                                │
│     Publica evento ASIENTO_CONTABILIZADO                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

IMPORTANTE:
  - Nadie llama a INSERT INTO asiento directamente
  - Nadie llama a INSERT INTO asiento_linea directamente
  - Todo pasa por AccountingEngine.generate_entry(event)
```

### 10.2 Ejemplo: Factura de Venta

```
Evento: FACTURA_EMITIDA
Monto: C$ 11,500 (subtotal 10,000 + IVA 1,500)

Plantilla: FACTURA_VENTA_CONTADO
Lineas:
  #  Naturaleza  Cuenta                     Monto     Fuente
  ───────────────────────────────────────────────────────────
  1  Debe        CxC Clientes               11,500    PARAM(cxc.CXC_CLIENTES)
  2  Haber       Ventas                     10,000    PARAM(sales.VENTAS_CONTADO)
  3  Haber       IVA Debito                 1,500     PARAM(sales.IVA_DEBITO)

  #  Dimension   Valor                      Fuente
  ───────────────────────────────────────────────────────────
  1  Centro Costo  {del documento}          FROM_TRANSACTION

Validacion:
  Debe:  11,500
  Haber: 10,000 + 1,500 = 11,500
  → OK
```

### 10.3 Ejemplo: Compra con Retencion

```
Evento: COMPRA_REGISTRADA
Monto: C$ 115,000 (subtotal 100,000 + IVA 15,000)
Retencion: IR 2% (C$ 2,000)

Plantilla: COMPRA_NACIONAL_CREDITO
Lineas:
  #  Naturaleza  Cuenta                     Monto     Fuente
  ───────────────────────────────────────────────────────────
  1  Debe        Compras Nacionales         100,000   PARAM(purchasing.COMPRAS_NAC)
  2  Debe        IVA Credito Fiscal         15,000    PARAM(purchasing.IVA_CREDITO)
  3  Haber       CxP Proveedores            113,000   PARAM(cxp.CXP_PROVEEDORES)
                                                      (Total - Retencion)

  Nota: La retencion se aplica en el pago, no en la compra.
  En el pago:
  1  Debe        CxP Proveedores            113,000
  2  Haber       Retencion IR por Pagar     2,000     retencion.cuenta_retencion_id
  3  Haber       Banco                      111,000   cuenta_banco.cuenta_contable_id
```

---

## 11. Tablas Nuevas y Modificadas

### 11.1 Resumen

| Tabla | Estado | Modulo |
|-------|--------|--------|
| empresa | Existente | Admin General |
| sucursal | **Nueva** | Admin General |
| tercero | **Nueva** (reemplaza cliente, proveedor, empleado) | Admin General |
| usuario | Existente | Admin General |
| rol | Existente | Admin General |
| permiso | **Extender** (module_id, action_type, scope) | Admin General |
| sod_restriction | **Nueva** | Admin General |
| sod_conflict | **Nueva** | Admin General |
| pais | **Nueva** | Admin General |
| moneda | Existente | Admin General |
| tipo_cambio | Existente | Admin General |
| condicion_pago | Existente | Admin General |
| periodo_contable | Existente | Admin General |
| ejercicio_fiscal | **Nueva** | Admin General |
| numeracion | **Extender** (mask, reinicio, reserva) | Admin General |
| numeracion_reserva | **Nueva** | Admin General |
| parametro | Existente | Admin General |
| bodega | **Nueva** | Admin General |
| unidad_medida | **Nueva** | Admin General |
| departamento | **Nueva** | Admin General |
| centro_costo | Existente | Admin General |
| auditoria | Existente | Admin General |
| bitacora_proceso | **Nueva** | Admin General |
| feature_flag | **Nueva** | Admin General |

| producto | **Refactor** (unico, compartido) | Inventario |
| categoria | Existente | Inventario |
| kardex_movimiento | **Nueva** (inmutable) | Inventario |
| inventario_fisico | **Nueva** (conteo) | Inventario |
| traslado_bodega | **Nueva** | Inventario |

| account (antes cuenta_contable) | **Renovar** | Contabilidad General |
| account_type | **Nueva** | Contabilidad General |
| company_account_structure | **Nueva** | Contabilidad General |
| financial_classification | **Nueva** | Contabilidad General |
| tax_classification | **Nueva** | Contabilidad General |
| ifrs_classification | **Nueva** | Contabilidad General |
| accounting_dimension | **Nueva** | Contabilidad General |
| accounting_dimension_value | **Nueva** | Contabilidad General |
| asiento | Existente | Contabilidad General |
| asiento_linea | Existente | Contabilidad General |

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

| wf_workflow | **Nueva** | Motor Workflow |
| wf_status | **Nueva** | Motor Workflow |
| wf_transition | **Nueva** | Motor Workflow |
| wf_document_history | **Nueva** | Motor Workflow |
| wf_pending_approval | **Nueva** | Motor Workflow |

| cuenta_banco | Existente | Bancos |
| movimiento_banco | Existente | Bancos |
| conciliacion_bancaria | **Nueva** | Bancos |
| conciliacion_detalle | **Nueva** | Bancos |
| chequera | **Nueva** | Bancos |
| caja_apertura | **Nueva** | Bancos |
| caja_chica | **Nueva** | Bancos |

| retencion | **Nueva** | CxP |
| cxc_documento | **Nueva** (unifica factura, recibo, etc) | CxC |
| cxp_documento | **Nueva** (unifica factura, pago, etc) | CxP |
| cxc_aplicacion | **Nueva** (aplicacion cobros) | CxC |
| cxp_aplicacion | **Nueva** (aplicacion pagos) | CxP |

| orden_compra | **Refactor** (usar tercero unico) | Compras |
| recepcion_compra | **Nueva** | Compras |

| factura_venta | **Refactor** (usar tercero unico, producto unico) | Facturacion |
| nota_credito | **Nueva** | Facturacion |
| nota_debito | **Nueva** | Facturacion |

| activo_fijo | Existente | Activos Fijos |
| depreciacion_periodo | **Nueva** | Activos Fijos |
| revaluacion_activo | **Nueva** | Activos Fijos |

| empleado | **Migrar** a tercero (es_cliente=true) | Nomina |
| nomina_periodo | Existente | Nomina |
| nomina_detalle | Existente | Nomina |
| nomina_provision | **Nueva** | Nomina |

| presupuesto_cabecera | **Nueva** | Presupuestos |
| presupuesto_detalle | **Nueva** | Presupuestos |
| presupuesto_ejecucion | **Nueva** | Presupuestos |

### 11.2 Tablas del Motor Contable

```sql
-- accounting_event: define que eventos de negocio generan contabilizacion
CREATE TABLE accounting_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    code VARCHAR(50) NOT NULL,        -- 'COMPRA_REGISTRADA', 'FACTURA_EMITIDA'
    name VARCHAR(200) NOT NULL,
    module VARCHAR(50) NOT NULL,      -- 'compras', 'facturacion', etc.

    -- Resolucion de journal_type
    journal_type_resolution VARCHAR(20) NOT NULL DEFAULT 'DIRECT'
        CHECK (journal_type_resolution IN ('DIRECT', 'SUBTYPE', 'RULE', 'PARAM')),
    journal_type_id UUID REFERENCES journal_type(id),

    -- Control
    requires_approval BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, code)
);

-- journal_type: tipos de asiento contable
CREATE TABLE journal_type (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    code VARCHAR(20) NOT NULL,         -- 'VENTA_CONT', 'COMPRA_NAC', 'COBRO'
    name VARCHAR(100) NOT NULL,
    module VARCHAR(50),
    nature VARCHAR(20) NOT NULL
        CHECK (nature IN ('AUTOMATIC', 'MANUAL', 'RECURRING')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, code)
);

-- journal_template: plantillas de asiento
CREATE TABLE journal_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_type_id UUID NOT NULL REFERENCES journal_type(id),
    company_id UUID NOT NULL REFERENCES empresa(id),
    name VARCHAR(100) NOT NULL,
    priority INT DEFAULT 0,
    condition_expression TEXT,
    is_active BOOLEAN DEFAULT TRUE,
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
        CHECK (account_source IN ('FIXED', 'PARAM', 'CONTEXT', 'RULE')),
    account_param_key VARCHAR(100),

    -- Monto
    amount_expression TEXT NOT NULL,

    -- Descripcion
    description_expression TEXT,

    -- Dimensiones
    cost_center_source VARCHAR(20) DEFAULT 'FROM_TRANSACTION',

    -- Condicion de inclusion
    condition_expression TEXT,

    is_mandatory BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 11.3 Tablas de Retenciones

```sql
CREATE TABLE retencion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(20) NOT NULL
        CHECK (tipo IN ('IR', 'IVA', 'ITF', 'OTRO')),
    porcentaje DECIMAL(5,2) NOT NULL,
    aplica_a VARCHAR(20) DEFAULT 'NACIONAL'
        CHECK (aplica_a IN ('NACIONAL', 'EXTRANJERO', 'AMBOS')),
    monto_minimo DECIMAL(14,2),
    cuenta_retencion_id UUID REFERENCES account(id),
    vigencia_desde DATE NOT NULL,
    vigencia_hasta DATE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(company_id, codigo, vigencia_desde)
);
```

### 11.4 Tablas de Conciliacion Bancaria

```sql
CREATE TABLE conciliacion_bancaria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    cuenta_banco_id UUID NOT NULL REFERENCES cuenta_banco(id),
    periodo_id UUID NOT NULL REFERENCES periodo_contable(id),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    saldo_inicial_banco DECIMAL(14,2) NOT NULL,
    saldo_final_banco DECIMAL(14,2) NOT NULL,
    saldo_inicial_libro DECIMAL(14,2) NOT NULL,
    saldo_final_libro DECIMAL(14,2) NOT NULL,
    diferencia DECIMAL(14,2) DEFAULT 0,
    estado VARCHAR(20) DEFAULT 'BORRADOR'
        CHECK (estado IN ('BORRADOR', 'EN_PROCESO', 'CUADRADA', 'CERRADA')),
    creada_por UUID NOT NULL REFERENCES usuario(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conciliacion_detalle (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conciliacion_id UUID NOT NULL REFERENCES conciliacion_bancaria(id),
    movimiento_banco_id UUID REFERENCES movimiento_banco(id),
    tipo VARCHAR(20) NOT NULL
        CHECK (tipo IN ('CONCILIADO', 'NO_CONCILIADO_LIBRO', 'NO_CONCILIADO_BANCO')),
    monto DECIMAL(14,2) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 11.5 Tablas de Kardex (Inmutable)

```sql
CREATE TABLE kardex_movimiento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    producto_id UUID NOT NULL REFERENCES producto(id),
    bodega_id UUID NOT NULL REFERENCES bodega(id),
    tipo_movimiento VARCHAR(50) NOT NULL
        CHECK (tipo_movimiento IN ('ENTRADA_COMPRA', 'SALIDA_FACTURA',
                'AJUSTE_POSITIVO', 'AJUSTE_NEGATIVO', 'TRASLADO_SALIDA',
                'TRASLADO_ENTRADA', 'CONSUMO_PROPIO', 'ENTRADA_INICIAL',
                'REVERSION')),
    documento_tipo VARCHAR(20),
    documento_id UUID,
    cantidad DECIMAL(14,4) NOT NULL,
    costo_unitario DECIMAL(14,4) NOT NULL,
    costo_total DECIMAL(14,4) NOT NULL,
    existencia_antes DECIMAL(14,4) NOT NULL,
    existencia_despues DECIMAL(14,4) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES usuario(id),

    -- Indices para auditoria
    CONSTRAINT kardex_no_modificable UNIQUE (id)
);

CREATE INDEX idx_kardex_producto_bodega
    ON kardex_movimiento(producto_id, bodega_id, created_at);
```

### 11.6 Tablas de Presupuestos

```sql
CREATE TABLE presupuesto_cabecera (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    ejercicio_id UUID NOT NULL REFERENCES ejercicio_fiscal(id),
    centro_costo_id UUID REFERENCES centro_costo(id),
    moneda_id UUID NOT NULL REFERENCES moneda(id),
    tipo VARCHAR(20) DEFAULT 'OPERATIVO'
        CHECK (tipo IN ('OPERATIVO', 'INVERSION', 'FINANCIERO')),
    estado VARCHAR(20) DEFAULT 'BORRADOR'
        CHECK (estado IN ('BORRADOR', 'APROBADO', 'EJECUCION', 'CERRADO')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, codigo)
);

CREATE TABLE presupuesto_detalle (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    presupuesto_id UUID NOT NULL REFERENCES presupuesto_cabecera(id),
    cuenta_id UUID NOT NULL REFERENCES account(id),
    mes_01 DECIMAL(14,2) DEFAULT 0,
    mes_02 DECIMAL(14,2) DEFAULT 0,
    -- ... meses 03-12
    total DECIMAL(14,2) DEFAULT 0,
    UNIQUE(presupuesto_id, cuenta_id)
);

CREATE TABLE presupuesto_ejecucion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    presupuesto_id UUID NOT NULL REFERENCES presupuesto_cabecera(id),
    cuenta_id UUID NOT NULL REFERENCES account(id),
    mes INT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    presupuestado DECIMAL(14,2) DEFAULT 0,
    ejecutado DECIMAL(14,2) DEFAULT 0,
    variacion DECIMAL(14,2) DEFAULT 0,
    porcentaje_ejecucion DECIMAL(5,2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 12. Mejoras Aplicadas

### 12.1 Resumen de Mejoras vs Estado Actual

| Mejora | Estado Anterior | Estado Nuevo |
|--------|----------------|--------------|
| Catalogo unico de terceros | cliente, proveedor, empleado separados | Tabla tercero con roles |
| Codigo unico de producto | Producto solo en inventario | Producto compartido Compras/Facturacion/Inventario |
| Conciliacion bancaria | Modulo independiente (planeado) | Dentro de Bancos |
| Reportes por modulo | Modulo Reportes independiente | Cada modulo tiene sus reportes |
| Configuracion | Esparcida | Centralizada en Admin General |
| Retenciones | No implementadas | Tabla retencion + asientos desde CxP |
| Presupuestos | No implementados | Modulo completo con ejecucion vs real |
| Numeracion | Serie simple | Mascara, reinicio, reserva, multi-sucursal |
| Motor Contable | Cuentas en codigo | Plantillas + parametros + eventos |
| Kardex | No implementado | Tabla inmutable con auditoria |
| Workflow | No implementado | Motor completo con estados/transiciones |
| Rule Engine | No implementado | Motor de reglas configurable |
| Bus de eventos | No existe | Bus interno para desacoplar modulos |
| Permisos | Basicos | Modulo × Accion × Alcance + SoD |
| Auditoria | Basica | Bitacora tecnica + funcional completa |

### 12.2 Beneficios Clave

```
1. PARAMETRIZACION TOTAL
   Contador configura cuentas, reglas y workflows sin programar.

2. CERO ACOPLAMIENTO
   Modulos independientes via Bus de Eventos.
   Motor Contable es el unico que escribe asientos.

3. INTEGRIDAD DE INVENTARIO
   Kardex inmutable, costeo configurable, sin negativos.
   Cada movimiento queda auditado.

4. UNIFICACION DE DATOS MAESTROS
   Un solo tercero, un solo producto.
   Sin duplicidad ni inconsistencia.

5. REPORTES DESCENTRALIZADOS
   Cada modulo dueño de sus reportes.
   Sin dependencia de un modulo central de reportes.

6. ARQUITECTURA PREPARADA
   Multiempresa, multipais, multimoneda desde el diseno.
   Escalable a 20+ anos.
```

---

## 13. Riesgos Identificados

| # | Riesgo | Probabilidad | Impacto | Mitigacion |
|---|--------|-------------|---------|------------|
| 1 | Migracion de datos existentes (cliente, proveedor, empleado a tercero) | Alta | Alto | Script de migracion transaccional con rollback; validacion previa |
| 2 | Refactor de factura_venta para usar producto unico | Media | Alto | Mantener tabla antigua como vista durante migracion |
| 3 | Performance de ExpressionEvaluator con muchas reglas | Baja | Medio | Cache LRU de expresiones compiladas; limite de timeout |
| 4 | Curva de aprendizaje para contadores (plantillas, eventos) | Media | Medio | UI intuitiva con preview de asientos; modo validacion inicial |
| 5 | Desacople por Bus de Eventos sin mensajeria externa (RabbitMQ) | Media | Medio | Implementar con Redis Streams o tabla de eventos en BD; migrar a RabbitMQ en Fase 10 |
| 6 | Catálogo de cuentas vacio al inicio (usuario debe cargar) | Media | Bajo | Incluir importador Excel con preview y validacion |
| 7 | Migracion de 32 cuentas actuales a nuevo catalogo | Media | Alto | Script automatico que crea company_account_structure desde constants.py |
| 8 | Concurrencia en numeracion (mismo numero para dos docs) | Baja | Alto | Lock pesimista por serie en NumeracionEngine |

---

## 14. Roadmap de Implementacion por Fases

### FASE 1 — Fundacion Empresarial (Semanas 1-4)

**Objetivo:** Base del ERP con Admin General + Motor de Numeraciones + RBAC/SoD

**Backend:**
- [ ] Models: empresa, sucursal, bodega, departamento, unidad_medida
- [ ] Models: tercero (unico), moneda, tipo_cambio, condicion_pago
- [ ] Models: periodo_contable, ejercicio_fiscal
- [ ] Models: numeracion extendida (mask, reinicio, reserva)
- [ ] Models: rol, permiso extendido (module_id, action_type, scope), sod_*
- [ ] Models: auditoria, bitacora_proceso, feature_flag
- [ ] CRUDs para todas las tablas nuevas
- [ ] Seeds de modulos, permisos base
- [ ] Servicio de NumeracionEngine
- [ ] Servicio de Autenticacion con JWT + permisos

**Frontend:**
- [ ] Pagina de Admin General (submodulos)
- [ ] CRUD Terceros (unificado)
- [ ] CRUD Productos
- [ ] Pagina de Numeraciones con mascara
- [ ] Pagina de Roles con matriz permisos (Modulo x Accion)
- [ ] Gestion de Empresas/Sucursales

---

### FASE 2 — Motor Contable (Semanas 5-8)

**Objetivo:** Centro del ERP con eventos, plantillas, expresiones

- [ ] Models: accounting_module, accounting_parameter, accounting_parameter_value
- [ ] Models: accounting_event, journal_type, journal_template, journal_template_line
- [ ] Models: account, account_type, company_account_structure
- [ ] Models: accounting_rule, accounting_condition, accounting_variable
- [ ] Implementar ExpressionEvaluator
- [ ] Implementar TemplateEngine
- [ ] Implementar JournalEngine
- [ ] Implementar AccountingEngine (servicio central)
- [ ] Importador de Catalogo de Cuentas (Excel)
- [ ] Migrar constants.py → accounting_parameter_value
- [ ] Feature flag NEW_ACCOUNTING_ENGINE

**Frontend:**
- [ ] Editor de Eventos Contables
- [ ] Editor de Tipos de Asiento
- [ ] Editor de Plantillas con preview
- [ ] Configuracion Contable por Modulo
- [ ] Catalogo de Cuentas en arbol
- [ ] Importador de Catalogo

---

### FASE 3 — Workflow + Rule Engine (Semanas 9-10)

- [ ] Models: wf_workflow, wf_status, wf_transition, wf_document_history, wf_pending_approval
- [ ] Models: accounting_rule (completar), accounting_rule_log
- [ ] Implementar WorkflowEngine
- [ ] Implementar RuleEngine
- [ ] Integrar con AccountingEngine

**Frontend:**
- [ ] Workflow Designer visual (estados, transiciones)
- [ ] Rule Designer (condiciones + acciones)

---

### FASE 4 — Catalogos Compartidos + Inventario (Semanas 11-12)

- [ ] Models: producto (refactor), kardex_movimiento, traslado_bodega
- [ ] Servicio de Costeo (PROMEDIO, FIFO, LIFO)
- [ ] Servicio de Kardex (inmutable)
- [ ] Conteo Fisico
- [ ] Integracion con AccountingEngine (eventos de inventario)

**Frontend:**
- [ ] Kardex por producto/bodega
- [ ] Ajustes de Inventario
- [ ] Traslados
- [ ] Conteo Fisico

---

### FASE 5 — Compras + CxP + Retenciones (Semanas 13-14)

- [ ] Models: orden_compra (refactor), recepcion_compra
- [ ] Models: cxp_documento, cxp_aplicacion, retencion
- [ ] Flujo completo: OC → Recepcion → Factura → Pago → Retencion
- [ ] Integracion con AccountingEngine

**Frontend:**
- [ ] Ordenes de Compra
- [ ] Recepcion de Mercancia
- [ ] CxP Documentos
- [ ] Gestion de Retenciones
- [ ] Aplicacion de Pagos

---

### FASE 6 — Facturacion + CxC (Semanas 15-16)

- [ ] Models: factura_venta (refactor), nota_credito, nota_debito
- [ ] Models: cxc_documento, cxc_aplicacion
- [ ] Flujo completo: Cotizacion → Factura → Cobro
- [ ] Intereses de Mora
- [ ] Antiguedad de Saldos
- [ ] Integracion con AccountingEngine

**Frontend:**
- [ ] Facturacion Electronica
- [ ] Notas Credito/Debito
- [ ] CxC Documentos
- [ ] Aplicacion de Cobros
- [ ] Estados de Cuenta
- [ ] Antiguedad de Saldos

---

### FASE 7 — Bancos + Conciliacion (Semanas 17-18)

- [ ] Models: cuenta_banco (refactor), conciliacion_bancaria, conciliacion_detalle
- [ ] Chequeras, Cheques Emitidos/Recibidos
- [ ] Caja General y Caja Chica
- [ ] Algoritmo de cruce automatico para conciliacion

**Frontend:**
- [ ] Movimientos Bancarios
- [ ] Conciliacion Bancaria
- [ ] Cheques
- [ ] Arqueo de Caja

---

### FASE 8 — Activos Fijos (Semanas 19-20)

- [ ] Models: activo_fijo (refactor), depreciacion_periodo, revaluacion_activo
- [ ] Metodos: LINEA_RECTA, DOBLE_DECLINANTE, SUMA_DIGITOS
- [ ] Bajas, Mejoras, Revaluaciones
- [ ] Integracion con AccountingEngine

---

### FASE 9 — Nomina (Semanas 21-22)

- [ ] Migrar empleado a tercero (es_empleado=true)
- [ ] Models: nomina_periodo, nomina_detalle, nomina_provision
- [ ] Calculo INSS Patronal/Laboral
- [ ] Calculo IR (tabla progresiva)
- [ ] Aguinaldo, Vacaciones, Prestaciones
- [ ] Integracion con AccountingEngine

---

### FASE 10 — Presupuestos + Reportes + Cierre (Semanas 23-24)

- [ ] Models: presupuesto_cabecera, presupuesto_detalle, presupuesto_ejecucion
- [ ] Vistas materializadas para reportes
- [ ] Balanza de Comprobacion con filtros
- [ ] Estados Financieros (Balance, ER, Flujo Efectivo)
- [ ] Libros: Diario, Mayor, Auxiliares
- [ ] Exportacion Excel/PDF
- [ ] Cierres contables

---

## 15. Proximos Pasos

### Inmediatos (luego de aprobacion)

1. **Revisar y aprobar** este documento ARQUITECTURA_FINAL_v3.md
2. **Iniciar Fase 1:**
   - Crear modelos de Admin General (empresa, sucursal, tercero, etc.)
   - Extension de numeracion
   - RBAC con permisos detallados
   - CRUDs base
   - Seeds de modulos
3. **Configurar entorno de desarrollo** si es necesario
4. **Implementar Fase 1 completa** antes de pasar a Fase 2

### Pendientes de Decision

- Usar Redis Streams o tabla de eventos para el Bus de Eventos interno
- Metodo de costeo por defecto para nuevos productos (PROMEDIO recomendado)
- Si la migracion de cliente/proveedor/empleado existente a tercero se hace en Fase 1 o Fase 4

---

*Documento generado por Arquitecto de Software Senior*
*Basado en requerimientos de reingenieria completa del sistema contable*
*Supersede al Plan Maestro v2.0 en la estructura de modulos y alcance*
