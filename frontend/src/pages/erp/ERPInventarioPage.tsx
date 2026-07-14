import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, Package, Warehouse, BarChart3 } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

type Tab = 'articulos' | 'bodegas' | 'existencias'

export default function ERPInventarioPage() {
  const [tab, setTab] = useState<Tab>('articulos')
  const [articulos, setArticulos] = useState<any[]>([])
  const [bodegas, setBodegas] = useState<any[]>([])
  const [existencias, setExistencias] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formType, setFormType] = useState<'articulo' | 'bodega'>('articulo')
  const [form, setForm] = useState({ codigo: '', nombre: '', unidad_medida: 'UNIDAD' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [art, bod, ex] = await Promise.all([
        api.erpGetArticulos().catch(() => []),
        api.erpGetBodegas().catch(() => []),
        api.erpGetExistencias().catch(() => []),
      ])
      setArticulos(art); setBodegas(bod); setExistencias(ex)
    } catch {}
    setLoading(false)
  }

  function getItems() {
    if (tab === 'articulos') return articulos
    if (tab === 'bodegas') return bodegas
    return existencias
  }

  const filtered = getItems().filter((i: any) =>
    !search || i.nombre?.toLowerCase().includes(search.toLowerCase()) || i.codigo?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate(type: 'articulo' | 'bodega') {
    setFormType(type)
    setForm(type === 'articulo' ? { codigo: '', nombre: '', unidad_medida: 'UNIDAD' } : { codigo: '', nombre: '', unidad_medida: '' })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      if (formType === 'articulo') {
        const data = await api.erpCrearArticulo(form)
        setArticulos((prev) => [...prev, data])
      } else {
        const data = await api.erpCrearBodega(form)
        setBodegas((prev) => [...prev, data])
      }
      setShowForm(false)
      notify(`${formType === 'articulo' ? 'Articulo' : 'Bodega'} creado`)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'articulos', label: 'Articulos', icon: Package },
    { key: 'bodegas', label: 'Bodegas', icon: Warehouse },
    { key: 'existencias', label: 'Existencias', icon: BarChart3 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Inventario</h1>
          <p className="text-sm text-slate-400">Articulos, bodegas y existencias</p>
        </div>
        {tab !== 'existencias' && (
          <button onClick={() => openCreate(tab === 'articulos' ? 'articulo' : 'bodega')} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Nuevo {tab === 'articulos' ? 'Articulo' : 'Bodega'}
          </button>
        )}
      </div>

      <div className="flex gap-1 bg-slate-800 rounded-lg p-1 w-fit">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm ${tab === t.key ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder={`Buscar ${tab}...`} />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nuevo {formType === 'articulo' ? 'Articulo' : 'Bodega'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
            <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} className="input-filter w-full" required placeholder="ART-001" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
            <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Nombre" />
          </div>
          {formType === 'articulo' && (
            <div>
              <label className="block text-xs text-slate-400 mb-1">Unidad de Medida</label>
              <input value={form.unidad_medida} onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })} className="input-filter w-full" placeholder="UNIDAD" />
            </div>
          )}
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> Crear</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <Skeleton rows={6} />
      ) : filtered.length === 0 ? (
        <EmptyState message={`No hay ${tab} registrados`} />
      ) : tab === 'existencias' ? (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-700/50">
                <th className="py-2 px-3">Articulo</th>
                <th className="py-2 px-3">Bodega</th>
                <th className="py-2 px-3 text-right">Cantidad</th>
                <th className="py-2 px-3 text-right">Costo</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((i: any, idx: number) => (
                <tr key={idx} className="border-b border-slate-700/30 hover:bg-slate-700/20">
                  <td className="py-2 px-3 text-white">{i.articulo_nombre || i.articulo_id}</td>
                  <td className="py-2 px-3 text-slate-300">{i.bodega_nombre || i.bodega_id}</td>
                  <td className="py-2 px-3 text-right text-white">{i.cantidad}</td>
                  <td className="py-2 px-3 text-right text-white">{i.costo?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center gap-2 mb-1">
                {tab === 'articulos' ? <Package className="w-4 h-4 text-primary-400" /> : <Warehouse className="w-4 h-4 text-primary-400" />}
                <span className="text-sm font-semibold text-white">{i.nombre}</span>
              </div>
              <p className="text-xs text-slate-500 font-mono">{i.codigo}</p>
              {i.unidad_medida && <p className="text-xs text-slate-400 mt-1">UM: {i.unidad_medida}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
