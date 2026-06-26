import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import ChartCard from '../components/ChartCard'
import DataTable from '../components/DataTable'
import { api } from '../services/api'

const formatCurrency = (v: number) =>
  'C$ ' + (v ?? 0).toLocaleString('es-NI', { minimumFractionDigits: 2 })

export default function AntiguedadCxCPage() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getAntiguedadCxC().then(setData).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-white">Antiguedad de Saldos - CxC</h1>
        <p className="text-sm text-slate-400">Cuentas por cobrar por rango de vencimiento</p>
      </div>

      <ChartCard title="Antiguedad CxC" subtitle="Saldos por cliente" height={350}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" barSize={20}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis type="number" stroke="#64748b" fontSize={12} />
            <YAxis dataKey="nombre" type="category" stroke="#64748b" fontSize={11} width={100} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
              labelStyle={{ color: '#e2e8f0' }}
              formatter={(v: number) => [formatCurrency(v)]}
            />
            <Bar dataKey="entre_0_30" name="0-30 dias" stackId="a" fill="#10b981" />
            <Bar dataKey="entre_30_60" name="31-60 dias" stackId="a" fill="#f59e0b" />
            <Bar dataKey="entre_60_90" name="61-90 dias" stackId="a" fill="#ef4444" />
            <Bar dataKey="mas_90" name="+90 dias" stackId="a" fill="#7f1d1d" />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <DataTable
        columns={[
          { key: 'codigo', label: 'Codigo' },
          { key: 'nombre', label: 'Cliente' },
          { key: 'entre_0_30', label: '0-30 dias', format: (v) => formatCurrency(v || 0), align: 'right' },
          { key: 'entre_30_60', label: '31-60 dias', format: (v) => formatCurrency(v || 0), align: 'right' },
          { key: 'entre_60_90', label: '61-90 dias', format: (v) => formatCurrency(v || 0), align: 'right' },
          { key: 'mas_90', label: '+90 dias', format: (v) => formatCurrency(v || 0), align: 'right' },
          { key: 'saldo_total', label: 'Total', format: (v) => formatCurrency(v || 0), align: 'right' },
        ]}
        data={data}
        loading={loading}
      />
    </div>
  )
}
