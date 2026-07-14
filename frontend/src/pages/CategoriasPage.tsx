import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, BookOpen, Trash2 } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'

export default function CategoriasPage() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({ nombre: '' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { setItems(await api.getCategorias()) } catch {}
    setLoading(false)
  }

  const filtered = items.filter((i) =>
    !search || i.nombre?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() { setEditId(null); setForm({ nombre: '' }); setShowForm(true) }
  function openEdit(i: any) { setEditId(i.id); setForm({ nombre: i.nombre }); setShowForm(true) }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const catId = editId
      if (catId) {
        const data = await api.actualizarCategoria(catId, form)
        setItems((prev) => prev.map((i) => (i.id === catId ? data : i)))
      } else {
        const data = await api.crearCategoria(form)
        setItems((prev) => [...prev, data])
      }
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDelete(id: string) {
    if (!confirm('Eliminar categoria?')) return
    try {
      await api.eliminarCategoria(id)
      setItems((prev) => prev.filter((i) => i.id !== id))
    } catch (err: any) { notify(err.message) }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Categorias</h1>
          <p className="text-sm text-slate-400">Categorias de productos</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Categoria
        </button>
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar categoria..." />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar Categoria' : 'Nueva Categoria'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
            <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Cosmeticos" />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
<Skeleton />
      ) : filtered.length === 0 ? (
        <EmptyState message="No hay categorias registradas" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i) => (
            <div key={i.id} className="card relative">
              <div className="absolute top-3 right-3 flex gap-1">
                <button onClick={() => openEdit(i)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                <button onClick={() => handleDelete(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
              </div>
              <div className="flex items-center gap-2 mb-1">
                <BookOpen className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{i.nombre}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
