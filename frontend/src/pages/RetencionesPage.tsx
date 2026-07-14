import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, Percent } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import type { Retencion, CuentaContable, CentroCosto } from '../types/api'

const emptyForm = {
  codigo: '', nombre: '', descripcion: '', tipo: 'IR', porcentaje: 0,
  aplica_a: 'NACIONAL', monto_minimo: undefined as number | undefined,
  base_imponible: 'SUBTOTAL', prioridad: 10, redondeo: 2, naturaleza: 'CREDITO',
  cuenta_retencion_id: '', cuenta_pagar_id: '', cuenta_cobrar_id: '', centro_costo_id: '',
  vigencia_desde: new Date().toISOString().split('T')[0],
  vigencia_hasta: '' as string | undefined,
}

export default function RetencionesPage() {
  const [items, setItems] = useState<Retencion[]>([])
  const [cuentas, setCuentas] = useState<CuentaContable[]>([])
  const [centrosCosto, setCentrosCosto] = useState<CentroCosto[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([
      api.getRetenciones(),
      api.getCuentasContables(),
      api.getCentrosCosto(),
    ]).then(([r, c, cc]) => {
      setItems(r)
      setCuentas(c)
      setCentrosCosto(cc)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const filtered = items.filter((i) =>
    !search || i.codigo.toLowerCase().includes(search.toLowerCase()) ||
    i.nombre.toLowerCase().includes(search.toLowerCase()) ||
    i.tipo.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() { setEditId(null); setForm(emptyForm); setShowForm(true) }

  function openEdit(r: Retencion) {
    setEditId(r.id)
    setForm({
      codigo: r.codigo, nombre: r.nombre,
      descripcion: r.descripcion || '',
      tipo: r.tipo, porcentaje: r.porcentaje,
      aplica_a: r.aplica_a,
      monto_minimo: r.monto_minimo,
      base_imponible: r.base_imponible,
      prioridad: r.prioridad,
      redondeo: r.redondeo,
      naturaleza: r.naturaleza,
      cuenta_retencion_id: r.cuenta_retencion_id || '',
      cuenta_pagar_id: r.cuenta_pagar_id || '',
      cuenta_cobrar_id: r.cuenta_cobrar_id || '',
      centro_costo_id: r.centro_costo_id || '',
      vigencia_desde: r.vigencia_desde,
      vigencia_hasta: r.vigencia_hasta || '',
    })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const payload: any = {
        ...form,
        vigencia_hasta: form.vigencia_hasta || null,
        monto_minimo: form.monto_minimo || null,
        cuenta_retencion_id: form.cuenta_retencion_id || null,
        cuenta_pagar_id: form.cuenta_pagar_id || null,
        cuenta_cobrar_id: form.cuenta_cobrar_id || null,
        centro_costo_id: form.centro_costo_id || null,
      }
      const data = editId
        ? await api.actualizarRetencion(editId, payload)
        : await api.crearRetencion(payload)
      setItems((prev) => editId ? prev.map((i) => (i.id === editId ? data : i)) : [...prev, data])
      setShowForm(false)
    } catch (err: any) { alert(err.message) }
    setSaving(false)
  }

  async function handleToggleActivo(r: Retencion) {
    try {
      await api.actualizarRetencion(r.id, { is_active: !r.is_active })
      setItems((prev) => prev.map((i) => i.id === r.id ? { ...i, is_active: !i.is_active } : i))
    } catch {}
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Retenciones</h1>
          <p className="text-sm text-slate-400">Catalogo de retenciones completamente configurable</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Retencion
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar' : 'Nueva'} Retencion</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
              <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} className="input-filter w-full" required placeholder="IR_2" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="IR 2%" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-filter w-full">
                <option value="IR">IR</option>
                <option value="IVA">IVA</option>
                <option value="MUNICIPAL">Municipal</option>
                <option value="OTRO">Otro</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Porcentaje (%) *</label>
              <input type="number" step="0.01" min="0" max="100" value={form.porcentaje}
                onChange={(e) => setForm({ ...form, porcentaje: Number(e.target.value) })}
                className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Aplica a</label>
              <select value={form.aplica_a} onChange={(e) => setForm({ ...form, aplica_a: e.target.value })} className="input-filter w-full">
                <option value="NACIONAL">Nacional</option>
                <option value="EXTRANJERO">Extranjero</option>
                <option value="AMBOS">Ambos</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Base Imponible</label>
              <select value={form.base_imponible} onChange={(e) => setForm({ ...form, base_imponible: e.target.value })} className="input-filter w-full">
                <option value="SUBTOTAL">Subtotal</option>
                <option value="TOTAL">Total</option>
                <option value="MONTO">Monto</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Naturaleza</label>
              <select value={form.naturaleza} onChange={(e) => setForm({ ...form, naturaleza: e.target.value })} className="input-filter w-full">
                <option value="DEBITO">Debito</option>
                <option value="CREDITO">Credito</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Prioridad</label>
              <input type="number" min="1" max="999" value={form.prioridad}
                onChange={(e) => setForm({ ...form, prioridad: Number(e.target.value) })}
                className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Redondeo (decimales)</label>
              <input type="number" min="0" max="6" value={form.redondeo}
                onChange={(e) => setForm({ ...form, redondeo: Number(e.target.value) })}
                className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Monto Minimo</label>
              <input type="number" step="0.01" value={form.monto_minimo || ''}
                onChange={(e) => setForm({ ...form, monto_minimo: e.target.value ? Number(e.target.value) : undefined })}
                className="input-filter w-full" placeholder="0" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Vigencia Desde *</label>
              <input type="date" value={form.vigencia_desde} onChange={(e) => setForm({ ...form, vigencia_desde: e.target.value })} className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Vigencia Hasta</label>
              <input type="date" value={form.vigencia_hasta || ''} onChange={(e) => setForm({ ...form, vigencia_hasta: e.target.value || undefined })} className="input-filter w-full" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Descripcion</label>
              <textarea value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
                className="input-filter w-full" rows={2} placeholder="Descripcion opcional" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta Contable (retencion)</label>
              <select value={form.cuenta_retencion_id} onChange={(e) => setForm({ ...form, cuenta_retencion_id: e.target.value })} className="input-filter w-full">
                <option value="">Seleccionar cuenta</option>
                {cuentas.map((c) => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta por Pagar</label>
              <select value={form.cuenta_pagar_id} onChange={(e) => setForm({ ...form, cuenta_pagar_id: e.target.value })} className="input-filter w-full">
                <option value="">Seleccionar cuenta</option>
                {cuentas.map((c) => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta por Cobrar</label>
              <select value={form.cuenta_cobrar_id} onChange={(e) => setForm({ ...form, cuenta_cobrar_id: e.target.value })} className="input-filter w-full">
                <option value="">Seleccionar cuenta</option>
                {cuentas.map((c) => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Centro de Costo</label>
              <select value={form.centro_costo_id} onChange={(e) => setForm({ ...form, centro_costo_id: e.target.value })} className="input-filter w-full">
                <option value="">Sin centro de costo</option>
                {centrosCosto.map((cc) => <option key={cc.id} value={cc.id}>{cc.codigo} - {cc.nombre}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'} Retencion</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar retencion..." />
        </div>
        <span className="text-xs text-slate-500">{filtered.length} registros</span>
      </div>

      {loading ? <Skeleton rows={5} /> : filtered.length === 0 ? (
        <EmptyState message={search ? 'Ninguna retencion coincide' : 'No hay retenciones registradas'} />
      ) : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Codigo</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Nombre</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Tipo</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">%</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Base</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Nat.</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Pri.</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Activa</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400 w-20">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filtered.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3"><span className="text-slate-400 font-mono text-xs">{r.codigo}</span></td>
                    <td className="px-4 py-3"><span className="text-white font-medium">{r.nombre}</span></td>
                    <td className="px-4 py-3"><span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">{r.tipo}</span></td>
                    <td className="px-4 py-3 text-right font-mono text-sm">{r.porcentaje}%</td>
                    <td className="px-4 py-3 text-xs text-slate-400">{r.base_imponible}</td>
                    <td className="px-4 py-3 text-center text-xs">{r.naturaleza === 'DEBITO' ? 'Db' : 'Cr'}</td>
                    <td className="px-4 py-3 text-right text-xs text-slate-400">{r.prioridad}</td>
                    <td className="px-4 py-3 text-center">
                      <button onClick={() => handleToggleActivo(r)}
                        className={`p-1 rounded ${r.is_active ? 'text-emerald-400' : 'text-slate-600'}`}>
                        {r.is_active ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button onClick={() => openEdit(r)} className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors">
                        <Pencil className="w-4 h-4" />
                      </button>
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
