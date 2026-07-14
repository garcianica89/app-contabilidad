import { useState, useEffect } from 'react'
import {
  Search, Plus, Pencil, X, Check, AlertCircle, ChevronRight, ChevronDown,
  FolderOpen, FileText, ToggleLeft, ToggleRight,
} from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useNotification } from '../contexts/NotificationContext'

interface Cuenta {
  id: string
  codigo: string
  nombre: string
  tipo: string
  nivel: number
  padre_id: string | null
  acepta_datos: boolean
  moneda_id: string | null
  activa: boolean
}

interface CuentaArbol {
  id: string
  codigo: string
  nombre: string
  tipo: string
  nivel: number
  acepta_datos: boolean
  hijos: CuentaArbol[]
}

const emptyForm = {
  codigo: '',
  nombre: '',
  tipo: 'ACTIVO',
  nivel: 1,
  padre_id: '' as string | null,
  acepta_datos: false,
  moneda_id: '' as string | null,
}

const TIPOS = ['ACTIVO', 'PASIVO', 'PATRIMONIO', 'INGRESO', 'COSTO', 'GASTO']

export default function CatalogoCuentasPage() {
  const [cuentas, setCuentas] = useState<Cuenta[]>([])
  const [arbol, setArbol] = useState<CuentaArbol[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'tree' | 'list'>('tree')
  const { notify } = useNotification()

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [lista, tree] = await Promise.all([
        api.getCuentasContables(),
        api.getCuentasArbol(),
      ])
      setCuentas(lista)
      setArbol(tree)
    } catch { }
    setLoading(false)
  }

  const filtered = cuentas.filter((c) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      c.codigo.toLowerCase().includes(q) ||
      c.nombre.toLowerCase().includes(q) ||
      c.tipo.toLowerCase().includes(q)
    )
  })

  function openCreate(padreId?: string) {
    setEditId(null)
    const padre = padreId ? cuentas.find((c) => c.id === padreId) : null
    setForm({
      ...emptyForm,
      padre_id: padreId || null,
      nivel: padre ? padre.nivel + 1 : 1,
      tipo: padre ? padre.tipo : 'ACTIVO',
    })
    setShowForm(true)
  }

  function openEdit(item: Cuenta) {
    setEditId(item.id)
    setForm({
      codigo: item.codigo,
      nombre: item.nombre,
      tipo: item.tipo,
      nivel: item.nivel,
      padre_id: item.padre_id,
      acepta_datos: item.acepta_datos,
      moneda_id: item.moneda_id || '',
    })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        ...form,
        moneda_id: form.moneda_id || null,
        padre_id: form.padre_id || null,
      }
      if (editId) {
        await api.actualizarCuentaContable(editId, payload)
      } else {
        await api.crearCuentaContable(payload)
      }
      setShowForm(false)
      await loadData()
    } catch (err: any) {
      notify(err.message)
    }
    setSaving(false)
  }

  async function toggleAceptaDatos(cuenta: Cuenta) {
    try {
      await api.actualizarCuentaContable(cuenta.id, {
        acepta_datos: !cuenta.acepta_datos,
      })
      await loadData()
    } catch (err: any) {
      notify(err.message)
    }
  }

  const padreOptions = cuentas.filter((c) => c.nivel < 5)

  function toggleExpand(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function renderTreeNode(nodo: CuentaArbol, depth = 0): React.ReactNode {
    const hasChildren = nodo.hijos && nodo.hijos.length > 0
    const isExpanded = expanded.has(nodo.id)

    return (
      <div key={nodo.id}>
        <div
          className="flex items-center gap-2 px-4 py-2 hover:bg-slate-800/30 transition-colors group"
          style={{ paddingLeft: `${depth * 24 + 16}px` }}
        >
          <button
            onClick={() => hasChildren && toggleExpand(nodo.id)}
            className={`p-0.5 rounded ${hasChildren ? 'text-slate-400 hover:text-white' : 'invisible'}`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>

          {hasChildren
            ? <FolderOpen className="w-4 h-4 text-amber-400 shrink-0" />
            : <FileText className="w-4 h-4 text-slate-500 shrink-0" />
          }

          <span className="text-xs font-mono text-slate-500 w-28 shrink-0">{nodo.codigo}</span>
          <span className="text-sm text-white flex-1 truncate">{nodo.nombre}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${nodo.acepta_datos ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/50 text-slate-500'}`}>
            {nodo.acepta_datos ? 'Datos' : 'Agrupa'}
          </span>

          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {!hasChildren && (
              <button
                onClick={(e) => { e.stopPropagation(); toggleAceptaDatos(nodo as any) }}
                className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white"
                title="Toggle acepta datos"
              >
                {nodo.acepta_datos
                  ? <ToggleRight className="w-4 h-4 text-emerald-400" />
                  : <ToggleLeft className="w-4 h-4" />
                }
              </button>
            )}
            <button
              onClick={() => openEdit(cuentas.find((c) => c.id === nodo.id)!)}
              className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white"
            >
              <Pencil className="w-4 h-4" />
            </button>
            <button
              onClick={() => openCreate(nodo.id)}
              className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-emerald-400"
              title="Agregar subcuenta"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>
        {hasChildren && isExpanded && nodo.hijos.map((h) => renderTreeNode(h, depth + 1))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Catalogo de Cuentas</h1>
          <p className="text-sm text-slate-400">Plan de cuentas contable</p>
        </div>
        <button onClick={() => openCreate()} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Nueva Cuenta
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">
              {editId ? 'Editar Cuenta' : 'Nueva Cuenta'}
            </h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="label">Codigo</label>
              <input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })}
                className="input" placeholder="1-1-1-1-01-00-00-0000" required />
            </div>
            <div>
              <label className="label">Nombre</label>
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                className="input" placeholder="Nombre de la cuenta" required />
            </div>
            <div>
              <label className="label">Tipo</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                className="input">
                {TIPOS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Nivel</label>
              <input type="number" value={form.nivel} onChange={(e) => setForm({ ...form, nivel: parseInt(e.target.value) || 1 })}
                className="input" min={1} max={8} required />
            </div>
            <div>
              <label className="label">Cuenta Padre</label>
              <select value={form.padre_id || ''} onChange={(e) => {
                const pid = e.target.value || null
                const padre = pid ? cuentas.find((c) => c.id === pid) : null
                setForm({
                  ...form,
                  padre_id: pid,
                  nivel: padre ? padre.nivel + 1 : 1,
                  tipo: padre ? padre.tipo : form.tipo,
                })
              }} className="input">
                <option value="">-- Ninguna (raiz) --</option>
                {padreOptions.map((p) => (
                  <option key={p.id} value={p.id}>{p.codigo} - {p.nombre}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-3 pt-6">
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" checked={form.acepta_datos}
                  onChange={(e) => setForm({ ...form, acepta_datos: e.target.checked })}
                  className="sr-only peer" />
                <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600"></div>
                <span className="ms-3 text-sm text-slate-300">Acepta datos</span>
              </label>
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

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            className="input-filter w-full pl-10" placeholder="Buscar por codigo, nombre o tipo..." />
        </div>
        <div className="flex bg-slate-800 rounded-lg p-0.5">
          <button
            onClick={() => setViewMode('tree')}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${viewMode === 'tree' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}
          >
            Arbol
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${viewMode === 'list' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}
          >
            Lista
          </button>
        </div>
        <span className="text-xs text-slate-500">{cuentas.length} cuentas</span>
      </div>

      {loading ? (
<Skeleton rows={10} barHeight="h-10" />
      ) : viewMode === 'tree' ? (
        <div className="card overflow-hidden !p-0">
          {arbol.length === 0 ? (
            <EmptyState message="No hay cuentas contables" />
          ) : (
            <div className="divide-y divide-slate-800/50">
              {arbol.map((nodo) => renderTreeNode(nodo))}
            </div>
          )}
        </div>
      ) : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            {filtered.length === 0 ? (
              <EmptyState message={search ? 'Sin resultados' : 'No hay cuentas contables'} />
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Codigo</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Nombre</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Tipo</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Nivel</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Acepta Datos</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Activa</th>
                    <th className="px-4 py-3 text-center w-20">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {filtered.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-slate-400">{c.codigo}</td>
                      <td className="px-4 py-3 text-white">{c.nombre}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          c.tipo === 'ACTIVO' ? 'bg-blue-500/20 text-blue-400' :
                          c.tipo === 'PASIVO' ? 'bg-orange-500/20 text-orange-400' :
                          c.tipo === 'PATRIMONIO' ? 'bg-purple-500/20 text-purple-400' :
                          c.tipo === 'INGRESO' ? 'bg-emerald-500/20 text-emerald-400' :
                          c.tipo === 'COSTO' ? 'bg-red-500/20 text-red-400' :
                          'bg-slate-500/20 text-slate-400'
                        }`}>{c.tipo}</span>
                      </td>
                      <td className="px-4 py-3 text-center text-slate-400">{c.nivel}</td>
                      <td className="px-4 py-3 text-center">
                        <button onClick={() => toggleAceptaDatos(c)} className="mx-auto">
                          {c.acepta_datos
                            ? <ToggleRight className="w-5 h-5 text-emerald-400" />
                            : <ToggleLeft className="w-5 h-5 text-slate-500" />
                          }
                        </button>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {c.activa
                          ? <Check className="w-4 h-4 text-emerald-400 mx-auto" />
                          : <X className="w-4 h-4 text-red-400 mx-auto" />
                        }
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button onClick={() => openEdit(c)}
                          className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white">
                          <Pencil className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  )
}