import { useState, useEffect } from 'react'
import { Search, Building2, Pencil, X, Check, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import type { Proveedor, Retencion } from '../types/api'

const emptyForm = {
  codigo: '', nombre: '', ruc: '', direccion: '', telefono: '', email: '',
  plazo_credito: 30, aplica_iva: true, tasa_iva: 15, retenciones: [] as string[],
}

export default function ProveedoresPage() {
  const [items, setItems] = useState<Proveedor[]>([])
  const [retenciones, setRetenciones] = useState<Retencion[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([
      api.getProveedores(),
      api.getRetenciones(true),
    ]).then(([p, r]) => {
      setItems(p)
      setRetenciones(r)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const filtered = items.filter((c) =>
    !search || c.nombre.toLowerCase().includes(search.toLowerCase()) ||
    (c.codigo && c.codigo.toLowerCase().includes(search.toLowerCase())) ||
    (c.ruc && c.ruc.includes(search))
  )

  function openCreate() { setEditId(null); setForm(emptyForm); setShowForm(true) }

  function openEdit(c: Proveedor) {
    setEditId(c.id)
    setForm({
      codigo: c.codigo || '', nombre: c.nombre, ruc: c.ruc || '',
      direccion: c.direccion || '', telefono: c.telefono || '', email: c.email || '',
      plazo_credito: 30, aplica_iva: c.aplica_iva, tasa_iva: c.tasa_iva,
      retenciones: (c.retenciones || []).map((r) => r.id),
    })
    setShowForm(true)
  }

  function toggleRetencion(id: string) {
    setForm({
      ...form,
      retenciones: form.retenciones.includes(id)
        ? form.retenciones.filter((rid) => rid !== id)
        : [...form.retenciones, id],
    })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload: any = { ...form, retenciones: form.retenciones }
      if (!payload.codigo) delete payload.codigo
      const updated = editId
        ? await api.actualizarProveedor(editId, payload)
        : await api.crearProveedor(payload)
      setItems((prev) => editId ? prev.map((c) => (c.id === editId ? updated : c)) : [...prev, updated])
      setShowForm(false)
    } catch {}
    setSaving(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Proveedores</h1>
          <p className="text-sm text-slate-400">Administracion de proveedores</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Building2 className="w-4 h-4" /> Nuevo Proveedor
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar Proveedor' : 'Nuevo Proveedor'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo</label>
              <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} className="input-filter w-full" placeholder="PROV-001" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Nombre del proveedor" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">RUC</label>
              <input value={form.ruc} onChange={(e) => setForm({ ...form, ruc: e.target.value })} className="input-filter w-full" placeholder="J000000000" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Telefono</label>
              <input value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className="input-filter w-full" placeholder="+505 0000 0000" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-filter w-full" placeholder="proveedor@email.com" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Plazo Credito (dias)</label>
              <input type="number" value={form.plazo_credito} onChange={(e) => setForm({ ...form, plazo_credito: Number(e.target.value) })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">IVA</label>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5 text-xs text-slate-300">
                  <input type="checkbox" checked={form.aplica_iva} onChange={(e) => setForm({ ...form, aplica_iva: e.target.checked })} className="rounded border-slate-600 bg-slate-700 text-primary-500" />
                  Aplica IVA
                </label>
                {form.aplica_iva && (
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-slate-400">Tasa:</span>
                    <input type="number" step="0.01" min="0" max="100" value={form.tasa_iva} onChange={(e) => setForm({ ...form, tasa_iva: Number(e.target.value) })} className="input-filter w-20 text-xs" />
                    <span className="text-xs text-slate-400">%</span>
                  </div>
                )}
              </div>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Retenciones</label>
              <div className="flex flex-wrap gap-2">
                {retenciones.length === 0 && <span className="text-xs text-slate-500">Cree retenciones en Configuracion</span>}
                {retenciones.filter((r) => r.is_active).map((r) => (
                  <label key={r.id} className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs cursor-pointer border transition-colors ${
                    form.retenciones.includes(r.id)
                      ? 'bg-primary-900/50 border-primary-500 text-primary-300'
                      : 'bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-500'
                  }`}>
                    <input type="checkbox" checked={form.retenciones.includes(r.id)}
                      onChange={() => toggleRetencion(r.id)} className="hidden" />
                    {r.codigo} ({r.porcentaje}%)
                  </label>
                ))}
              </div>
            </div>
            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-xs text-slate-400 mb-1">Direccion</label>
              <input value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} className="input-filter w-full" placeholder="Direccion completa" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'} Proveedor</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar proveedor..." />
        </div>
        <span className="text-xs text-slate-500">{filtered.length} registros</span>
      </div>

      {loading ? (
<Skeleton rows={5} />
      ) : filtered.length === 0 ? (
        <EmptyState message={search ? 'Ningun proveedor coincide con la busqueda' : 'No hay proveedores registrados'} />
      ) : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Codigo</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Nombre</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">RUC</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Telefono</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Saldo</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400 w-20">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3"><span className="text-slate-400 font-mono text-xs">{c.codigo || '-'}</span></td>
                    <td className="px-4 py-3"><span className="text-white font-medium">{c.nombre}</span></td>
                    <td className="px-4 py-3 text-slate-400 text-xs">{c.ruc || '-'}</td>
                    <td className="px-4 py-3 text-slate-400">{c.telefono || '-'}</td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      <span className={c.saldo > 0 ? 'text-amber-400' : 'text-slate-400'}>
                        C$ {c.saldo.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button onClick={() => openEdit(c)} className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors">
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