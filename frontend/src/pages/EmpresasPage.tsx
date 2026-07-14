import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, Globe, Trash2 } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'

export default function EmpresasPage() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ nombre: '', ruc: '', direccion: '', telefono: '', email: '', moneda_base: 'C$' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { setItems(await api.getEmpresas()) } catch {}
    setLoading(false)
  }

  const filtered = items.filter((i) =>
    !search || i.nombre?.toLowerCase().includes(search.toLowerCase()) ||
    i.ruc?.toLowerCase().includes(search.toLowerCase())
  )

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const data = await api.crearEmpresa(form)
      setItems((prev) => [...prev, data])
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Empresas</h1>
          <p className="text-sm text-slate-400">Gestion de empresas del grupo</p>
        </div>
        <button onClick={() => { setShowForm(true); setForm({ nombre: '', ruc: '', direccion: '', telefono: '', email: '', moneda_base: 'C$' }) }}
          className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Empresa
        </button>
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar empresa..." />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nueva Empresa</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Tuckler Beauty" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">RUC</label>
              <input value={form.ruc} onChange={(e) => setForm({ ...form, ruc: e.target.value })} className="input-filter w-full" placeholder="J000000000" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Direccion</label>
              <input value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} className="input-filter w-full" placeholder="Managua, Nicaragua" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Telefono</label>
              <input value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className="input-filter w-full" placeholder="+505 0000 0000" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-filter w-full" placeholder="info@tuckler.com" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Moneda Base</label>
              <input value={form.moneda_base} onChange={(e) => setForm({ ...form, moneda_base: e.target.value })} className="input-filter w-full" placeholder="C$" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> Crear Empresa</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
<Skeleton rows={3} barHeight="h-20" />
      ) : filtered.length === 0 ? (
        <EmptyState message="No hay empresas registradas" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((e) => (
            <div key={e.id} className="card">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary-400" />
                  <span className="text-sm font-semibold text-white">{e.nombre}</span>
                </div>
              </div>
              {e.ruc && <div className="text-xs text-slate-500 font-mono">RUC: {e.ruc}</div>}
              {e.direccion && <div className="text-xs text-slate-500 mt-1">{e.direccion}</div>}
              {e.email && <div className="text-xs text-slate-500 mt-1">{e.email}</div>}
              <div className="text-xs text-slate-500 mt-1">{e.telefono || ''}</div>
              {e.moneda_base && <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded bg-emerald-600/20 text-emerald-400">Moneda: {e.moneda_base}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
