import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import ChartCard from '../components/ChartCard'
import DataTable from '../components/DataTable'

const formatCurrency = (v: number) =>
  'C$ ' + (v ?? 0).toLocaleString('es-NI', { minimumFractionDigits: 2 })

export default function FlujoEfectivoPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const hoy = new Date()
    const inicio = new Date(hoy.getFullYear(), 0, 1).toISOString().split('T')[0]
    const fin = hoy.toISOString().split('T')[0]

    fetch(`/api/v1/reportes/flujo-efectivo?fecha_desde=${inicio}&fecha_hasta=${fin}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const op = data?.actividades_operacion || {}
  const inv = data?.actividades_inversion || {}
  const fin = data?.actividades_financiamiento || {}

  const movimientos = [
    ...(op.movimientos || []).map((m: any) => ({ ...m, categoria: 'Operacion' })),
    ...(inv.movimientos || []).map((m: any) => ({ ...m, categoria: 'Inversion' })),
    ...(fin.movimientos || []).map((m: any) => ({ ...m, categoria: 'Financiamiento' })),
  ]

  const chartData = [
    { name: 'Operacion\nIngresos', valor: op.ingresos || 0 },
    { name: 'Operacion\nEgresos', valor: -(op.egresos || 0) },
    { name: 'Inversion\nIngresos', valor: inv.ingresos || 0 },
    { name: 'Inversion\nEgresos', valor: -(inv.egresos || 0) },
    { name: 'Financ.\nIngresos', valor: fin.ingresos || 0 },
    { name: 'Financ.\nEgresos', valor: -(fin.egresos || 0) },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-white">Flujo de Efectivo</h1>
        <p className="text-sm text-slate-400">Movimientos de efectivo del periodo actual</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <span className="card-header">Operacion</span>
          <div className="kpi-value text-emerald-400">{formatCurrency(op.neto || 0)}</div>
          <div className="text-xs text-slate-500 mt-1">
            Ing: {formatCurrency(op.ingresos || 0)} | Egr: {formatCurrency(op.egresos || 0)}
          </div>
        </div>
        <div className="card">
          <span className="card-header">Inversion</span>
          <div className="kpi-value text-amber-400">{formatCurrency(inv.neto || 0)}</div>
          <div className="text-xs text-slate-500 mt-1">
            Ing: {formatCurrency(inv.ingresos || 0)} | Egr: {formatCurrency(inv.egresos || 0)}
          </div>
        </div>
        <div className="card">
          <span className="card-header">Financiamiento</span>
          <div className="kpi-value text-blue-400">{formatCurrency(fin.neto || 0)}</div>
          <div className="text-xs text-slate-500 mt-1">
            Ing: {formatCurrency(fin.ingresos || 0)} | Egr: {formatCurrency(fin.egresos || 0)}
          </div>
        </div>
      </div>

      <div className="card">
        <span className="card-header text-lg">Variacion Neta del Periodo</span>
        <div className="kpi-value text-white">{formatCurrency(data?.variacion_neta || 0)}</div>
      </div>

      <ChartCard title="Flujo por Actividad" subtitle="Ingresos y egresos del periodo" height={300}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={12} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
              labelStyle={{ color: '#e2e8f0' }}
              formatter={(v: number) => [formatCurrency(Math.abs(v))]}
            />
            <Bar dataKey="valor" radius={[4, 4, 0, 0]}>
              {chartData.map((d, i) => (
                <Bar key={i} dataKey="valor" fill={d.valor >= 0 ? '#10b981' : '#ef4444'} radius={[4, 4, 0, 0]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <DataTable
        columns={[
          { key: 'fecha', label: 'Fecha' },
          { key: 'concepto', label: 'Concepto' },
          { key: 'categoria', label: 'Categoria' },
          { key: 'descripcion', label: 'Detalle' },
          { key: 'monto', label: 'Monto', format: (v: number) => formatCurrency(v || 0), align: 'right' },
          { key: 'tipo_movimiento', label: 'Tipo' },
        ]}
        data={movimientos}
        loading={loading}
      />
    </div>
  )
}
