import { useState, useEffect } from 'react'
import { ClipboardList, Plus, X, AlertCircle, Settings } from 'lucide-react'
import { api } from '../services/api'
import { useNotification } from '../contexts/NotificationContext'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import type {
  SalidaInventarioListadoItem,
  SalidaInventarioCreate,
  SalidaInventarioResponse,
  Producto,
  Bodega,
} from '../types/api'

interface SubtipoOption {
  id: string
  codigo: string
  nombre: string
  cuenta_principal_id: string | null
}

interface LineaForm {
  producto_id: string
  producto_nombre: string
  cantidad: number
}

const emptyLinea: LineaForm = {
  producto_id: '',
  producto_nombre: '',
  cantidad: 0,
}

export default function SalidasInventarioPage() {
  const { notify } = useNotification()
  const [items, setItems] = useState<SalidaInventarioListadoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [productos, setProductos] = useState<Producto[]>([])
  const [bodegas, setBodegas] = useState<Bodega[]>([])
  const [subtipos, setSubtipos] = useState<SubtipoOption[]>([])
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
  const [subtypeCode, setSubtypeCode] = useState('')
  const [bodegaId, setBodegaId] = useState('')
  const [motivo, setMotivo] = useState('')
  const [lineas, setLineas] = useState<LineaForm[]>([{ ...emptyLinea }])
  const [showNewSubtipo, setShowNewSubtipo] = useState(false)
  const [newSubtipoCodigo, setNewSubtipoCodigo] = useState('')
  const [newSubtipoNombre, setNewSubtipoNombre] = useState('')

  useEffect(() => {
    loadData()
    loadCatalogos()
    loadSubtipos()
  }, [])

  async function loadData() {
    try {
      const data = await api.listarSalidasInventario()
      setItems(data)
    } catch { /* ignore */ }
    setLoading(false)
  }

  async function loadCatalogos() {
    try {
      const [prods, bods] = await Promise.all([
        api.getProductos(),
        api.getBodegas(),
      ])
      setProductos(prods)
      setBodegas(bods)
      if (bods.length > 0) setBodegaId(bods[0].id)
    } catch { /* ignore */ }
  }

  async function loadSubtipos() {
    try {
      const list = await api.getSubtiposPorTipo('SALIDA_INV')
      setSubtipos(list)
      if (list.length > 0) setSubtypeCode(list[0].codigo)
    } catch { /* ignore */ }
  }

  async function handleCrearSubtipo() {
    if (!newSubtipoCodigo.trim() || !newSubtipoNombre.trim()) {
      notify('Codigo y nombre son requeridos', 'error')
      return
    }
    try {
      await api.crearSubtipoDocumento({
        tipo_codigo: 'SALIDA_INV',
        codigo: newSubtipoCodigo.trim().toUpperCase().replace(/\s+/g, '_'),
        nombre: newSubtipoNombre.trim(),
        genera_asiento: true,
        afecta_inventario: true,
        calcula_iva: false,
      })
      notify('Subtipo creado exitosamente', 'success')
      setShowNewSubtipo(false)
      setNewSubtipoCodigo('')
      setNewSubtipoNombre('')
      loadSubtipos()
    } catch (e: any) {
      notify(e?.message || 'Error al crear subtipo', 'error')
    }
  }

  function addLinea() {
    setLineas([...lineas, { ...emptyLinea }])
  }

  function removeLinea(idx: number) {
    if (lineas.length <= 1) return
    setLineas(lineas.filter((_, i) => i !== idx))
  }

  function updateLinea(idx: number, field: keyof LineaForm, value: any) {
    const copy = [...lineas]
    if (field === 'producto_id') {
      const prod = productos.find(p => p.id === value)
      copy[idx] = { ...copy[idx], producto_id: value, producto_nombre: prod?.nombre || '' }
    } else {
      copy[idx] = { ...copy[idx], [field]: value }
    }
    setLineas(copy)
  }

  function calcularTotal() {
    return lineas.reduce((sum, l) => {
      const prod = productos.find(p => p.id === l.producto_id)
      const costo = prod?.costo_promedio || 0
      return sum + (l.cantidad || 0) * costo
    }, 0)
  }

  function validate(): string | null {
    if (!fecha) return 'La fecha es requerida'
    if (!subtypeCode) return 'El tipo de salida es requerido'
    if (!bodegaId) return 'La bodega es requerida'
    if (!motivo.trim()) return 'El motivo es requerido'
    for (let i = 0; i < lineas.length; i++) {
      if (!lineas[i].producto_id) return `Linea ${i + 1}: seleccione un producto`
      if (!lineas[i].cantidad || lineas[i].cantidad <= 0) return `Linea ${i + 1}: cantidad invalida`
    }
    return null
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const error = validate()
    if (error) { notify(error, 'error'); return }
    setSaving(true)
    try {
      const payload: SalidaInventarioCreate = {
        fecha,
        subtype_code: subtypeCode,
        bodega_id: bodegaId,
        motivo: motivo.trim(),
        lineas: lineas.map(l => ({
          producto_id: l.producto_id,
          cantidad: l.cantidad,
        })),
      }
      const result = await api.crearSalidaInventario(payload)
      if (result.success) {
        notify('Salida de inventario registrada exitosamente', 'success')
        setShowForm(false)
        resetForm()
        loadData()
      } else {
        notify(result.errors?.join(', ') || 'Error al crear salida', 'error')
      }
    } catch (e: any) {
      notify(e?.message || 'Error al crear salida', 'error')
    }
    setSaving(false)
  }

  function resetForm() {
    setFecha(new Date().toISOString().split('T')[0])
    setSubtypeCode(subtipos[0]?.codigo || '')
    setBodegaId(bodegas[0]?.id || '')
    setMotivo('')
    setLineas([{ ...emptyLinea }])
  }

  function badgeColor(estado?: string) {
    switch (estado) {
      case 'CONTABILIZADO': return 'bg-green-900/50 text-green-300 border-green-700'
      case 'APROBADO': return 'bg-blue-900/50 text-blue-300 border-blue-700'
      case 'BORRADOR': return 'bg-yellow-900/50 text-yellow-300 border-yellow-700'
      case 'ANULADO': return 'bg-red-900/50 text-red-300 border-red-700'
      default: return 'bg-slate-700 text-slate-300 border-slate-600'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ClipboardList className="w-6 h-6 text-purple-400" />
          Salidas de Inventario
        </h1>
        <button onClick={() => { resetForm(); setShowForm(!showForm) }}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2">
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? 'Cancelar' : 'Nueva Salida'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-slate-800 rounded-xl p-6 border border-slate-700 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Fecha</label>
              <input type="date" value={fecha} onChange={e => setFecha(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Tipo de Salida</label>
              <div className="flex gap-2">
                <select value={subtypeCode} onChange={e => setSubtypeCode(e.target.value)}
                  className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                  {subtipos.length === 0 && <option value="">Sin subtipos — cree uno</option>}
                  {subtipos.map(s => (
                    <option key={s.codigo} value={s.codigo}>{s.nombre}</option>
                  ))}
                </select>
                <button type="button" onClick={() => setShowNewSubtipo(true)}
                  className="px-3 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 transition-colors"
                  title="Crear nuevo subtipo">
                  <Settings className="w-4 h-4" />
                </button>
              </div>
              {showNewSubtipo && (
                <div className="mt-2 p-3 bg-slate-700 rounded-lg border border-slate-600 space-y-2">
                  <p className="text-xs text-slate-400">Nuevo subtipo para SALIDA_INV</p>
                  <div className="flex gap-2">
                    <input type="text" value={newSubtipoCodigo} onChange={e => setNewSubtipoCodigo(e.target.value)}
                      placeholder="Codigo (ej: AUTOCONSUMO)"
                      className="flex-1 px-2 py-1 bg-slate-600 border border-slate-500 rounded text-white text-sm" />
                    <input type="text" value={newSubtipoNombre} onChange={e => setNewSubtipoNombre(e.target.value)}
                      placeholder="Nombre"
                      className="flex-1 px-2 py-1 bg-slate-600 border border-slate-500 rounded text-white text-sm" />
                    <button type="button" onClick={handleCrearSubtipo}
                      className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm">
                      Crear
                    </button>
                    <button type="button" onClick={() => setShowNewSubtipo(false)}
                      className="px-3 py-1 bg-slate-500 text-white rounded hover:bg-slate-400 text-sm">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Bodega</label>
              <select value={bodegaId} onChange={e => setBodegaId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white">
                <option value="">Seleccione...</option>
                {bodegas.map(b => (
                  <option key={b.id} value={b.id}>{b.nombre}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Motivo</label>
              <input type="text" value={motivo} onChange={e => setMotivo(e.target.value)}
                placeholder="Ej: Consumo interno"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-slate-400">Productos</label>
              <button type="button" onClick={addLinea}
                className="text-xs px-3 py-1 bg-slate-700 text-slate-300 rounded hover:bg-slate-600">
                + Agregar linea
              </button>
            </div>
            {lineas.map((l, i) => (
              <div key={i} className="flex gap-3 mb-2 items-start">
                <div className="flex-1">
                  <select value={l.producto_id} onChange={e => updateLinea(i, 'producto_id', e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm">
                    <option value="">Seleccione producto...</option>
                    {productos.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.codigo} - {p.nombre} (C$ {p.costo_promedio?.toFixed(2) || '0.00'})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="w-28">
                  <input type="number" step="0.01" min="0" value={l.cantidad} placeholder="Cant."
                    onChange={e => updateLinea(i, 'cantidad', parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm" />
                </div>
                <div className="w-24 pt-2 text-sm text-slate-300 text-right">
                  {(() => {
                    const prod = productos.find(p => p.id === l.producto_id)
                    const val = (l.cantidad || 0) * (prod?.costo_promedio || 0)
                    return `C$ ${val.toFixed(2)}`
                  })()}
                </div>
                <button type="button" onClick={() => removeLinea(i)}
                  className="pt-2 text-red-400 hover:text-red-300">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
            <div className="text-right text-sm text-slate-300 mt-2">
              <span className="font-semibold">Total: C$ {calcularTotal().toFixed(2)}</span>
            </div>
          </div>

          <button type="submit" disabled={saving}
            className="w-full py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors">
            {saving ? 'Procesando...' : 'Registrar Salida'}
          </button>
        </form>
      )}

      {loading ? (
        <Skeleton />
      ) : items.length === 0 ? (
        <EmptyState icon={<ClipboardList className="w-8 h-8 mx-auto mb-2 opacity-50" />}
          message="No hay salidas registradas" />
      ) : (
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Numero</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Concepto</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Estado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Asiento</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 text-sm text-white font-mono">{item.numero}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{item.fecha ? new Date(item.fecha).toLocaleDateString() : '-'}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{item.concepto}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs border ${badgeColor('CONTABILIZADO')}`}>
                        CONTABILIZADO
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300 font-mono">{item.numero}</td>
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
