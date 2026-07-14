# Frontend — Análisis Técnico

## Stack Tecnológico
- **Framework**: React 18.3.1 (functional components + hooks)
- **Routing**: React Router DOM 6.26.0
- **Bundler**: Vite 5.4.2
- **Lenguaje**: TypeScript 5.5.4 (modo estricto)
- **Estilos**: TailwindCSS 3.4.7 (utility-first, dark theme)
- **Gráficos**: Recharts 2.12.7
- **Iconos**: Lucide React 0.441.0
- **PWA**: vite-plugin-pwa 0.20.1

## Estructura de Archivos

```
frontend/src/
├── main.tsx                      # Entry point: ReactDOM + BrowserRouter
├── App.tsx                       # Router principal (30 rutas)
├── index.css                     # Tailwind directives + clases utilitarias custom
├── services/
│   └── api.ts                    # Cliente HTTP (~80 métodos)
├── hooks/
│   └── useApi.ts                 # Hook genérico para data fetching
├── pages/                        # 30 páginas (una por ruta)
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── CatalogoCuentasPage.tsx
│   ├── ClientesPage.tsx
│   ├── ProveedoresPage.tsx
│   ├── FacturacionPage.tsx
│   ├── ComprasPage.tsx
│   ├── BancosPage.tsx
│   ├── ConciliacionPage.tsx
│   ├── ActivosFijosPage.tsx
│   ├── InventarioPage.tsx
│   ├── NominaPage.tsx
│   ├── EmpleadosPage.tsx
│   ├── PresupuestosPage.tsx
│   ├── RolesPage.tsx
│   ├── UsuariosPage.tsx
│   ├── EmpresasPage.tsx
│   ├── CierrePage.tsx
│   ├── CategoriasPage.tsx
│   ├── PeriodosPage.tsx
│   ├── ConfiguracionPage.tsx
│   ├── TiposAsientoPage.tsx
│   ├── PlantillasPage.tsx
│   ├── BalanceGeneralPage.tsx
│   ├── EstadoResultadosPage.tsx
│   ├── FlujoEfectivoPage.tsx
│   ├── AntiguedadCxCPage.tsx
│   ├── AntiguedadCxPPage.tsx
│   ├── OCRPage.tsx
│   └── IAPage.tsx
├── components/
│   ├── Sidebar.tsx                # Navegación principal (menú agrupado)
│   ├── MobileNav.tsx              # Navegación móvil
│   ├── DataTable.tsx              # Tabla genérica con columnas
│   ├── KPICard.tsx                # Tarjeta de KPI
│   ├── ChartCard.tsx              # Wrapper para gráficos
│   └── PeriodFilter.tsx           # Selector de período
├── features/                      # CARPETAS VACÍAS (7 directorios sin archivos)
│   ├── accounting/
│   ├── auth/
│   ├── inventory/
│   ├── purchases/
│   ├── reports/
│   ├── sales/
│   └── treasury/
├── stores/                        # VACÍO
├── api/                           # VACÍO
├── lib/                           # VACÍO
├── types/
│   └── lucide-react.d.ts          # Type declarations para iconos
└── lucide-react.d.ts
```

## Routing

30 rutas registradas en `App.tsx`:
- 1 pública: `/login`
- 29 protegidas dentro de `ProtectedLayout`

Protección de rutas: `ProtectedLayout` verifica `localStorage.getItem('token')`. Si no existe, redirige a `/login`.

## Patrón de Páginas

Cada página sigue la misma estructura:

```tsx
export default function PageName() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => { load() }, [])

  async function load() {
    // api.getX().then().catch().finally()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      {/* Search */}
      {/* Form modal (conditional) */}
      {/* Loading ? Skeleton : Empty ? EmptyState : Data */}
    </div>
  )
}
```

## Estados de UI (3 estados)

1. **Loading**: Skeleton con `animate-pulse`
2. **Empty**: Mensaje "Sin datos disponibles" con icono
3. **Data**: Tabla o grid o árbol

Los componentes Skeleton y Empty están duplicados inline en cada página (no extraídos a componentes compartidos).

## Llamadas API

- **Cliente único**: `services/api.ts`
- **Método**: `fetch()` nativo (no axios)
- **Autenticación**: Token JWT del `localStorage`
- **Manejo 401**: Redirección automática a `/login`
- **Aprox. 80 métodos**: Desde `login()` hasta `getModulos()`
- **Respuestas**: Tipadas como `any` en su mayoría

## Estado Global
- **No existe**. Cada página maneja su estado con `useState`
- No hay Context, Redux, Zustand, ni stores de estado global
- Las carpetas `stores/` y `api/` están vacías (intencionales o legacy)

## Carpetas Features
Las 7 carpetas en `features/` están **totalmente vacías**. Parecen ser estructura planificada pero no implementada. Todo el código de UI está en `pages/`.

## Componentes Reutilizables

| Componente | Props | Uso |
|-----------|-------|-----|
| `Sidebar` | open, onClose | Menú lateral con grupos colapsables |
| `MobileNav` | onMenuClick | Barra superior en móvil |
| `DataTable` | columns, data, loading | Tabla genérica |
| `KPICard` | title, value, subtitle, icon, trend, color | Tarjetas de métricas |
| `ChartCard` | title, subtitle, children, height, action | Wrapper de gráficos |
| `PeriodFilter` | value, onChange | Selector de período |

## Sistema de Temas
- **Dark theme**: Toda la UI usa fondo `bg-slate-950/900/800`, texto `text-white/slate-400`
- **Sin light theme**: No hay soporte para tema claro
- **Clases utilitarias**: `card`, `card-header`, `kpi-value`, `btn-primary`, `btn-secondary`, `input-filter`

## PWA
- Service Worker con `vite-plugin-pwa`
- Modo `autoUpdate`
- Caché de API con estrategia `NetworkFirst`
- Manifest con iconos SVG
- Orientación portrait-primary

## Observaciones

1. **Sin estado global**: Escalable para pocas páginas, pero insostenible para un ERP completo
2. **Sin tests frontend**: No hay archivos de test en el frontend
3. **TypeScript subutilizado**: Uso extensivo de `any[]`
4. **Features vacías**: Las carpetas features son estructura soñada no implementada
5. **Sin manejo de errores global**: Cada página maneja errores a su manera (algunas silenciosamente)
6. **Sin lazy loading**: Todas las páginas se importan estáticamente en App.tsx
7. **CategoriasPage usa fetch directo**: Única página que no usa el objeto `api`
