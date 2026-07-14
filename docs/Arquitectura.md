# Arquitectura General

## Visión General

Aplicación ERP contable full-stack con 3 clientes (web, mobile PWA, desktop Electron) que consumen una única API REST cloud. Sigue una arquitectura de 3 capas (API → Servicios → Base de Datos) con un motor de contabilización centralizado.

```
┌─────────────────────┐     ┌──────────────────┐
│  Desktop (Electron) │     │  Mobile (PWA)    │
│  React + Electron   │     │  React + Vite    │
└──────────┬──────────┘     └────────┬─────────┘
           │                         │
           └──────────┬──────────────┘
                      │ HTTP/JSON
              ┌───────▼────────┐
              │  FastAPI (cloud)│
              │  Railway/Fly   │
              └───────┬────────┘
                      │ asyncpg
              ┌───────▼────────┐
              │  PostgreSQL    │
              │  (Neon.tech)   │
              └────────────────┘
```

## Estructura de Directorios

```
/
├── backend/           # API FastAPI (Python)
│   ├── app/
│   │   ├── api/       # Capa de presentación (endpoints REST)
│   │   ├── core/      # Configuración, seguridad, base de datos
│   │   ├── domain/    # Modelos SQLAlchemy, esquemas Pydantic
│   │   ├── service/   # Lógica de negocio
│   │   ├── repository/# Acceso a datos (patrón repositorio)
│   │   ├── modules/   # Módulos independientes (vacío)
│   │   └── seeds/     # Datos semilla
│   ├── alembic/       # Migraciones de base de datos
│   └── tests/         # Tests unitarios y de integración
├── frontend/          # SPA React + Vite + TailwindCSS
│   └── src/
│       ├── pages/     # 30 páginas (una por ruta)
│       ├── components/# Componentes compartidos
│       ├── services/  # Cliente API centralizado
│       └── hooks/     # Custom hooks
├── electron/          # Wrapper de escritorio
├── database/          # Scripts SQL auxiliares
└── docs/              # Documentación técnica
```

## Capas del Backend

### 1. API Layer (`backend/app/api/`)
- **v1/endpoints/**: 51 archivos, uno por recurso/módulo
- **v1/__init__.py**: Registro central de routers con prefijos y tags
- **deps.py**: Dependencias de FastAPI (autenticación, autorización)
- Patrón: Endpoints → Servicios (o SQL directo) → Modelos

### 2. Service Layer (`backend/app/service/`)
- **asiento_service.py**: CRUD de asientos contables
- **cxc_service.py / cxp_service.py**: Facturación, cobros, pagos, antigüedad
- **reporte_service.py**: Estados financieros y reportes
- **activo_fijo_service.py / inventario_service.py**: Módulos específicos
- **auditoria_service.py / config_service.py**: Transversales
- **numeracion_service.py**: Correlativos automáticos
- **document_engine/engine.py**: Pipeline central de procesamiento
- **accounting/accounting_engine.py**: Motor de contabilización
- **accounting/template_engine.py**: Plantillas de asientos
- **accounting/expression_evaluator.py**: Evaluador de expresiones
- **rule_engine.py**: Motor de reglas de negocio
- **workflow_engine.py**: Motor de workflows
- **erp/**: Motores clonados de ERP heredado (accounting_engine, cost_engine)

### 3. Domain Layer (`backend/app/domain/`)
- **models/**: 42 modelos SQLAlchemy (entidades de base de datos)
- **schemas/__init__.py**: Esquemas Pydantic para validación de entrada/salida
- **accounting/models.py**: Modelos del core contable (14 modelos adicionales)
- **erp/**: 11 archivos de modelos clonados de ERP heredado (32 tablas)

### 4. Core Layer (`backend/app/core/`)
- **config.py**: Settings vía Pydantic + .env
- **database.py**: Engine asíncrono, session factory, Base declarativa
- **security.py**: JWT, bcrypt, hash/verify
- **logging_config.py**: Logger JSON estructurado

## Capas del Frontend

### 1. Entry Point
- **main.tsx**: Mount React con BrowserRouter
- **App.tsx**: 30 rutas con layout protegido y público

### 2. Pages (30 componentes)
- Una página por ruta, cada una con su propio estado local
- Patrón: `useState + useEffect + api.method()`

### 3. Components (6 compartidos)
- **Sidebar.tsx**: Navegación principal (agrupada por módulo)
- **MobileNav.tsx**: Barra de navegación móvil
- **DataTable.tsx**, **KPICard.tsx**, **ChartCard.tsx**: Widgets reutilizables
- **PeriodFilter.tsx**: Selector de período contable

### 4. API Layer
- **services/api.ts**: ~80 métodos que envuelven fetch()
- Manejo automático de token JWT y redirección 401

### 5. State Management
- Sin estado global (no Redux/Zustand/Context)
- Estado local en cada página via hooks

## Patrón de Diseño

No existe una arquitectura DDD o Clean Architecture estricta. La organización es por carpetas funcionales:

- **No hay inyección de dependencias**: Los servicios se instancian manualmente en los endpoints (`svc = AsientoService(db, user.id, empresa_id)`)
- **No hay repositorios genéricos**: Solo existe un repositorio real (`repository/accounting/repositories.py`) usado por el TemplateEngine
- **Los servicios no tienen interfaces/abstract**: Todo es implementación concreta
- **Mezcla de estilos**: Algunos endpoints usan servicios, otros hacen SQL directo

## Convenciones

- **Backend**: FastAPI async, SQLAlchemy 2.x `Mapped` annotations, Pydantic v2
- **Frontend**: React funcional con hooks, TailwindCSS utility-first
- **BD**: UUID como PKs, snake_case en nombres de tablas y columnas
- **API**: Prefijo `/api/v1/`, respuestas JSON, auth via Bearer JWT
