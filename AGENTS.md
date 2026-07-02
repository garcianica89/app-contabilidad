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

## Correcciones Frontend (Build Fixes)
- Agregado `src/lucide-react.d.ts` - declaraciones de tipos para todos los iconos usados (lucide-react v0.441.0 no incluye .d.ts)
- `src/services/api.ts` - agregados ~80 metodos faltantes para todos los modulos (activos fijos, cuentas contables, tipos asiento, plantillas, conciliacion, parametros, monedas, tipos de cambio, condiciones pago, impuestos, empleados, nomina, OCR, IA, presupuestos, roles/permisos, ordenes compra, facturas compra, numeraciones, categorias)
- Corregidas firmas de `getAnalisisIA(tipo?)` y `getEmpleados(params?)` para aceptar filtros opcionales

## Alembic Migrations
- Migraciones existentes en `backend/alembic/versions/` (0001-0012)
- DB actualmente en version `0012`
- Para aplicar migraciones pendientes: `cd backend && PYTHONPATH=. alembic upgrade head`
- Nota: Usar `op.execute('CREATE ... IF NOT EXISTS')` para idempotencia en PostgreSQL
- **Schema diff pendiente**: `asiento.numero` es `integer` en DB pero `String(30)` en modelo

## Session Actual (Jul 2026)
**Ultima sesion**: Reingeniería arquitectónica mayor completada:
- Fix: `AccountingEngine._get_periodo_abierto()` ahora usa `PeriodoContable.cerrado == False` (antes consultaba columna inexistente `.abierto`)
- Fix: `DocumentoSubtipo` consolidado con journal_type_id, journal_template_id, cuenta_mora/puente/retencion_iva/retencion_ir — CxcDocumentSubtype/CxpDocumentSubtype deprecados
- Creado: `InventarioService` con soporte ENTRADA/SALIDA/AJUSTE/TRASLADO/CONSUMO + costo promedio
- Fix: `DocumentEngine._update_cxc/_update_cxp` implementados (antes eran `pass`)
- Fix: `TemplateEngine` ahora acepta `DocumentoSubtipo` como subtipo general + soporta `invert_in_banking` para inversión bancaria (Débito doc = Crédito asiento)
- Nuevos modelos: `CierreMensual` (control cierre periodos + reapertura), `CierreFiscal` (cierre anual + resultado ejercicio + asiento apertura)
- Migración `0014` creada: tablas cierre_mensual, cierre_fiscal + columnas subtipo + invert_in_banking
**Pendiente**: Aplicar migración 0014, migrar CxC/CxP endpoints a Document Engine pipeline, agregar integración contable a Nomina/Activos Fijos, verificar backend arranque

## Notas Importantes
- Los modelos SQLAlchemy usan `Uuid()` (compatible PostgreSQL/SQLite)
- El frontend tiene PWA configurado con `vite-plugin-pwa`
- El build del frontend se copia a `backend/static/` para produccion
- Todos los clientes (desktop, mobile, web) usan la misma API cloud
