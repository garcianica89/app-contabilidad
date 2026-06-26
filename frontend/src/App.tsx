import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useState } from 'react'
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

function ProtectedLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  if (!localStorage.getItem('token')) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <MobileNav onMenuClick={() => setSidebarOpen(true)} />
      <main className="flex-1 overflow-y-auto pt-16 md:pt-0 pb-20 md:pb-0">
        <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
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
        <Route path="/usuarios" element={<UsuariosPage />} />
      </Route>
    </Routes>
  )
}
