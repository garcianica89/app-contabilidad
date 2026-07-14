import { useEffect, useState } from 'react'
import { api } from '../services/api'
import {
  Plus, X, Check, Shield,
  FileText, Lock, Search, AlertTriangle,
} from 'lucide-react'

interface Periodo {
  id: string
  nombre: string
  fecha_inicio: string
  fecha_fin: string
}

interface Conciliacion {
  id: string
  cuenta_id: string
  cuenta_nombre: string | null
  periodo_id: string | null
  periodo_nombre: string | null
  fecha_inicio: string | null
  fecha_fin: string | null
  saldo_inicial_banco: number
  saldo_inicial_libro: number
  saldo_final_banco: number
  saldo_final_libro: number
  diferencia: number
  estado: string
  observaciones: string | null
  created_at: string
  cerrada_at: string | null
  partidas: Partida[]
}

interface Partida {
  id: string
  conciliacion_id: string
  movimiento_banco_id: string | null
  tipo: string
  concepto: string
  referencia: string | null
  fecha: string
  monto: number
  conciliado: boolean
  observacion: string | null
}

export default function ConciliacionPage() {
  const [conciliaciones, setConciliaciones] = useState<Conciliacion[]>([])
  const [cuentas, setCuentas] = useState<any[]>([])
  const [periodos, setPeriodos] = useState<Periodo[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    cuenta_id: '', periodo_id: '', saldo_final_banco: 0, saldo_inicial_banco: 0, observaciones: '',
  })
  const [saving, setSaving] = useState(false)
  const [autoMatchSugerencias, setAutoMatchSugerencias] = useState<any[] | null>(null)
  const [loadingAutoMatch, setLoadingAutoMatch] = useState(false)
  const [showAjusteForm, setShowAjusteForm] = useState(false)
  const [ajusteForm, setAjusteForm] = useState({ concepto: '', monto: 0, tipo_ajuste: 'COMISION', cuenta_contable_id: '' })

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [conciliacionesData, cuentasData, periodosData] = await Promise.all([
        api.getConciliaciones(),
        api.getCuentasBanco(),
        api.getPeriodos(),
      ])
      setConciliaciones(conciliacionesData)
      setCuentas(cuentasData)
      setPeriodos(periodosData)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function createConciliacion(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const c = await api.crearConciliacion({
        cuenta_id: form.cuenta_id,
        periodo_id: form.periodo_id,
        saldo_final_banco: Number(form.saldo_final_banco),
        saldo_inicial_banco: Number(form.saldo_inicial_banco),
        observaciones: form.observaciones || undefined,
      })
      setConciliaciones(prev => [c, ...prev])
      setSelected(c.id)
      setShowForm(false)
    } catch (e) { console.error(e) }
    setSaving(false)
  }

  async function togglePartida(conciliacionId: string, partidaIds: string[], conciliado: boolean) {
    await api.conciliarPartidas(conciliacionId, { partida_ids: partidaIds, conciliado })
    const updated = await api.getConciliacion(conciliacionId)
    setConciliaciones(prev => prev.map(c => c.id === conciliacionId ? updated : c))
  }

  async function cerrarConciliacion(id: string) {
    if (!confirm('Cerrar esta conciliacion en firme?')) return
    await api.cerrarConciliacion(id)
    const updated = await api.getConciliacion(id)
    setConciliaciones(prev => prev.map(c => c.id === id ? updated : c))
  }

  async function handleAutoMatch() {
    if (!selected) return
    setLoadingAutoMatch(true)
    try {
      const sugerencias = await api.autoMatchConciliacion(selected)
      setAutoMatchSugerencias(sugerencias)
    } catch (e: any) {
      alert('Error al ejecutar auto-match: ' + (e.message || ''))
    }
    setLoadingAutoMatch(false)
  }

  async function aplicarAutoMatch() {
    if (!selected || !autoMatchSugerencias?.length) return
    const matches = autoMatchSugerencias.map(s => ({
      partida_libro_id: s.partida_libro_id,
      partida_estado_id: s.partida_estado_id,
    }))
    try {
      const r = await api.aplicarAutoMatch(selected, matches)
      alert(r.mensaje)
      setAutoMatchSugerencias(null)
      const updated = await api.getConciliacion(selected)
      setConciliaciones(prev => prev.map(c => c.id === selected ? updated : c))
    } catch (e: any) {
      alert('Error: ' + (e.message || ''))
    }
  }

  async function handleCrearAjuste(e: React.FormEvent) {
    e.preventDefault()
    if (!selected) return
    try {
      const r = await api.crearAjusteConciliacion({
        conciliacion_id: selected,
        ...ajusteForm,
      })
      alert(`Ajuste creado. Asiento: ${r.asiento_numero || 'N/A'}`)
      setShowAjusteForm(false)
      const updated = await api.getConciliacion(selected)
      setConciliaciones(prev => prev.map(c => c.id === selected ? updated : c))
    } catch (e: any) {
      alert('Error: ' + (e.message || ''))
    }
  }

  const conciliacion = conciliaciones.find(c => c.id === selected)
  const selectedPeriodo = periodos.find(p => p.id === form.periodo_id)

  function statusBadge(estado: string) {
    const styles: Record<string, string> = {
      TEMPORAL: 'bg-amber-600/20 text-amber-400',
      EN_FIRME: 'bg-emerald-600/20 text-emerald-400',
      PENDIENTE: 'bg-slate-600/20 text-slate-400',
    }
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full ${styles[estado] || 'bg-slate-600/20 text-slate-400'}`}>
        {estado === 'TEMPORAL' ? 'Temporal' : estado === 'EN_FIRME' ? 'En Firme' : estado}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Conciliacion Bancaria</h1>
          <p className="text-slate-400 text-sm mt-1">Compara movimientos del sistema (LIBRO) vs estado de cuenta (BANCO)</p>
        </div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium">
          <Plus className="w-4 h-4" />
          Nueva Conciliacion
        </button>
      </div>

      {showForm && (
        <form onSubmit={createConciliacion} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nueva Conciliacion</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta Bancaria *</label>
              <select value={form.cuenta_id} onChange={e => setForm(f => ({ ...f, cuenta_id: e.target.value }))} className="input-filter w-full" required>
                <option value="">Seleccionar cuenta</option>
                {cuentas.map(c => <option key={c.id} value={c.id}>{c.banco} - {c.numero_cuenta}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Periodo Contable *</label>
              <select value={form.periodo_id} onChange={e => setForm(f => ({ ...f, periodo_id: e.target.value }))} className="input-filter w-full" required>
                <option value="">Seleccionar periodo</option>
                {periodos.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
              {selectedPeriodo && (
                <p className="text-xs text-slate-500 mt-1">{selectedPeriodo.fecha_inicio} al {selectedPeriodo.fecha_fin}</p>
              )}
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Saldo Final segun Banco *</label>
              <input type="number" step="0.01" value={form.saldo_final_banco} onChange={e => setForm(f => ({ ...f, saldo_final_banco: Number(e.target.value) }))} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Saldo Inicial Banco</label>
              <input type="number" step="0.01" value={form.saldo_inicial_banco} onChange={e => setForm(f => ({ ...f, saldo_inicial_banco: Number(e.target.value) }))} className="input-filter w-full" placeholder="0" />
            </div>
            <div className="lg:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Observaciones</label>
              <input value={form.observaciones} onChange={e => setForm(f => ({ ...f, observaciones: e.target.value }))} className="input-filter w-full" placeholder="Opcional" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Creando...' : <><Check className="w-4 h-4" /> Iniciar Conciliacion</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Conciliaciones</h2>
          {loading ? (
            <div className="text-slate-500">Cargando...</div>
          ) : conciliaciones.length === 0 ? (
            <div className="text-slate-500 text-sm text-center py-8">Sin conciliaciones</div>
          ) : conciliaciones.map(c => (
            <div
              key={c.id}
              onClick={() => setSelected(c.id)}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selected === c.id
                  ? 'bg-primary-600/20 border-primary-500/40 text-primary-300'
                  : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-500">{c.cuenta_nombre || 'Cuenta'}</span>
                {statusBadge(c.estado)}
              </div>
              <div className="font-medium text-sm">{c.periodo_nombre || 'Sin periodo'}</div>
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>Libro: C$ {c.saldo_final_libro.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</span>
                <span>Banco: C$ {c.saldo_final_banco.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</span>
              </div>
              {c.diferencia > 0 && (
                <div className="text-xs text-amber-400 mt-1 font-mono">
                  Diff: C$ {c.diferencia.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="lg:col-span-2">
          {conciliacion ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                    Detalle - {conciliacion.cuenta_nombre}
                  </h2>
                  {statusBadge(conciliacion.estado)}
                </div>
                {conciliacion.estado !== 'EN_FIRME' && (
                  <div className="flex items-center gap-2">
                    <button onClick={handleAutoMatch} disabled={loadingAutoMatch} className="flex items-center gap-2 px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 rounded-lg transition-colors text-xs font-medium">
                      <Search className="w-3.5 h-3.5" />
                      {loadingAutoMatch ? 'Buscando...' : 'Auto-Match'}
                    </button>
                    <button onClick={() => setShowAjusteForm(true)} className="flex items-center gap-2 px-3 py-1.5 bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 rounded-lg transition-colors text-xs font-medium">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Ajuste
                    </button>
                    <button onClick={() => cerrarConciliacion(conciliacion.id)} className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-xs font-medium">
                      <Lock className="w-3.5 h-3.5" />
                      Cerrar en Firme
                    </button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Saldo Inicial Libro</div>
                  <div className="text-sm font-bold text-white font-mono">
                    C$ {conciliacion.saldo_inicial_libro.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Saldo Final Libro</div>
                  <div className="text-sm font-bold text-emerald-400 font-mono">
                    C$ {conciliacion.saldo_final_libro.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Saldo Inicial Banco</div>
                  <div className="text-sm font-bold text-white font-mono">
                    C$ {conciliacion.saldo_inicial_banco.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Saldo Final Banco</div>
                  <div className="text-sm font-bold text-blue-400 font-mono">
                    C$ {conciliacion.saldo_final_banco.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Diferencia</div>
                  <div className={`text-sm font-bold font-mono ${conciliacion.diferencia === 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                    C$ {conciliacion.diferencia.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-500 mb-3">
                Periodo: {conciliacion.periodo_nombre || 'N/A'} ({conciliacion.fecha_inicio || '?'} al {conciliacion.fecha_fin || '?'})
              </div>

              {/* Auto-Match Sugerencias */}
              {autoMatchSugerencias && (
                <div className="card mb-4 p-4 border border-purple-700/30">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-purple-400">
                      {autoMatchSugerencias.length} sugerencias de auto-match
                    </h3>
                    <div className="flex gap-2">
                      <button onClick={aplicarAutoMatch} className="px-3 py-1 bg-purple-600 text-white text-xs rounded-lg hover:bg-purple-500">
                        Aplicar todos
                      </button>
                      <button onClick={() => setAutoMatchSugerencias(null)} className="px-3 py-1 bg-slate-700 text-slate-300 text-xs rounded-lg hover:bg-slate-600">
                        Cerrar
                      </button>
                    </div>
                  </div>
                  <div className="overflow-x-auto max-h-48 overflow-y-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-slate-400 border-b border-slate-700">
                          <th className="text-left py-1 px-2">LIBRO</th>
                          <th className="text-left py-1 px-2">Monto</th>
                          <th className="text-left py-1 px-2">↔</th>
                          <th className="text-left py-1 px-2">BANCO</th>
                          <th className="text-left py-1 px-2">Monto</th>
                          <th className="text-center py-1 px-2">Confianza</th>
                        </tr>
                      </thead>
                      <tbody>
                        {autoMatchSugerencias.map((s, i) => (
                          <tr key={i} className="border-b border-slate-800">
                            <td className="py-1 px-2 text-blue-300 truncate max-w-[150px]">{s.partida_libro_concepto}</td>
                            <td className="py-1 px-2 font-mono text-white">C${s.partida_libro_monto.toFixed(2)}</td>
                            <td className="py-1 px-2 text-center text-slate-500">≈</td>
                            <td className="py-1 px-2 text-amber-300 truncate max-w-[150px]">{s.partida_estado_concepto}</td>
                            <td className="py-1 px-2 font-mono text-white">C${s.partida_estado_monto.toFixed(2)}</td>
                            <td className="py-1 px-2 text-center">
                              <span className={`px-1.5 py-0.5 rounded font-mono ${
                                s.confianza >= 0.9 ? 'text-green-400 bg-green-900/30' :
                                s.confianza >= 0.7 ? 'text-yellow-400 bg-yellow-900/30' : 'text-slate-400 bg-slate-800'
                              }`}>
                                {(s.confianza * 100).toFixed(0)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Formulario Ajuste */}
              {showAjusteForm && (
                <form onSubmit={handleCrearAjuste} className="card mb-4 p-4 border border-amber-700/30">
                  <h3 className="text-sm font-semibold text-amber-400 mb-3">Crear Ajuste de Conciliacion</h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Concepto *</label>
                      <input type="text" value={ajusteForm.concepto} onChange={e => setAjusteForm(f => ({ ...f, concepto: e.target.value }))} className="input-filter w-full" placeholder="Comision bancaria, interes..." required />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Monto *</label>
                      <input type="number" step="0.01" value={ajusteForm.monto} onChange={e => setAjusteForm(f => ({ ...f, monto: Number(e.target.value) }))} className="input-filter w-full" required />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Tipo Ajuste</label>
                      <select value={ajusteForm.tipo_ajuste} onChange={e => setAjusteForm(f => ({ ...f, tipo_ajuste: e.target.value }))} className="input-filter w-full">
                        <option value="COMISION">Comision</option>
                        <option value="INTERES">Interes</option>
                        <option value="DIFERENCIA_CAMBIARIA">Diferencia Cambiaria</option>
                        <option value="OTRO">Otro</option>
                      </select>
                    </div>
                    <div className="flex items-end gap-2">
                      <button type="submit" className="px-3 py-2 bg-amber-600 text-white text-xs rounded-lg hover:bg-amber-500 mr-2">Crear Ajuste</button>
                      <button type="button" onClick={() => setShowAjusteForm(false)} className="px-3 py-2 bg-slate-700 text-slate-300 text-xs rounded-lg hover:bg-slate-600">Cancelar</button>
                    </div>
                  </div>
                </form>
              )}

              <div className="card overflow-hidden !p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700/50">
                        <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400 w-10"><Shield className="w-3.5 h-3.5 mx-auto" /></th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Origen</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Fecha</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Concepto</th>
                        <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Ref</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Monto</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                      {conciliacion.partidas.map(p => (
                        <tr key={p.id} className={`hover:bg-slate-800/30 transition-colors ${p.conciliado ? 'opacity-50' : ''}`}>
                          <td className="px-4 py-3 text-center">
                            {conciliacion.estado !== 'EN_FIRME' ? (
                              <div onClick={() => togglePartida(conciliacion.id, [p.id], !p.conciliado)}
                                className={`w-5 h-5 rounded border-2 flex items-center justify-center mx-auto cursor-pointer transition-colors ${p.conciliado ? 'bg-emerald-600 border-emerald-600' : 'border-slate-600 hover:border-slate-500'}`}>
                                {p.conciliado && <Check className="w-3 h-3 text-white" />}
                              </div>
                            ) : (p.conciliado ? <Check className="w-4 h-4 text-emerald-500 mx-auto" /> : <X className="w-4 h-4 text-red-500 mx-auto" />)}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`text-xs px-2 py-0.5 rounded ${p.tipo === 'LIBRO' ? 'bg-blue-600/20 text-blue-400' : 'bg-amber-600/20 text-amber-400'}`}>
                              {p.tipo}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-400 text-xs">{p.fecha}</td>
                          <td className="px-4 py-3">
                            <span className="text-slate-300">{p.concepto}</span>
                            {p.observacion && <span className="text-xs text-slate-500 ml-2">({p.observacion})</span>}
                          </td>
                          <td className="px-4 py-3 text-center text-slate-500 text-xs">{p.referencia || '-'}</td>
                          <td className="px-4 py-3 text-right font-mono text-sm text-white">
                            {p.monto >= 0 ? '' : '-'}C$ {Math.abs(p.monto).toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-500 mt-3">
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-600/40 border border-emerald-600" /> Conciliado</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-slate-700 border border-slate-600" /> Pendiente</span>
                <span className="text-blue-400">LIBRO</span> = del sistema
                <span className="text-amber-400">BANCO</span> = importado
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-500">
              <div className="text-center">
                <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Selecciona una conciliacion o crea una nueva</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
