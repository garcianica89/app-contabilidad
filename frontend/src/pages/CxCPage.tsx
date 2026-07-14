import { useState, useEffect } from 'react'
import { DollarSign, X, Check, ArrowRight, Users } from 'lucide-react'
import { api } from '../services/api'
import { useNotification } from '../contexts/NotificationContext'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import type { Cliente, FacturaVenta, CuentaBanco, CobroResponse } from '../types/api'

interface RetencionFormItem {
  retencion_id: string
  retencion_nombre: string
  tipo: string
  porcentaje: number
  naturaleza: string
  base_imponible: number
  monto_retenido: number
}

export default function CxCPage() {
  const { notify } = useNotification()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [facturas, setFacturas] = useState<FacturaVenta[]>([])
  const [cuentasBanco, setCuentasBanco] = useState<CuentaBanco[]>([])
  const [clienteFilter, setClienteFilter] = useState('')
  const [selectedFactura, setSelectedFactura] = useState<FacturaVenta | null>(null)
  const [showCobroForm, setShowCobroForm] = useState(false)
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
  const [monto, setMonto] = useState(0)
  const [metodoPago, setMetodoPago] = useState('EFECTIVO')
  const [cuentaBancoId, setCuentaBancoId] = useState('')
  const [concepto, setConcepto] = useState('')
  const [retenciones, setRetenciones] = useState<RetencionFormItem[]>([])
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.getClientes(),
      api.getCuentasBanco(),
    ]).then(([cs, bs]) => {
      setClientes(cs)
      setCuentasBanco(bs)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  async function loadFacturas(clienteId: string) {
    try {
      if (clienteId === 'todas') {
        const all = await api.getFacturas({ estado: 'EMITIDA' })
        setFacturas(all)
      } else {
        const data = await api.getFacturas({ cliente_id: clienteId, estado: 'EMITIDA' })
        setFacturas(data)
      }
    } catch {}
  }

  function handleClienteChange(val: string) {
    setClienteFilter(val)
    if (val) loadFacturas(val)
    else setFacturas([])
  }

  function openCobro(factura: FacturaVenta) {
    setSelectedFactura(factura)
    setMonto(factura.total)
    setFecha(new Date().toISOString().split('T')[0])
    setMetodoPago('EFECTIVO')
    setCuentaBancoId('')
    setConcepto(`Cobro factura ${factura.numero}`)
    setRetenciones([])
    loadRetenciones(factura.id)
    setShowCobroForm(true)
  }

  async function loadRetenciones(facturaId: string) {
    try {
      const items: any[] = await api.getRetencionesFacturaCxC(facturaId)
      setRetenciones(items.map(r => ({
        retencion_id: r.retencion_id,
        retencion_nombre: r.retencion_nombre,
        tipo: r.tipo,
        porcentaje: r.porcentaje,
        naturaleza: r.naturaleza,
        base_imponible: r.base_imponible_calculada,
        monto_retenido: r.monto_retenido,
      })))
    } catch {}
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

  function totalACobrar() {
    if (!selectedFactura) return 0
    return Math.max(0, selectedFactura.total - totalRetenido())
  }

  async function handleCobro(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedFactura) return
    setSaving(true)
    try {
      const result: CobroResponse = await api.registrarCobro({
        factura_venta_id: selectedFactura.id,
        monto: totalACobrar(),
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
      notify(`Cobro registrado exitosamente. Asiento: ${result.numero_asiento}`, 'success')
      setShowCobroForm(false)
      setSelectedFactura(null)
      if (clienteFilter) loadFacturas(clienteFilter)
    } catch (e: any) {
      notify(e?.message || 'Error al registrar cobro', 'error')
    }
    setSaving(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Cuentas por Cobrar</h1>
          <p className="text-sm text-slate-400">Seleccione un cliente para ver facturas pendientes</p>
        </div>
      </div>

      <div className="relative max-w-xs">
        <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <select
          value={clienteFilter}
          onChange={e => handleClienteChange(e.target.value)}
          className="input-filter w-full pl-10"
        >
          <option value="">Seleccionar cliente...</option>
          <option value="todas">Todos los clientes</option>
          {clientes.map(c => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <Skeleton rows={6} />
      ) : facturas.length === 0 && clienteFilter ? (
        <EmptyState message="No hay facturas pendientes de cobro para este cliente" />
      ) : clienteFilter ? (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-700/50">
                <th className="py-3 px-4">Factura</th>
                <th className="py-3 px-4">Fecha</th>
                <th className="py-3 px-4 text-right">Total</th>
                <th className="py-3 px-4 text-center">Estado</th>
                <th className="py-3 px-4 text-center">Accion</th>
              </tr>
            </thead>
            <tbody>
              {facturas.map(f => (
                <tr key={f.id} className="border-b border-slate-700/30 hover:bg-slate-700/20">
                  <td className="py-3 px-4 text-white font-medium">{f.numero}</td>
                  <td className="py-3 px-4 text-slate-300">{f.fecha?.split('T')[0]}</td>
                  <td className="py-3 px-4 text-right text-white font-semibold">
                    C$ {f.total?.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="px-2 py-0.5 bg-yellow-900/50 text-yellow-400 rounded-full text-xs">
                      {f.estado}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => openCobro(f)}
                      className="flex items-center gap-1 mx-auto text-xs bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg transition-colors"
                    >
                      <DollarSign className="w-3.5 h-3.5" /> Cobrar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState message="Seleccione un cliente para ver sus facturas pendientes" />
      )}

      {/* Modal Cobro */}
      {showCobroForm && selectedFactura && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <form onSubmit={handleCobro} className="bg-slate-800 rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-xl border border-slate-600">
            <div className="flex items-center justify-between p-5 border-b border-slate-700">
              <div>
                <h2 className="text-lg font-bold text-white">Registrar Cobro</h2>
                <p className="text-sm text-slate-400">Factura: {selectedFactura.numero}</p>
              </div>
              <button type="button" onClick={() => setShowCobroForm(false)} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between bg-slate-700/50 rounded-lg p-3">
                <span className="text-slate-300">Total factura</span>
                <span className="text-white font-bold text-lg">C$ {selectedFactura.total?.toFixed(2)}</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Fecha *</label>
                  <input type="date" value={fecha} onChange={e => setFecha(e.target.value)}
                    className="input-filter w-full" required />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Monto a cobrar *</label>
                  <input type="number" step="0.01" value={monto} onChange={e => setMonto(parseFloat(e.target.value) || 0)}
                    className="input-filter w-full" required />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Metodo de pago</label>
                <select value={metodoPago} onChange={e => setMetodoPago(e.target.value)}
                  className="input-filter w-full">
                  <option value="EFECTIVO">Efectivo</option>
                  <option value="TRANSFERENCIA">Transferencia</option>
                  <option value="CHEQUE">Cheque</option>
                </select>
              </div>

              {metodoPago !== 'EFECTIVO' && (
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Cuenta bancaria</label>
                  <select value={cuentaBancoId} onChange={e => setCuentaBancoId(e.target.value)}
                    className="input-filter w-full">
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
                  className="input-filter w-full" placeholder="Concepto del cobro" />
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

              <div className="flex items-center justify-between bg-primary-900/30 rounded-lg p-3 border border-primary-700">
                <span className="text-primary-300 font-semibold">Total a cobrar</span>
                <span className="text-white font-bold text-lg">
                  C$ {totalACobrar().toFixed(2)}
                  <ArrowRight className="inline w-4 h-4 ml-2 text-primary-400" />
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-3 p-5 border-t border-slate-700">
              <button type="button" onClick={() => setShowCobroForm(false)} className="btn-secondary">
                Cancelar
              </button>
              <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
                <Check className="w-4 h-4" /> {saving ? 'Registrando...' : 'Registrar Cobro'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
