import { useState, useEffect } from 'react'
import { Search, FileText, Plus, X, Check, AlertCircle } from 'lucide-react'
import { api } from '../services/api'

interface Factura {
  id: string
  numero: string
  fecha: string
  cliente_id: string
  cliente_nombre?: string
  total: number
  estado: string
  tipo: string
}

interface Cliente {
  id: string
  nombre: string
  codigo: string | null
}

interface Producto {
  id: string
  nombre: string
  precio_venta: number
}

const estados: Record<string, string> = {
  PENDIENTE: 'Pendiente',
  PAGADA: 'Pagada',
  ANULADA: 'Anulada',
  VENCIDA: 'Vencida',
}

export default function FacturacionPage() {
  const [facturas, setFacturas] = useState<Factura[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [productos, setProductos] = useState<Producto[]>([])

  const [form, setForm] = useState({
    numero: '', cliente_id: '', fecha: new Date().toISOString().split('T')[0],
    tipo: 'CONTADO', moneda_id: '', periodo_id: '',
    descuento: 0, iva: 0, fecha_vencimiento: '',
  })
  const [lineas, setLineas] = useState<{ producto_id: string; nombre: string; cantidad: number; precio: number }[]>([])

  useEffect(() => {
    Promise.all([
      api.getFacturas(),
      api.getClientes(),
      api.getProductos(),
    ]).then(([f, c, p]) => {
      setFacturas(f)
      setClientes(c)
      setProductos(p)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const filtered = facturas.filter((f) =>
    !search || f.numero.toLowerCase().includes(search.toLowerCase()) ||
    f.estado.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() {
    setForm({
      numero: `FAC-${Date.now().toString().slice(-6)}`,
      cliente_id: '', fecha: new Date().toISOString().split('T')[0],
      tipo: 'CONTADO', moneda_id: '', periodo_id: '',
      descuento: 0, iva: 0, fecha_vencimiento: '',
    })
    setLineas([{ producto_id: '', nombre: '', cantidad: 1, precio: 0 }])
    setShowForm(true)
  }

  function addLinea() {
    setLineas([...lineas, { producto_id: '', nombre: '', cantidad: 1, precio: 0 }])
  }

  function removeLinea(i: number) {
    setLineas(lineas.filter((_, idx) => idx !== i))
  }

  function updateLinea(i: number, field: string, value: any) {
    const newLineas = [...lineas]
    if (field === 'producto_id') {
      const prod = productos.find((p) => p.id === value)
      newLineas[i] = { ...newLineas[i], producto_id: value, nombre: prod?.nombre || '', precio: prod?.precio_venta || 0 }
    } else {
      newLineas[i] = { ...newLineas[i], [field]: value }
    }
    setLineas(newLineas)
  }

  const subtotal = lineas.reduce((sum, l) => sum + (l.cantidad || 0) * (l.precio || 0), 0)
  const total = subtotal - form.descuento + form.iva

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const factura = await api.crearFactura({
        numero: form.numero,
        cliente_id: form.cliente_id,
        fecha: form.fecha,
        tipo: form.tipo,
        lineas: lineas.map((l) => ({
          producto_id: l.producto_id, cantidad: l.cantidad, precio: l.precio,
        })),
        moneda_id: '00000000-0000-0000-0000-000000000001',
        periodo_id: '00000000-0000-0000-0000-000000000001',
        fecha_vencimiento: form.fecha_vencimiento || null,
        descuento: form.descuento,
        iva: form.iva,
      })
      setFacturas((prev) => [factura, ...prev])
      setShowForm(false)
    } catch (err: any) {
      alert(err.message || 'Error al crear factura')
    }
    setSaving(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Facturacion</h1>
          <p className="text-sm text-slate-400">Facturas de venta a clientes</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Factura
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nueva Factura</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Numero *</label>
              <input value={form.numero} onChange={(e) => setForm({ ...form, numero: e.target.value })} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cliente *</label>
              <select value={form.cliente_id} onChange={(e) => setForm({ ...form, cliente_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar cliente</option>
                {clientes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha</label>
              <input type="date" value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-filter w-full">
                <option value="CONTADO">Contado</option>
                <option value="CREDITO">Credito</option>
              </select>
            </div>
            {form.tipo === 'CREDITO' && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">Vencimiento</label>
                <input type="date" value={form.fecha_vencimiento} onChange={(e) => setForm({ ...form, fecha_vencimiento: e.target.value })} className="input-filter w-full" />
              </div>
            )}
          </div>

          <div className="border-t border-slate-700/50 pt-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-white">Lineas</span>
              <button type="button" onClick={addLinea} className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1">
                <Plus className="w-3 h-3" /> Agregar linea
              </button>
            </div>
            <div className="space-y-2">
              {lineas.map((l, i) => (
                <div key={i} className="grid grid-cols-12 gap-2 items-end">
                  <div className="col-span-6">
                    <select value={l.producto_id} onChange={(e) => updateLinea(i, 'producto_id', e.target.value)}
                      className="input-filter w-full text-xs">
                      <option value="">Seleccionar producto</option>
                      {productos.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <input type="number" step="0.01" value={l.cantidad} onChange={(e) => updateLinea(i, 'cantidad', Number(e.target.value))}
                      className="input-filter w-full text-xs" placeholder="Cant" />
                  </div>
                  <div className="col-span-2">
                    <input type="number" step="0.01" value={l.precio} onChange={(e) => updateLinea(i, 'precio', Number(e.target.value))}
                      className="input-filter w-full text-xs" placeholder="Precio" />
                  </div>
                  <div className="col-span-1 text-right text-xs text-slate-400 py-2">
                    C$ {(l.cantidad * l.precio).toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                  </div>
                  <div className="col-span-1 text-center">
                    {lineas.length > 1 && (
                      <button type="button" onClick={() => removeLinea(i)} className="text-red-400 hover:text-red-300">
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-700/50 pt-4 flex flex-col items-end space-y-1 text-sm">
            <div className="flex gap-8">
              <span className="text-slate-400">Subtotal:</span>
              <span className="text-white font-mono w-28 text-right">C$ {subtotal.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex gap-8">
              <span className="text-slate-400">Descuento:</span>
              <input type="number" step="0.01" value={form.descuento}
                onChange={(e) => setForm({ ...form, descuento: Number(e.target.value) })}
                className="input-filter w-28 text-right text-xs" />
            </div>
            <div className="flex gap-8">
              <span className="text-slate-400">IVA:</span>
              <input type="number" step="0.01" value={form.iva}
                onChange={(e) => setForm({ ...form, iva: Number(e.target.value) })}
                className="input-filter w-28 text-right text-xs" />
            </div>
            <div className="flex gap-8 text-base font-bold">
              <span className="text-white">Total:</span>
              <span className="text-emerald-400 font-mono w-28 text-right">
                C$ {total.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> Crear Factura</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar factura..." />
        </div>
        <span className="text-xs text-slate-500">{filtered.length} registros</span>
      </div>

      {loading ? (
        <div className="card animate-pulse space-y-3">
          {[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-slate-700/50 rounded" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-12 text-slate-500">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
          {search ? 'Ninguna factura coincide con la busqueda' : 'No hay facturas registradas'}
        </div>
      ) : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Numero</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Cliente</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Fecha</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Tipo</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Total</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filtered.map((f) => (
                  <tr key={f.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3"><span className="text-white font-mono text-xs font-medium">{f.numero}</span></td>
                    <td className="px-4 py-3"><span className="text-slate-300">{f.cliente_nombre || f.cliente_id.slice(0, 8)}</span></td>
                    <td className="px-4 py-3 text-center text-slate-400">{f.fecha}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded ${f.tipo === 'CREDITO' ? 'bg-amber-600/20 text-amber-400' : 'bg-slate-600/20 text-slate-400'}`}>
                        {f.tipo}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-white">
                      C$ {f.total.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                        f.estado === 'PAGADA' ? 'bg-emerald-600/20 text-emerald-400' :
                        f.estado === 'VENCIDA' ? 'bg-red-600/20 text-red-400' :
                        f.estado === 'ANULADA' ? 'bg-slate-600/20 text-slate-400' :
                        'bg-amber-600/20 text-amber-400'
                      }`}>
                        {estados[f.estado] || f.estado}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}