import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, Cpu, Box, TrendingDown, Trash2, History } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

type Tab = 'tipos' | 'activos'

export default function ERPActivosFijosPage() {
  const [tab, setTab] = useState<Tab>('activos')
  const [tipos, setTipos] = useState<any[]>([])
  const [activos, setActivos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<'tipo' | 'activo'>('activo')
  const [form, setForm] = useState<any>({})
  const [saving, setSaving] = useState(false)
  const [selectedActivo, setSelectedActivo] = useState<any>(null)
  const [depreciaciones, setDepreciaciones] = useState<any[]>([])
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [t, a] = await Promise.all([
        api.erpGetTiposActivo().catch(() => []),
        api.erpGetActivosFijos().catch(() => []),
      ])
      setTipos(t); setActivos(a)
    } catch {}
    setLoading(false)
  }

  function getItems() {
    return tab === 'tipos' ? tipos : activos
  }

  const filtered = getItems().filter((i: any) =>
    !search || i.nombre?.toLowerCase().includes(search.toLowerCase()) || i.codigo?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate(mode: 'tipo' | 'activo') {
    setFormMode(mode)
    setForm({})
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      if (formMode === 'tipo') {
        const data = await api.erpCrearTipoActivo(form)
        setTipos((prev) => [...prev, data])
      } else {
        const data = await api.erpCrearActivoFijo(form)
        setActivos((prev) => [...prev, data])
      }
      setShowForm(false)
      notify('Creado exitosamente')
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDepreciar(id: string) {
    try {
      await api.erpDepreciarActivo(id)
      const a = await api.erpGetActivosFijos()
      setActivos(a)
      notify('Depreciacion aplicada')
    } catch (err: any) { notify(err.message) }
  }

  async function handleDarBaja(id: string) {
    const causa = prompt('Motivo de baja:')
    if (!causa) return
    try {
      await api.erpDarBajaActivo(id, { motivo: causa })
      setActivos((prev) => prev.map((a) => a.id === id ? { ...a, estado: 'DADO_DE_BAJA' } : a))
      notify('Activo dado de baja')
    } catch (err: any) { notify(err.message) }
  }

  async function verDepreciaciones(id: string) {
    try {
      const deps = await api.erpGetDepreciaciones(id)
      const act = activos.find((a) => a.id === id)
      setSelectedActivo(act)
      setDepreciaciones(deps)
    } catch (err: any) { notify(err.message) }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Activos Fijos</h1>
          <p className="text-sm text-slate-400">Tipos de activo y activos fijos</p>
        </div>
        <div className="flex gap-2">
          {tab === 'tipos' && <button onClick={() => openCreate('tipo')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Tipo</button>}
          {tab === 'activos' && <button onClick={() => openCreate('activo')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Activo</button>}
        </div>
      </div>

      <div className="flex gap-1 bg-slate-800 rounded-lg p-1 w-fit">
        <button onClick={() => setTab('activos')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm ${tab === 'activos' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}>
          <Box className="w-4 h-4" /> Activos
        </button>
        <button onClick={() => setTab('tipos')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm ${tab === 'tipos' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}>
          <Cpu className="w-4 h-4" /> Tipos
        </button>
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar..." />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{formMode === 'tipo' ? 'Nuevo Tipo de Activo' : 'Nuevo Activo Fijo'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
            <input value={form.nombre || ''} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Nombre" />
          </div>
          {formMode === 'activo' && (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Codigo</label>
                <input value={form.codigo || ''} onChange={(e) => setForm({ ...form, codigo: e.target.value })} className="input-filter w-full" placeholder="AF-001" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Costo de Adquisicion *</label>
                <input type="number" step="0.01" value={form.costo || ''} onChange={(e) => setForm({ ...form, costo: e.target.value })} className="input-filter w-full" required placeholder="0.00" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Vida Util (años)</label>
                <input type="number" value={form.vida_util || ''} onChange={(e) => setForm({ ...form, vida_util: e.target.value })} className="input-filter w-full" placeholder="5" />
              </div>
            </>
          )}
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> Crear</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {selectedActivo && (
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Depreciaciones: {selectedActivo.nombre}</h3>
            <button onClick={() => setSelectedActivo(null)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          {depreciaciones.length === 0 ? (
            <p className="text-sm text-slate-400">Sin depreciaciones registradas</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-700/50">
                  <th className="py-2 px-3">Periodo</th>
                  <th className="py-2 px-3 text-right">Monto</th>
                  <th className="py-2 px-3">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {depreciaciones.map((d: any, idx: number) => (
                  <tr key={idx} className="border-b border-slate-700/30">
                    <td className="py-2 px-3 text-white">{d.periodo || d.mes}</td>
                    <td className="py-2 px-3 text-right text-white">C${d.monto?.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-400">{d.fecha || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {loading ? (
        <Skeleton rows={6} />
      ) : filtered.length === 0 ? (
        <EmptyState message={`No hay ${tab} registrados`} />
      ) : tab === 'tipos' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{i.nombre}</span>
              </div>
              {i.vida_util && <p className="text-xs text-slate-400 mt-1">Vida util: {i.vida_util} años</p>}
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Box className="w-4 h-4 text-primary-400" />
                  <span className="text-sm font-semibold text-white">{i.nombre}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    i.estado === 'ACTIVO' ? 'bg-green-900/40 text-green-400' :
                    i.estado === 'DEPRECIADO' ? 'bg-yellow-900/40 text-yellow-400' :
                    'bg-red-900/40 text-red-400'
                  }`}>{i.estado || 'ACTIVO'}</span>
                </div>
                <div className="flex gap-1">
                  <button onClick={() => verDepreciaciones(i.id)} className="p-1 text-slate-500 hover:text-white" title="Ver depreciaciones">
                    <History className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => handleDepreciar(i.id)} className="p-1 text-slate-500 hover:text-green-400" title="Depreciar">
                    <TrendingDown className="w-3.5 h-3.5" />
                  </button>
                  {i.estado !== 'DADO_DE_BAJA' && (
                    <button onClick={() => handleDarBaja(i.id)} className="p-1 text-slate-500 hover:text-red-400" title="Dar de baja">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-2 text-xs">
                <div>
                  <span className="text-slate-400">Costo:</span>
                  <span className="text-white ml-1">C${i.costo?.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-slate-400">Deprec.:</span>
                  <span className="text-white ml-1">C${i.depreciacion_acumulada?.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-slate-400">Neto:</span>
                  <span className="text-white ml-1">C${(i.costo - i.depreciacion_acumulada)?.toFixed(2)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
