import { useState, useEffect } from 'react'
import { Lock, Unlock, Plus, X, Check, AlertCircle, FileText, RefreshCw, Search } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'

type Tab = 'mensual' | 'fiscal'

export default function CierrePage() {
  const [tab, setTab] = useState<Tab>('mensual')

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Cierre Contable</h1>
          <p className="text-sm text-slate-400">Cierre mensual y fiscal de periodos</p>
        </div>
      </div>

      <div className="flex gap-1 border-b border-slate-800 overflow-x-auto">
        {([
          ['mensual', 'Cierre Mensual', Lock],
          ['fiscal', 'Cierre Fiscal', FileText],
        ] as [Tab, string, any][]).map(([key, label, Icon]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === key
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}>
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {tab === 'mensual' && <CierreMensualTab />}
      {tab === 'fiscal' && <CierreFiscalTab />}
    </div>
  )
}

function CierreMensualTab() {
  const [cierres, setCierres] = useState<any[]>([])
  const [periodos, setPeriodos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ periodo_id: '', observaciones: '' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try {
      const [c, p] = await Promise.all([api.getCierresMensuales(), api.getPeriodos()])
      setCierres(c)
      setPeriodos(p)
    } catch {}
    setLoading(false)
  }

  const periodosAbiertos = periodos.filter((p) => !p.cerrado)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const data = await api.crearCierreMensual({ periodo_id: form.periodo_id, observaciones: form.observaciones || null })
      setCierres((prev) => [data, ...prev])
      setShowForm(false)
      load()
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleReabrir(id: string) {
    if (!confirm('Reabrir este periodo? Los cambios permitiran nuevas modificaciones.')) return
    try {
      await api.reabrirCierreMensual(id)
      load()
    } catch (err: any) { notify(err.message) }
  }

  const periodoMap = Object.fromEntries(periodos.map((p) => [p.id, p]))

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => { setShowForm(true); setForm({ periodo_id: '', observaciones: '' }) }}
          className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo Cierre Mensual
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nuevo Cierre Mensual</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Periodo *</label>
              <select value={form.periodo_id} onChange={(e) => setForm({ ...form, periodo_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar periodo...</option>
                {periodosAbiertos.map((p) => (
                  <option key={p.id} value={p.id}>{p.codigo} - {p.nombre}</option>
                ))}
              </select>
              {periodosAbiertos.length === 0 && <p className="text-xs text-red-400 mt-1">No hay periodos abiertos disponibles</p>}
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Observaciones</label>
              <input value={form.observaciones} onChange={(e) => setForm({ ...form, observaciones: e.target.value })} className="input-filter w-full" placeholder="Cierre mensual opcional" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving || periodosAbiertos.length === 0} className="btn-primary"><Check className="w-4 h-4" /> Cerrar Periodo</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <Skeleton rows={4} />
      ) : cierres.length === 0 ? (
        <EmptyState message="No hay cierres mensuales registrados" />
      ) : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Periodo</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Estado</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Cerrado por</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Cerrado en</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Observaciones</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {cierres.map((c) => {
                  const per = periodoMap[c.periodo_id]
                  return (
                    <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-xs font-medium text-primary-400">{per?.codigo || c.periodo_id}</span>
                        <span className="text-xs text-slate-500 ml-1">{per?.nombre || ''}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded ${
                          c.estado === 'CERRADO' ? 'bg-red-600/20 text-red-400' :
                          c.estado === 'REABIERTO' ? 'bg-amber-600/20 text-amber-400' : 'bg-slate-600/20 text-slate-400'
                        }`}>
                          {c.estado === 'CERRADO' ? <Lock className="w-3 h-3" /> :
                           c.estado === 'REABIERTO' ? <Unlock className="w-3 h-3" /> : null}
                          {c.estado}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-xs">{c.cerrado_por || '-'}</td>
                      <td className="px-4 py-3 text-slate-400 text-xs">{c.cerrado_en ? new Date(c.cerrado_en).toLocaleString() : '-'}</td>
                      <td className="px-4 py-3 text-slate-500 text-xs max-w-[200px] truncate">{c.observaciones || '-'}</td>
                      <td className="px-4 py-3 text-center">
                        {c.estado === 'CERRADO' && (
                          <button onClick={() => handleReabrir(c.id)} className="p-1 text-amber-500 hover:text-amber-400" title="Reabrir">
                            <RefreshCw className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function CierreFiscalTab() {
  const [cierres, setCierres] = useState<any[]>([])
  const [ejercicios, setEjercicios] = useState<any[]>([])
  const [cuentas, setCuentas] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ ejercicio_id: '', cuenta_resultado_id: '', cuenta_utilidad_id: '', observaciones: '' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try {
      const [c, ej, ct] = await Promise.all([
        api.getCierresFiscales(),
        api.getEjercicios(),
        api.getCuentasContables(),
      ])
      setCierres(c)
      setEjercicios(ej)
      setCuentas(ct)
    } catch {}
    setLoading(false)
  }

  const ejerciciosAbiertos = ejercicios.filter((e) => !e.cerrado)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const data = await api.crearCierreFiscal({
        ejercicio_id: form.ejercicio_id,
        cuenta_resultado_id: form.cuenta_resultado_id,
        cuenta_utilidad_id: form.cuenta_utilidad_id,
        observaciones: form.observaciones || null,
      })
      setCierres((prev) => [data, ...prev])
      setShowForm(false)
      load()
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  const cuentaMap = Object.fromEntries(cuentas.map((c) => [c.id, c]))

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => { setShowForm(true); setForm({ ejercicio_id: '', cuenta_resultado_id: '', cuenta_utilidad_id: '', observaciones: '' }) }}
          className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo Cierre Fiscal
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nuevo Cierre Fiscal</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Ejercicio Fiscal *</label>
              <select value={form.ejercicio_id} onChange={(e) => setForm({ ...form, ejercicio_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar...</option>
                {ejerciciosAbiertos.map((ej) => (
                  <option key={ej.id} value={ej.id}>{ej.codigo} - {ej.nombre}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta Resultado *</label>
              <select value={form.cuenta_resultado_id} onChange={(e) => setForm({ ...form, cuenta_resultado_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar...</option>
                {cuentas.filter((c) => c.tipo_cuenta === 'RESULTADO').map((c) => (
                  <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta Utilidad *</label>
              <select value={form.cuenta_utilidad_id} onChange={(e) => setForm({ ...form, cuenta_utilidad_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar...</option>
                {cuentas.filter((c) => c.tipo_cuenta === 'PATRIMONIO').map((c) => (
                  <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Observaciones</label>
              <input value={form.observaciones} onChange={(e) => setForm({ ...form, observaciones: e.target.value })} className="input-filter w-full" placeholder="Opcional" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> Cerrar Ejercicio</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <Skeleton rows={4} />
      ) : cierres.length === 0 ? (
        <EmptyState message="No hay cierres fiscales registrados" />
      ) : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Ejercicio</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Estado</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Resultado</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Cerrado en</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Observaciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {cierres.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 text-xs font-medium text-primary-400">{c.ejercicio_id?.slice(0, 8)}...</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        c.estado === 'CERRADO' ? 'bg-red-600/20 text-red-400' : 'bg-slate-600/20 text-slate-400'
                      }`}>{c.estado}</span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-emerald-400">
                      {c.resultado_ejercicio != null
                        ? `C$ ${c.resultado_ejercicio.toLocaleString('es-NI', { minimumFractionDigits: 2 })}`
                        : '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {c.cerrado_en ? new Date(c.cerrado_en).toLocaleString() : '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs max-w-[200px] truncate">{c.observaciones || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
