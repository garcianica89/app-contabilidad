import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, ChevronRight, ChevronDown, FolderOpen, FileText } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

interface CuentaNode {
  id: string
  codigo: string
  nombre: string
  tipo: string
  nivel: number
  hijos?: CuentaNode[]
}

function CuentaRow({ node, depth = 0 }: { node: CuentaNode; depth?: number }) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = node.hijos && node.hijos.length > 0
  return (
    <>
      <div
        className="flex items-center gap-2 py-1.5 px-2 hover:bg-slate-700/30 rounded text-sm"
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
      >
        {hasChildren ? (
          <button onClick={() => setExpanded(!expanded)} className="text-slate-400 hover:text-white">
            {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>
        ) : (
          <FileText className="w-3.5 h-3.5 text-slate-500" />
        )}
        <span className="text-slate-400 font-mono text-xs w-20">{node.codigo}</span>
        <span className="text-white flex-1">{node.nombre}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full ${
          node.tipo === 'ACREEDORA' ? 'bg-green-900/40 text-green-400' :
          node.tipo === 'DEUDORA' ? 'bg-blue-900/40 text-blue-400' :
          'bg-slate-700 text-slate-300'
        }`}>{node.tipo}</span>
      </div>
      {hasChildren && expanded && node.hijos!.map((child) => (
        <CuentaRow key={child.id} node={child} depth={depth + 1} />
      ))}
    </>
  )
}

export default function ERPContabilidadPage() {
  const [cuentas, setCuentas] = useState<CuentaNode[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ codigo: '', nombre: '', tipo: 'DEUDORA' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])
  async function load() {
    try { setCuentas(await api.erpGetCuentasArbol()) } catch { notify('Error al cargar cuentas') }
    setLoading(false)
  }

  function flattenNodes(nodes: CuentaNode[]): CuentaNode[] {
    const result: CuentaNode[] = []
    for (const n of nodes) {
      result.push(n)
      if (n.hijos) result.push(...flattenNodes(n.hijos))
    }
    return result
  }

  const filtered = search
    ? flattenNodes(cuentas).filter((i) =>
        i.codigo?.toLowerCase().includes(search.toLowerCase()) ||
        i.nombre?.toLowerCase().includes(search.toLowerCase())
      )
    : []

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      const data = await api.erpCrearCuenta(form)
      setCuentas((prev) => [...prev, data])
      setShowForm(false)
      notify('Cuenta creada')
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Contabilidad General</h1>
          <p className="text-sm text-slate-400">Plan de cuentas contables</p>
        </div>
        <button onClick={() => { setForm({ codigo: '', nombre: '', tipo: 'DEUDORA' }); setShowForm(true) }} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Cuenta
        </button>
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar cuenta..." />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nueva Cuenta Contable</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Codigo *</label>
              <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} className="input-filter w-full" required placeholder="1.01.01" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo *</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-filter w-full">
                <option value="DEUDORA">Deudora</option>
                <option value="ACREEDORA">Acreedora</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
            <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Caja General" />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> Crear</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <Skeleton rows={6} />
      ) : search ? (
        filtered.length === 0 ? (
          <EmptyState message="No se encontraron cuentas" />
        ) : (
          <div className="card divide-y divide-slate-700/50">
            {filtered.map((i) => (
              <div key={i.id} className="flex items-center gap-2 py-2 px-3 text-sm">
                <span className="text-slate-400 font-mono w-20">{i.codigo}</span>
                <span className="text-white flex-1">{i.nombre}</span>
                <span className="text-xs text-slate-500">{i.tipo}</span>
              </div>
            ))}
          </div>
        )
      ) : cuentas.length === 0 ? (
        <EmptyState message="No hay cuentas contables registradas" />
      ) : (
        <div className="card divide-y divide-slate-700/50">
          <div className="flex items-center gap-2 py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <span className="w-20">Codigo</span>
            <span className="flex-1">Nombre</span>
            <span>Tipo</span>
          </div>
          {cuentas.map((node) => (
            <CuentaRow key={node.id} node={node} />
          ))}
        </div>
      )}
    </div>
  )
}
