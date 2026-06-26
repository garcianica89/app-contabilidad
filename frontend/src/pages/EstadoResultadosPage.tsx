import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import ChartCard from '../components/ChartCard'
import DataTable from '../components/DataTable'
import PeriodFilter from '../components/PeriodFilter'

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']
const formatCurrency = (v: number) =>
  'C$ ' + (v ?? 0).toLocaleString('es-NI', { minimumFractionDigits: 2 })

export default function EstadoResultadosPage() {
  const [periodoId, setPeriodoId] = useState('')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!periodoId) return
    setLoading(true)
    fetch(`/api/v1/reportes/estado-resultados?periodo_id=${periodoId}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [periodoId])

  const ingresos = data?.ingresos?.cuentas || []
  const costos = data?.costos?.cuentas || []
  const gastos = data?.gastos?.cuentas || []

  const tableRows = [...ingresos, ...costos, ...gastos].map((d: any) => ({
    cuenta: `${d.codigo} - ${d.nombre}`,
    tipo: d.tipo,
    valor: formatCurrency(d.saldo_local),
  }))

  const chartData = [
    { name: 'Ingresos', valor: data?.ingresos?.total || 0 },
    { name: 'Costos', valor: data?.costos?.total || 0 },
    { name: 'Gastos', valor: data?.gastos?.total || 0 },
  ]

  const pieData = [
    { name: 'Utilidad Bruta', valor: data?.utilidad_bruta || 0 },
    { name: 'Gastos', valor: data?.gastos?.total || 0 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Estado de Resultados</h1>
          <p className="text-sm text-slate-400">Rendimiento economico del periodo</p>
        </div>
        <PeriodFilter value={periodoId} onChange={setPeriodoId} />
      </div>

      {!periodoId ? (
        <div className="card text-center py-12 text-slate-500">Seleccione un periodo para ver el reporte</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card">
              <span className="card-header">Ingresos</span>
              <div className="kpi-value text-emerald-400">{formatCurrency(data?.ingresos?.total || 0)}</div>
            </div>
            <div className="card">
              <span className="card-header">Costos</span>
              <div className="kpi-value text-red-400">{formatCurrency(data?.costos?.total || 0)}</div>
            </div>
            <div className="card">
              <span className="card-header">Utilidad Neta</span>
              <div className="kpi-value text-amber-400">{formatCurrency(data?.utilidad_neta || 0)}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title="Ingresos vs Costos vs Gastos" subtitle="Comparativa">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                    labelStyle={{ color: '#e2e8f0' }}
                    formatter={(v: number) => [formatCurrency(v)]}
                  />
                  <Bar dataKey="valor" radius={[4, 4, 0, 0]}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={['#10b981', '#f59e0b', '#ef4444'][i]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Distribucion" subtitle="Utilidad vs Gastos">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="valor"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={['#10b981', '#ef4444'][i]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                    labelStyle={{ color: '#e2e8f0' }}
                    formatter={(v: number) => [formatCurrency(v)]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <DataTable
            columns={[
              { key: 'cuenta', label: 'Cuenta' },
              { key: 'valor', label: 'Saldo', align: 'right' },
            ]}
            data={tableRows}
          />
        </>
      )}
    </div>
  )
}
