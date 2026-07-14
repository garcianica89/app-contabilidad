import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, ShoppingBag, BarChart3, CheckCircle, Ban } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

type Tab = 'pedidos' | 'presupuestos'

export default function ERPPedidosPage() {
  const [tab, setTab] = useState<Tab>('pedidos')
  const [pedidos, setPedidos] = useState<any[]>([])
  const [presupuestos, setPresupuestos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<'pedido' | 'presupuesto'>('pedido')
  const [form, setForm] = useState<any>({})
  const [saving, setSaving] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detalleLines, setDetalleLines] = useState<any[]>([])
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [p, pr] = await Promise.all([
        api.erpGetPedidos().catch(() => []),
        api.erpGetPresupuestos().catch(() => []),
      ])
      setPedidos(p); setPresupuestos(pr)
    } catch {}
    setLoading(false)
  }

  function getItems() {
    return tab === 'pedidos' ? pedidos : presupuestos
  }

  const filtered = getItems().filter((i: any) =>
    !search || i.numero?.toLowerCase().includes(search.toLowerCase()) || i.cliente_nombre?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate(mode: 'pedido' | 'presupuesto') {
    setFormMode(mode)
    setForm({})
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      if (formMode === 'pedido') {
        const data = await api.erpCrearPedido(form)
        setPedidos((prev) => [...prev, data])
      } else {
        const data = await api.erpCrearPresupuesto(form)
        setPresupuestos((prev) => [...prev, data])
      }
      setShowForm(false)
      notify('Creado exitosamente')
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleAprobar(id: string) {
    try {
      if (tab === 'pedidos') {
        await api.erpAprobarPedido(id)
        setPedidos((prev) => prev.map((p) => p.id === id ? { ...p, estado: 'APROBADO' } : p))
      } else {
        await api.erpAprobarPresupuesto(id)
        setPresupuestos((prev) => prev.map((p) => p.id === id ? { ...p, estado: 'APROBADO' } : p))
      }
      notify('Aprobado')
    } catch (err: any) { notify(err.message) }
  }

  async function handleAnular(id: string) {
    if (!confirm('Anular este elemento?')) return
    try {
      await api.erpAnularPedido(id)
      setPedidos((prev) => prev.map((p) => p.id === id ? { ...p, estado: 'ANULADO' } : p))
      notify('Anulado')
    } catch (err: any) { notify(err.message) }
  }

  async function verDetalle(id: string) {
    try {
      const lines = await api.erpGetPedidoLines(id)
      setSelectedId(id)
      setDetalleLines(lines)
    } catch (err: any) { notify(err.message) }
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'pedidos', label: 'Pedidos', icon: ShoppingBag },
    { key: 'presupuestos', label: 'Presupuestos', icon: BarChart3 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Pedidos y Presupuestos</h1>
          <p className="text-sm text-slate-400">Gestion de pedidos y presupuestos</p>
        </div>
        <div className="flex gap-2">
          {tab === 'pedidos' && <button onClick={() => openCreate('pedido')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Pedido</button>}
          {tab === 'presupuestos' && <button onClick={() => openCreate('presupuesto')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Presupuesto</button>}
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
            <h3 className="text-sm font-semibold text-white">{formMode === 'pedido' ? 'Nuevo Pedido' : 'Nuevo Presupuesto'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Cliente ID *</label>
            <input value={form.cliente_id || ''} onChange={(e) => setForm({ ...form, cliente_id: e.target.value })} className="input-filter w-full" required placeholder="ID del cliente" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Total</label>
            <input type="number" step="0.01" value={form.total || ''} onChange={(e) => setForm({ ...form, total: e.target.value })} className="input-filter w-full" placeholder="0.00" />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> Crear</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {selectedId && detalleLines.length > 0 && (
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Lineas del Pedido</h3>
            <button onClick={() => { setSelectedId(null); setDetalleLines([]) }} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-700/50">
                <th className="py-2 px-3">Articulo</th>
                <th className="py-2 px-3 text-right">Cantidad</th>
                <th className="py-2 px-3 text-right">Precio</th>
                <th className="py-2 px-3 text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {detalleLines.map((l: any, idx: number) => (
                <tr key={idx} className="border-b border-slate-700/30">
                  <td className="py-2 px-3 text-white">{l.articulo_nombre || l.articulo_id}</td>
                  <td className="py-2 px-3 text-right text-white">{l.cantidad}</td>
                  <td className="py-2 px-3 text-right text-white">C${l.precio_unitario?.toFixed(2)}</td>
                  <td className="py-2 px-3 text-right text-white">C${l.total?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {loading ? (
        <Skeleton rows={6} />
      ) : filtered.length === 0 ? (
        <EmptyState message={`No hay ${tab} registrados`} />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {tab === 'pedidos' ? <ShoppingBag className="w-4 h-4 text-primary-400" /> : <BarChart3 className="w-4 h-4 text-primary-400" />}
                  <span className="text-sm font-semibold text-white">{i.numero || `#${i.id}`}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    i.estado === 'APROBADO' ? 'bg-green-900/40 text-green-400' :
                    i.estado === 'ANULADO' ? 'bg-red-900/40 text-red-400' :
                    'bg-yellow-900/40 text-yellow-400'
                  }`}>{i.estado || 'PENDIENTE'}</span>
                </div>
                <div className="flex gap-1">
                  {tab === 'pedidos' && (
                    <button onClick={() => verDetalle(i.id)} className="p-1 text-slate-500 hover:text-white" title="Ver detalle">
                      <ShoppingBag className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {i.estado !== 'APROBADO' && i.estado !== 'ANULADO' && (
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
              <p className="text-xs text-slate-400 mt-1">Cliente: {i.cliente_nombre || i.cliente_id}</p>
              <p className="text-sm text-white mt-1">C${i.total?.toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
