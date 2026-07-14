import { useState, useEffect } from 'react'
import {
  Search, Plus, Pencil, X, Check, AlertCircle, Trash2,
  FileText, ChevronDown, ChevronRight,
} from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'

const ACCOUNT_SOURCES = [
  { value: 'FIXED', label: 'Codigo Fijo' },
  { value: 'PARAM', label: 'Parametro Modulo' },
  { value: 'CONTEXT', label: 'Variable Contexto' },
  { value: 'SUBTYPE', label: 'Subtipo Documento' },
]
const NATURES = ['DEBIT', 'CREDIT']
const CC_SOURCES = ['SUBTYPE', 'FIXED', 'CONTEXT']

const CONTEXT_VARIABLES = [
  'total', 'subtotal', 'descuento', 'iva', 'ir', 'total_lineas',
  'fecha', 'periodo_id', 'cliente_id', 'proveedor_id',
  'documento_id', 'documento_tipo', 'documento_numero',
]

export default function PlantillasPage() {
  const [items, setItems] = useState<any[]>([])
  const [tipos, setTipos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [form, setForm] = useState<any>({
    journal_type_id: '', name: '', priority: 0, condition_expr: '', is_active: true,
    lines: [],
  })
  const [saving, setSaving] = useState(false)
  const [lineForm, setLineForm] = useState<any>(null)
  const [editingLineId, setEditingLineId] = useState<string | null>(null)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [p, t] = await Promise.all([api.getPlantillas(), api.getTiposAsiento()])
      setItems(p)
      setTipos(t)
    } catch {}
    setLoading(false)
  }

  const tipoMap = Object.fromEntries(tipos.map((t) => [t.id, t]))
  function groupBy(arr: any[], key: string) {
    return arr.reduce((acc: any, i: any) => {
      const k = i[key]
      if (!acc[k]) acc[k] = []
      acc[k].push(i)
      return acc
    }, {})
  }
  const grouped = groupBy(items, 'journal_type_id')

  const filtered = items.filter((i) =>
    !search || i.name.toLowerCase().includes(search.toLowerCase()) ||
    (tipoMap[i.journal_type_id]?.code || '').toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() {
    setEditId(null)
    setForm({ journal_type_id: '', name: '', priority: 0, condition_expr: '', is_active: true, lines: [] })
    setLineForm(null)
    setShowForm(true)
  }

  function openEdit(i: any) {
    setEditId(i.id)
    setForm({
      journal_type_id: i.journal_type_id,
      name: i.name,
      priority: i.priority,
      condition_expr: i.condition_expr || '',
      is_active: i.is_active,
      lines: i.lines || [],
    })
    setLineForm(null)
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        ...form,
        condition_expr: form.condition_expr || null,
        lines: editId ? undefined : form.lines.map((l: any) => ({
          line_order: l.line_order,
          nature: l.nature,
          account_source: l.account_source,
          account_code: l.account_code || null,
          account_param_concept: l.account_param_concept || null,
          account_context_var: l.account_context_var || null,
          amount_expression: l.amount_expression,
          description_expression: l.description_expression || null,
          cost_center_source: l.cost_center_source || 'SUBTYPE',
          cost_center_id: l.cost_center_id || null,
          cost_center_context_var: l.cost_center_context_var || null,
          condition_expr: l.condition_expr || null,
          is_mandatory: l.is_mandatory ?? true,
        })),
      }
      const data = editId
        ? await api.actualizarPlantilla(editId, payload)
        : await api.crearPlantilla(payload)
      setItems((prev) => editId ? prev.map((i) => (i.id === editId ? data : i)) : [...prev, data])
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleDelete(id: string) {
    if (!confirm('Eliminar plantilla?')) return
    try {
      await api.eliminarPlantilla(id)
      setItems((prev) => prev.filter((i) => i.id !== id))
    } catch (err: any) { notify(err.message) }
  }

  function openLineForm(line?: any, index?: number) {
    if (line) {
      setEditingLineId(`new-${index}`)
      setLineForm({
        line_order: line.line_order,
        nature: line.nature,
        account_source: line.account_source,
        account_code: line.account_code || '',
        account_param_concept: line.account_param_concept || '',
        account_context_var: line.account_context_var || '',
        amount_expression: line.amount_expression,
        description_expression: line.description_expression || '',
        cost_center_source: line.cost_center_source || 'SUBTYPE',
        cost_center_id: '',
        cost_center_context_var: line.cost_center_context_var || '',
        condition_expr: line.condition_expr || '',
        is_mandatory: line.is_mandatory ?? true,
      })
    } else {
      setEditingLineId(null)
      setLineForm({
        line_order: (form.lines.length + 1) * 10,
        nature: 'DEBIT', account_source: 'FIXED',
        account_code: '', account_param_concept: '', account_context_var: '',
        amount_expression: '{{total}}', description_expression: '',
        cost_center_source: 'SUBTYPE', cost_center_id: '',
        cost_center_context_var: '', condition_expr: '', is_mandatory: true,
      })
    }
  }

  function saveLine(e: React.FormEvent) {
    e.preventDefault()
    const cleaned = { ...lineForm, account_code: lineForm.account_code || null, account_param_concept: lineForm.account_param_concept || null, account_context_var: lineForm.account_context_var || null }
    const newLines = [...form.lines]
    if (editingLineId?.startsWith('new-')) {
      const idx = parseInt(editingLineId.split('-')[1])
      if (!isNaN(idx) && idx >= 0 && idx < newLines.length) {
        newLines[idx] = cleaned
      } else {
        newLines.push(cleaned)
      }
    }
    setForm({ ...form, lines: newLines.sort((a: any, b: any) => a.line_order - b.line_order) })
    setLineForm(null)
  }

  function removeLine(index: number) {
    setForm({ ...form, lines: form.lines.filter((_: any, i: number) => i !== index) })
  }

  const filteredGrouped = groupBy(filtered, 'journal_type_id')

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Plantillas Contables</h1>
          <p className="text-sm text-slate-400">Diseno de plantillas para generacion automatica de asientos</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Plantilla
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar' : 'Nueva'} Plantilla</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo de Asiento *</label>
              <select value={form.journal_type_id} onChange={(e) => setForm({ ...form, journal_type_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar...</option>
                {tipos.map((t) => <option key={t.id} value={t.id}>{t.code} - {t.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-filter w-full" required placeholder="Plantilla Venta Contado" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Prioridad</label>
              <input type="number" value={form.priority} onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Condicion</label>
              <input value={form.condition_expr} onChange={(e) => setForm({ ...form, condition_expr: e.target.value })} className="input-filter w-full font-mono text-xs" placeholder="{{tipo_documento}} == 'CONTADO'" />
            </div>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500" />
            <span className="text-xs text-slate-400">Activa</span>
          </label>

          <div className="border-t border-slate-700/50 pt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-xs font-semibold uppercase text-slate-400">Lineas de la Plantilla</h4>
              {!editId && (
                <button type="button" onClick={() => openLineForm()} className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1">
                  <Plus className="w-3 h-3" /> Agregar Linea
                </button>
              )}
            </div>

            {lineForm && !editId && (
              <LineForm lineForm={lineForm} setLineForm={setLineForm} onSave={saveLine} onCancel={() => setLineForm(null)} />
            )}

            {form.lines.length === 0 ? (
              <div className="text-xs text-slate-500 py-4 text-center">Sin lineas definidas</div>
            ) : (
              <div className="space-y-2">
                {form.lines.map((line: any, idx: number) => (
                  <div key={idx} className="flex items-start gap-2 p-3 rounded-lg bg-slate-800/50 group">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-slate-500 font-mono">#{line.line_order}</span>
                        <span className={`font-semibold ${line.nature === 'DEBIT' ? 'text-emerald-400' : 'text-red-400'}`}>{line.nature}</span>
                        <span className="text-slate-400">{ACCOUNT_SOURCES.find((s) => s.value === line.account_source)?.label || line.account_source}</span>
                        <span className="font-mono text-primary-400">{line.amount_expression}</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {line.account_code && <span className="mr-2">Cta: {line.account_code}</span>}
                        {line.account_param_concept && <span className="mr-2">Param: {line.account_param_concept}</span>}
                        {line.account_context_var && <span className="mr-2">Var: {line.account_context_var}</span>}
                        {line.condition_expr && <span className="text-yellow-500">Cond: {line.condition_expr}</span>}
                      </div>
                    </div>
                    <div className="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button type="button" onClick={() => openLineForm(line, idx)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3 h-3" /></button>
                      <button type="button" onClick={() => removeLine(idx)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3 h-3" /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'} Plantilla</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar plantilla..." />
      </div>

      {loading ? <Skeleton /> : filtered.length === 0 ? <EmptyState message="No hay plantillas registradas" /> : (
        <div className="space-y-4">
          {Object.entries(filteredGrouped).map(([jtId, plantillas]: [string, any]) => {
            const tipo = tipoMap[jtId]
            const isExpanded = expanded[jtId] !== false
            return (
              <div key={jtId} className="card !p-0 overflow-hidden">
                <button
                  onClick={() => setExpanded({ ...expanded, [jtId]: !isExpanded })}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                    <FileText className="w-4 h-4 text-primary-400" />
                    <span className="text-sm font-semibold text-white">{tipo?.code || 'Sin tipo'}</span>
                    <span className="text-xs text-slate-500">({plantillas.length} plantillas)</span>
                  </div>
                </button>
                {isExpanded && (
                  <div className="divide-y divide-slate-800/50 border-t border-slate-800/50">
                    {plantillas.map((p: any) => (
                      <div key={p.id} className="flex items-center justify-between px-4 py-3 hover:bg-slate-800/30 transition-colors">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-white">{p.name}</span>
                            <span className="text-xs text-slate-500 font-mono">P{p.priority}</span>
                            {!p.is_active && <span className="text-xs px-1.5 py-0.5 rounded bg-red-600/20 text-red-400">Inactiva</span>}
                          </div>
                          <div className="text-xs text-slate-500 mt-0.5">
                            {p.condition_expr && <span className="text-yellow-500">Cond: {p.condition_expr}</span>}
                            <span className="ml-2">{p.lines?.length || 0} lineas</span>
                          </div>
                        </div>
                        <div className="flex gap-1 shrink-0 ml-3">
                          <button onClick={() => openEdit(p)} className="p-1.5 text-slate-500 hover:text-white rounded hover:bg-slate-700/50"><Pencil className="w-3.5 h-3.5" /></button>
                          <button onClick={() => handleDelete(p.id)} className="p-1.5 text-slate-500 hover:text-red-400 rounded hover:bg-slate-700/50"><Trash2 className="w-3.5 h-3.5" /></button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function LineForm({ lineForm, setLineForm, onSave, onCancel }: any) {
  return (
    <form onSubmit={onSave} className="bg-slate-800/30 rounded-lg p-4 space-y-3 mb-3 border border-slate-700/50">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Orden</label>
          <input type="number" value={lineForm.line_order} onChange={(e) => setLineForm({ ...lineForm, line_order: Number(e.target.value) })}
            className="input-filter w-full" required />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Naturaleza</label>
          <select value={lineForm.nature} onChange={(e) => setLineForm({ ...lineForm, nature: e.target.value })} className="input-filter w-full">
            {NATURES.map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Fuente Cuenta</label>
          <select value={lineForm.account_source} onChange={(e) => setLineForm({ ...lineForm, account_source: e.target.value })} className="input-filter w-full">
            {ACCOUNT_SOURCES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>
        {lineForm.account_source === 'FIXED' && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">Codigo Cuenta</label>
            <input value={lineForm.account_code} onChange={(e) => setLineForm({ ...lineForm, account_code: e.target.value })}
              className="input-filter w-full font-mono text-xs" placeholder="1-1-1-1-01-00-00-0000" />
          </div>
        )}
        {lineForm.account_source === 'PARAM' && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">Concepto Parametro</label>
            <input value={lineForm.account_param_concept} onChange={(e) => setLineForm({ ...lineForm, account_param_concept: e.target.value })}
              className="input-filter w-full font-mono text-xs" placeholder="CTA_VENTAS_CONTADO" />
          </div>
        )}
        {lineForm.account_source === 'CONTEXT' && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">Variable Contexto</label>
            <select value={lineForm.account_context_var} onChange={(e) => setLineForm({ ...lineForm, account_context_var: e.target.value })} className="input-filter w-full">
              <option value="">Seleccionar...</option>
              {CONTEXT_VARIABLES.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
        )}
        <div className="md:col-span-2">
          <label className="block text-xs text-slate-400 mb-1">Expresion Monto</label>
          <input value={lineForm.amount_expression} onChange={(e) => setLineForm({ ...lineForm, amount_expression: e.target.value })}
            className="input-filter w-full font-mono text-xs" required placeholder="{{total}}" />
        </div>
        <div className="md:col-span-2">
          <label className="block text-xs text-slate-400 mb-1">Expresion Descripcion</label>
          <input value={lineForm.description_expression} onChange={(e) => setLineForm({ ...lineForm, description_expression: e.target.value })}
            className="input-filter w-full font-mono text-xs" placeholder="Venta al contado {{documento_numero}}" />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Centro Costo</label>
          <select value={lineForm.cost_center_source} onChange={(e) => setLineForm({ ...lineForm, cost_center_source: e.target.value })} className="input-filter w-full">
            {CC_SOURCES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Condicion</label>
          <input value={lineForm.condition_expr} onChange={(e) => setLineForm({ ...lineForm, condition_expr: e.target.value })}
            className="input-filter w-full font-mono text-xs" placeholder="{{tipo}} == 'CONTADO'" />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={lineForm.is_mandatory} onChange={(e) => setLineForm({ ...lineForm, is_mandatory: e.target.checked })}
            className="rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500" />
          <span className="text-xs text-slate-400">Obligatoria</span>
        </label>
      </div>
      <div className="flex gap-2">
        <button type="submit" className="btn-primary text-xs py-1.5"><Check className="w-3 h-3" /> Guardar Linea</button>
        <button type="button" onClick={onCancel} className="btn-secondary text-xs py-1.5">Cancelar</button>
      </div>
    </form>
  )
}


