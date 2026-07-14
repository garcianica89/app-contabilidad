import { useEffect, useState } from 'react'
import { api } from '../services/api'
import {
  Plus, X, Check, Pencil, Trash2, Search, AlertCircle,
  Database, TrendingDown, ArrowLeft, ArrowRight,
} from 'lucide-react'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'
import type { CuentaContable, ActivoFijo, CategoriaActivo, DepreciacionLinea } from '../types/api'

export default function ActivosFijosPage() {
  const { notify } = useNotification()
  const [activos, setActivos] = useState<ActivoFijo[]>([])
  const [categorias, setCategorias] = useState<CategoriaActivo[]>([])
  const [periodos, setPeriodos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterEstado, setFilterEstado] = useState('')
  const [filterCategoria, setFilterCategoria] = useState('')
  const [selected, setSelected] = useState<ActivoFijo | null>(null)
  const [depreciaciones, setDepreciaciones] = useState<DepreciacionLinea[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [showCatForm, setShowCatForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [catForm, setCatForm] = useState({ codigo: '', nombre: '', vida_util_default: '', metodo_depreciacion_default: 'LINEA_RECTA' })
  const [form, setForm] = useState({
    categoria_id: '', codigo: '', nombre: '', descripcion: '',
    fecha_adquisicion: new Date().toISOString().split('T')[0],
    costo_adquisicion: 0, valor_residual: 0, vida_util_anos: 5,
    metodo_depreciacion: 'LINEA_RECTA', ubicacion: '',
    cuenta_contable_id: '', cuenta_depreciacion_gasto_id: '',
    cuenta_depreciacion_acumulada_id: '', cuenta_baja_id: '',
  })
  const [cuentas, setCuentas] = useState<CuentaContable[]>([])

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [activosData, categoriasData, periodosData, cuentasData] = await Promise.all([
        api.getActivosFijos(),
        api.getCategoriasActivo(),
        api.getPeriodos(),
        api.getCuentasContables(),
      ])
      setActivos(activosData)
      setCategorias(categoriasData)
      setPeriodos(periodosData)
      setCuentas(cuentasData.filter(c => c.acepta_datos))
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function selectActivo(a: ActivoFijo) {
    setSelected(a)
    try {
      const d = await api.getDepreciacionesActivo(a.id)
      setDepreciaciones(d)
    } catch { setDepreciaciones([]) }
  }

  async function saveActivo(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        ...form,
        costo_adquisicion: Number(form.costo_adquisicion),
        valor_residual: Number(form.valor_residual),
        vida_util_anos: Number(form.vida_util_anos),
      }
      if (editId) {
        const updated = await api.actualizarActivoFijo(editId, payload)
        setActivos(prev => prev.map(a => a.id === editId ? updated : a))
      } else {
        const created = await api.crearActivoFijo(payload)
        setActivos(prev => [created, ...prev])
      }
      setShowForm(false)
    } catch (e) { console.error(e) }
    setSaving(false)
  }

  async function saveCategoria(e: React.FormEvent) {
    e.preventDefault()
    try {
      const cat = await api.crearCategoriaActivo({
        ...catForm,
        vida_util_default: catForm.vida_util_default ? Number(catForm.vida_util_default) : undefined,
      })
      setCategorias(prev => [...prev, cat])
      setShowCatForm(false)
    } catch (e) { console.error(e) }
  }

  async function depreciar(activoId: string) {
    const periodoId = prompt('ID del periodo (vacio = ultimo abierto):')
    if (!periodoId) return
    try {
      const result: any = await api.depreciarActivo(activoId, periodoId)
      notify(`Depreciacion: C$${result.monto}\nValor libros: C$${result.valor_libros}`, 'success')
      loadData()
    } catch (e: any) { notify(e.message) }
  }

  async function darBaja(activo: ActivoFijo) {
    const fecha = prompt('Fecha de baja (YYYY-MM-DD):', new Date().toISOString().split('T')[0])
    if (!fecha) return
    const motivo = prompt('Motivo de baja:')
    if (!motivo) return
    try {
      await api.darBajaActivo(activo.id, { fecha_baja: fecha, motivo_baja: motivo })
      loadData()
      if (selected?.id === activo.id) setSelected(null)
    } catch (e: any) { notify(e.message) }
  }

  function openCreate() {
    setEditId(null); setForm({
      categoria_id: categorias[0]?.id || '', codigo: '', nombre: '', descripcion: '',
      fecha_adquisicion: new Date().toISOString().split('T')[0],
      costo_adquisicion: 0, valor_residual: 0, vida_util_anos: 5,
      metodo_depreciacion: 'LINEA_RECTA', ubicacion: '',
      cuenta_contable_id: '', cuenta_depreciacion_gasto_id: '',
      cuenta_depreciacion_acumulada_id: '', cuenta_baja_id: '',
    }); setShowForm(true)
  }

  function openEdit(a: ActivoFijo) {
    setEditId(a.id); setForm({
      categoria_id: a.categoria_id, codigo: a.codigo, nombre: a.nombre,
      descripcion: a.descripcion || '', fecha_adquisicion: a.fecha_adquisicion,
      costo_adquisicion: a.costo_adquisicion, valor_residual: a.valor_residual,
      vida_util_anos: a.vida_util_anos, metodo_depreciacion: a.metodo_depreciacion,
      ubicacion: a.ubicacion || '',
      cuenta_contable_id: a.cuenta_contable_id || '',
      cuenta_depreciacion_gasto_id: a.cuenta_depreciacion_gasto_id || '',
      cuenta_depreciacion_acumulada_id: a.cuenta_depreciacion_acumulada_id || '',
      cuenta_baja_id: a.cuenta_baja_id || '',
    }); setShowForm(true)
  }

  async function eliminar(id: string) {
    if (!confirm('Eliminar este activo?')) return
    await api.eliminarActivoFijo(id)
    setActivos(prev => prev.filter(a => a.id !== id))
    if (selected?.id === id) setSelected(null)
  }

  const filtrados = activos.filter(a => {
    if (filterEstado && a.estado !== filterEstado) return false
    if (filterCategoria && a.categoria_id !== filterCategoria) return false
    if (search && !a.nombre.toLowerCase().includes(search.toLowerCase()) && !a.codigo.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  function statusBadge(estado: string) {
    const styles: Record<string, string> = {
      ACTIVO: 'bg-emerald-600/20 text-emerald-400',
      DEPRECIADO_TOTAL: 'bg-blue-600/20 text-blue-400',
      BAJA: 'bg-red-600/20 text-red-400',
      VENDIDO: 'bg-amber-600/20 text-amber-400',
    }
    return <span className={`text-xs px-2 py-0.5 rounded-full ${styles[estado] || 'bg-slate-600/20 text-slate-400'}`}>{estado}</span>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Activos Fijos</h1>
          <p className="text-slate-400 text-sm mt-1">Registro, depreciacion y control de activos fijos</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCatForm(true)} className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm font-medium">
            <Database className="w-4 h-4" /> Categorias
          </button>
          <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium">
            <Plus className="w-4 h-4" /> Nuevo Activo
          </button>
        </div>
      </div>

      {showCatForm && (
        <form onSubmit={saveCategoria} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nueva Categoria</h3>
            <button type="button" onClick={() => setShowCatForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
              <input value={catForm.codigo} onChange={e => setCatForm(f => ({ ...f, codigo: e.target.value }))} className="input-filter w-full" required placeholder="EQP" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={catForm.nombre} onChange={e => setCatForm(f => ({ ...f, nombre: e.target.value }))} className="input-filter w-full" required placeholder="Equipo de Computo" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Vida Util Default (anos)</label>
              <input type="number" value={catForm.vida_util_default} onChange={e => setCatForm(f => ({ ...f, vida_util_default: e.target.value }))} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Metodo Dep. Default</label>
              <select value={catForm.metodo_depreciacion_default} onChange={e => setCatForm(f => ({ ...f, metodo_depreciacion_default: e.target.value }))} className="input-filter w-full">
                <option value="LINEA_RECTA">Linea Recta</option>
                <option value="DOBLE_DECLINANTE">Doble Declinante</option>
                <option value="SUMA_DIGITOS">Suma de Digitos</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" className="btn-primary flex items-center gap-2"><Check className="w-4 h-4" /> Guardar</button>
            <button type="button" onClick={() => setShowCatForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {showForm && (
        <form onSubmit={saveActivo} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar Activo' : 'Nuevo Activo Fijo'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Categoria *</label>
              <select value={form.categoria_id} onChange={e => setForm(f => ({ ...f, categoria_id: e.target.value }))} className="input-filter w-full" required>
                <option value="">Seleccionar</option>
                {categorias.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
              <input value={form.codigo} onChange={e => setForm(f => ({ ...f, codigo: e.target.value }))} className="input-filter w-full" required placeholder="AF-001" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} className="input-filter w-full" required placeholder="Laptop Dell Latitude" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha Adquisicion *</label>
              <input type="date" value={form.fecha_adquisicion} onChange={e => setForm(f => ({ ...f, fecha_adquisicion: e.target.value }))} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Costo Adquisicion *</label>
              <input type="number" step="0.01" value={form.costo_adquisicion} onChange={e => setForm(f => ({ ...f, costo_adquisicion: Number(e.target.value) }))} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Valor Residual</label>
              <input type="number" step="0.01" value={form.valor_residual} onChange={e => setForm(f => ({ ...f, valor_residual: Number(e.target.value) }))} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Vida Util (anos) *</label>
              <input type="number" value={form.vida_util_anos} onChange={e => setForm(f => ({ ...f, vida_util_anos: Number(e.target.value) }))} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Metodo Depreciacion *</label>
              <select value={form.metodo_depreciacion} onChange={e => setForm(f => ({ ...f, metodo_depreciacion: e.target.value }))} className="input-filter w-full">
                <option value="LINEA_RECTA">Linea Recta</option>
                <option value="DOBLE_DECLINANTE">Doble Declinante</option>
                <option value="SUMA_DIGITOS">Suma de Digitos</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Ubicacion</label>
              <input value={form.ubicacion} onChange={e => setForm(f => ({ ...f, ubicacion: e.target.value }))} className="input-filter w-full" placeholder="Oficina Central" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Descripcion</label>
              <input value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} className="input-filter w-full" placeholder="Detalles del activo" />
            </div>
          </div>
          <div className="border-t border-slate-700/50 pt-4">
            <h4 className="text-xs font-semibold text-slate-400 uppercase mb-3">Cuentas Contables</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Cuenta Activo (Alta)</label>
                <select value={form.cuenta_contable_id} onChange={e => setForm(f => ({ ...f, cuenta_contable_id: e.target.value }))} className="input-filter w-full text-xs">
                  <option value="">Sin asignar</option>
                  {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Gasto Depreciacion</label>
                <select value={form.cuenta_depreciacion_gasto_id} onChange={e => setForm(f => ({ ...f, cuenta_depreciacion_gasto_id: e.target.value }))} className="input-filter w-full text-xs">
                  <option value="">Sin asignar</option>
                  {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Dep. Acumulada</label>
                <select value={form.cuenta_depreciacion_acumulada_id} onChange={e => setForm(f => ({ ...f, cuenta_depreciacion_acumulada_id: e.target.value }))} className="input-filter w-full text-xs">
                  <option value="">Sin asignar</option>
                  {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Resultado Baja</label>
                <select value={form.cuenta_baja_id} onChange={e => setForm(f => ({ ...f, cuenta_baja_id: e.target.value }))} className="input-filter w-full text-xs">
                  <option value="">Sin asignar</option>
                  {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'} Activo</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={e => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar activo..." />
        </div>
        <select value={filterEstado} onChange={e => setFilterEstado(e.target.value)} className="input-filter w-40">
          <option value="">Todos estados</option>
          <option value="ACTIVO">Activo</option>
          <option value="DEPRECIADO_TOTAL">Depreciado Total</option>
          <option value="BAJA">Dado de Baja</option>
        </select>
        <select value={filterCategoria} onChange={e => setFilterCategoria(e.target.value)} className="input-filter w-48">
          <option value="">Todas categorias</option>
          {categorias.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2">
          {loading ? (
            <div className="text-slate-500 text-center py-8">Cargando...</div>
          ) : filtrados.length === 0 ? (
            <div className="text-slate-500 text-sm text-center py-8">Sin activos registrados</div>
          ) : filtrados.map(a => (
            <div
              key={a.id}
              onClick={() => selectActivo(a)}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selected?.id === a.id
                  ? 'bg-primary-600/20 border-primary-500/40 text-primary-300'
                  : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono text-slate-500">{a.codigo}</span>
                {statusBadge(a.estado)}
              </div>
              <div className="font-medium text-sm">{a.nombre}</div>
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>Costo: C$ {a.costo_adquisicion.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</span>
                <span>Libros: C$ {a.valor_libros.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-slate-600">{a.categoria_nombre}</span>
                <div className="flex gap-1">
                  <button onClick={e => { e.stopPropagation(); openEdit(a) }} className="p-1 hover:bg-slate-800 rounded text-slate-500 hover:text-slate-200">
                    <Pencil className="w-3 h-3" />
                  </button>
                  {a.estado === 'ACTIVO' && (
                    <button onClick={e => { e.stopPropagation(); depreciar(a.id) }} className="p-1 hover:bg-slate-800 rounded text-slate-500 hover:text-emerald-400" title="Depreciar">
                      <TrendingDown className="w-3 h-3" />
                    </button>
                  )}
                  {a.estado === 'ACTIVO' && (
                    <button onClick={e => { e.stopPropagation(); darBaja(a) }} className="p-1 hover:bg-slate-800 rounded text-slate-500 hover:text-red-400" title="Dar de Baja">
                      <X className="w-3 h-3" />
                    </button>
                  )}
                  <button onClick={e => { e.stopPropagation(); eliminar(a.id) }} className="p-1 hover:bg-slate-800 rounded text-slate-500 hover:text-red-400">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="lg:col-span-2">
          {selected ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                  {selected.codigo} - {selected.nombre}
                </h2>
                {statusBadge(selected.estado)}
              </div>

              <div className="grid grid-cols-4 gap-3 mb-4">
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Costo Adquisicion</div>
                  <div className="text-lg font-bold text-white font-mono">C$ {selected.costo_adquisicion.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
                </div>
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Valor Libros</div>
                  <div className="text-lg font-bold text-emerald-400 font-mono">C$ {selected.valor_libros.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
                </div>
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Dep. Acumulada</div>
                  <div className="text-lg font-bold text-amber-400 font-mono">C$ {selected.depreciacion_acumulada.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
                </div>
                <div className="card !p-3 text-center">
                  <div className="text-xs text-slate-500 mb-1">Valor Residual</div>
                  <div className="text-lg font-bold text-slate-400 font-mono">C$ {selected.valor_residual.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="card !p-3">
                  <div className="text-xs text-slate-500 space-y-1">
                    <p><span className="text-slate-400">Categoria:</span> {selected.categoria_nombre}</p>
                    <p><span className="text-slate-400">Fecha Adq.:</span> {selected.fecha_adquisicion}</p>
                    <p><span className="text-slate-400">Vida Util:</span> {selected.vida_util_anos} anos</p>
                    <p><span className="text-slate-400">Metodo:</span> {selected.metodo_depreciacion}</p>
                  </div>
                </div>
                <div className="card !p-3">
                  <div className="text-xs text-slate-500 space-y-1">
                    <p><span className="text-slate-400">Ubicacion:</span> {selected.ubicacion || '-'}</p>
                    <p><span className="text-slate-400">Descripcion:</span> {selected.descripcion || '-'}</p>
                    {selected.estado === 'BAJA' && (
                      <>
                        <p><span className="text-red-400">Fecha Baja:</span> {selected.fecha_baja}</p>
                        <p><span className="text-red-400">Motivo:</span> {selected.motivo_baja}</p>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Historial de Depreciacion</h3>
              {depreciaciones.length === 0 ? (
              <EmptyState
                message="Sin depreciaciones registradas"
                className="bg-slate-900 rounded-lg border border-slate-800"
              />
              ) : (
                <div className="card overflow-hidden !p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700/50">
                          <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Fecha</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Monto</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Dep. Acumulada</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Valor Libros</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/50">
                        {depreciaciones.map(d => (
                          <tr key={d.id} className="hover:bg-slate-800/30">
                            <td className="px-4 py-3 text-slate-400 text-xs">{d.fecha_depreciacion}</td>
                            <td className="px-4 py-3 text-right font-mono text-sm text-amber-400">C$ {d.monto_depreciacion.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</td>
                            <td className="px-4 py-3 text-right font-mono text-sm text-slate-300">C$ {d.depreciacion_acumulada.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</td>
                            <td className="px-4 py-3 text-right font-mono text-sm text-emerald-400">C$ {d.valor_libros_despues.toLocaleString('es-NI', { minimumFractionDigits: 2 })}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-500">
              <div className="text-center">
                <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Selecciona un activo para ver detalles</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
