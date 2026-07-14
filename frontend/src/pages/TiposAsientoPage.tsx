import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, Trash2, BookOpen } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'

export default function TiposAsientoPage() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({
    code: '', name: '', module: '', nature: 'DIARIO',
    affects_inventory: false, affects_receivable: false, affects_payable: false,
    affects_cash: false, affects_bank: false, requires_approval: false,
    approval_max_amount: null as number | null, is_active: true,
  })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { setItems(await api.getTiposAsiento()) } catch {}
    setLoading(false)
  }

  const filtered = items.filter((i) =>
    !search || i.code.toLowerCase().includes(search.toLowerCase()) ||
    i.name.toLowerCase().includes(search.toLowerCase()) ||
    (i.module || '').toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() {
    setEditId(null)
    setForm({ code: '', name: '', module: '', nature: 'DIARIO', affects_inventory: false, affects_receivable: false, affects_payable: false, affects_cash: false, affects_bank: false, requires_approval: false, approval_max_amount: null, is_active: true })
    setShowForm(true)
  }

  function openEdit(i: any) {
    setEditId(i.id)
    setForm({ code: i.code, name: i.name, module: i.module || '', nature: i.nature, affects_inventory: i.affects_inventory, affects_receivable: i.affects_receivable, affects_payable: i.affects_payable, affects_cash: i.affects_cash, affects_bank: i.affects_bank, requires_approval: i.requires_approval, approval_max_amount: i.approval_max_amount, is_active: i.is_active })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { ...form, approval_max_amount: form.approval_max_amount || null, module: form.module || null }
      const data = editId ? await api.actualizarTipoAsiento(editId, payload) : await api.crearTipoAsiento(payload)
      setItems((prev) => editId ? prev.map((i) => (i.id === editId ? data : i)) : [...prev, data])
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDelete(id: string) {
    if (!confirm('Eliminar tipo de asiento?')) return
    try { await api.eliminarTipoAsiento(id); setItems((prev) => prev.filter((i) => i.id !== id)) }
    catch (err: any) { notify(err.message) }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Tipos de Asiento</h1>
          <p className="text-sm text-slate-400">Configuracion de tipos de asiento contable</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo Tipo
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar' : 'Nuevo'} Tipo de Asiento</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
              <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} className="input-filter w-full" required placeholder="VENTA" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-filter w-full" required placeholder="Asiento de Venta" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Modulo</label>
              <input value={form.module} onChange={(e) => setForm({ ...form, module: e.target.value })} className="input-filter w-full" placeholder="CXC" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Naturaleza</label>
              <select value={form.nature} onChange={(e) => setForm({ ...form, nature: e.target.value })} className="input-filter w-full">
                <option value="DIARIO">Diario</option>
                <option value="APERTURA">Apertura</option>
                <option value="CIERRE">Cierre</option>
                <option value="AJUSTE">Ajuste</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Monto Max. Aprobacion</label>
              <input type="number" step="0.01" value={form.approval_max_amount || ''} onChange={(e) => setForm({ ...form, approval_max_amount: e.target.value ? Number(e.target.value) : null })} className="input-filter w-full" />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {([
              ['affects_inventory', 'Afecta Inventario'],
              ['affects_receivable', 'Afecta Cobrar'],
              ['affects_payable', 'Afecta Pagar'],
              ['affects_cash', 'Afecta Caja'],
              ['affects_bank', 'Afecta Bancos'],
              ['requires_approval', 'Requiere Aprobacion'],
            ] as [string, string][]).map(([key, label]) => (
              <label key={key} className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={(form as any)[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
                  className="rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500" />
                <span className="text-xs text-slate-400">{label}</span>
              </label>
            ))}
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar tipo de asiento..." />
      </div>

      {loading ? <Skeleton /> : filtered.length === 0 ? <EmptyState message="No hay tipos de asiento registrados" /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i) => (
            <div key={i.id} className="card relative">
              <div className="absolute top-3 right-3 flex gap-1">
                <button onClick={() => openEdit(i)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                <button onClick={() => handleDelete(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <BookOpen className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-bold text-white">{i.code}</span>
              </div>
              <div className="text-sm text-slate-300">{i.name}</div>
              {i.module && <div className="text-xs text-slate-500 mt-1">Modulo: {i.module}</div>}
              <div className="flex flex-wrap gap-1.5 mt-2">
                <span className="text-xs px-2 py-0.5 rounded bg-slate-700/50 text-slate-400">{i.nature}</span>
                {i.affects_inventory && <span className="text-xs px-2 py-0.5 rounded bg-emerald-600/20 text-emerald-400">Inv</span>}
                {i.affects_receivable && <span className="text-xs px-2 py-0.5 rounded bg-blue-600/20 text-blue-400">Cobrar</span>}
                {i.affects_payable && <span className="text-xs px-2 py-0.5 rounded bg-orange-600/20 text-orange-400">Pagar</span>}
                {i.affects_cash && <span className="text-xs px-2 py-0.5 rounded bg-yellow-600/20 text-yellow-400">Caja</span>}
                {i.affects_bank && <span className="text-xs px-2 py-0.5 rounded bg-purple-600/20 text-purple-400">Bcos</span>}
                {!i.is_active && <span className="text-xs px-2 py-0.5 rounded bg-red-600/20 text-red-400">Inactivo</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


