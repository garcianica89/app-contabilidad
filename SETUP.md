# Guia de Instalacion - App Contabilidad BI

## Requisitos

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Docker (opcional)

## 1. Base de Datos

### Opcion A: Con Docker (recomendado)

```bash
docker compose up -d db
```

### Opcion B: Manual

Crear base de datos en PostgreSQL:

```bash
createdb contabilidad
psql -d contabilidad -f database/01-schema.sql
```

## 2. Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar DATABASE_URL en .env

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor iniciara con datos semilla automaticamente:
- **Empresa:** Tuckler Beauty
- **Usuario master:** `rgarcia` / `exrgarcia`
- **Periodos:** Ene, Feb, Mar 2026
- **Catalogo de cuentas:** Contabilidad completa
- **Productos:** Sandalias, Zapatos, Ropa, Accesorios
- **Caja General:** C$6,290.00

## 3. Frontend (React + PWA)

```bash
cd frontend
npm install
npm run dev
```

## 4. Acceder

| Aplicacion | URL |
|---|---|
| Frontend BI | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| API Redoc | http://localhost:8000/redoc |

## 5. Instalar en Celular (PWA)

1. Abrir `http://localhost:5173` en Chrome/Edge en el celular
2. Ir al menu del navegador (3 puntos)
3. Seleccionar "Instalar aplicacion" / "Add to Home Screen"
4. La app se abrira como aplicacion nativa sin la barra del navegador

## 6. Estructura del Proyecto

```
backend/
  app/
    api/v1/endpoints/  # Endpoints REST
    core/              # Config, DB, Security
    domain/models/     # SQLAlchemy ORM
    domain/schemas/    # Pydantic schemas
    service/           # Logica de negocio
  alembic/             # Migraciones
  database/            # SQL DDL

frontend/
  src/
    components/        # Componentes reutilizables
    pages/             # Paginas del dashboard
    services/         # API client
    hooks/            # Custom hooks
```

## 7. Modulos Implementados

- [x] Autenticacion (JWT)
- [x] Empresas (multi-compania)
- [x] Usuarios + Roles + Permisos
- [x] Cuentas Contables (ISO 8583)
- [x] Asientos (partida doble)
- [x] Productos + Kardex (costo promedio)
- [x] Clientes + CxC (facturacion, antiguedad)
- [x] Proveedores + CxP (facturacion, antiguedad)
- [x] Caja (movimientos, arqueo)
- [ ] Bancos (cuentas, conciliacion)
- [ ] Reportes: Balance, ER, Flujo Efectivo
- [x] BI Dashboard (KPIs, graficos, PWA)
```
