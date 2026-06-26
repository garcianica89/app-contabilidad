# App Contabilidad — Documento Técnico de Arquitectura y Análisis

> Versión: 1.0
> Fecha: 2026-06-25
> Estado: Borrador para validación

---

## Índice

1. [Análisis del Archivo Excel](#1-análisis-del-archivo-excel)
2. [Diseño de Arquitectura del Sistema](#2-diseño-de-arquitectura-del-sistema)
3. [Diseño de Base de Datos](#3-diseño-de-base-de-datos)
4. [Roadmap del Proyecto](#4-roadmap-del-proyecto)
5. [Estrategia de Migración](#5-estrategia-de-migración)
6. [Riesgos Técnicos](#6-riesgos-técnicos)
7. [Recomendaciones](#7-recomendaciones)

---

# 1. Análisis del Archivo Excel

## 1.1 Identificación del Negocio

**Negocio:** Tuckler beauty  
**Tipo:** Comercio minorista de calzado y ropa  
**Ubicación:** Nicaragua (moneda funcional: Córdobas C$, con operaciones en USD)  
**Estructura:** Sociedad entre Sheyla (50%) y Ramón (50%)  
**Estado actual:** Operación manual completamente en Excel

### Otras fuentes de datos encontradas

Se identificaron archivos adicionales que reflejan el uso previo de **Softland ERP** en otro negocio (Ritter Sport Nicaragua — RSN, finca cacaotera). Esto indica que el usuario conoce el funcionamiento de un ERP profesional y busca replicar esa experiencia para Tuckler beauty.

Archivos relacionados:
- `Info Cacao Matagalpa 2025.xlsx` — Exportación de Mayor General desde Softland
- `RSN_Cargador_Movimientos_CP.xlsx` — Cargador de Cuentas por Pagar
- `Cargador Softland.xlsx` — Asientos de diario desde Softland
- Múltiples archivos en `RITTER/` — CxP, CxC, Nómina, Activos Fijos, Conciliación

## 1.2 Hojas del Archivo Principal (Tuckler beauty.xlsx)

| Hoja | Filas | Columnas | Propósito |
|------|-------|----------|-----------|
| **EEFF** | 19 | 10 | Balance General (Estado de Situación Financiera) |
| **Efectivo** | 12 | 9 | Flujo de efectivo (entradas, salidas, saldo) |
| **CXC** | 10 | 6 | Cuentas por Cobrar (actualmente vacío) |
| **Ingresos** | 11 | 6 | Registro de ventas/ingresos |
| **Kardex** | 26 | 16 | Control de inventario (entradas, salidas, costeo promedio) |
| **Hoja1** | 29 | 21 | Planificación de importaciones y pricing |
| **ER** | 9 | 4 | Estado de Resultados |

## 1.3 Datos Maestros Identificados

### Productos (desde Kardex + Hoja1)
| Producto | Tipo | Categoría |
|----------|------|-----------|
| Sandalias | Calzado | Inventario |
| Zapatos Negros Talla 39 | Calzado | Inventario |
| Zapatos Rosados Talla 36 | Calzado | Inventario |
| Zapatos B y N Talla 38 | Calzado | Inventario |
| Zapatos NB Talla 38 | Calzado | Inventario |
| Leggings Wide Leg | Ropa | Importación/Tránsito |
| Legging Short | Ropa | Importación/Tránsito |
| Falda Shorts | Ropa | Importación/Tránsito |
| Camisa de Ziper | Ropa | Importación/Tránsito |
| Conjunto Dyfane | Ropa | Importación/Tránsito |
| Licra Larga Corte V | Ropa | Importación/Tránsito |

### Clientes (desde Ingresos)
- Varios (ventas al por menor)
- Andrea
- Sheyla

### Proveedores
- No explicitados en el Excel principal (se infieren de Hoja1 como proveedores internacionales)

### Socios/Accionistas
- Sheyla (50% participación)
- Ramón (50% participación)

## 1.4 Documentos que Maneja

| Documento | Hoja | Descripción |
|-----------|------|-------------|
| Aporte de Capital | Efectivo, Kardex | Registro de capital inicial y adicional |
| Compra (Lote) | Efectivo, Kardex | Compra de inventario a proveedores |
| Venta | Ingresos, Kardex | Venta a clientes |
| Nota de Ingreso | Kardex | Entrada de productos a inventario |
| Nota de Salida | Kardex | Salida de productos de inventario |
| Liquidación | Hoja1 | Liquidación de importaciones |

## 1.5 Relaciones entre Hojas

```
EEFF (Balance General)
├── B4 (Efectivo) ← Efectivo!E12 (Saldo final de caja)
├── B5 (Inventario) ← Kardex!L18 (Valor total inventario)
├── B6 (CxC) ← CXC!E10 - CXC!F10 (Saldo neto CxC)
├── E8 (Capital) ← Efectivo!C5 + Efectivo!C8 (Aportes)
└── E9 (Utilidad) ← ER!B9 (Utilidad neta)

ER (Estado de Resultados)
├── B5 (Ingresos) ← Ingresos!F11 (Total ingresos)
└── B6 (Costo Ventas) ← Kardex!I18 (Total costo de ventas)

Efectivo
├── D6 (Compra Lote 1) ← Kardex!F4 (Costo total sandalias)
└── D9 (Compra Lote 2) ← Kardex!F10 (Costo total zapatos)

Ingresos
├── A5 (Fecha venta 1) ← CXC!A5
├── C5 (Descripción) ← Kardex!C11
└── C6 (Descripción) ← Kardex!C12
```

## 1.6 Cálculos y Fórmulas

### Kardex (Costeo Promedio Ponderado)
```
Costo Total Entrada = Cantidad × Costo Unitario
Saldo Físico = Saldo Anterior + Entradas - Salidas
Costo Promedio = Costo Total Acumulado / Cantidad Acumulada
Saldo Total = Saldo Anterior + Costo Entradas - Costo Salidas
Costo de Venta = Cantidad Vendida × Costo Promedio
```

### Efectivo
```
Saldo = Saldo Anterior + Entradas - Salidas
Saldo USD = Saldo C$ / Tipo de Cambio (36.6243)
```

### Hoja1 (Pricing)
```
Total Producto = Costo + Flete
Precio Unitario USD = Total Producto / Cantidad
Precio Unitario C$ = Precio USD × TC (37.00)
Precio Sugerido = MROUND(Precio C$ / (1 - 33%), 20)
Margen = 1 - (Precio C$ / Precio Sugerido)
```

### EEFF (Balance)
```
Total Activo Corriente = Efectivo + Inventario + CxC
Total Patrimonio = Capital Social + Utilidad del Ejercicio
Total Activo = Total Pasivo + Total Patrimonio
```

### ER (Resultados)
```
Utilidad Bruta = Ingresos - Costo de Ventas
Utilidad Neta = Utilidad Bruta - Gastos Operativos
```

## 1.7 Reglas de Negocio Implícitas

1. **Costeo Promedio Ponderado:** El inventario se valúa usando costo promedio. Cada entrada recalcula el costo unitario promedio.
2. **Doble Moneda:** Las operaciones se registran en Córdobas (moneda local), pero referencian USD para importaciones.
3. **Margen Mínimo:** El precio de venta sugerido se calcula para obtener un margen mínimo del 33%.
4. **Redondeo:** Los precios sugeridos se redondean a múltiplos de 20 C$.
5. **Partida Doble:** Los registros de Ingresos tienen columnas Débito/Crédito (contabilidad de partida doble rudimentaria).
6. **Capital vs Utilidad:** Diferenciación entre aportes de capital (patrimonio) e ingresos por ventas (resultados).
7. **Ciclo Contable:** El negocio opera con períodos no definidos explícitamente; los saldos se acumulan desde el inicio.
8. **Sin Gastos Operativos:** Actualmente no se registran gastos (la utilidad operativa = utilidad bruta).
9. **Sin Impuestos:** No se maneja IVA, IR, ni retenciones en el registro actual.

## 1.8 Procesos de Negocio a Convertir en Módulos

| Proceso Actual | Módulo Propuesto | Prioridad |
|----------------|-------------------|-----------|
| Kardex (inventario manual) | Inventario | Crítica |
| Efectivo (caja manual) | Caja / Efectivo | Crítica |
| Ingresos (ventas manual) | Ventas | Alta |
| CxC (cuentas por cobrar) | Cuentas por Cobrar | Alta |
| EEFF (balance manual) | Contabilidad General | Alta |
| ER (resultados manual) | Contabilidad General | Alta |
| Hoja1 (importaciones) | Compras / Inventario | Media |
| Pricing y márgenes | Inventario / Productos | Media |

---

# 2. Diseño de Arquitectura del Sistema

## 2.1 Principios Arquitectónicos

- **Clean Architecture** — Separación en capas con dependencias hacia adentro
- **API REST** — Comunicación desacoplada frontend-backend
- **Modular por Dominio** — Cada módulo de negocio es independiente
- **Base de Datos Normalizada** — Hasta 3FN con ajustes controlados por performance
- **Auditoría por Defecto** — Todas las operaciones quedan registradas
- **Multiempresa** — El sistema soporta múltiples empresas desde el inicio
- **Multimoneda** — Soporte nativo para Córdobas y Dólares (extensible)

## 2.2 Stack Tecnológico

### Backend
```
Capa             Tecnología         Propósito
─────────────────────────────────────────────────────
API              FastAPI            Framework REST
ORM              SQLAlchemy 2.x     Mapeo objeto-relacional
Migraciones      Alembic            Control de esquema DB
Validación       Pydantic v2        Validación de datos
Autenticación    JWT (python-jose)  Tokens de acceso
Hash             bcrypt / passlib   Hash de contraseñas
Documentación    OpenAPI / Swagger  Documentación automática
Pruebas          pytest             Tests unitarios e integración
```

### Frontend
```
Capa             Tecnología         Propósito
─────────────────────────────────────────────────────
Framework        React 18+          UI en componentes
Build            Vite               Bundle rápido
Estilos          TailwindCSS        CSS utilitario
Estado           React Context      Estado global simple
              + TanStack Query   Cache y fetching
Formularios      React Hook Form    Manejo de formularios
Tablas           TanStack Table     Tablas de datos
Gráficos         Recharts           Gráficos financieros
Pruebas          Vitest + Testing   Tests de componentes
```

### Base de Datos
```
Motor            PostgreSQL 16+     Base de datos relacional
Capa             pgvector           (futuro: búsqueda semántica)
Herramienta      pgAdmin / DBeaver   Administración
```

### Infraestructura
```
Contenedores     Docker             Entornos reproducibles
Orquestación     docker-compose     Entorno local/desarrollo
Proxy            Nginx / Traefik    Reverse proxy
```

## 2.3 Estructura de Directorios (Backend)

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/         # Endpoints REST por módulo
│   │   │   └── __init__.py
│   │   └── deps.py                # Dependencias (DB, auth)
│   ├── core/
│   │   ├── config.py              # Configuración (pydantic-settings)
│   │   ├── security.py            # JWT, hashing
│   │   └── database.py            # Sesión SQLAlchemy
│   ├── domain/
│   │   ├── models/                # Modelos SQLAlchemy (ORM)
│   │   ├── schemas/               # Schemas Pydantic (request/response)
│   │   └── enums.py               # Enumeraciones del dominio
│   ├── repository/                # Capa de acceso a datos
│   ├── service/                   # Lógica de negocio
│   └── modules/                   # Funcionalidad transversal
│       ├── audit/                 # Trazabilidad de operaciones
│       └── notifications/         # Notificaciones
│   ├── main.py                    # Punto de entrada FastAPI
│   └── seed.py                    # Datos iniciales
├── alembic/
│   ├── versions/                  # Migraciones
│   └── env.py
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 2.4 Estructura de Directorios (Frontend)

```
frontend/
├── src/
│   ├── api/                       # Clientes HTTP (axios)
│   ├── components/                # Componentes reutilizables
│   │   ├── ui/                    # Botones, inputs, tablas
│   │   ├── layout/                # Sidebar, header, layout
│   │   └── forms/                 # Formularios genéricos
│   ├── features/                  # Módulos de negocio
│   │   ├── auth/                  # Login, registro
│   │   ├── accounting/            # Contabilidad
│   │   ├── inventory/             # Inventario
│   │   ├── sales/                 # Ventas
│   │   ├── purchases/             # Compras
│   │   ├── treasury/              # Caja y Bancos
│   │   └── reports/               # Reportes
│   ├── hooks/                     # Custom hooks
│   ├── lib/                       # Utilidades
│   ├── stores/                    # Estado global
│   ├── types/                     # TypeScript interfaces
│   ├── App.tsx
│   └── main.tsx
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## 2.5 Capas de la Arquitectura

```
┌─────────────────────────────────────────────────┐
│                   FRONTEND (React)               │
│  Componentes → Hooks → API Client → HTTP         │
└──────────────────────┬──────────────────────────┘
                       │ API REST (JSON)
                       ▼
┌─────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)              │
│                                                   │
│  ┌──────────────┐   ┌──────────────┐            │
│  │  API Layer   │──▶│  Service     │            │
│  │  (Endpoints) │   │  Layer       │            │
│  └──────────────┘   └──────┬───────┘            │
│                             │                    │
│                    ┌────────▼───────┐            │
│                    │  Repository   │            │
│                    │  Layer        │            │
│                    └────────┬───────┘            │
│                             │                    │
│                    ┌────────▼───────┐            │
│                    │  Database     │            │
│                    │  (SQLAlchemy) │            │
│                    └────────┬───────┘            │
└─────────────────────────────┬────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    └──────────────────┘
```

**Flujo de datos:**
1. El frontend envía requests HTTP JSON al backend
2. La capa API valida el request (Pydantic) y llama al servicio
3. El servicio ejecuta la lógica de negocio y llama al repositorio
4. El repositorio ejecuta operaciones de DB (SQLAlchemy)
5. La respuesta viaja de vuelta: Repositorio → Servicio → API → Frontend

---

# 3. Diseño de Base de Datos

## 3.1 Modelo Entidad-Relación (Nivel Conceptual)

```
empresa 1──N usuario
usuario N──M rol
rol     1──N permiso

empresa 1──N periodo_contable
empresa 1──N moneda
empresa 1──N parametro

empresa 1──N cuenta_contable
cuenta_contable 1──N cuenta_contable (jerarquía padre-hijo)
cuenta_contable 1──N asiento_linea
asiento 1──N asiento_linea

empresa 1──N producto
producto 1──N categoria
categoria 1──N categoria (jerarquía)
producto 1──N kardex_movimiento

cliente 1──N factura_venta
factura_venta 1──N factura_venta_linea
factura_venta 1──N recibo
factura_venta 1──N nota_credito_venta

proveedor 1──N factura_compra
factura_compra 1──N factura_compra_linea
factura_compra 1──N orden_compra
factura_compra 1──N nota_credito_compra

cuenta_banco 1──N movimiento_banco
caja 1──N movimiento_caja

asiento N──N auditoria (polimórfico)
```

## 3.2 Diccionario de Tablas

### 3.2.1 Configuración

#### `empresa`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | Identificador único |
| nombre | VARCHAR(200) | NOT NULL | Nombre comercial |
| nombre_legal | VARCHAR(200) | | Razón social |
| ruc | VARCHAR(20) | UNIQUE | RUC/NIT |
| direccion | TEXT | | Dirección |
| telefono | VARCHAR(20) | | Teléfono |
| email | VARCHAR(100) | | Email |
| moneda_local_id | UUID | FK → moneda.id | Moneda funcional |
| activo | BOOLEAN | DEFAULT true | Está activa |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | | |

#### `usuario`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | |
| empresa_id | UUID | FK → empresa.id | |
| username | VARCHAR(50) | UNIQUE | |
| email | VARCHAR(100) | UNIQUE | |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| nombre_completo | VARCHAR(200) | | |
| activo | BOOLEAN | DEFAULT true | |
| created_at | TIMESTAMP | | |

#### `rol`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| nombre | VARCHAR(50) | NOT NULL |
| descripcion | TEXT | |

#### `usuario_rol`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| usuario_id | UUID | FK → usuario.id |
| rol_id | UUID | FK → rol.id |
| PK | | (usuario_id, rol_id) |

#### `permiso`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| codigo | VARCHAR(100) | UNIQUE |
| nombre | VARCHAR(100) | |
| modulo | VARCHAR(50) | |

#### `rol_permiso`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| rol_id | UUID | FK → rol.id |
| permiso_id | UUID | FK → permiso.id |
| PK | | (rol_id, permiso_id) |

#### `periodo_contable`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | |
| empresa_id | UUID | FK → empresa.id | |
| codigo | VARCHAR(10) | | Ej: "2026-01" |
| fecha_inicio | DATE | NOT NULL | |
| fecha_fin | DATE | NOT NULL | |
| cerrado | BOOLEAN | DEFAULT false | |
| cerrado_por | UUID | FK → usuario.id | |

#### `moneda`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| codigo | VARCHAR(3) | UNIQUE (NIO, USD, EUR) |
| nombre | VARCHAR(50) | |
| simbolo | VARCHAR(5) | "C$", "U$", "€" |
| tasa_cambio | DECIMAL(14,6) | Frente a moneda base |

#### `parametro`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| grupo | VARCHAR(50) | |
| clave | VARCHAR(100) | |
| valor | TEXT | |

### 3.2.2 Contabilidad

#### `cuenta_contable`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | |
| empresa_id | UUID | FK → empresa.id | |
| codigo | VARCHAR(20) | NOT NULL | "1-1-1-1-01-01-01-0001" |
| nombre | VARCHAR(200) | NOT NULL | |
| tipo | ENUM | | ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTO |
| nivel | INTEGER | | 1..8 (jerarquía) |
| padre_id | UUID | FK → cuenta_contable.id | Auto-referencia jerárquica |
| acepta_datos | BOOLEAN | DEFAULT false | ¿Se pueden registrar movimientos? |
| moneda_id | UUID | FK → moneda.id | |
| activa | BOOLEAN | DEFAULT true | |
| indice | VARCHAR(10) | | Índice de clasificación IFRS |

**Índice:** (empresa_id, codigo) UNIQUE, (empresa_id, padre_id)

#### `asiento`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | |
| empresa_id | UUID | FK → empresa.id | |
| numero | INTEGER | | Correlativo por período |
| fecha | DATE | NOT NULL | |
| periodo_id | UUID | FK → periodo_contable.id | |
| tipo | ENUM | | APERTURA, CIERRE, COMPRA, VENTA, CAJA, BANCO, DIARIO |
| concepto | TEXT | NOT NULL | |
| origen | VARCHAR(50) | | Módulo que lo generó |
| origen_id | UUID | | ID del documento origen |
| creado_por | UUID | FK → usuario.id | |
| reversado | BOOLEAN | DEFAULT false | |
| asiento_reversa_id | UUID | FK → asiento.id | |
| created_at | TIMESTAMP | | |

**Índice:** (empresa_id, periodo_id), (empresa_id, fecha)

#### `asiento_linea`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | |
| asiento_id | UUID | FK → asiento.id | |
| cuenta_id | UUID | FK → cuenta_contable.id | |
| centro_costo_id | UUID | FK → centro_costo.id | (opcional) |
| descripcion | TEXT | | |
| debe_local | DECIMAL(14,2) | DEFAULT 0 | |
| haber_local | DECIMAL(14,2) | DEFAULT 0 | |
| debe_dolar | DECIMAL(14,2) | DEFAULT 0 | |
| haber_dolar | DECIMAL(14,2) | DEFAULT 0 | |
| orden | INTEGER | | |

**Índice:** (asiento_id), (cuenta_id, fecha)

#### `centro_costo`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| codigo | VARCHAR(20) | |
| nombre | VARCHAR(200) | |
| padre_id | UUID | FK → centro_costo.id |
| activo | BOOLEAN | |

### 3.2.3 Inventario

#### `categoria`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| nombre | VARCHAR(100) | |
| padre_id | UUID | FK → categoria.id |

#### `producto`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| codigo | VARCHAR(50) | |
| nombre | VARCHAR(200) | NOT NULL |
| descripcion | TEXT | |
| categoria_id | UUID | FK → categoria.id |
| unidad_medida | VARCHAR(20) | "unidad", "kg", "par" |
| costo_promedio | DECIMAL(14,2) | Costo promedio actual |
| precio_venta | DECIMAL(14,2) | Precio de venta sugerido |
| moneda_id | UUID | FK → moneda.id |
| stock_actual | DECIMAL(14,2) | DEFAULT 0 |
| stock_minimo | DECIMAL(14,2) | DEFAULT 0 |
| activo | BOOLEAN | |

#### `kardex_movimiento`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | |
| empresa_id | UUID | FK → empresa.id | |
| producto_id | UUID | FK → producto.id | |
| fecha | DATE | NOT NULL | |
| tipo | ENUM | | ENTRADA, SALIDA, AJUSTE |
| tipo_documento | VARCHAR(20) | | COMPRA, VENTA, AJUSTE, NC, ND |
| documento_id | UUID | | ID del documento origen |
| cantidad | DECIMAL(14,2) | NOT NULL | |
| costo_unitario | DECIMAL(14,2) | | |
| costo_total | DECIMAL(14,2) | | |
| saldo_cantidad | DECIMAL(14,2) | | Saldo después del movimiento |
| saldo_costo_promedio | DECIMAL(14,2) | | |
| saldo_total | DECIMAL(14,2) | | |

**Índice:** (producto_id, fecha), (empresa_id, fecha)

### 3.2.4 Ventas

#### `cliente`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| codigo | VARCHAR(20) | |
| nombre | VARCHAR(200) | NOT NULL |
| ruc | VARCHAR(20) | |
| direccion | TEXT | |
| telefono | VARCHAR(20) | |
| email | VARCHAR(100) | |
| saldo | DECIMAL(14,2) | DEFAULT 0 |
| limite_credito | DECIMAL(14,2) | |
| activo | BOOLEAN | |

#### `factura_venta`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | |
| empresa_id | UUID | FK → empresa.id | |
| numero | VARCHAR(20) | | Factura número |
| cliente_id | UUID | FK → cliente.id | |
| fecha | DATE | NOT NULL | |
| fecha_vencimiento | DATE | | |
| tipo | ENUM | | CONTADO, CREDITO |
| subtotal | DECIMAL(14,2) | | |
| descuento | DECIMAL(14,2) | | |
| iva | DECIMAL(14,2) | | |
| total | DECIMAL(14,2) | | |
| moneda_id | UUID | FK → moneda.id | |
| asiento_id | UUID | FK → asiento.id | |
| estado | ENUM | | EMITIDA, COBRADA, ANULADA |
| created_at | TIMESTAMP | | |

#### `factura_venta_linea`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| factura_id | UUID | FK → factura_venta.id |
| producto_id | UUID | FK → producto.id |
| cantidad | DECIMAL(14,2) | |
| precio_unitario | DECIMAL(14,2) | |
| descuento | DECIMAL(14,2) | |
| subtotal | DECIMAL(14,2) | |

### 3.2.5 Compras

#### `proveedor`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| codigo | VARCHAR(20) | |
| nombre | VARCHAR(200) | |
| ruc | VARCHAR(20) | |
| direccion | TEXT | |
| telefono | VARCHAR(20) | |
| email | VARCHAR(100) | |
| saldo | DECIMAL(14,2) | |
| activo | BOOLEAN | |

#### `factura_compra`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| numero | VARCHAR(20) | |
| proveedor_id | UUID | FK → proveedor.id |
| fecha | DATE | |
| fecha_vencimiento | DATE | |
| subtotal | DECIMAL(14,2) | |
| iva | DECIMAL(14,2) | |
| retencion_ir | DECIMAL(14,2) | |
| total | DECIMAL(14,2) | |
| moneda_id | UUID | FK → moneda.id |
| asiento_id | UUID | FK → asiento.id |
| estado | ENUM | PENDIENTE, PAGADA, ANULADA |

### 3.2.6 Caja y Bancos

#### `cuenta_banco`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| banco | VARCHAR(100) | |
| numero_cuenta | VARCHAR(50) | |
| tipo | ENUM | CORRIENTE, AHORRO |
| moneda_id | UUID | FK → moneda.id |
| saldo | DECIMAL(14,2) | |
| activa | BOOLEAN | |

#### `caja`
| Columna | Tipo | Restricción |
|---------|------|-------------|
| id | UUID | PK |
| empresa_id | UUID | FK → empresa.id |
| nombre | VARCHAR(100) | "Caja General" |
| moneda_id | UUID | FK → moneda.id |
| saldo_actual | DECIMAL(14,2) | |

### 3.2.7 Auditoría

#### `auditoria`
| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| id | UUID | PK | |
| usuario_id | UUID | FK → usuario.id | |
| tabla | VARCHAR(50) | | Tabla afectada |
| registro_id | UUID | | ID del registro |
| accion | ENUM | | CREATE, UPDATE, DELETE |
| valor_anterior | JSONB | | |
| valor_nuevo | JSONB | | |
| direccion_ip | VARCHAR(45) | | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Índice:** (tabla, registro_id), (usuario_id), (created_at)

## 3.3 Restricciones de Integridad

1. **Partida Doble:** Todo asiento debe tener `SUM(debe) = SUM(haber)` (CHECK constraint en lógica de aplicación, no en DB).
2. **Saldo de Inventario:** `kardex_movimiento.saldo_cantidad` debe ser ≥ 0 (no puede haber stock negativo).
3. **Jerarquía de Cuentas:** Una cuenta que `acepta_datos = true` no puede tener hijos.
4. **Períodos Cerrados:** No se permiten asientos en períodos marcados como `cerrado = true`.
5. **Empresa Aislada:** Toda consulta multiempresa debe incluir `empresa_id` en el WHERE.
6. **Cascada:** Al anular un documento (factura, compra), se debe generar un asiento de reversión.
7. **Auditoría Obligatoria:** Toda operación CREATE, UPDATE, DELETE en tablas críticas genera un registro de auditoría.

---

# 4. Roadmap del Proyecto

## Justificación del Orden

El orden sigue el principio de **dependencias mínimas**: cada fase solo depende de las anteriores.

- **Configuración primero:** Sin empresas, usuarios y parámetros, no hay sistema.
- **Contabilidad antes que módulos operativos:** Porque compras, ventas e inventario generan asientos contables. Sin contabilidad, no pueden funcionar.
- **Inventario antes que Compras/Ventas:** Porque ambos módulos necesitan productos.
- **Caja/Bancos después de Ventas/Compras:** Porque los cobros y pagos son consecuencia de facturas.
- **Reportes al final:** Porque necesitan datos de todos los módulos.

## Fase 1: Infraestructura

**Duración estimada:** 1 semana

**Dependencias:** Ninguna

**Entregables:**
- [ ] Docker + docker-compose (PostgreSQL, backend, frontend)
- [ ] Proyecto FastAPI con estructura de capas
- [ ] Proyecto React + Vite + TailwindCSS
- [ ] Configuración de Alembic
- [ ] Script de base de datos inicial
- [ ] CI/CD básico (GitHub Actions)
- [ ] README con instrucciones de desarrollo

## Fase 2: Configuración y Seguridad

**Duración estimada:** 2 semanas

**Dependencias:** Fase 1

**Entregables:**
- [ ] CRUD Empresas
- [ ] CRUD Usuarios
- [ ] CRUD Roles y Permisos
- [ ] Autenticación JWT (login, logout, refresh)
- [ ] Protección de rutas (frontend y backend)
- [ ] CRUD Monedas + Tasas de cambio
- [ ] CRUD Parámetros del sistema
- [ ] CRUD Períodos Contables
- [ ] Auditoría básica

## Fase 3: Catálogo de Cuentas

**Duración estimada:** 2 semanas

**Dependencias:** Fase 2

**Entregables:**
- [ ] CRUD Cuenta Contable (jerárquico)
- [ ] Importación de catálogo desde Excel
- [ ] Validación de estructura jerárquica
- [ ] CRUD Centro de Costo (jerárquico)
- [ ] Visualización en árbol (frontend)

## Fase 4: Contabilidad General

**Duración estimada:** 3 semanas

**Dependencias:** Fase 3

**Entregables:**
- [ ] Registro de asientos manuales
- [ ] Partida doble (debe = haber)
- [ ] Diario General (consulta)
- [ ] Mayor General (consulta)
- [ ] Balance de Comprobación
- [ ] Estado de Resultados
- [ ] Balance General
- [ ] Cierre contable por período
- [ ] Reversión de asientos

## Fase 5: Inventario

**Duración estimada:** 3 semanas

**Dependencias:** Fase 3 (necesita cuentas contables)

**Entregables:**
- [ ] CRUD Categorías de productos
- [ ] CRUD Productos
- [ ] Kardex (entradas, salidas, ajustes)
- [ ] Costeo promedio ponderado
- [ ] Consulta de existencias
- [ ] Generación automática de asientos contables
- [ ] Ajustes de inventario

## Fase 6: Compras

**Duración estimada:** 3 semanas

**Dependencias:** Fases 4 y 5

**Entregables:**
- [ ] CRUD Proveedores
- [ ] Órdenes de compra
- [ ] Recepción de facturas de compra
- [ ] Notas de crédito de compra
- [ ] Retenciones (IR, IVA)
- [ ] Generación automática de asientos
- [ ] Actualización de inventario + costeo
- [ ] Cuentas por Pagar

## Fase 7: Ventas

**Duración estimada:** 3 semanas

**Dependencias:** Fases 4 y 5

**Entregables:**
- [ ] CRUD Clientes
- [ ] Cotizaciones
- [ ] Facturación (contado y crédito)
- [ ] Recibos de cobro
- [ ] Notas de crédito de venta
- [ ] Generación automática de asientos
- [ ] Descuento de inventario
- [ ] Cuentas por Cobrar

## Fase 8: Cuentas por Cobrar y Pagar

**Duración estimada:** 2 semanas

**Dependencias:** Fases 6 y 7

**Entregables:**
- [ ] Estados de cuenta (clientes y proveedores)
- [ ] Anticipos de clientes
- [ ] Anticipos a proveedores
- [ ] Reporte de vencimientos (aged trial balance)
- [ ] Saldos y aplicación de pagos

## Fase 9: Caja y Bancos

**Duración estimada:** 2 semanas

**Dependencias:** Fase 4

**Entregables:**
- [ ] CRUD Cuentas Bancarias
- [ ] Depósitos
- [ ] Cheques emitidos y recibidos
- [ ] Transferencias entre cuentas
- [ ] Caja General (apertura, cierre, arqueos)
- [ ] Conciliación bancaria
- [ ] Generación de asientos

## Fase 10: Reportes

**Duración estimada:** 3 semanas

**Dependencias:** Todas las fases anteriores

**Entregables:**
- [ ] Estados financieros (Balance General, ER, Flujo de Efectivo)
- [ ] Libros contables (Diario, Mayor)
- [ ] Reportes de Ventas (por cliente, por producto, por período)
- [ ] Reportes de Compras (por proveedor, por producto)
- [ ] Reportes de Inventario (kardex, existencias, rotación)
- [ ] Exportación a Excel (openpyxl)
- [ ] Exportación a PDF (ReportLab / WeasyPrint)

## Fase 11: Mejoras y Optimización

**Duración estimada:** 2 semanas

**Dependencias:** Todas las fases anteriores

**Entregables:**
- [ ] Respaldo y restauración de base de datos
- [ ] Dashboard con KPIs
- [ ] Notificaciones por email
- [ ] Mejoras de performance (índices, consultas)
- [ ] Pruebas de carga
- [ ] Documentación de usuario

---

# 5. Estrategia de Migración

## 5.1 Análisis de Datos a Migrar

### Datos del Excel → Tablas del Sistema

| Hoja Excel | Tabla Destino | Acción | Observaciones |
|------------|---------------|--------|---------------|
| EEFF (estructura) | cuenta_contable | Crear catálogo | Derivar cuentas de la estructura del balance |
| Kardex (productos) | producto | Migrar | Sandalias, Zapatos y sus variantes |
| Kardex (movimientos) | kardex_movimiento | Migrar | Cada fila es un movimiento |
| Efectivo | movimiento_caja | Migrar | Cada movimiento de efectivo |
| Ingresos | factura_venta | Migrar | Cada fila es una venta |
| CXC | factura_venta (saldos) | Migrar | Si hubiera saldos pendientes |
| Hoja1 (productos) | producto | Migrar | Productos en tránsito/importación |
| ER | (generado por sistema) | No migrar | Se calcula automáticamente |
| EEFF (saldos) | asiento (apertura) | Migrar | Saldos iniciales como asiento de apertura |

## 5.2 Proceso de Importación

### Paso 1: Preparación
1. Crear la empresa "Tuckler beauty" en el sistema
2. Configurar moneda local (C$) y tipo de cambio inicial
3. Crear período contable inicial
4. Cargar catálogo de cuentas (ver sección 5.3)

### Paso 2: Validación de Datos
Antes de importar, validar:
- [ ] ¿Los productos tienen nombre y costo unitario? → Sí
- [ ] ¿Las fechas son consistentes? → Parcialmente (algunas filas sin fecha)
- [ ] ¿Los montos cuadran (debe = haber en ingresos)? → Sí
- [ ] ¿Hay duplicados? → Verificar
- [ ] ¿Existen clientes sin nombre? → "Varios" necesita un registro genérico

### Paso 3: Creación de Maestros
1. Crear cliente "Varios" (cliente genérico para ventas al por menor)
2. Crear cliente "Andrea"
3. Crear cliente "Sheyla" (cuando compra como clienta)
4. Crear categorías: "Calzado", "Ropa"
5. Crear productos con su costo promedio inicial

### Paso 4: Migración de Inventario Inicial
1. Crear asiento de apertura:
   - Débito: Inventario (C$ 1,606)
   - Débito: Efectivo (C$ 6,290)
   - Crédito: Capital Social (C$ 5,340)
   - Crédito: Utilidad del Ejercicio (C$ 2,556)

2. Registrar movimientos de Kardex (cada venta/compra)
3. Registrar movimientos de Efectivo (cada entrada/salida)

### Paso 5: Migración de Transacciones
1. Registrar cada venta del Kardex como factura de contado
2. Registrar cada compra como factura de compra
3. Generar asientos automáticos desde cada documento

## 5.3 Catálogo de Cuentas Propuesto

Basado en la estructura del Balance General actual:

```
1-0-0-0-00-00-00-0000  ACTIVOS
1-1-0-0-00-00-00-0000    ACTIVOS CORRIENTES
1-1-1-0-00-00-00-0000      EFECTIVO Y EQUIVALENTES
1-1-1-1-01-00-00-0000        Efectivo (Caja)
1-1-2-0-00-00-00-0000      CUENTAS POR COBRAR
1-1-2-1-01-00-00-0000        Clientes
1-1-3-0-00-00-00-0000      INVENTARIOS
1-1-3-1-01-00-00-0000        Inventario de Mercadería

2-0-0-0-00-00-00-0000  PASIVOS
2-1-0-0-00-00-00-0000    PASIVOS CORRIENTES
2-1-1-0-00-00-00-0000      CUENTAS POR PAGAR
2-1-1-1-01-00-00-0000        Proveedores

3-0-0-0-00-00-00-0000  PATRIMONIO
3-1-0-0-00-00-00-0000    CAPITAL
3-1-1-1-01-00-00-0000      Capital Social
3-2-0-0-00-00-00-0000    RESULTADOS
3-2-1-1-01-00-00-0000      Utilidad del Ejercicio

4-0-0-0-00-00-00-0000  INGRESOS
4-1-0-0-00-00-00-0000    INGRESOS OPERATIVOS
4-1-1-1-01-00-00-0000      Ventas de Mercadería

5-0-0-0-00-00-00-0000  COSTOS
5-1-0-0-00-00-00-0000    COSTO DE VENTAS
5-1-1-1-01-00-00-0000      Costo de Ventas

6-0-0-0-00-00-00-0000  GASTOS
6-1-0-0-00-00-00-0000    GASTOS OPERATIVOS
6-1-1-1-01-00-00-0000      Gastos de Venta
6-1-2-1-01-00-00-0000      Gastos Administrativos
```

## 5.4 Datos que Faltan (No están en el Excel)

1. **RUC/NIT de la empresa** — No registrado
2. **RUC/NIT de clientes** — Solo nombres
3. **Direcciones completas** — No registradas
4. **Desglose de gastos** — Actualmente C$0 (se registran como gasto personal de los socios)
5. **Impuestos** — No se registra IVA (posiblemente exento o no registrado)
6. **Número de factura (legal)** — Las ventas se registran sin factura fiscal
7. **Proveedores con nombre completo** — Solo "Lote 1" y "Lote 2"
8. **Términos de pago** — No especificados
9. **Banco y número de cuenta** — No registrados
10. **Categoría fiscal de productos** — No clasificados

## 5.5 Tablas a Poblar en la Migración

| Orden | Tabla | Registros | Fuente |
|-------|-------|-----------|--------|
| 1 | empresa | 1 | Creación manual |
| 2 | moneda | 2 (C$, U$) | Creación manual |
| 3 | cuenta_contable | ~20 | Catálogo propuesto |
| 4 | periodo_contable | 1 | Período inicial |
| 5 | categoria | 2 | "Calzado", "Ropa" |
| 6 | producto | ~12 | Kardex + Hoja1 |
| 7 | cliente | 4 | "Varios", Andrea, Sheyla + 1 genérico |
| 8 | asiento | 1 | Asiento de apertura |
| 9 | asiento_linea | 4 | Líneas del asiento de apertura |
| 10 | factura_venta | ~7 | Ingresos |
| 11 | factura_venta_linea | ~7 | Ídem |
| 12 | movimiento_caja | ~8 | Efectivo |
| 13 | kardex_movimiento | ~10 | Kardex |

---

# 6. Riesgos Técnicos

## 6.1 Riesgos Identificados

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| **Falta de datos fiscales** | Alto | Alta | El sistema debe funcionar con datos mínimos; la facturación legal puede agregarse después |
| **Curva de aprendizaje** | Medio | Alta | Capacitación progresiva por módulos; interfaz intuitiva |
| **Migración de datos incompleta** | Alto | Media | Validación exhaustiva pre-migración; permitir corrección manual post-migración |
| **Deuda técnica por velocidad** | Medio | Media | Seguir estrictamente Clean Architecture; no sacrificar diseño por rapidez |
| **Cambio de requisitos** | Medio | Alta | Arquitectura modular permite cambios localizados |
| **Pérdida de datos** | Alto | Baja | PostgreSQL + respaldos automáticos; pruebas de restauración |
| **Rendimiento en consultas grandes** | Bajo | Baja (negocio pequeño) | Índices adecuados; proyección simple de crecimiento |
| **Seguridad (accesos no autorizados)** | Alto | Baja | JWT + RBAC desde el inicio; auditoría obligatoria |

---

# 7. Recomendaciones

## 7.1 Técnicas

1. **Usar UUID como PK** — Escalabilidad, merge de datos, seguridad (no expone secuencias).
2. **ISO 8583 para estructura de cuentas** — El formato `X-X-X-X-XX-XX-XX-XXXX` permite 8 niveles de jerarquía, compatible con IFRS/NIIF.
3. **API Versionada** — `/api/v1/...` desde el inicio para permitir evolución sin breaking changes.
4. **Pruebas desde el día 1** — Cada módulo debe tener tests unitarios y de integración antes de darse por terminado.
5. **Docker para desarrollo** — Entorno reproducible para todos los desarrolladores.
6. **Git Flow** — Ramas `main`, `develop`, `feature/*`, `hotfix/*`.
7. **Logging estructurado** — Usar `structlog` o `loguru` en backend para trazabilidad.

## 7.2 Funcionales

1. **Comenzar con lo esencial** — Fases 1-4 (Infraestructura, Configuración, Catálogo, Contabilidad) son el corazón del sistema. No avanzar a módulos operativos hasta que la contabilidad esté sólida.
2. **Validar con el usuario cada fase** — Al terminar cada fase, el usuario debe probar y aprobar antes de continuar.
3. **Migrar datos manualmente al inicio** — La primera migración debe ser supervisada. Después, construir el importador automático.
4. **No subestimar la contabilidad** — La partida doble, el cierre contable y la estructura de cuentas son la base de todo el ERP. Invertir tiempo en validar que funcione correctamente.
5. **Planificar la facturación fiscal** — Aunque ahora no se emiten facturas fiscales, el diseño debe contemplarlo para el futuro (DGI, impuestos).
6. **Documentar mientras se desarrolla** — Cada API endpoint debe documentarse (FastAPI lo hace automático con OpenAPI).

## 7.3 De Desarrollo

1. **Commits atómicos** — Un commit por funcionalidad, con mensaje descriptivo en español.
2. **Code Review obligatorio** — No mergear a `main` sin revisión.
3. **Mantener AGENTS.md** — Registrar comandos de lint, test, build para facilitar el trabajo con asistentes de IA.
4. **Usar type hints en Python** — SQLAlchemy 2.x con `mapped_column` y tipos modernos.
5. **TypeScript estricto en frontend** — `strict: true` en tsconfig.

---

## Apéndice A: Referencia del Análisis del Excel

### A.1 Datos del Balance General (EEFF)

| Concepto | C$ Córdobas |
|----------|-------------|
| Efectivo (Caja) | 6,290.00 |
| Inventario | 1,606.00 |
| Cuentas por Cobrar | 0.00 |
| **Total Activo Corriente** | **7,896.00** |
| Capital Social | 5,340.00 |
| Utilidad del Ejercicio | 2,556.00 |
| **Total Pasivo + Patrimonio** | **7,896.00** |

### A.2 Datos del Estado de Resultados (ER)

| Concepto | C$ Córdobas |
|----------|-------------|
| Ingresos por Ventas | 9,520.00 |
| Costo de Ventas | (6,964.00) |
| **Utilidad Bruta** | **2,556.00** |
| Gastos Operativos | 0.00 |
| **Utilidad Neta** | **2,556.00** |

### A.3 Resumen de Movimientos de Efectivo

| Movimiento | Entrada | Salida | Saldo |
|-----------|---------|--------|-------|
| Capital Inicial | 3,240 | 0 | 3,240 |
| Compra Lote 1 (Sandalias) | 0 | 3,240 | 0 |
| Ingresos por Ventas | 4,020 | 0 | 4,020 |
| Capitalización Adicional | 2,100 | 0 | 6,120 |
| Compra Lote 2 (Zapatos) | 0 | 5,330 | 790 |
| Venta Zapatos Negros | 1,400 | 0 | 2,190 |
| Venta Zapatos Negros | 1,500 | 0 | 3,690 |
| Venta Zapatos Negros | 2,600 | 0 | 6,290 |

### A.4 Costo de Ventas por Producto

| Producto | Costo Total |
|----------|-------------|
| Sandalias (4+1 vendidas) | 2,700 |
| Zapatos Negros Talla 39 | 1,066 |
| Zapatos Rosados Talla 36 | 1,066 |
| Zapatos B y N Talla 38 | 1,066 |
| Zapatos NB Talla 38 | 1,066 |
| **Total Costo de Ventas** | **6,964** |

---

> **Fin del documento.**
>
> Próximo paso: Validar este análisis y diseño antes de comenzar la implementación.
> Una vez aprobado, iniciaremos con la **Fase 1: Infraestructura**.
