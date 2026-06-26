import { useState, useEffect } from 'react'
import {
  DollarSign, ShoppingCart, TrendingUp, PiggyBank,
  Users, Truck, Activity,
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, Legend,
} from 'recharts'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import DataTable from '../components/DataTable'
import PeriodFilter from '../components/PeriodFilter'

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function DashboardPage() {
  const [periodoId, setPeriodoId] = useState('')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const params = periodoId ? `?periodo_id=${periodoId}` : ''
    fetch(`/api/v1/bi/dashboard${params}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [periodoId])

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card h-28" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card h-80" />
          <div className="card h-80" />
        </div>
      </div>
    )
  }

  const d = data || {}
  const kpis = d.kpis || {}
  const ventasPorMes = d.ventas_por_mes || []
  const gastosPorCategoria = d.gastos_por_categoria || []
  const topClientes = d.top_clientes || []
  const ingresosVsGastos = d.ingresos_vs_gastos || []
  const cuentasCxC = d.antiguedad_cxc || []

  const formatCurrency = (v: number) =>
    'C$ ' + (v ?? 0).toLocaleString('es-NI', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Dashboard Ejecutivo</h1>
          <p className="text-sm text-slate-400">Panorama general del negocio</p>
        </div>
        <PeriodFilter value={periodoId} onChange={setPeriodoId} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          title="Ventas Totales"
          value={formatCurrency(kpis.ventas_totales)}
          subtitle="Periodo seleccionado"
          icon={<DollarSign className="w-5 h-5 text-emerald-400" />}
          color="emerald"
          trend={kpis.trend_ventas ? { value: kpis.trend_ventas, up: true } : undefined}
        />
        <KPICard
          title="Gastos"
          value={formatCurrency(kpis.gastos_totales)}
          subtitle="Periodo seleccionado"
          icon={<ShoppingCart className="w-5 h-5 text-red-400" />}
          color="red"
        />
        <KPICard
          title="Utilidad Neta"
          value={formatCurrency(kpis.utilidad_neta)}
          subtitle={kpis.margen ? `Margen: ${kpis.margen}%` : ''}
          icon={<TrendingUp className="w-5 h-5 text-amber-400" />}
          color="amber"
        />
        <KPICard
          title="Saldo Caja"
          value={formatCurrency(kpis.saldo_caja)}
          subtitle="Disponible"
          icon={<PiggyBank className="w-5 h-5 text-blue-400" />}
          color="blue"
        />
        <KPICard
          title="CxC Pendiente"
          value={formatCurrency(kpis.cxc_pendiente)}
          subtitle="Cuentas por cobrar"
          icon={<Users className="w-5 h-5 text-purple-400" />}
          color="purple"
        />
        <KPICard
          title="CxP Pendiente"
          value={formatCurrency(kpis.cxp_pendiente)}
          subtitle="Cuentas por pagar"
          icon={<Truck className="w-5 h-5 text-red-400" />}
          color="red"
        />
        <KPICard
          title="Inventario"
          value={formatCurrency(kpis.inventario_valor)}
          subtitle={`${kpis.inventario_items || 0} productos`}
          icon={<Activity className="w-5 h-5 text-primary-400" />}
          color="primary"
        />
        <KPICard
          title="Clientes Activos"
          value={String(kpis.clientes_activos || 0)}
          subtitle="Con movimientos"
          icon={<Users className="w-5 h-5 text-emerald-400" />}
          color="emerald"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Ingresos vs Gastos" subtitle="Comparativa mensual">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={ingresosVsGastos}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="mes" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Bar dataKey="ingresos" name="Ingresos" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="gastos" name="Gastos" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Ventas Mensuales" subtitle="Tendencia del periodo">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={ventasPorMes}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="mes" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Area type="monotone" dataKey="ventas" name="Ventas" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Gastos por Categoria" subtitle="Distribucion">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={gastosPorCategoria}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="valor"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {gastosPorCategoria.map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Antiguedad CxC" subtitle="Saldos por rango de dias">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={cuentasCxC} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" stroke="#64748b" fontSize={12} />
              <YAxis dataKey="nombre" type="category" stroke="#64748b" fontSize={11} width={80} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Bar dataKey="saldo_total" name="Saldo Total" fill="#f59e0b" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard title="Top Clientes" subtitle="Por volumen de ventas" height={250}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={topClientes} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis type="number" stroke="#64748b" fontSize={12} />
            <YAxis dataKey="nombre" type="category" stroke="#64748b" fontSize={11} width={100} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Bar dataKey="total" name="Ventas" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <div>
        <h3 className="text-sm font-semibold text-white mb-3">Ultimos Movimientos</h3>
        <DataTable
          columns={[
            { key: 'fecha', label: 'Fecha' },
            { key: 'concepto', label: 'Concepto' },
            { key: 'tipo', label: 'Tipo' },
            { key: 'entrada', label: 'Entrada', format: (v) => (v ? formatCurrency(v) : '-'), align: 'right' },
            { key: 'salida', label: 'Salida', format: (v) => (v ? formatCurrency(v) : '-'), align: 'right' },
          ]}
          data={d.ultimos_movimientos || []}
        />
      </div>
    </div>
  )
}
