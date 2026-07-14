import { useState, useEffect } from 'react'
import { Search, Database, Pencil, X, Check, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import type { Producto, CuentaContable } from '../types/api'

const emptyForm = {
  codigo: '', nombre: '', unidad_medida: 'UNIDAD',
  precio_venta: 0, stock_minimo: 0, aplica_iva: true,
  cuenta_compra_id: '', cuenta_venta_id: '', cuenta_inventario_id: '',
}

export default function InventarioPage() {
  const [items, setItems] = useState<Producto[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [cuentas, setCuentas] = useState<CuentaContable[]>([])

  useEffect(() => {
    Promise.all([
      api.getProductos(),
      api.getCuentasContables(),
    ]).then(([prods, cts]) => {
      setItems(prods)
      setCuentas(cts.filter(c => c.acepta_datos))
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const filtered = items.filter((c) =>
    !search || c.nombre.toLowerCase().includes(search.toLowerCase()) ||
    (c.codigo && c.codigo.toLowerCase().includes(search.toLowerCase()))
  )

  function openCreate() { setEditId(null); setForm(emptyForm); setShowForm(true) }

  function openEdit(c: Producto) {
    setEditId(c.id)
    setForm({
      codigo: c.codigo || '', nombre: c.nombre,
      unidad_medida: c.unidad_medida || 'UNIDAD',
      precio_venta: c.precio_venta, stock_minimo: c.stock_minimo,
      aplica_iva: c.aplica_iva,
      cuenta_compra_id: c.cuenta_compra_id || '',
      cuenta_venta_id: c.cuenta_venta_id || '',
      cuenta_inventario_id: c.cuenta_inventario_id || '',
    })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { ...form }
      if (!payload.codigo) delete (payload as any).codigo
      const updated = editId
        ? await api.actualizarProducto(editId, payload)
        : await api.crearProducto(payload)
      setItems((prev) => editId ? prev.map((c) => (c.id === editId ? updated : c)) : [...prev, updated])
      setShowForm(false)
    } catch {}
    setSaving(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Inventario</h1>
          <p className="text-sm text-slate-400">Gestion de productos y servicios</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Database className="w-4 h-4" /> Nuevo Producto
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar Producto' : 'Nuevo Producto'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo</label>
              <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} className="input-filter w-full" placeholder="PROD-001" />
            </div>
            <div className="lg:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Nombre del producto" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Unidad Medida</label>
              <select value={form.unidad_medida} onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })} className="input-filter w-full">
                <option value="UNIDAD">Unidad</option>
                <option value="CAJA">Caja</option>
                <option value="KG">Kilogramo</option>
                <option value="LTS">Litros</option>
                <option value="MTS">Metros</option>
                <option value="SERVICIO">Servicio</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Precio Venta (C$)</label>
              <input type="number" step="0.01" value={form.precio_venta} onChange={(e) => setForm({ ...form, precio_venta: Number(e.target.value) })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Stock Minimo</label>
              <input type="number" step="0.01" value={form.stock_minimo} onChange={(e) => setForm({ ...form, stock_minimo: Number(e.target.value) })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">IVA</label>
              <label className="flex items-center gap-1.5 text-xs text-slate-300 mt-1">
                <input type="checkbox" checked={form.aplica_iva} onChange={(e) => setForm({ ...form, aplica_iva: e.target.checked })} className="rounded border-slate-600 bg-slate-700 text-primary-500" />
                Aplica IVA
              </label>
            </div>
          </div>
          <div className="border-t border-slate-700/50 pt-4">
            <h4 className="text-xs font-semibold text-slate-400 uppercase mb-3">Cuentas Contables</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Cuenta Compra</label>
                <select value={form.cuenta_compra_id} onChange={(e) => setForm({ ...form, cuenta_compra_id: e.target.value })} className="input-filter w-full text-xs">
                  <option value="">Sin asignar</option>
                  {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Cuenta Venta</label>
                <select value={form.cuenta_venta_id} onChange={(e) => setForm({ ...form, cuenta_venta_id: e.target.value })} className="input-filter w-full text-xs">
                  <option value="">Sin asignar</option>
                  {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Cuenta Inventario</label>
                <select value={form.cuenta_inventario_id} onChange={(e) => setForm({ ...form, cuenta_inventario_id: e.target.value })} className="input-filter w-full text-xs">
                  <option value="">Sin asignar</option>
                  {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'} Producto</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar producto..." />
        </div>
        <span className="text-xs text-slate-500">{filtered.length} registros</span>
      </div>

      {loading ? (
<Skeleton rows={5} />
      ) : filtered.length === 0 ? (
        <EmptyState message={search ? 'Ningun producto coincide con la busqueda' : 'No hay productos registrados'} />
      ) : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Codigo</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Nombre</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Stock</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">U/M</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Costo Prom.</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Precio Venta</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400 w-20">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filtered.map((c) => {
                  const bajoStock = c.stock_minimo > 0 && c.stock_actual <= c.stock_minimo
                  return (
                    <tr key={c.id} className={`hover:bg-slate-800/30 transition-colors ${bajoStock ? 'bg-red-900/10' : ''}`}>
                      <td className="px-4 py-3"><span className="text-slate-400 font-mono text-xs">{c.codigo || '-'}</span></td>
                      <td className="px-4 py-3">
                        <span className="text-white font-medium">{c.nombre}</span>
                        {bajoStock && <span className="ml-2 px-1.5 py-0.5 bg-red-600/20 text-red-400 rounded text-[10px] font-semibold">BAJO STOCK</span>}
                      </td>
                      <td className="px-4 py-3 text-center font-mono text-sm">
                        <span className={bajoStock ? 'text-red-400 font-semibold' : 'text-slate-300'}>
                          {c.stock_actual}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-slate-400 text-xs">{c.unidad_medida || 'UNIDAD'}</td>
                      <td className="px-4 py-3 text-right font-mono text-sm text-slate-400">
                        C$ {c.costo_promedio.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm text-emerald-400">
                        C$ {c.precio_venta.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button onClick={() => openEdit(c)} className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors">
                          <Pencil className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}