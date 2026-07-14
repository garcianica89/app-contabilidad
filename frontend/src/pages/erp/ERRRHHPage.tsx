import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, Users, Briefcase, User, Receipt, Calendar, DollarSign, Trash2 } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

type Tab = 'departamentos' | 'puestos' | 'empleados' | 'nominas'

export default function ERPRRHHPPage() {
  const [tab, setTab] = useState<Tab>('empleados')
  const [departamentos, setDepartamentos] = useState<any[]>([])
  const [puestos, setPuestos] = useState<any[]>([])
  const [empleados, setEmpleados] = useState<any[]>([])
  const [nominas, setNominas] = useState<any[]>([])
  const [periodos, setPeriodos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<'departamento' | 'puesto' | 'empleado' | 'nomina' | 'periodo'>('empleado')
  const [form, setForm] = useState<any>({})
  const [saving, setSaving] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [deps, pst, emp, nom, per] = await Promise.all([
        api.erpGetDepartamentos().catch(() => []),
        api.erpGetPuestos().catch(() => []),
        api.erpGetEmpleados().catch(() => []),
        api.erpGetNominas().catch(() => []),
        api.erpGetPeriodosNomina().catch(() => []),
      ])
      setDepartamentos(deps); setPuestos(pst); setEmpleados(emp); setNominas(nom); setPeriodos(per)
    } catch {}
    setLoading(false)
  }

  function getItems() {
    if (tab === 'departamentos') return departamentos
    if (tab === 'puestos') return puestos
    if (tab === 'empleados') return empleados
    return nominas
  }

  const filtered = getItems().filter((i: any) =>
    !search || i.nombre?.toLowerCase().includes(search.toLowerCase()) || i.cedula?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate(mode: typeof formMode) {
    setFormMode(mode)
    setForm({})
    setEditId(null)
    setShowForm(true)
  }

  function openEdit(i: any) {
    setFormMode('empleado')
    setEditId(i.id)
    setForm({ nombre: i.nombre, cedula: i.cedula || '', telefono: i.telefono || '', email: i.email || '', salario: i.salario || '', departamento_id: i.departamento_id || '', puesto_id: i.puesto_id || '' })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      if (formMode === 'departamento') {
        const data = await api.erpCrearDepartamento(form)
        setDepartamentos((prev) => [...prev, data])
      } else if (formMode === 'puesto') {
        const data = await api.erpCrearPuesto(form)
        setPuestos((prev) => [...prev, data])
      } else if (formMode === 'empleado') {
        if (editId) {
          const data = await api.erpActualizarEmpleado(editId, form)
          setEmpleados((prev) => prev.map((e) => (e.id === editId ? data : e)))
        } else {
          const data = await api.erpCrearEmpleado(form)
          setEmpleados((prev) => [...prev, data])
        }
      } else if (formMode === 'nomina') {
        const data = await api.erpCrearNomina(form)
        setNominas((prev) => [...prev, data])
      } else if (formMode === 'periodo') {
        const data = await api.erpCrearPeriodoNomina(form)
        setPeriodos((prev) => [...prev, data])
      }
      setShowForm(false)
      notify(editId ? 'Actualizado' : 'Creado')
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleEliminarEmpleado(id: string) {
    if (!confirm('Eliminar empleado?')) return
    try {
      await api.erpEliminarEmpleado(id)
      setEmpleados((prev) => prev.filter((e) => e.id !== id))
      notify('Empleado eliminado')
    } catch (err: any) { notify(err.message) }
  }

  async function handleProcesarNomina(periodoId: string) {
    try {
      await api.erpProcesarNomina(periodoId)
      notify('Nomina procesada')
    } catch (err: any) { notify(err.message) }
  }

  async function handlePagarNomina(periodoId: string) {
    try {
      await api.erpPagarNomina(periodoId)
      notify('Nomina pagada')
    } catch (err: any) { notify(err.message) }
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'departamentos', label: 'Departamentos', icon: Briefcase },
    { key: 'puestos', label: 'Puestos', icon: Users },
    { key: 'empleados', label: 'Empleados', icon: User },
    { key: 'nominas', label: 'Nominas', icon: Receipt },
  ]

  const extraButtons: Record<string, { label: string; mode: typeof formMode }[]> = {
    departamentos: [{ label: 'Nuevo Departamento', mode: 'departamento' }],
    puestos: [{ label: 'Nuevo Puesto', mode: 'puesto' }],
    empleados: [{ label: 'Nuevo Empleado', mode: 'empleado' }],
    nominas: [
      { label: 'Nueva Nomina', mode: 'nomina' },
      { label: 'Nuevo Periodo', mode: 'periodo' },
    ],
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">RRHH / Nómina</h1>
          <p className="text-sm text-slate-400">Departamentos, puestos, empleados y nominas</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {extraButtons[tab]?.map((btn) => (
            <button key={btn.mode} onClick={() => openCreate(btn.mode)} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> {btn.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-1 bg-slate-800 rounded-lg p-1 w-fit flex-wrap">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm ${tab === t.key ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar..." />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4 max-w-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">
              {formMode === 'departamento' ? 'Nuevo Departamento' :
               formMode === 'puesto' ? 'Nuevo Puesto' :
               editId ? 'Editar Empleado' : 'Nuevo Empleado'}
            </h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          {formMode === 'departamento' && (
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre || ''} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Ventas" />
            </div>
          )}
          {formMode === 'puesto' && (
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
              <input value={form.nombre || ''} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Gerente de Ventas" />
            </div>
          )}
          {(formMode === 'empleado') && (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
                <input value={form.nombre || ''} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Juan Perez" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Cedula</label>
                  <input value={form.cedula || ''} onChange={(e) => setForm({ ...form, cedula: e.target.value })} className="input-filter w-full" placeholder="001-123456-7" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Salario</label>
                  <input type="number" step="0.01" value={form.salario || ''} onChange={(e) => setForm({ ...form, salario: e.target.value })} className="input-filter w-full" placeholder="0.00" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Telefono</label>
                  <input value={form.telefono || ''} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className="input-filter w-full" placeholder="8888-8888" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Email</label>
                  <input type="email" value={form.email || ''} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-filter w-full" placeholder="correo@ejemplo.com" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Departamento ID</label>
                  <input value={form.departamento_id || ''} onChange={(e) => setForm({ ...form, departamento_id: e.target.value })} className="input-filter w-full" placeholder="ID" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Puesto ID</label>
                  <input value={form.puesto_id || ''} onChange={(e) => setForm({ ...form, puesto_id: e.target.value })} className="input-filter w-full" placeholder="ID" />
                </div>
              </div>
            </>
          )}
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <Skeleton rows={6} />
      ) : filtered.length === 0 ? (
        <EmptyState message={`No hay ${tab} registrados`} />
      ) : tab === 'departamentos' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{i.nombre}</span>
              </div>
            </div>
          ))}
        </div>
      ) : tab === 'puestos' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{i.nombre}</span>
              </div>
            </div>
          ))}
        </div>
      ) : tab === 'empleados' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card relative">
              <div className="absolute top-3 right-3 flex gap-1">
                <button onClick={() => openEdit(i)} className="p-1 text-slate-500 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                <button onClick={() => handleEliminarEmpleado(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
              </div>
              <div className="flex items-center gap-2 mb-1">
                <User className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{i.nombre}</span>
              </div>
              {i.cedula && <p className="text-xs text-slate-400">{i.cedula}</p>}
              {i.telefono && <p className="text-xs text-slate-400">{i.telefono}</p>}
              <p className="text-sm text-white mt-1">C${i.salario?.toFixed(2)}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {periodos.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-white mb-3">Periodos de Nomina</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {periodos.map((p: any) => (
                  <div key={p.id} className="flex items-center justify-between bg-slate-700/30 rounded-lg p-3">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-primary-400" />
                      <div>
                        <p className="text-sm text-white">{p.nombre || `Periodo #${p.id}`}</p>
                        <p className={`text-xs ${p.estado === 'PROCESADO' ? 'text-green-400' : p.estado === 'PAGADO' ? 'text-blue-400' : 'text-yellow-400'}`}>
                          {p.estado || 'PENDIENTE'}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      {p.estado !== 'PROCESADO' && p.estado !== 'PAGADO' && (
                        <button onClick={() => handleProcesarNomina(p.id)} className="p-1 text-slate-500 hover:text-green-400" title="Procesar">
                          <DollarSign className="w-3.5 h-3.5" />
                        </button>
                      )}
                      {p.estado === 'PROCESADO' && (
                        <button onClick={() => handlePagarNomina(p.id)} className="p-1 text-slate-500 hover:text-blue-400" title="Pagar">
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 gap-4">
            {filtered.map((i: any) => (
              <div key={i.id} className="card">
                <div className="flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-primary-400" />
                  <span className="text-sm font-semibold text-white">{i.nombre || `Nomina #${i.id}`}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    i.estado === 'PAGADA' ? 'bg-green-900/40 text-green-400' :
                    i.estado === 'PROCESADA' ? 'bg-blue-900/40 text-blue-400' :
                    'bg-yellow-900/40 text-yellow-400'
                  }`}>{i.estado || 'BORRADOR'}</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">Periodo: {i.periodo_nombre || i.periodo_id}</p>
                <p className="text-sm text-white mt-1">C${i.total?.toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
