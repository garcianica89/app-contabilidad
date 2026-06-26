import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  BarChart3,
  PiggyBank,
  TrendingUp,
  ArrowRightLeft,
  Users,
  Truck,
  Settings,
  X,
} from 'lucide-react'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/balance-general', label: 'Balance General', icon: BarChart3 },
  { to: '/estado-resultados', label: 'Estado Resultados', icon: TrendingUp },
  { to: '/flujo-efectivo', label: 'Flujo de Efectivo', icon: ArrowRightLeft },
  { to: '/antiguedad-cxc', label: 'Antiguedad Cuentas x Cobrar', icon: Users },
  { to: '/antiguedad-cxp', label: 'Antiguedad Cuentas x Pagar', icon: Truck },
  { to: '/usuarios', label: 'Usuarios', icon: Settings },
]

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {open && <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={onClose} />}
      <aside className={`
        fixed md:static inset-y-0 left-0 z-50 w-64 bg-slate-900/95 border-r border-slate-800
        transform transition-transform duration-200 ease-in-out
        ${open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="font-semibold text-white">Contabilidad BI</span>
          </div>
          <button onClick={onClose} className="md:hidden text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-3 space-y-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`
              }
            >
              <link.icon className="w-5 h-5" />
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800">
          <button
            onClick={() => {
              localStorage.removeItem('token')
              window.location.href = '/login'
            }}
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-red-400 transition-colors w-full"
          >
            <PiggyBank className="w-4 h-4" />
            Cerrar Sesion
          </button>
        </div>
      </aside>
    </>
  )
}
