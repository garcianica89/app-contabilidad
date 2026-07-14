import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, PiggyBank } from 'lucide-react'
import { useNotification } from '../contexts/NotificationContext'

export default function NominaPage() {
  const { notify } = useNotification()
  const [periodos, setPeriodos] = useState<any[]>([])
  const [config, setConfig] = useState<any>(null)
  const [selected, setSelected] = useState<any>(null)
  const [tab, setTab] = useState<'periodos' | 'config'>('periodos')

  const load = async () => {
    setPeriodos(await api.getPeriodosNomina())
    setConfig(await api.getNominaConfig())
  }
  useEffect(() => { load() }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Nomina</h1>
      <div className="flex gap-2 mb-4">
        <button onClick={() => setTab('periodos')}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === 'periodos' ? 'bg-primary-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Periodos</button>
        <button onClick={() => setTab('config')}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === 'config' ? 'bg-primary-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Configuracion</button>
      </div>

      {tab === 'periodos' && (
        <>
          {selected && <DetallePeriodo periodo={selected} onBack={() => setSelected(null)} onRefresh={load} />}
          {!selected && (
            <>
              <div className="flex gap-2 mb-4">
                <button onClick={async () => {
                  const codigo = prompt('Codigo del periodo:')
                  if (!codigo) return
                  const fi = prompt('Fecha inicio (YYYY-MM-DD):')
                  const ff = prompt('Fecha fin (YYYY-MM-DD):')
                  const fp = prompt('Fecha pago (YYYY-MM-DD):')
                  if (!fi || !ff || !fp) return
                  await api.crearPeriodoNomina({ codigo, fecha_inicio: fi, fecha_fin: ff, fecha_pago: fp })
                  load()
                }} className="bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-700">
                  <Plus className="w-4 h-4" /> Nuevo Periodo</button>
              </div>
              <div className="grid gap-3">
                {periodos.map((p: any) => (
                  <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-center justify-between">
                    <div>
                      <p className="text-white font-medium">{p.codigo}</p>
                      <p className="text-sm text-slate-400">{p.fecha_inicio} → {p.fecha_fin}</p>
                      <p className="text-sm text-slate-500">Dev: C$ {Number(p.total_devengado).toLocaleString()} · Ded: C$ {Number(p.total_deducciones).toLocaleString()} · Neto: C$ {Number(p.total_neto).toLocaleString()}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        p.estado === 'PAGADA' ? 'bg-green-900 text-green-400' :
                        p.estado === 'PROCESADA' ? 'bg-yellow-900 text-yellow-400' :
                        'bg-slate-800 text-slate-400'}`}>{p.estado}</span>
                      <button onClick={() => setSelected(p)} className="p-2 text-slate-400 hover:text-white">Ver</button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {tab === 'config' && config && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-md">
          <h2 className="text-lg font-semibold text-white mb-4">Configuracion de Nomina</h2>
          {(['salario_minimo', 'inss_patronal_rate', 'inss_laboral_rate', 'aguinaldo_dias'] as const).map(f => (
            <div key={f} className="mb-3">
              <label className="text-sm text-slate-400 block mb-1">{f}</label>
              <input type="number" step="0.0001" value={config[f] || ''} onChange={e => setConfig({...config, [f]: parseFloat(e.target.value) || 0})}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
            </div>
          ))}
          <button onClick={async () => { await api.actualizarNominaConfig(config); notify('Guardado', 'success') }}
            className="mt-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">Guardar</button>
        </div>
      )}
    </div>
  )
}

function DetallePeriodo({ periodo, onBack, onRefresh }: { periodo: any; onBack: () => void; onRefresh: () => void }) {
  const [detalles, setDetalles] = useState<any[]>([])
  const [empleados, setEmpleados] = useState<any[]>([])
  const [procesando, setProcesando] = useState(false)

  const loadDetalle = async () => {
    const p = await api.getPeriodoNomina(periodo.id)
    setDetalles(p.detalles || [])
    setEmpleados(await api.getEmpleados({ activo: true }))
  }
  useEffect(() => { loadDetalle() }, [periodo.id])

  const empMap = Object.fromEntries(empleados.map((e: any) => [e.id, e.nombre]))

  const procesar = async () => {
    setProcesando(true)
    const hrsExtra: any = {}
    const bonos: any = {}
    const comisiones: any = {}
    const otras: any = {}
    detalles.forEach((d: any) => {
      if (d.horas_extra > 0) hrsExtra[d.empleado_id] = d.horas_extra
      if (d.bonos > 0) bonos[d.empleado_id] = d.bonos
      if (d.comisiones > 0) comisiones[d.empleado_id] = d.comisiones
      if (d.otras_deducciones > 0) otras[d.empleado_id] = d.otras_deducciones
    })
    await api.procesarNomina(periodo.id, { horas_extra: hrsExtra, bonos, comisiones, otras_deducciones: otras })
    setProcesando(false)
    onRefresh()
    loadDetalle()
  }

  return (
    <div>
      <button onClick={onBack} className="text-sm text-primary-400 hover:text-primary-300 mb-4">← Volver</button>
      <h2 className="text-xl font-semibold text-white mb-4">{periodo.codigo}</h2>
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: 'Total Devengado', value: Number(periodo.total_devengado).toLocaleString(), color: 'text-green-400' },
          { label: 'Total Deducciones', value: Number(periodo.total_deducciones).toLocaleString(), color: 'text-red-400' },
          { label: 'Total Neto', value: Number(periodo.total_neto).toLocaleString(), color: 'text-white font-bold' },
        ].map(s => (
          <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <p className="text-sm text-slate-400">{s.label}</p>
            <p className={`text-2xl ${s.color}`}>C$ {s.value}</p>
          </div>
        ))}
      </div>
      <div className="flex gap-2 mb-4">
        {periodo.estado === 'BORRADOR' && (
          <button onClick={procesar} disabled={procesando}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-700 disabled:opacity-50">
            <PiggyBank className="w-4 h-4" /> {procesando ? 'Procesando...' : 'Procesar Nomina'}</button>
        )}
        {periodo.estado === 'PROCESADA' && (
          <button onClick={async () => { await api.pagarNomina(periodo.id); onRefresh(); loadDetalle() }}
            className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-green-700">
            <PiggyBank className="w-4 h-4" /> Pagar Nomina</button>
        )}
      </div>
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-800 text-slate-400">
            <th className="text-left p-3">Empleado</th>
            <th className="text-right p-3">Salario</th>
            <th className="text-right p-3">HE</th>
            <th className="text-right p-3">Bonos</th>
            <th className="text-right p-3">Devengado</th>
            <th className="text-right p-3">INSS</th>
            <th className="text-right p-3">IR</th>
            <th className="text-right p-3">Deducc.</th>
            <th className="text-right p-3">Neto</th>
          </tr></thead>
          <tbody>
            {detalles.map((d: any) => (
              <tr key={d.id} className="border-b border-slate-800 text-white">
                <td className="p-3">{empMap[d.empleado_id] || d.empleado_id}</td>
                <td className="p-3 text-right">{Number(d.salario_base).toFixed(2)}</td>
                <td className="p-3 text-right">{Number(d.horas_extra).toFixed(2)}</td>
                <td className="p-3 text-right">{Number(d.bonos).toFixed(2)}</td>
                <td className="p-3 text-right">{Number(d.total_devengado).toFixed(2)}</td>
                <td className="p-3 text-right text-red-400">{Number(d.inss_laboral).toFixed(2)}</td>
                <td className="p-3 text-right text-red-400">{Number(d.ir).toFixed(2)}</td>
                <td className="p-3 text-right text-red-400">{Number(d.total_deducciones).toFixed(2)}</td>
                <td className="p-3 text-right font-bold">{Number(d.neto).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
