# App Contabilidad - Guia para Agentes AI

## Stack
- **Backend**: FastAPI + SQLAlchemy 2.x + asyncpg (PostgreSQL en Neon.tech)
- **Frontend**: React 18 + Vite + TailwindCSS + Recharts + PWA
- **Desktop**: Electron (wrapper alrededor del frontend web)
- **Database**: PostgreSQL 16+ (Neon.tech cloud)

## Comandos

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Build Frontend + Copiar a Backend
```bash
cd frontend && npm run build
rm -rf ../backend/static && cp -r dist ../backend/static
```

### Desktop (Electron)
```bash
cd electron
npm install
npm run dev  # Desarrollo (conecta a localhost:5173)
npm run build:win  # Empaquetar para Windows
```

### Base de Datos
- **URL actual**: `postgresql+asyncpg://neondb_owner:npg_3cY0yoMxnfah@ep-red-lab-atfxoamb-pooler.c-9.us-east-1.aws.neon.tech/neondb`
- **Host**: Neon.tech (serverless PostgreSQL)
- **Credenciales en**: `backend/.env`

### Docker (produccion en la nube)
```bash
docker compose up backend -d  # Solo backend (usa Neon.tech)
```

## Arquitectura

```
┌─────────────────────────┐     ┌──────────────────┐
│   Desktop (Electron)    │     │   Mobile (PWA)   │
│   Windows App           │     │   Android/iOS    │
└──────────┬──────────────┘     └────────┬─────────┘
           │                             │
           └──────────┬──────────────────┘
                      │ HTTP/JSON
              ┌───────▼────────┐
              │  FastAPI (cloud)│
              │  Railway/Fly   │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │  PostgreSQL    │
              │  (Neon.tech)   │
              └────────────────┘
```

## Usuarios Seed
- **Usuario**: `rgarcia` / `exrgarcia` (admin)
- **Empresa**: Tuckler Beauty (Nicaragua, C$)

## Endpoints Principales
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/bi/dashboard` - Dashboard KPIs
- `GET /api/v1/reportes/*` - Reportes financieros
- `POST /api/v1/asientos` - Crear asientos contables
- `POST /api/v1/cuentas-por-cobrar/facturas` - Facturas de venta

## Notas Importantes
- Los modelos SQLAlchemy usan `Uuid()` (compatible PostgreSQL/SQLite)
- El frontend tiene PWA configurado con `vite-plugin-pwa`
- El build del frontend se copia a `backend/static/` para produccion
- Todos los clientes (desktop, mobile, web) usan la misma API cloud
