import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, Users, FileText, Receipt } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

type Tab = 'clientes' | 'facturas'

export default function ERPFacturacionPage() {
  const [tab, setTab] = useState<Tab>('clientes')
  const [clientes, setClientes] = useState<any[]>([])
  const [facturas, setFacturas] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<'cliente' | 'factura'>('cliente')
  const [form, setForm] = useState<any>({})
  const [saving, setSaving] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [c, f] = await Promise.all([
        api.erpGetClientes().catch(() => []),
        api.erpGetFacturas().catch(() => []),
      ])
      setClientes(c); setFacturas(f)
    } catch {}
    setLoading(false)
  }

  function getItems() {
    return tab === 'clientes' ? clientes : facturas
  }

  const filtered = getItems().filter((i: any) =>
    !search || i.nombre?.toLowerCase().includes(search.toLowerCase()) || i.numero?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate(mode: 'cliente' | 'factura') {
    setFormMode(mode)
    setForm({})
    setEditId(null)
    setShowForm(true)
  }

  function openEdit(i: any) {
    setFormMode('cliente')
    setEditId(i.id)
    setForm({ nombre: i.nombre, email: i.email || '', telefono: i.telefono || '', direccion: i.direccion || '', ruc: i.ruc || '' })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      if (formMode === 'cliente') {
        if (editId) {
          const data = await api.erpActualizarCliente(editId, form)
          setClientes((prev) => prev.map((c) => (c.id === editId ? data : c)))
        } else {
          const data = await api.erpCrearCliente(form)
          setClientes((prev) => [...prev, data])
        }
      } else {
        const data = await api.erpCrearFactura(form)
        setFacturas((prev) => [...prev, data])
      }
      setShowForm(false)
      notify(editId ? 'Actualizado' : 'Creado exitosamente')
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'clientes', label: 'Clientes', icon: Users },
    { key: 'facturas', label: 'Facturas', icon: Receipt },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Facturación</h1>
          <p className="text-sm text-slate-400">Clientes y facturas de venta</p>
        </div>
        <div className="flex gap-2">
          {tab === 'clientes' && <button onClick={() => openCreate('cliente')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Cliente</button>}
          {tab === 'facturas' && <button onClick={() => openCreate('factura')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nueva Factura</button>}
        </div>
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
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar..." />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">
              {formMode === 'cliente' ? (editId ? 'Editar Cliente' : 'Nuevo Cliente') : 'Nueva Factura'}
            </h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          {formMode === 'cliente' ? (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
                <input value={form.nombre || ''} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Cliente" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">RUC</label>
                  <input value={form.ruc || ''} onChange={(e) => setForm({ ...form, ruc: e.target.value })} className="input-filter w-full" placeholder="J123456789" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Telefono</label>
                  <input value={form.telefono || ''} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className="input-filter w-full" placeholder="8888-8888" />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Email</label>
                <input type="email" value={form.email || ''} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-filter w-full" placeholder="correo@ejemplo.com" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Direccion</label>
                <textarea value={form.direccion || ''} onChange={(e) => setForm({ ...form, direccion: e.target.value })} className="input-filter w-full" rows={2} />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Cliente ID *</label>
                <input value={form.cliente_id || ''} onChange={(e) => setForm({ ...form, cliente_id: e.target.value })} className="input-filter w-full" required placeholder="ID del cliente" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Monto Total *</label>
                <input type="number" step="0.01" value={form.total || ''} onChange={(e) => setForm({ ...form, total: e.target.value })} className="input-filter w-full" required placeholder="0.00" />
              </div>
            </>
          )}
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <Skeleton rows={6} />
      ) : filtered.length === 0 ? (
        <EmptyState message={`No hay ${tab} registrados`} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card relative">
              {tab === 'clientes' && (
                <div className="absolute top-3 right-3 flex gap-1">
                  <button onClick={() => openEdit(i)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                </div>
              )}
              <div className="flex items-center gap-2 mb-1">
                {tab === 'clientes' ? <Users className="w-4 h-4 text-primary-400" /> : <FileText className="w-4 h-4 text-primary-400" />}
                <span className="text-sm font-semibold text-white">{i.nombre || i.numero || `Factura #${i.id}`}</span>
              </div>
              {tab === 'clientes' ? (
                <>
                  {i.ruc && <p className="text-xs text-slate-400">{i.ruc}</p>}
                  {i.email && <p className="text-xs text-slate-400">{i.email}</p>}
                  {i.telefono && <p className="text-xs text-slate-400">{i.telefono}</p>}
                </>
              ) : (
                <>
                  <p className="text-xs text-slate-400">Cliente: {i.cliente_nombre || i.cliente_id}</p>
                  <p className="text-sm text-white mt-1">C${i.total?.toFixed(2)}</p>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
