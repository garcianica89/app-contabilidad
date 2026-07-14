import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import Sidebar from './components/Sidebar'
import MobileNav from './components/MobileNav'
import DashboardPage from './pages/DashboardPage'
import BalanceGeneralPage from './pages/BalanceGeneralPage'
import EstadoResultadosPage from './pages/EstadoResultadosPage'
import FlujoEfectivoPage from './pages/FlujoEfectivoPage'
import AntiguedadCxCPage from './pages/AntiguedadCxCPage'
import AntiguedadCxPPage from './pages/AntiguedadCxPPage'
import UsuariosPage from './pages/UsuariosPage'
import ClientesPage from './pages/ClientesPage'
import ProveedoresPage from './pages/ProveedoresPage'
import InventarioPage from './pages/InventarioPage'
import FacturacionPage from './pages/FacturacionPage'
import BancosPage from './pages/BancosPage'
import ChequesPage from './pages/ChequesPage'
import RolesPage from './pages/RolesPage'
import ConfiguracionPage from './pages/ConfiguracionPage'
import CatalogoCuentasPage from './pages/CatalogoCuentasPage'
import TiposAsientoPage from './pages/TiposAsientoPage'
import PlantillasPage from './pages/PlantillasPage'
import PeriodosPage from './pages/PeriodosPage'
import ComprasPage from './pages/ComprasPage'
import ConciliacionPage from './pages/ConciliacionPage'
import ActivosFijosPage from './pages/ActivosFijosPage'
import EmpleadosPage from './pages/EmpleadosPage'
import NominaPage from './pages/NominaPage'
import PresupuestosPage from './pages/PresupuestosPage'
import OCRPage from './pages/OCRPage'
import IAPage from './pages/IAPage'
import EmpresasPage from './pages/EmpresasPage'
import CierrePage from './pages/CierrePage'
import CategoriasPage from './pages/CategoriasPage'
import RetencionesPage from './pages/RetencionesPage'
import SalidasInventarioPage from './pages/SalidasInventarioPage'
import CxPPage from './pages/CxPPage'
import CxCPage from './pages/CxCPage'
import AuditoriaPage from './pages/AuditoriaPage'
import CargadorMovimientosPage from './pages/CargadorMovimientosPage'
import TiposCuentaBancoPage from './pages/TiposCuentaBancoPage'
import BalanzaPage from './pages/BalanzaPage'
import { PermissionProvider } from './contexts/PermissionContext'
import PermisosUsuariosPage from './pages/PermisosUsuariosPage'

// Modulos ERP
import ERPContabilidadPage from './pages/erp/ERPContabilidadPage'
import ERPInventarioPage from './pages/erp/ERPInventarioPage'
import ERPCobrarPage from './pages/erp/ERPCobrarPage'
import ERPTesoreriaPage from './pages/erp/ERPTesoreriaPage'
import ERPActivosFijosPage from './pages/erp/ERPActivosFijosPage'
import ERPFacturacionPage from './pages/erp/ERPFacturacionPage'
import ERPComprasPage from './pages/erp/ERPComprasPage'
import ERPPedidosPage from './pages/erp/ERPPedidosPage'
import ERRRHHPage from './pages/erp/ERRRHHPage'

function ProtectedLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { token, loading } = useAuth()

  if (loading) return null
  if (!token) return <Navigate to="/login" replace />

  return (
    <PermissionProvider>
      <div className="flex h-screen overflow-hidden bg-slate-950">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <MobileNav onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto pt-16 md:pt-0 pb-20 md:pb-0">
          <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </PermissionProvider>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/balance-general" element={<BalanceGeneralPage />} />
        <Route path="/estado-resultados" element={<EstadoResultadosPage />} />
        <Route path="/flujo-efectivo" element={<FlujoEfectivoPage />} />
        <Route path="/antiguedad-cxc" element={<AntiguedadCxCPage />} />
        <Route path="/antiguedad-cxp" element={<AntiguedadCxPPage />} />
        <Route path="/clientes" element={<ClientesPage />} />
        <Route path="/proveedores" element={<ProveedoresPage />} />
        <Route path="/inventario" element={<InventarioPage />} />
        <Route path="/facturacion" element={<FacturacionPage />} />
        <Route path="/bancos" element={<BancosPage />} />
        <Route path="/cheques" element={<ChequesPage />} />
        <Route path="/usuarios" element={<UsuariosPage />} />
        <Route path="/roles" element={<RolesPage />} />
        <Route path="/configuracion" element={<ConfiguracionPage />} />
        <Route path="/catalogo-cuentas" element={<CatalogoCuentasPage />} />
        <Route path="/tipos-asiento" element={<TiposAsientoPage />} />
        <Route path="/plantillas" element={<PlantillasPage />} />
        <Route path="/periodos-contables" element={<PeriodosPage />} />
        <Route path="/compras" element={<ComprasPage />} />
        <Route path="/conciliacion" element={<ConciliacionPage />} />
        <Route path="/activos-fijos" element={<ActivosFijosPage />} />
        <Route path="/empleados" element={<EmpleadosPage />} />
        <Route path="/nomina" element={<NominaPage />} />
        <Route path="/presupuestos" element={<PresupuestosPage />} />
        <Route path="/ocr" element={<OCRPage />} />
        <Route path="/ia" element={<IAPage />} />
        <Route path="/empresas" element={<EmpresasPage />} />
        <Route path="/cierre" element={<CierrePage />} />
        <Route path="/categorias" element={<CategoriasPage />} />
        <Route path="/retenciones" element={<RetencionesPage />} />
        <Route path="/salidas-inventario" element={<SalidasInventarioPage />} />
        <Route path="/cuentas-por-pagar" element={<CxPPage />} />
        <Route path="/cuentas-por-cobrar" element={<CxCPage />} />
        <Route path="/auditoria" element={<AuditoriaPage />} />
        <Route path="/cargador-movimientos" element={<CargadorMovimientosPage />} />
        <Route path="/tipos-cuenta-banco" element={<TiposCuentaBancoPage />} />
        <Route path="/balanza-comprobacion" element={<BalanzaPage />} />
        <Route path="/permisos" element={<PermisosUsuariosPage />} />

        {/* ── Modulos ERP ─────────────────────────────── */}
        <Route path="/erp/contabilidad" element={<ERPContabilidadPage />} />
        <Route path="/erp/inventario" element={<ERPInventarioPage />} />
        <Route path="/erp/cxc" element={<ERPCobrarPage />} />
        <Route path="/erp/tesoreria" element={<ERPTesoreriaPage />} />
        <Route path="/erp/activos-fijos" element={<ERPActivosFijosPage />} />
        <Route path="/erp/facturacion" element={<ERPFacturacionPage />} />
        <Route path="/erp/compras" element={<ERPComprasPage />} />
        <Route path="/erp/pedidos" element={<ERPPedidosPage />} />
        <Route path="/erp/rrhh" element={<ERRRHHPage />} />
      </Route>
    </Routes>
  )
}
