import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import ChartCard from '../components/ChartCard'
import DataTable from '../components/DataTable'
import PeriodFilter from '../components/PeriodFilter'
import { api } from '../services/api'

const formatCurrency = (v: number) =>
  'C$ ' + (v ?? 0).toLocaleString('es-NI', { minimumFractionDigits: 2 })

export default function BalanceGeneralPage() {
  const [periodoId, setPeriodoId] = useState('')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!periodoId) return
    setLoading(true)
    api.getBalanceGeneral(periodoId).then(setData).catch(() => {}).finally(() => setLoading(false))
  }, [periodoId])

  const activo = data?.activo || {}
  const pasivo = data?.pasivo || {}
  const patrimonio = data?.patrimonio || {}

  const activosCuentas = [
    ...(activo.corriente?.cuentas || []),
    ...(activo.no_corriente?.cuentas || []),
  ]
  const pasivosCuentas = [
    ...(pasivo.corriente?.cuentas || []),
    ...(pasivo.no_corriente?.cuentas || []),
  ]
  const patrimonioCuentas = patrimonio.cuentas || []

  const formatRow = (r: any, isTotal = false) => ({
    cuenta: r.nombre,
    valor: formatCurrency(r.saldo_local),
    es_total: isTotal,
  })

  const activos = activosCuentas.length
    ? [...activosCuentas.map((d) => formatRow(d)), formatRow({ nombre: 'Total Activos', saldo_local: activo.total_activo }, true)]
    : []

  const pasivos = pasivosCuentas.length
    ? [...pasivosCuentas.map((d) => formatRow(d)), formatRow({ nombre: 'Total Pasivos', saldo_local: pasivo.total_pasivo }, true)]
    : []

  const patrimonioRows = patrimonioCuentas.length
    ? [...patrimonioCuentas.map((d: any) => formatRow(d)), formatRow({ nombre: 'Total Patrimonio', saldo_local: patrimonio.total }, true)]
    : []

  const all = [...activos, { cuenta: '', valor: '', es_total: false }, ...pasivos, { cuenta: '', valor: '', es_total: false }, ...patrimonioRows]

  const chartData = [
    { name: 'Activos', valor: activo.total_activo || 0 },
    { name: 'Pasivos', valor: pasivo.total_pasivo || 0 },
    { name: 'Patrimonio', valor: patrimonio.total || 0 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Balance General</h1>
          <p className="text-sm text-slate-400">Estado de situacion financiera</p>
        </div>
        <PeriodFilter value={periodoId} onChange={setPeriodoId} />
      </div>

      {!periodoId ? (
        <div className="card text-center py-12 text-slate-500">Seleccione un periodo para ver el balance</div>
      ) : (
        <>
          <ChartCard title="Distribucion" subtitle="Activos, Pasivos y Patrimonio" height={250}>
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
                    <Bar key={i} dataKey="valor" fill={['#10b981', '#f59e0b', '#6366f1'][i]} radius={[4, 4, 0, 0]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <DataTable
            columns={[
              { key: 'cuenta', label: 'Cuenta' },
              { key: 'valor', label: 'Saldo', align: 'right' },
            ]}
            data={all}
          />
        </>
      )}
    </div>
  )
}
