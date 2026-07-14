import { useState, useEffect } from 'react'
import { Search, Plus, X, Check, ShoppingCart, Truck, Receipt } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'
import type { Moneda, PeriodoContable, Proveedor, Producto, Bodega, CondicionPago, OrdenCompra } from '../types/api'

interface FacturaCompra {
  id: string; numero: string; proveedor_id: string; fecha: string; proveedor_nombre?: string; total: number; estado: string
}

const emptyFacturaForm = {
  numero: '', proveedor_id: '', fecha: new Date().toISOString().split('T')[0],
  moneda_id: '', periodo_id: '', fecha_vencimiento: '', descuento: 0, retencion_ir: 0, orden_id: '',
}

export default function ComprasPage() {
  const [tab, setTab] = useState<'ordenes' | 'facturas'>('ordenes')
  const [ordenes, setOrdenes] = useState<OrdenCompra[]>([])
  const [facturas, setFacturas] = useState<FacturaCompra[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [showFacturaForm, setShowFacturaForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [productos, setProductos] = useState<Producto[]>([])
  const [monedas, setMonedas] = useState<Moneda[]>([])
  const [periodos, setPeriodos] = useState<PeriodoContable[]>([])
  const [bodegas, setBodegas] = useState<Bodega[]>([])
  const [condicionesPago, setCondicionesPago] = useState<CondicionPago[]>([])

  const [form, setForm] = useState({
    numero: '', proveedor_id: '', fecha: new Date().toISOString().split('T')[0],
    moneda_id: '', fecha_entrega: '', bodega_id: '', condicion_pago_id: '', descuento: 0, retencion_ir: 0,
  })
  const [lineas, setLineas] = useState<{ producto_id: string; nombre: string; cantidad: number; precio: number; aplica_iva: boolean; tasa_iva: number }[]>([])
  const [facForm, setFacForm] = useState(emptyFacturaForm)
  const [facLineas, setFacLineas] = useState<{ producto_id: string; nombre: string; cantidad: number; precio: number; aplica_iva: boolean; tasa_iva: number }[]>([])
  const [selectedProveedor, setSelectedProveedor] = useState<Proveedor | null>(null)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const [ords, facs, provs, prods, mons, pers, bods, cps] = await Promise.all([
        api.getOrdenesCompra(), api.getFacturasCompra(),
        api.getProveedores(), api.getProductos(),
        api.getMonedas(), api.getPeriodos(),
        api.getBodegas(), api.getCondicionesPago(),
      ])
      setOrdenes(ords)
      setFacturas(facs)
      setProveedores(provs)
      setProductos(prods)
      setMonedas(mons)
      setPeriodos(pers)
      setBodegas(bods)
      setCondicionesPago(cps)
    } catch {}
    setLoading(false)
  }

  const filteredOrdenes = ordenes.filter((o) =>
    !search || o.numero.toLowerCase().includes(search.toLowerCase()) ||
    o.estado.toLowerCase().includes(search.toLowerCase())
  )
  const filteredFacturas = facturas.filter((f) =>
    !search || f.numero.toLowerCase().includes(search.toLowerCase()) ||
    f.estado.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() {
    setForm({
      numero: `OC-${Date.now().toString().slice(-6)}`,
      proveedor_id: '', fecha: new Date().toISOString().split('T')[0],
      moneda_id: '', fecha_entrega: '', bodega_id: '', condicion_pago_id: '', descuento: 0, retencion_ir: 0,
    })
    setLineas([{ producto_id: '', nombre: '', cantidad: 1, precio: 0, aplica_iva: true, tasa_iva: 15 }])
    setShowForm(true)
  }

  function openCreateFactura() {
    setFacForm({
      ...emptyFacturaForm,
      numero: `FC-${Date.now().toString().slice(-6)}`,
    })
    setFacLineas([{ producto_id: '', nombre: '', cantidad: 1, precio: 0, aplica_iva: true, tasa_iva: 15 }])
    setSelectedProveedor(null)
    setShowFacturaForm(true)
  }

  function addLinea() {
    setLineas([...lineas, { producto_id: '', nombre: '', cantidad: 1, precio: 0, aplica_iva: true, tasa_iva: 15 }])
  }
  function removeLinea(i: number) {
    setLineas(lineas.filter((_, idx) => idx !== i))
  }
  function updateLinea(i: number, field: string, value: any) {
    const newLineas = [...lineas]
    if (field === 'producto_id') {
      const prod = productos.find((p) => p.id === value)
      newLineas[i] = { ...newLineas[i], producto_id: value, nombre: prod?.nombre || '', precio: prod?.precio_venta || 0, aplica_iva: prod?.aplica_iva ?? true, tasa_iva: 15 }
    } else {
      newLineas[i] = { ...newLineas[i], [field]: value }
    }
    setLineas(newLineas)
  }

  const lineaSubtotales = lineas.map((l) => (l.cantidad || 0) * (l.precio || 0))
  const lineasDescuento = lineas.map((l) => (l.cantidad || 0) * (l.precio || 0) * (form.descuento || 0) / 100)
  const subtotal = lineaSubtotales.reduce((a, b) => a + b, 0)
  const descuentoTotal = lineasDescuento.reduce((a, b) => a + b, 0)
  const neto = subtotal - descuentoTotal
  const total = neto - (form.retencion_ir || 0)

  // ── Factura helpers ──
  function addFacLinea() {
    setFacLineas([...facLineas, { producto_id: '', nombre: '', cantidad: 1, precio: 0, aplica_iva: true, tasa_iva: 15 }])
  }
  function removeFacLinea(i: number) {
    setFacLineas(facLineas.filter((_, idx) => idx !== i))
  }
  function updateFacLinea(i: number, field: string, value: any) {
    const newLineas = [...facLineas]
    if (field === 'producto_id') {
      const prod = productos.find((p) => p.id === value)
      newLineas[i] = {
        ...newLineas[i],
        producto_id: value,
        nombre: prod?.nombre || '',
        precio: prod?.precio_venta || 0,
        aplica_iva: prod?.aplica_iva ?? true,
        tasa_iva: selectedProveedor?.tasa_iva || 15,
      }
    } else {
      newLineas[i] = { ...newLineas[i], [field]: value }
    }
    setFacLineas(newLineas)
  }

  function handleProveedorChange(id: string) {
    const p = proveedores.find((pr) => pr.id === id) || null
    setSelectedProveedor(p)
    setFacForm({ ...facForm, proveedor_id: id })
    setFacLineas(facLineas.map((l) => ({
      ...l,
      tasa_iva: p?.tasa_iva || l.tasa_iva,
    })))
  }

  const facSubtotal = facLineas.reduce((sum, l) => sum + (l.cantidad || 0) * (l.precio || 0), 0)
  const facIva = facLineas.reduce((sum, l) => {
    if (!l.aplica_iva || l.producto_id === '') return sum
    const prod = productos.find((p) => p.id === l.producto_id)
    if (!prod || !prod.aplica_iva) return sum
    const tasa = l.tasa_iva || selectedProveedor?.tasa_iva || 15
    return sum + (l.cantidad || 0) * (l.precio || 0) * tasa / 100
  }, 0)
  const facTotal = facSubtotal - (facForm.descuento || 0) + facIva - (facForm.retencion_ir || 0)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const orden = await api.crearOrdenCompra({
        numero: form.numero,
        proveedor_id: form.proveedor_id,
        fecha: form.fecha,
        lineas: lineas.map((l) => ({
          producto_id: l.producto_id, cantidad: l.cantidad, precio_unitario: l.precio,
          aplica_iva: l.aplica_iva,
          tasa_iva: l.aplica_iva ? (l.tasa_iva || 15) : undefined,
        })),
        moneda_id: form.moneda_id,
        fecha_entrega: form.fecha_entrega || null,
        bodega_id: form.bodega_id || null,
        condicion_pago_id: form.condicion_pago_id || null,
        descuento: form.descuento,
        retencion_ir: form.retencion_ir,
      })
      setOrdenes((prev) => [orden, ...prev])
      setShowForm(false)
    } catch (err: any) {
      notify(err.message || 'Error al crear orden')
    }
    setSaving(false)
  }

  async function handleAprobar(id: string) {
    try {
      const r = await api.aprobarOrdenCompra(id)
      setOrdenes((prev) => prev.map((o) => o.id === id ? { ...o, estado: r.estado } : o))
    } catch (err: any) { notify(err.message) }
  }

  async function handleAnular(id: string) {
    if (!confirm('Anular orden de compra?')) return
    try {
      const r = await api.anularOrdenCompra(id)
      setOrdenes((prev) => prev.map((o) => o.id === id ? { ...o, estado: r.estado } : o))
    } catch (err: any) { notify(err.message) }
  }

  async function handleSubmitFactura(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const factura = await api.crearFacturaCompra({
        numero: facForm.numero,
        proveedor_id: facForm.proveedor_id,
        fecha: facForm.fecha,
        lineas: facLineas.map((l) => ({
          producto_id: l.producto_id,
          cantidad: l.cantidad,
          precio_unitario: l.precio,
          aplica_iva: l.aplica_iva,
          tasa_iva: l.aplica_iva ? (l.tasa_iva || selectedProveedor?.tasa_iva) : undefined,
        })),
        moneda_id: facForm.moneda_id,
        periodo_id: facForm.periodo_id,
        orden_id: facForm.orden_id || undefined,
        fecha_vencimiento: facForm.fecha_vencimiento || undefined,
        descuento: facForm.descuento,
        iva: Math.round(facIva * 100) / 100,
        retencion_ir: facForm.retencion_ir,
      })
      setFacturas((prev) => [factura, ...prev])
      setShowFacturaForm(false)
    } catch (err: any) {
      notify(err.message || 'Error al crear factura')
    }
    setSaving(false)
  }

  const badgeColor = (estado: string) => {
    switch (estado) {
      case 'EMITIDA': return 'bg-amber-600/20 text-amber-400'
      case 'APROBADA': return 'bg-emerald-600/20 text-emerald-400'
      case 'ANULADA': return 'bg-slate-600/20 text-slate-400'
      case 'RECIBIDA': return 'bg-blue-600/20 text-blue-400'
      case 'PENDIENTE': return 'bg-amber-600/20 text-amber-400'
      case 'PAGADA': return 'bg-emerald-600/20 text-emerald-400'
      default: return 'bg-slate-600/20 text-slate-400'
    }
  }

  const ordenesAprobadas = ordenes.filter((o) => o.estado === 'APROBADA')

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Compras</h1>
          <p className="text-sm text-slate-400">Ordenes de compra y facturas de proveedores</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-slate-800 rounded-lg p-1">
            <button onClick={() => setTab('ordenes')} className={`px-4 py-1.5 text-xs rounded-md font-medium transition-colors ${tab === 'ordenes' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}>Ordenes</button>
            <button onClick={() => setTab('facturas')} className={`px-4 py-1.5 text-xs rounded-md font-medium transition-colors ${tab === 'facturas' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}>Facturas</button>
          </div>
          {tab === 'ordenes' ? (
            <button onClick={openCreate} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Nueva Orden
            </button>
          ) : (
            <button onClick={openCreateFactura} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Nueva Factura
            </button>
          )}
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nueva Orden de Compra</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Numero *</label>
              <input value={form.numero} onChange={(e) => setForm({ ...form, numero: e.target.value })} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Proveedor *</label>
              <select value={form.proveedor_id} onChange={(e) => setForm({ ...form, proveedor_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar proveedor</option>
                {proveedores.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Moneda *</label>
              <select value={form.moneda_id} onChange={(e) => setForm({ ...form, moneda_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar moneda</option>
                {monedas.map((m) => <option key={m.id} value={m.id}>{m.codigo} - {m.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Bodega destino</label>
              <select value={form.bodega_id} onChange={(e) => setForm({ ...form, bodega_id: e.target.value })} className="input-filter w-full">
                <option value="">Sin bodega</option>
                {bodegas.map((b) => <option key={b.id} value={b.id}>{b.codigo} - {b.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha</label>
              <input type="date" value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha Entrega</label>
              <input type="date" value={form.fecha_entrega} onChange={(e) => setForm({ ...form, fecha_entrega: e.target.value })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Condicion Pago</label>
              <select value={form.condicion_pago_id} onChange={(e) => setForm({ ...form, condicion_pago_id: e.target.value })} className="input-filter w-full">
                <option value="">Seleccionar</option>
                {condicionesPago.filter((cp) => cp.activa).map((cp) => <option key={cp.id} value={cp.id}>{cp.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Descuento %</label>
              <input type="number" step="0.01" min="0" max="100" value={form.descuento}
                onChange={(e) => setForm({ ...form, descuento: Number(e.target.value) })}
                className="input-filter w-full" />
            </div>
          </div>

          <div className="border-t border-slate-700/50 pt-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-white">Lineas</span>
              <button type="button" onClick={addLinea} className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1">
                <Plus className="w-3 h-3" /> Agregar linea
              </button>
            </div>
            {lineas.map((l, i) => (
              <div key={i} className="grid grid-cols-12 gap-2 items-end mb-2">
                <div className="col-span-4">
                  <select value={l.producto_id} onChange={(e) => updateLinea(i, 'producto_id', e.target.value)} className="input-filter w-full text-xs">
                    <option value="">Seleccionar producto</option>
                    {productos.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <input type="number" step="0.01" value={l.cantidad} onChange={(e) => updateLinea(i, 'cantidad', Number(e.target.value))} className="input-filter w-full text-xs" placeholder="Cant" />
                </div>
                <div className="col-span-2">
                  <input type="number" step="0.01" value={l.precio} onChange={(e) => updateLinea(i, 'precio', Number(e.target.value))} className="input-filter w-full text-xs" placeholder="Precio" />
                </div>
                <div className="col-span-1 flex items-center gap-1">
                  <input type="checkbox" checked={l.aplica_iva}
                    onChange={(e) => updateLinea(i, 'aplica_iva', e.target.checked)}
                    className="w-3 h-3" title="Aplica IVA" />
                  {l.aplica_iva && (
                    <input type="number" step="0.01" value={l.tasa_iva}
                      onChange={(e) => updateLinea(i, 'tasa_iva', Number(e.target.value))}
                      className="input-filter w-12 text-right text-xs" placeholder="%" />
                  )}
                </div>
                <div className="col-span-2 text-right text-xs text-slate-400 py-2">
                  C$ {(lineaSubtotales[i]).toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                </div>
                <div className="col-span-1 text-center">
                  {lineas.length > 1 && (
                    <button type="button" onClick={() => removeLinea(i)} className="text-red-400 hover:text-red-300"><X className="w-4 h-4" /></button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-slate-700/50 pt-4 flex justify-between items-start">
            <div className="text-xs text-slate-500">
              <div>Subtotal: C$ {subtotal.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
              {descuentoTotal > 0 && <div>Dto. ({form.descuento}%): -C$ {descuentoTotal.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>}
            </div>
            <div className="flex gap-8 text-base font-bold">
              <div className="text-right">
                <div className="text-xs text-slate-400 font-normal">Neto</div>
                <div className="text-white font-mono">C$ {neto.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
              </div>
              {form.retencion_ir > 0 && (
                <div className="text-right">
                  <div className="text-xs text-slate-400 font-normal">Ret. IR</div>
                  <div className="text-red-400 font-mono">-C$ {form.retencion_ir.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
                </div>
              )}
              <div className="text-right">
                <div className="text-xs text-slate-400 font-normal">Total</div>
                <div className="text-emerald-400 font-mono">C$ {total.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> Crear Orden</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {showFacturaForm && (
        <form onSubmit={handleSubmitFactura} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nueva Factura de Compra</h3>
            <button type="button" onClick={() => setShowFacturaForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Numero *</label>
              <input value={facForm.numero} onChange={(e) => setFacForm({ ...facForm, numero: e.target.value })} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Proveedor *</label>
              <select value={facForm.proveedor_id} onChange={(e) => handleProveedorChange(e.target.value)} className="input-filter w-full" required>
                <option value="">Seleccionar proveedor</option>
                {proveedores.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre} {p.aplica_iva ? `(IVA ${p.tasa_iva}%)` : '(No IVA)'}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Moneda *</label>
              <select value={facForm.moneda_id} onChange={(e) => setFacForm({ ...facForm, moneda_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar moneda</option>
                {monedas.map((m) => <option key={m.id} value={m.id}>{m.codigo} - {m.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Periodo *</label>
              <select value={facForm.periodo_id} onChange={(e) => setFacForm({ ...facForm, periodo_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar periodo</option>
                {periodos.filter((p) => !p.cerrado).map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Orden de Compra</label>
              <select value={facForm.orden_id} onChange={(e) => setFacForm({ ...facForm, orden_id: e.target.value })} className="input-filter w-full">
                <option value="">Sin orden</option>
                {ordenesAprobadas.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.numero} - {o.proveedor_nombre || ''} (C$ {o.total.toLocaleString('es-NI', { minimumFractionDigits: 2 })})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha</label>
              <input type="date" value={facForm.fecha} onChange={(e) => setFacForm({ ...facForm, fecha: e.target.value })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha Vencimiento</label>
              <input type="date" value={facForm.fecha_vencimiento} onChange={(e) => setFacForm({ ...facForm, fecha_vencimiento: e.target.value })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Descuento</label>
              <input type="number" step="0.01" value={facForm.descuento} onChange={(e) => setFacForm({ ...facForm, descuento: Number(e.target.value) })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Retencion IR</label>
              <input type="number" step="0.01" value={facForm.retencion_ir} onChange={(e) => setFacForm({ ...facForm, retencion_ir: Number(e.target.value) })} className="input-filter w-full" />
            </div>
          </div>

          <div className="border-t border-slate-700/50 pt-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-white">Lineas</span>
              <button type="button" onClick={addFacLinea} className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1">
                <Plus className="w-3 h-3" /> Agregar linea
              </button>
            </div>
            {facLineas.map((l, i) => {
              const lineTotal = (l.cantidad || 0) * (l.precio || 0)
              const lineaIva = l.aplica_iva ? lineTotal * (l.tasa_iva || selectedProveedor?.tasa_iva || 15) / 100 : 0
              return (
                <div key={i} className="grid grid-cols-12 gap-2 items-end mb-2">
                  <div className="col-span-4">
                    <select value={l.producto_id} onChange={(e) => updateFacLinea(i, 'producto_id', e.target.value)} className="input-filter w-full text-xs">
                      <option value="">Seleccionar producto</option>
                      {productos.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.nombre} {p.aplica_iva ? '' : '(sin IVA)'}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <input type="number" step="0.01" value={l.cantidad} onChange={(e) => updateFacLinea(i, 'cantidad', Number(e.target.value))} className="input-filter w-full text-xs" placeholder="Cant" />
                  </div>
                  <div className="col-span-2">
                    <input type="number" step="0.01" value={l.precio} onChange={(e) => updateFacLinea(i, 'precio', Number(e.target.value))} className="input-filter w-full text-xs" placeholder="Precio" />
                  </div>
                  <div className="col-span-1 flex items-center gap-1">
                    <input type="checkbox" checked={l.aplica_iva}
                      onChange={(e) => updateFacLinea(i, 'aplica_iva', e.target.checked)}
                      className="w-3 h-3" title="Aplica IVA" />
                    {l.aplica_iva && (
                      <input type="number" step="0.01" value={l.tasa_iva}
                        onChange={(e) => updateFacLinea(i, 'tasa_iva', Number(e.target.value))}
                        className="input-filter w-12 text-right text-xs" placeholder="%" />
                    )}
                  </div>
                  <div className="col-span-2 text-right text-xs text-slate-400 py-2">
                    <div>C$ {lineTotal.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
                    {lineaIva > 0 && <div className="text-amber-400">IVA: C$ {lineaIva.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>}
                  </div>
                  <div className="col-span-1 text-center">
                    {facLineas.length > 1 && (
                      <button type="button" onClick={() => removeFacLinea(i)} className="text-red-400 hover:text-red-300"><X className="w-4 h-4" /></button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="border-t border-slate-700/50 pt-4 flex justify-end">
            <div className="flex gap-8 text-base font-bold">
              <div className="text-right">
                <div className="text-xs text-slate-400 font-normal">Subtotal</div>
                <div className="text-white font-mono">C$ {facSubtotal.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
              </div>
              {facIva > 0 && (
                <div className="text-right">
                  <div className="text-xs text-slate-400 font-normal">IVA</div>
                  <div className="text-amber-400 font-mono">C$ {facIva.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
                </div>
              )}
              <div className="text-right">
                <div className="text-xs text-slate-400 font-normal">Total</div>
                <div className="text-emerald-400 font-mono">C$ {facTotal.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Receipt className="w-4 h-4" /> Crear Factura</>}
            </button>
            <button type="button" onClick={() => setShowFacturaForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar..." />
        </div>
        <span className="text-xs text-slate-500">{tab === 'ordenes' ? filteredOrdenes.length : filteredFacturas.length} registros</span>
      </div>

      {loading ? (
<Skeleton rows={5} />
      ) : tab === 'ordenes' ? (
        filteredOrdenes.length === 0 ? (
          <EmptyState
            icon={<ShoppingCart className="w-8 h-8 mx-auto mb-2 opacity-50" />}
            message="No hay ordenes de compra registradas"
          />
        ) : (
          <div className="card overflow-hidden !p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Numero</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Proveedor</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Fecha</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Total</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Estado</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filteredOrdenes.map((o) => (
                  <tr key={o.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-white font-medium">{o.numero}</td>
                    <td className="px-4 py-3 text-slate-300">{o.proveedor_nombre || o.proveedor_id.slice(0, 8)}</td>
                    <td className="px-4 py-3 text-center text-slate-400">{o.fecha}</td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-white">
                      C$ {o.total.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${badgeColor(o.estado)}`}>{o.estado}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {o.estado === 'EMITIDA' && (
                          <button onClick={() => handleAprobar(o.id)} className="text-xs text-emerald-400 hover:text-emerald-300 font-medium">Aprobar</button>
                        )}
                        {(o.estado === 'EMITIDA' || o.estado === 'APROBADA') && (
                          <button onClick={() => handleAnular(o.id)} className="text-xs text-red-400 hover:text-red-300 font-medium">Anular</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        filteredFacturas.length === 0 ? (
          <EmptyState
            icon={<Truck className="w-8 h-8 mx-auto mb-2 opacity-50" />}
            message="No hay facturas de compra registradas"
          />
        ) : (
          <div className="card overflow-hidden !p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Numero</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Proveedor</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Fecha</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Total</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filteredFacturas.map((f) => (
                  <tr key={f.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-white font-medium">{f.numero}</td>
                    <td className="px-4 py-3 text-slate-300">{f.proveedor_nombre || f.proveedor_id.slice(0, 8)}</td>
                    <td className="px-4 py-3 text-center text-slate-400">{f.fecha}</td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-white">
                      C$ {f.total.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${badgeColor(f.estado)}`}>{f.estado}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  )
}
