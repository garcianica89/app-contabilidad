import { useState, useEffect } from 'react'
import { DollarSign, X, Check, ArrowRight, Building2 } from 'lucide-react'
import { api } from '../services/api'
import { useNotification } from '../contexts/NotificationContext'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import type { Proveedor, FacturaCompra, CuentaBanco, RetencionFacturaItem, PagoResponse } from '../types/api'

interface RetencionFormItem {
  retencion_id: string
  retencion_nombre: string
  tipo: string
  porcentaje: number
  naturaleza: string
  base_imponible: number
  monto_retenido: number
}

export default function CxPPage() {
  const { notify } = useNotification()
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [facturas, setFacturas] = useState<FacturaCompra[]>([])
  const [cuentasBanco, setCuentasBanco] = useState<CuentaBanco[]>([])
  const [loading, setLoading] = useState(true)
  const [proveedorFilter, setProveedorFilter] = useState('')
  const [selectedFactura, setSelectedFactura] = useState<FacturaCompra | null>(null)
  const [showPagoForm, setShowPagoForm] = useState(false)

  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
  const [monto, setMonto] = useState(0)
  const [metodoPago, setMetodoPago] = useState('EFECTIVO')
  const [cuentaBancoId, setCuentaBancoId] = useState('')
  const [concepto, setConcepto] = useState('')
  const [retenciones, setRetenciones] = useState<RetencionFormItem[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (proveedorFilter) {
      loadFacturas(proveedorFilter)
    } else {
      setFacturas([])
    }
  }, [proveedorFilter])

  async function loadData() {
    try {
      const [provs, cuentas] = await Promise.all([
        api.getProveedores(),
        api.getCuentasBanco(),
      ])
      setProveedores(provs)
      setCuentasBanco(cuentas)
    } catch { /* ignore */ }
    setLoading(false)
  }

  async function loadFacturas(proveedorId: string) {
    try {
      const list = await api.getFacturasCompra({ proveedor_id: proveedorId, estado: 'PENDIENTE' })
      setFacturas(list)
    } catch { /* ignore */ }
  }

  function openPago(factura: FacturaCompra) {
    setSelectedFactura(factura)
    setMonto(factura.total)
    setFecha(new Date().toISOString().split('T')[0])
    setMetodoPago('EFECTIVO')
    setCuentaBancoId('')
    setConcepto(`Pago factura ${factura.numero}`)
    setRetenciones([])
    loadRetenciones(factura.id)
    setShowPagoForm(true)
  }

  async function loadRetenciones(facturaId: string) {
    try {
      const items: RetencionFacturaItem[] = await api.getRetencionesFactura(facturaId)
      setRetenciones(items.map(r => ({
        retencion_id: r.retencion_id,
        retencion_nombre: r.retencion_nombre,
        tipo: r.tipo,
        porcentaje: r.porcentaje,
        naturaleza: r.naturaleza,
        base_imponible: r.base_imponible_calculada,
        monto_retenido: r.monto_retenido,
      })))
    } catch { /* ignore */ }
  }

  function updateRetencion(idx: number, field: keyof RetencionFormItem, value: number) {
    const copy = [...retenciones]
    copy[idx] = { ...copy[idx], [field]: value }
    if (field === 'base_imponible') {
      copy[idx].monto_retenido = Math.round(value * (copy[idx].porcentaje / 100) * 100) / 100
    }
    setRetenciones(copy)
  }

  function totalRetenido() {
    return retenciones.reduce((s, r) => s + r.monto_retenido, 0)
  }

  function totalAPagar() {
    if (!selectedFactura) return 0
    return Math.max(0, selectedFactura.total - totalRetenido())
  }

  async function handlePago(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedFactura) return
    setSaving(true)
    try {
      const result: PagoResponse = await api.registrarPago({
        factura_compra_id: selectedFactura.id,
        monto: totalAPagar(),
        fecha,
        metodo_pago: metodoPago,
        cuenta_banco_id: cuentaBancoId || undefined,
        concepto: concepto.trim(),
        retenciones: retenciones.filter(r => r.monto_retenido > 0).map(r => ({
          retencion_id: r.retencion_id,
          base_imponible: r.base_imponible,
          monto_retenido: r.monto_retenido,
        })),
      })
      notify(`Pago registrado exitosamente. Asiento: ${result.numero_asiento}`, 'success')
      setShowPagoForm(false)
      setSelectedFactura(null)
      if (proveedorFilter) loadFacturas(proveedorFilter)
    } catch (e: any) {
      notify(e?.message || 'Error al registrar pago', 'error')
    }
    setSaving(false)
  }

  function badgeEstado(estado: string) {
    const map: Record<string, string> = {
      'PENDIENTE': 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
      'PAGADA': 'bg-emerald-900/50 text-emerald-300 border-emerald-700',
      'ANULADA': 'bg-red-900/50 text-red-300 border-red-700',
      'VENCIDA': 'bg-orange-900/50 text-orange-300 border-orange-700',
    }
    return map[estado] || 'bg-slate-700 text-slate-300 border-slate-600'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <DollarSign className="w-6 h-6 text-emerald-400" />
          Cuentas por Pagar
        </h1>
      </div>

      <div className="flex gap-4 items-start">
        <div className="w-72">
          <label className="block text-xs text-slate-400 mb-1">Proveedor</label>
          <select value={proveedorFilter} onChange={e => setProveedorFilter(e.target.value)}
            className="input-filter w-full">
            <option value="">Seleccionar proveedor...</option>
            {proveedores.map(p => (
              <option key={p.id} value={p.id}>{p.nombre}</option>
            ))}
          </select>
        </div>
        {facturas.length > 0 && (
          <div className="pt-5 text-xs text-slate-500">
            {facturas.filter(f => f.estado === 'PENDIENTE').length} facturas pendientes
            — Total: C$ {facturas.filter(f => f.estado === 'PENDIENTE').reduce((s, f) => s + f.total, 0).toLocaleString('es-NI', { minimumFractionDigits: 2 })}
          </div>
        )}
      </div>

      {loading ? (
        <Skeleton rows={5} />
      ) : !proveedorFilter ? (
        <EmptyState icon={<Building2 className="w-8 h-8 mx-auto mb-2 opacity-50" />}
          message="Seleccione un proveedor para ver sus facturas pendientes" />
      ) : facturas.length === 0 ? (
        <EmptyState icon={<DollarSign className="w-8 h-8 mx-auto mb-2 opacity-50" />}
          message="No hay facturas pendientes para este proveedor" />
      ) : (
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Numero</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Fecha</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Vencimiento</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Subtotal</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">IVA</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Total</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">Estado</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">Accion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {facturas.map(f => (
                  <tr key={f.id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 text-sm text-white font-mono">{f.numero}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{new Date(f.fecha).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-sm text-slate-300 text-right">
                      {f.fecha_vencimiento ? new Date(f.fecha_vencimiento).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300 text-right font-mono">C$ {f.subtotal.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-slate-300 text-right font-mono">C$ {f.iva.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-white text-right font-mono font-semibold">C$ {f.total.toFixed(2)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs border ${badgeEstado(f.estado)}`}>{f.estado}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button onClick={() => openPago(f)}
                        className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-xs flex items-center gap-1 mx-auto"
                        disabled={f.estado !== 'PENDIENTE'}>
                        <ArrowRight className="w-3 h-3" /> Pagar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showPagoForm && selectedFactura && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Registrar Pago</h2>
              <button onClick={() => setShowPagoForm(false)} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 bg-slate-700/30 rounded-lg p-4">
              <div>
                <span className="text-xs text-slate-400">Factura</span>
                <p className="text-white font-semibold">{selectedFactura.numero}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400">Total Factura</span>
                <p className="text-white font-semibold">C$ {selectedFactura.total.toFixed(2)}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400">Fecha</span>
                <p className="text-white">{new Date(selectedFactura.fecha).toLocaleDateString()}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400">Vencimiento</span>
                <p className="text-white">{selectedFactura.fecha_vencimiento ? new Date(selectedFactura.fecha_vencimiento).toLocaleDateString() : '-'}</p>
              </div>
            </div>

            <form onSubmit={handlePago} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Fecha de Pago</label>
                  <input type="date" value={fecha} onChange={e => setFecha(e.target.value)}
                    className="input-filter w-full" required />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Metodo de Pago</label>
                  <select value={metodoPago} onChange={e => {
                    setMetodoPago(e.target.value)
                    if (e.target.value === 'EFECTIVO') setCuentaBancoId('')
                  }} className="input-filter w-full">
                    <option value="EFECTIVO">Efectivo</option>
                    <option value="TRANSFERENCIA">Transferencia</option>
                    <option value="CHEQUE">Cheque</option>
                  </select>
                </div>
                {metodoPago !== 'EFECTIVO' && (
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Cuenta Bancaria</label>
                    <select value={cuentaBancoId} onChange={e => setCuentaBancoId(e.target.value)}
                      className="input-filter w-full" required>
                      <option value="">Seleccionar cuenta...</option>
                      {cuentasBanco.map(c => (
                        <option key={c.id} value={c.id}>{c.banco} - {c.numero_cuenta}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Concepto</label>
                  <input type="text" value={concepto} onChange={e => setConcepto(e.target.value)}
                    className="input-filter w-full" placeholder="Concepto del pago" />
                </div>
              </div>

              {retenciones.length > 0 && (
                <div className="bg-slate-700/30 rounded-lg p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-white">Retenciones</h3>
                    <span className="text-xs text-slate-400">
                      Total retenido: C$ {totalRetenido().toFixed(2)}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {retenciones.map((r, i) => (
                      <div key={r.retencion_id} className="flex items-center gap-3 bg-slate-800 rounded-lg p-3 border border-slate-600">
                        <div className="flex-1">
                          <span className="text-sm text-white">{r.retencion_nombre}</span>
                          <span className="text-xs text-slate-400 ml-2">({r.tipo} - {r.porcentaje}%)</span>
                        </div>
                        <div className="w-36">
                          <label className="block text-xs text-slate-400">Base</label>
                          <input type="number" step="0.01" value={r.base_imponible}
                            onChange={e => updateRetencion(i, 'base_imponible', parseFloat(e.target.value) || 0)}
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm" />
                        </div>
                        <div className="w-36">
                          <label className="block text-xs text-slate-400">Monto</label>
                          <input type="number" step="0.01" value={r.monto_retenido}
                            onChange={e => updateRetencion(i, 'monto_retenido', parseFloat(e.target.value) || 0)}
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-emerald-900/20 border border-emerald-700/30 rounded-lg p-4">
                <div className="flex items-center justify-between text-lg">
                  <span className="text-slate-300">Total a Pagar</span>
                  <span className="text-emerald-400 font-bold">C$ {totalAPagar().toFixed(2)}</span>
                </div>
              </div>

              <div className="flex gap-3">
                <button type="submit" disabled={saving || totalAPagar() <= 0}
                  className="flex-1 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2">
                  {saving ? 'Procesando...' : <><Check className="w-5 h-5" /> Registrar Pago</>}
                </button>
                <button type="button" onClick={() => setShowPagoForm(false)}
                  className="px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors">
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
