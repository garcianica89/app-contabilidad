import { useState, useEffect } from 'react'
import {
  Settings, Search, Plus, Pencil, X, Check, AlertCircle, Trash2,
  DollarSign, BadgePercent, CalendarDays, Banknote,
} from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'

type Tab = 'parametros' | 'monedas' | 'tipos-cambio' | 'condiciones-pago' | 'impuestos'

export default function ConfiguracionPage() {
  const [tab, setTab] = useState<Tab>('parametros')
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Configuracion</h1>
          <p className="text-sm text-slate-400">Parametros del sistema, monedas, impuestos y mas</p>
        </div>
      </div>

      <div className="flex gap-1 border-b border-slate-800 overflow-x-auto">
        {([
          ['parametros', 'Parametros', Settings],
          ['monedas', 'Monedas', DollarSign],
          ['tipos-cambio', 'Tipos de Cambio', CalendarDays],
          ['condiciones-pago', 'Condiciones Pago', Banknote],
          ['impuestos', 'Impuestos', BadgePercent],
        ] as [Tab, string, any][]).map(([key, label, Icon]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === key
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}>
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)}
          className="input-filter w-full pl-10" placeholder={`Buscar en ${tab}...`} />
      </div>

      {tab === 'parametros' && <ParametrosTab search={search} />}
      {tab === 'monedas' && <MonedasTab search={search} />}
      {tab === 'tipos-cambio' && <TiposCambioTab search={search} />}
      {tab === 'condiciones-pago' && <CondicionesPagoTab search={search} />}
      {tab === 'impuestos' && <ImpuestosTab search={search} />}
    </div>
  )
}

function ParametrosTab({ search }: { search: string }) {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({ grupo: '', clave: '', valor: '', tipo_dato: 'TEXTO' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { setItems(await api.getParametros()) } catch {}
    setLoading(false)
  }

  const filtered = items.filter((i) =>
    !search || i.grupo.toLowerCase().includes(search.toLowerCase()) ||
    i.clave.toLowerCase().includes(search.toLowerCase()) ||
    (i.valor || '').toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() { setEditId(null); setForm({ grupo: '', clave: '', valor: '', tipo_dato: 'TEXTO' }); setShowForm(true) }
  function openEdit(i: any) { setEditId(i.id); setForm({ grupo: i.grupo, clave: i.clave, valor: i.valor || '', tipo_dato: i.tipo_dato }); setShowForm(true) }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const data = editId ? await api.actualizarParametro(editId, form) : await api.crearParametro(form)
      setItems((prev) => editId ? prev.map((i) => (i.id === editId ? data : i)) : [...prev, data])
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDelete(id: string) {
    if (!confirm('Eliminar parametro?')) return
    try { await api.eliminarParametro(id); setItems((prev) => prev.filter((i) => i.id !== id)) }
    catch (err: any) { notify(err.message) }
  }

  return (
    <>
      <div className="flex justify-end">
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo Parametro
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar Parametro' : 'Nuevo Parametro'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Grupo *</label>
              <input value={form.grupo} onChange={(e) => setForm({ ...form, grupo: e.target.value })} className="input-filter w-full" required placeholder="CONTABILIDAD" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Clave *</label>
              <input value={form.clave} onChange={(e) => setForm({ ...form, clave: e.target.value })} className="input-filter w-full" required placeholder="PERIODO_ACTIVO" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Valor</label>
              <input value={form.valor} onChange={(e) => setForm({ ...form, valor: e.target.value })} className="input-filter w-full" placeholder="2026-01" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo Dato</label>
              <select value={form.tipo_dato} onChange={(e) => setForm({ ...form, tipo_dato: e.target.value })} className="input-filter w-full">
                <option value="TEXTO">Texto</option>
                <option value="NUMERO">Numero</option>
                <option value="BOOLEANO">Booleano</option>
                <option value="FECHA">Fecha</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'}</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? <Skeleton /> : filtered.length === 0 ? <EmptyState /> : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Grupo</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Clave</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Valor</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Tipo</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filtered.map((i) => (
                  <tr key={i.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3"><span className="text-xs font-medium text-primary-400">{i.grupo}</span></td>
                    <td className="px-4 py-3"><span className="text-slate-200 font-mono text-xs">{i.clave}</span></td>
                    <td className="px-4 py-3"><span className="text-slate-400 text-xs">{i.valor || '-'}</span></td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-700/50 text-slate-400">{i.tipo_dato}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        <button onClick={() => openEdit(i)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                        <button onClick={() => handleDelete(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}

function MonedasTab({ search }: { search: string }) {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({ codigo: '', nombre: '', simbolo: '', tasa_cambio: 1, es_base: false })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { setItems(await api.getMonedas()) } catch {}
    setLoading(false)
  }

  const filtered = items.filter((i) =>
    !search || i.codigo.toLowerCase().includes(search.toLowerCase()) ||
    i.nombre.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() { setEditId(null); setForm({ codigo: '', nombre: '', simbolo: '', tasa_cambio: 1, es_base: false }); setShowForm(true) }
  function openEdit(i: any) { setEditId(i.id); setForm({ codigo: i.codigo, nombre: i.nombre, simbolo: i.simbolo, tasa_cambio: i.tasa_cambio, es_base: i.es_base }); setShowForm(true) }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const data = editId ? await api.actualizarMoneda(editId, form) : await api.crearMoneda(form)
      setItems((prev) => editId ? prev.map((i) => (i.id === editId ? data : i)) : [...prev, data])
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDelete(id: string) {
    if (!confirm('Eliminar moneda?')) return
    try { await api.eliminarMoneda(id); setItems((prev) => prev.filter((i) => i.id !== id)) }
    catch (err: any) { notify(err.message) }
  }

  return (
    <>
      <div className="flex justify-end">
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Moneda
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar Moneda' : 'Nueva Moneda'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
              <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value.toUpperCase() })} className="input-filter w-full" required placeholder="USD" maxLength={3} />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Dolar Estadounidense" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Simbolo *</label>
              <input value={form.simbolo} onChange={(e) => setForm({ ...form, simbolo: e.target.value })} className="input-filter w-full" required placeholder="U$" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tasa de Cambio</label>
              <input type="number" step="0.0001" value={form.tasa_cambio} onChange={(e) => setForm({ ...form, tasa_cambio: Number(e.target.value) })} className="input-filter w-full" />
            </div>
            <div className="flex items-end pb-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.es_base} onChange={(e) => setForm({ ...form, es_base: e.target.checked })} className="rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500" />
                <span className="text-xs text-slate-400">Moneda Base</span>
              </label>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? <Skeleton /> : filtered.length === 0 ? <EmptyState /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i) => (
            <div key={i.id} className="card relative">
              <div className="absolute top-3 right-3 flex gap-1">
                <button onClick={() => openEdit(i)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                <button onClick={() => handleDelete(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
              </div>
              <div className="text-2xl font-bold text-white mb-1">{i.simbolo}</div>
              <div className="text-sm font-semibold text-slate-200">{i.codigo} - {i.nombre}</div>
              <div className="text-xs text-slate-500 mt-1">
                TC: <span className="font-mono text-emerald-400">{i.tasa_cambio.toLocaleString('es-NI', { minimumFractionDigits: 4 })}</span>
              </div>
              {i.es_base && <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded bg-primary-600/20 text-primary-400">Base</span>}
            </div>
          ))}
        </div>
      )}
    </>
  )
}

function TiposCambioTab({ search }: { search: string }) {
  const [items, setItems] = useState<any[]>([])
  const [monedas, setMonedas] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ moneda_id: '', fecha: new Date().toISOString().split('T')[0], tasa_compra: 0, tasa_venta: 0 })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { const [t, m] = await Promise.all([api.getTiposCambio(), api.getMonedas()]); setItems(t); setMonedas(m) } catch {}
    setLoading(false)
  }

  const monedaMap = Object.fromEntries(monedas.map((m) => [m.id, m]))
  const filtered = items.filter((i) => {
    if (!search) return true
    const mon = monedaMap[i.moneda_id]
    return mon?.codigo?.toLowerCase().includes(search.toLowerCase()) ||
      mon?.nombre?.toLowerCase().includes(search.toLowerCase()) ||
      i.fecha?.includes(search)
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const data = await api.crearTipoCambio({
        ...form,
        tasa_compra: Number(form.tasa_compra),
        tasa_venta: Number(form.tasa_venta),
      })
      setItems((prev) => [data, ...prev])
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDelete(id: string) {
    if (!confirm('Eliminar tipo de cambio?')) return
    try { await api.eliminarTipoCambio(id); setItems((prev) => prev.filter((i) => i.id !== id)) }
    catch (err: any) { notify(err.message) }
  }

  return (
    <>
      <div className="flex justify-end">
        <button onClick={() => { setShowForm(true); setForm({ moneda_id: '', fecha: new Date().toISOString().split('T')[0], tasa_compra: 0, tasa_venta: 0 }) }}
          className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo Tipo de Cambio
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nuevo Tipo de Cambio</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Moneda *</label>
              <select value={form.moneda_id} onChange={(e) => setForm({ ...form, moneda_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar...</option>
                {monedas.filter((m) => !m.es_base).map((m) => <option key={m.id} value={m.id}>{m.codigo} - {m.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha *</label>
              <input type="date" value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tasa Compra *</label>
              <input type="number" step="0.0001" value={form.tasa_compra} onChange={(e) => setForm({ ...form, tasa_compra: Number(e.target.value) })} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tasa Venta *</label>
              <input type="number" step="0.0001" value={form.tasa_venta} onChange={(e) => setForm({ ...form, tasa_venta: Number(e.target.value) })} className="input-filter w-full" required />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> Crear</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? <Skeleton /> : filtered.length === 0 ? <EmptyState /> : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Moneda</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Fecha</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Compra</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Venta</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filtered.map((i) => (
                  <tr key={i.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3"><span className="text-xs font-medium text-primary-400">{monedaMap[i.moneda_id]?.codigo || i.moneda_id}</span></td>
                    <td className="px-4 py-3"><span className="text-slate-300 text-xs">{i.fecha}</span></td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-emerald-400">{i.tasa_compra?.toLocaleString('es-NI', { minimumFractionDigits: 4 })}</td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-red-400">{i.tasa_venta?.toLocaleString('es-NI', { minimumFractionDigits: 4 })}</td>
                    <td className="px-4 py-3 text-center">
                      <button onClick={() => handleDelete(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}

function CondicionesPagoTab({ search }: { search: string }) {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({ codigo: '', nombre: '', dias_neto: 0, descuento_contado: 0 })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { setItems(await api.getCondicionesPago()) } catch {}
    setLoading(false)
  }

  const filtered = items.filter((i) =>
    !search || i.codigo.toLowerCase().includes(search.toLowerCase()) ||
    i.nombre.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() { setEditId(null); setForm({ codigo: '', nombre: '', dias_neto: 0, descuento_contado: 0 }); setShowForm(true) }
  function openEdit(i: any) { setEditId(i.id); setForm({ codigo: i.codigo, nombre: i.nombre, dias_neto: i.dias_neto, descuento_contado: i.descuento_contado }); setShowForm(true) }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const data = editId ? await api.actualizarCondicionPago(editId, form) : await api.crearCondicionPago(form)
      setItems((prev) => editId ? prev.map((i) => (i.id === editId ? data : i)) : [...prev, data])
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDelete(id: string) {
    if (!confirm('Eliminar condicion de pago?')) return
    try { await api.eliminarCondicionPago(id); setItems((prev) => prev.filter((i) => i.id !== id)) }
    catch (err: any) { notify(err.message) }
  }

  return (
    <>
      <div className="flex justify-end">
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Condicion de Pago
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar' : 'Nueva'} Condicion de Pago</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
              <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} className="input-filter w-full" required placeholder="30D" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="30 Dias" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Dias Neto</label>
              <input type="number" value={form.dias_neto} onChange={(e) => setForm({ ...form, dias_neto: Number(e.target.value) })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Descuento Contado (%)</label>
              <input type="number" step="0.01" value={form.descuento_contado} onChange={(e) => setForm({ ...form, descuento_contado: Number(e.target.value) })} className="input-filter w-full" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? <Skeleton /> : filtered.length === 0 ? <EmptyState /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i) => (
            <div key={i.id} className="card relative">
              <div className="absolute top-3 right-3 flex gap-1">
                <button onClick={() => openEdit(i)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                <button onClick={() => handleDelete(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
              </div>
              <div className="text-sm font-semibold text-white">{i.codigo}</div>
              <div className="text-xs text-slate-400">{i.nombre}</div>
              <div className="flex gap-4 mt-2 text-xs">
                <span className="text-slate-500">Neto: <span className="text-slate-300 font-mono">{i.dias_neto}d</span></span>
                {i.descuento_contado > 0 && (
                  <span className="text-emerald-400">Dto: {i.descuento_contado}%</span>
                )}
              </div>
              {!i.activa && <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded bg-red-600/20 text-red-400">Inactiva</span>}
            </div>
          ))}
        </div>
      )}
    </>
  )
}

function ImpuestosTab({ search }: { search: string }) {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({ codigo: '', nombre: '', tipo: 'IVA', tasa: 0, cuenta_contable_id: '' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { setItems(await api.getImpuestos()) } catch {}
    setLoading(false)
  }

  const filtered = items.filter((i) =>
    !search || i.codigo.toLowerCase().includes(search.toLowerCase()) ||
    i.nombre.toLowerCase().includes(search.toLowerCase()) ||
    i.tipo.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() { setEditId(null); setForm({ codigo: '', nombre: '', tipo: 'IVA', tasa: 0, cuenta_contable_id: '' }); setShowForm(true) }
  function openEdit(i: any) { setEditId(i.id); setForm({ codigo: i.codigo, nombre: i.nombre, tipo: i.tipo, tasa: i.tasa, cuenta_contable_id: i.cuenta_contable_id || '' }); setShowForm(true) }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const payload = { ...form, cuenta_contable_id: form.cuenta_contable_id || null }
      const data = editId ? await api.actualizarImpuesto(editId, payload) : await api.crearImpuesto(payload)
      setItems((prev) => editId ? prev.map((i) => (i.id === editId ? data : i)) : [...prev, data])
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDelete(id: string) {
    if (!confirm('Eliminar impuesto?')) return
    try { await api.eliminarImpuesto(id); setItems((prev) => prev.filter((i) => i.id !== id)) }
    catch (err: any) { notify(err.message) }
  }

  return (
    <>
      <div className="flex justify-end">
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo Impuesto
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar' : 'Nuevo'} Impuesto</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
              <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} className="input-filter w-full" required placeholder="IVA_15" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="IVA 15%" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-filter w-full">
                <option value="IVA">IVA</option>
                <option value="IR">IR</option>
                <option value="MUNICIPAL">Municipal</option>
                <option value="OTRO">Otro</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tasa (%) *</label>
              <input type="number" step="0.001" value={form.tasa} onChange={(e) => setForm({ ...form, tasa: Number(e.target.value) })} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta Contable</label>
              <input value={form.cuenta_contable_id} onChange={(e) => setForm({ ...form, cuenta_contable_id: e.target.value })} className="input-filter w-full font-mono text-xs" placeholder="UUID de la cuenta" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? <Skeleton /> : filtered.length === 0 ? <EmptyState /> : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Codigo</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Nombre</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Tipo</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Tasa</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Estado</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filtered.map((i) => (
                  <tr key={i.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3"><span className="text-xs font-medium text-primary-400">{i.codigo}</span></td>
                    <td className="px-4 py-3"><span className="text-slate-300 text-xs">{i.nombre}</span></td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-700/50 text-slate-400">{i.tipo}</span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-emerald-400">{i.tasa}%</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        i.activa ? 'bg-emerald-600/20 text-emerald-400' : 'bg-red-600/20 text-red-400'
                      }`}>{i.activa ? 'Activo' : 'Inactivo'}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button onClick={() => openEdit(i)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                        <button onClick={() => handleDelete(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}


