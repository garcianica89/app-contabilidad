import { useState, useEffect } from 'react'
import { Plus, X, Search, Edit2, Trash2 } from 'lucide-react'
import { useNotification } from '../contexts/NotificationContext'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { api } from '../services/api'
import type { TipoCuentaBanco } from '../types/api'

export default function TiposCuentaBancoPage() {
  const [items, setItems] = useState<TipoCuentaBanco[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [filter, setFilter] = useState('')
  const [form, setForm] = useState({ codigo: '', nombre: '' })
  const { notify } = useNotification()

  const loadData = async () => {
    setLoading(true)
    try {
      const data = await api.getTiposCuentaBanco()
      setItems(data)
    } catch { notify('Error al cargar tipos de cuenta', 'error') }
    finally { setLoading(false) }
  }

  useEffect(() => { loadData() }, [])

  const resetForm = () => { setForm({ codigo: '', nombre: '' }); setEditId(null); setShowForm(false) }

  const openEdit = (t: TipoCuentaBanco) => {
    setForm({ codigo: t.codigo, nombre: t.nombre })
    setEditId(t.id)
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.codigo || !form.nombre) return notify('Codigo y nombre requeridos', 'error')
    setSaving(true)
    try {
      if (editId) {
        await api.actualizarTipoCuentaBanco(editId, form)
        notify('Tipo actualizado', 'success')
      } else {
        await api.crearTipoCuentaBanco(form)
        notify('Tipo creado', 'success')
      }
      resetForm()
      await loadData()
    } catch { notify('Error al guardar', 'error') }
    finally { setSaving(false) }
  }

  const handleToggleActivo = async (t: TipoCuentaBanco) => {
    try {
      await api.actualizarTipoCuentaBanco(t.id, { activo: !t.activo })
      notify(t.activo ? 'Desactivado' : 'Activado', 'success')
      await loadData()
    } catch { notify('Error al actualizar', 'error') }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Eliminar este tipo de cuenta?')) return
    try {
      await api.eliminarTipoCuentaBanco(id)
      notify('Eliminado', 'success')
      await loadData()
    } catch { notify('Error al eliminar', 'error') }
  }

  const filtered = items.filter(t =>
    t.codigo.toLowerCase().includes(filter.toLowerCase()) ||
    t.nombre.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Tipos de Cuenta Bancaria</h1>
        <button className="btn-primary flex items-center gap-2" onClick={() => { resetForm(); setShowForm(true) }}>
          <Plus size={18} /> Nuevo Tipo
        </button>
      </div>

      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input className="input-filter pl-10" placeholder="Buscar..." value={filter} onChange={e => setFilter(e.target.value)} />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">{editId ? 'Editar' : 'Nuevo'} Tipo de Cuenta</h3>
            <button type="button" onClick={resetForm}><X size={18} /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Codigo</label>
              <input className="input" value={form.codigo} onChange={e => setForm({ ...form, codigo: e.target.value.toUpperCase() })} required maxLength={20} />
            </div>
            <div>
              <label className="label">Nombre</label>
              <input className="input" value={form.nombre} onChange={e => setForm({ ...form, nombre: e.target.value })} required maxLength={100} />
            </div>
          </div>
          <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando...' : 'Guardar'}</button>
        </form>
      )}

      {loading ? <Skeleton rows={5} /> : filtered.length === 0 ? (
        <EmptyState message={filter ? 'Sin resultados' : 'No hay tipos de cuenta'} />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="p-3 font-medium">Codigo</th>
                <th className="p-3 font-medium">Nombre</th>
                <th className="p-3 font-medium">Estado</th>
                <th className="p-3 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map(t => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="p-3 font-mono font-medium">{t.codigo}</td>
                  <td className="p-3">{t.nombre}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${t.activo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {t.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="p-3 text-right space-x-2">
                    <button className="btn-icon" onClick={() => openEdit(t)} title="Editar"><Edit2 size={16} /></button>
                    <button className="btn-icon" onClick={() => handleToggleActivo(t)} title={t.activo ? 'Desactivar' : 'Activar'}><Trash2 size={16} /></button>
                    <button className="btn-icon text-red-500" onClick={() => handleDelete(t.id)} title="Eliminar"><X size={16} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
