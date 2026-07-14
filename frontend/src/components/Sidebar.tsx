import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, BarChart3, PiggyBank, TrendingUp, ArrowRightLeft,
  Users, Truck, Database, ShoppingCart, Building2, FileText, Settings,
  BookOpen, Shield, X, Search, ChevronDown, ChevronRight, UserCheck,
  DollarSign, CreditCard, Receipt, Wallet, Briefcase, Calculator,
  Globe, HardDrive, Lock, ClipboardList, Percent, Upload, Key, Scale,
} from 'lucide-react'
import { usePermissions } from '../contexts/PermissionContext'

interface MenuItem {
  to: string; label: string; icon: any; permiso?: string
}

interface MenuGroup {
  label: string; icon: any; items: MenuItem[]; permiso?: string
}

type SidebarEntry = { type: 'group'; data: MenuGroup } | { type: 'link'; data: MenuItem } | { type: 'divider' }

const menu: SidebarEntry[] = [
  { type: 'link', data: { to: '/', label: 'Dashboard', icon: LayoutDashboard } },
  { type: 'divider' },
  {
    type: 'group', data: {
      label: 'Administracion General', icon: Building2, items: [
        { to: '/empresas', label: 'Empresas', icon: Globe, permiso: 'empresas_ver' },
        { to: '/usuarios', label: 'Usuarios', icon: Users, permiso: 'usuarios_ver' },
        { to: '/roles', label: 'Roles y Permisos', icon: Shield, permiso: 'roles_ver' },
        { to: '/permisos', label: 'Permisos Usuario', icon: Key, permiso: 'permisos_usuario_asignar' },
        { to: '/configuracion', label: 'Configuracion', icon: Settings, permiso: 'configuracion_ver' },
      ],
    },
  },
  {
    type: 'group', data: {
      label: 'Contabilidad General', icon: BookOpen, items: [
        { to: '/catalogo-cuentas', label: 'Catalogo Cuentas', icon: BookOpen, permiso: 'cuentas_ver' },
        { to: '/tipos-asiento', label: 'Tipos de Asiento', icon: FileText, permiso: 'tipos_asiento_ver' },
        { to: '/plantillas', label: 'Plantillas', icon: FileText, permiso: 'plantillas_ver' },
        { to: '/periodos-contables', label: 'Periodos', icon: Calendar },
        { to: '/cierre', label: 'Cierre Contable', icon: Lock, permiso: 'cierre_ejecutar' },
        { to: '/auditoria', label: 'Auditoria', icon: Shield, permiso: 'auditoria_ver' },
      ],
    },
  },
  {
    type: 'group', data: {
      label: 'Cuentas por Cobrar', icon: Users, items: [
        { to: '/clientes', label: 'Clientes', icon: Users, permiso: 'clientes_ver' },
        { to: '/facturacion', label: 'Facturacion', icon: Receipt, permiso: 'facturacion_ver' },
        { to: '/cuentas-por-cobrar', label: 'CxC - Cobros', icon: DollarSign, permiso: 'cxc_ver' },
      ],
    },
  },
  {
    type: 'group', data: {
      label: 'Cuentas por Pagar', icon: Truck, items: [
        { to: '/proveedores', label: 'Proveedores', icon: Building2, permiso: 'proveedores_ver' },
        { to: '/compras', label: 'Compras', icon: ShoppingCart, permiso: 'compras_ver' },
        { to: '/cuentas-por-pagar', label: 'CxP - Pagos', icon: DollarSign, permiso: 'cxp_ver' },
        { to: '/retenciones', label: 'Retenciones', icon: Percent, permiso: 'retenciones_ver' },
      ],
    },
  },
  {
    type: 'group', data: {
      label: 'Control Bancario', icon: PiggyBank, items: [
        { to: '/bancos', label: 'Bancos', icon: Wallet, permiso: 'bancos_ver' },
        { to: '/conciliacion', label: 'Conciliacion', icon: Search, permiso: 'conciliacion_ver' },
        { to: '/cargador-movimientos', label: 'Cargador Mov.', icon: Upload, permiso: 'cargador_ver' },
        { to: '/tipos-cuenta-banco', label: 'Tipos Cuenta', icon: PiggyBank },
        { to: '/cheques', label: 'Cheques', icon: CreditCard, permiso: 'cheques_ver' },
      ],
    },
  },
  {
    type: 'group', data: {
      label: 'Inventarios', icon: Database, items: [
        { to: '/inventario', label: 'Productos', icon: Database, permiso: 'inventario_ver' },
        { to: '/categorias', label: 'Categorias', icon: BookOpen, permiso: 'categorias_ver' },
        { to: '/salidas-inventario', label: 'Salidas Inventario', icon: ClipboardList, permiso: 'inventario_salida' },
      ],
    },
  },
  {
    type: 'group', data: {
      label: 'Activo Fijo', icon: HardDrive, items: [
        { to: '/activos-fijos', label: 'Activos Fijos', icon: HardDrive, permiso: 'activos_fijos_ver' },
      ],
    },
  },
  {
    type: 'group', data: {
      label: 'Gestion Nomina', icon: Calculator, items: [
        { to: '/empleados', label: 'Empleados', icon: UserCheck, permiso: 'empleados_ver' },
        { to: '/nomina', label: 'Nominas', icon: Calculator, permiso: 'nomina_ver' },
      ],
    },
  },
  { type: 'divider' },
  {
    type: 'group', data: {
      label: 'ERP - Contabilidad', icon: BookOpen, items: [
        { to: '/erp/contabilidad', label: 'Plan Cuentas', icon: BookOpen },
        { to: '/erp/inventario', label: 'Inventario', icon: Database },
        { to: '/erp/cxc', label: 'CxC', icon: Users },
        { to: '/erp/tesoreria', label: 'Tesorería', icon: Wallet },
        { to: '/erp/activos-fijos', label: 'Activos Fijos', icon: HardDrive },
        { to: '/erp/facturacion', label: 'Facturación', icon: Receipt },
        { to: '/erp/compras', label: 'Compras', icon: ShoppingCart },
        { to: '/erp/pedidos', label: 'Pedidos', icon: FileText },
        { to: '/erp/rrhh', label: 'RRHH', icon: UserCheck },
      ],
    },
  },
  { type: 'divider' },
  {
    type: 'group', data: {
      label: 'Reportes', icon: BarChart3, items: [
        { to: '/balance-general', label: 'Balance General', icon: BarChart3, permiso: 'reportes_balance' },
        { to: '/estado-resultados', label: 'Estado Resultados', icon: TrendingUp, permiso: 'reportes_estado_resultados' },
        { to: '/balanza-comprobacion', label: 'Balanza Comprobación', icon: Scale, permiso: 'reportes_balanza' },
        { to: '/flujo-efectivo', label: 'Flujo de Efectivo', icon: ArrowRightLeft, permiso: 'reportes_flujo_efectivo' },
      ],
    },
  },
  {
    type: 'group', data: {
      label: 'Herramientas', icon: Settings, items: [
        { to: '/presupuestos', label: 'Presupuestos', icon: TrendingUp, permiso: 'presupuestos_ver' },
        { to: '/ocr', label: 'OCR Documentos', icon: FileText, permiso: 'ocr_ver' },
        { to: '/ia', label: 'Inteligencia Artificial', icon: BarChart3, permiso: 'ia_ver' },
      ],
    },
  },
]

function MenuGroupComp({ group, defaultOpen }: { group: MenuGroup; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  const { has } = usePermissions()

  const visibleItems = group.items.filter(item => !item.permiso || has(item.permiso))
  if (visibleItems.length === 0) return null

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-colors"
      >
        <group.icon className="w-5 h-5 flex-shrink-0" />
        <span className="flex-1 text-left">{group.label}</span>
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {open && (
        <div className="ml-4 mt-1 space-y-1 border-l border-slate-700/50 pl-3">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`
              }
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { has } = usePermissions()

  const visibleMenu = menu.filter(entry => {
    if (entry.type === 'divider') return true
    if (entry.type === 'link') return !entry.data.permiso || has(entry.data.permiso)
    if (entry.type === 'group') {
      const items = entry.data.items.filter(i => !i.permiso || has(i.permiso))
      return items.length > 0
    }
    return true
  })

  return (
    <>
      {open && <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={onClose} />}
      <aside className={`
        fixed md:static inset-y-0 left-0 z-50 w-64 bg-slate-900/95 border-r border-slate-800
        transform transition-transform duration-200 ease-in-out overflow-y-auto
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
          {visibleMenu.map((entry, i) =>
            entry.type === 'divider' ? (
              <div key={`div-${i}`} className="border-t border-slate-800 my-3" />
            ) : entry.type === 'link' ? (
              <NavLink
                key={entry.data.to}
                to={entry.data.to}
                end={entry.data.to === '/'}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`
                }
              >
                <entry.data.icon className="w-5 h-5" />
                {entry.data.label}
              </NavLink>
            ) : (
              <MenuGroupComp key={entry.data.label} group={entry.data} defaultOpen={true} />
            )
          )}
        </nav>

        <div className="p-4 border-t border-slate-800">
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

function Calendar(props: any) {
  return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
}
