import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, Truck, ShoppingCart, FileText, CheckCircle, Ban } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

type Tab = 'proveedores' | 'ordenes' | 'documentos'

export default function ERPComprasPage() {
  const [tab, setTab] = useState<Tab>('proveedores')
  const [proveedores, setProveedores] = useState<any[]>([])
  const [ordenes, setOrdenes] = useState<any[]>([])
  const [documentos, setDocumentos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<'proveedor' | 'orden' | 'documento'>('proveedor')
  const [form, setForm] = useState<any>({})
  const [saving, setSaving] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [p, o, d] = await Promise.all([
        api.erpGetProveedores().catch(() => []),
        api.erpGetOrdenesCompra().catch(() => []),
        api.erpGetDocumentosCP().catch(() => []),
      ])
      setProveedores(p); setOrdenes(o); setDocumentos(d)
    } catch {}
    setLoading(false)
  }

  function getItems() {
    if (tab === 'proveedores') return proveedores
    if (tab === 'ordenes') return ordenes
    return documentos
  }

  const filtered = getItems().filter((i: any) =>
    !search || i.nombre?.toLowerCase().includes(search.toLowerCase()) || i.numero?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate(mode: 'proveedor' | 'orden' | 'documento') {
    setFormMode(mode)
    setForm({})
    setEditId(null)
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      if (formMode === 'proveedor') {
        const data = await api.erpCrearProveedor(form)
        setProveedores((prev) => [...prev, data])
      } else if (formMode === 'orden') {
        const data = await api.erpCrearOrdenCompra(form)
        setOrdenes((prev) => [...prev, data])
      } else {
        const data = await api.erpCrearDocumentoCP(form)
        setDocumentos((prev) => [...prev, data])
      }
      setShowForm(false)
      notify('Creado exitosamente')
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleAprobar(id: string) {
    try {
      await api.erpAprobarOrdenCompra(id)
      setOrdenes((prev) => prev.map((o) => o.id === id ? { ...o, estado: 'APROBADA' } : o))
      notify('Orden aprobada')
    } catch (err: any) { notify(err.message) }
  }

  async function handleAnular(id: string) {
    if (!confirm('Anular esta orden de compra?')) return
    try {
      await api.erpAnularOrdenCompra(id)
      setOrdenes((prev) => prev.map((o) => o.id === id ? { ...o, estado: 'ANULADA' } : o))
      notify('Orden anulada')
    } catch (err: any) { notify(err.message) }
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'proveedores', label: 'Proveedores', icon: Truck },
    { key: 'ordenes', label: 'Ordenes de Compra', icon: ShoppingCart },
    { key: 'documentos', label: 'Documentos CP', icon: FileText },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Compras</h1>
          <p className="text-sm text-slate-400">Proveedores, ordenes de compra y documentos</p>
        </div>
        <div className="flex gap-2">
          {tab === 'proveedores' && <button onClick={() => openCreate('proveedor')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Proveedor</button>}
          {tab === 'ordenes' && <button onClick={() => openCreate('orden')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nueva Orden</button>}
          {tab === 'documentos' && <button onClick={() => openCreate('documento')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Documento</button>}
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
              {formMode === 'proveedor' ? 'Nuevo Proveedor' : formMode === 'orden' ? 'Nueva Orden de Compra' : 'Nuevo Documento CP'}
            </h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          {formMode === 'proveedor' && (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
                <input value={form.nombre || ''} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Proveedor" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">RUC</label>
                <input value={form.ruc || ''} onChange={(e) => setForm({ ...form, ruc: e.target.value })} className="input-filter w-full" placeholder="J123456789" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Contacto</label>
                <input value={form.contacto || ''} onChange={(e) => setForm({ ...form, contacto: e.target.value })} className="input-filter w-full" placeholder="Nombre contacto" />
              </div>
            </>
          )}
          {formMode === 'orden' && (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Proveedor ID *</label>
                <input value={form.proveedor_id || ''} onChange={(e) => setForm({ ...form, proveedor_id: e.target.value })} className="input-filter w-full" required placeholder="ID del proveedor" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Total Estimado</label>
                <input type="number" step="0.01" value={form.total || ''} onChange={(e) => setForm({ ...form, total: e.target.value })} className="input-filter w-full" placeholder="0.00" />
              </div>
            </>
          )}
          {formMode === 'documento' && (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Proveedor ID *</label>
                <input value={form.proveedor_id || ''} onChange={(e) => setForm({ ...form, proveedor_id: e.target.value })} className="input-filter w-full" required placeholder="ID del proveedor" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Monto *</label>
                <input type="number" step="0.01" value={form.monto || ''} onChange={(e) => setForm({ ...form, monto: e.target.value })} className="input-filter w-full" required placeholder="0.00" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Tipo</label>
                <select value={form.tipo || 'FACTURA'} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-filter w-full">
                  <option value="FACTURA">Factura</option>
                  <option value="NOTA_DEBITO">Nota de Debito</option>
                  <option value="NOTA_CREDITO">Nota de Credito</option>
                </select>
              </div>
            </>
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
      ) : tab === 'proveedores' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center gap-2 mb-1">
                <Truck className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{i.nombre}</span>
              </div>
              {i.ruc && <p className="text-xs text-slate-400">{i.ruc}</p>}
              {i.contacto && <p className="text-xs text-slate-400">{i.contacto}</p>}
            </div>
          ))}
        </div>
      ) : tab === 'ordenes' ? (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShoppingCart className="w-4 h-4 text-primary-400" />
                  <span className="text-sm font-semibold text-white">Orden #{i.numero || i.id}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    i.estado === 'APROBADA' ? 'bg-green-900/40 text-green-400' :
                    i.estado === 'ANULADA' ? 'bg-red-900/40 text-red-400' :
                    'bg-yellow-900/40 text-yellow-400'
                  }`}>{i.estado || 'PENDIENTE'}</span>
                </div>
                <div className="flex gap-1">
                  {i.estado !== 'APROBADA' && i.estado !== 'ANULADA' && (
                    <>
                      <button onClick={() => handleAprobar(i.id)} className="p-1 text-slate-500 hover:text-green-400" title="Aprobar">
                        <CheckCircle className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleAnular(i.id)} className="p-1 text-slate-500 hover:text-red-400" title="Anular">
                        <Ban className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>
              <p className="text-xs text-slate-400 mt-1">Proveedor: {i.proveedor_nombre || i.proveedor_id}</p>
              <p className="text-sm text-white mt-1">C${i.total?.toFixed(2)}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center gap-2 mb-1">
                <FileText className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{i.tipo || 'Documento'}</span>
              </div>
              <p className="text-xs text-slate-400">Proveedor: {i.proveedor_nombre || i.proveedor_id}</p>
              <p className="text-sm text-white mt-1">C${i.monto?.toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
