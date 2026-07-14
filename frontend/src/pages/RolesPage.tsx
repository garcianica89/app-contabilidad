import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { Shield, Plus, Pencil, Trash2, X, Check } from 'lucide-react'
import { useNotification } from '../contexts/NotificationContext'

interface Rol {
  id: string
  nombre: string
  descripcion: string | null
  activo: boolean
  is_admin: boolean
}

interface Permiso {
  id: string
  codigo: string
  nombre: string
  modulo: string
}

export default function RolesPage() {
  const { notify } = useNotification()
  const [roles, setRoles] = useState<Rol[]>([])
  const [permisos, setPermisos] = useState<Permiso[]>([])
  const [selectedRol, setSelectedRol] = useState<string | null>(null)
  const [rolPermisos, setRolPermisos] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingRol, setEditingRol] = useState<Rol | null>(null)
  const [form, setForm] = useState({ nombre: '', descripcion: '' })

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [rolesData, permisosData] = await Promise.all([
        api.getRoles(),
        api.getPermisos(),
      ])
      setRoles(rolesData)
      setPermisos(permisosData)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  async function selectRol(rolId: string) {
    setSelectedRol(rolId)
    if (!rolId) return
    const data = await api.getPermisosRol(rolId)
    setRolPermisos(new Set(data.map((p: Permiso) => p.id)))
  }

  function togglePermiso(permisoId: string) {
    setRolPermisos(prev => {
      const next = new Set(prev)
      if (next.has(permisoId)) next.delete(permisoId)
      else next.add(permisoId)
      return next
    })
  }

  async function savePermisos() {
    if (!selectedRol) return
    await api.asignarPermisosRol(selectedRol, Array.from(rolPermisos))
    notify('Permisos actualizados', 'success')
  }

  function openCreate() {
    setEditingRol(null)
    setForm({ nombre: '', descripcion: '' })
    setShowForm(true)
  }

  function openEdit(rol: Rol) {
    setEditingRol(rol)
    setForm({ nombre: rol.nombre, descripcion: rol.descripcion || '' })
    setShowForm(true)
  }

  async function saveRol() {
    if (editingRol) {
      await api.actualizarRol(editingRol.id, form)
    } else {
      await api.crearRol(form)
    }
    setShowForm(false)
    loadData()
  }

  async function deleteRol(id: string) {
    if (!confirm('Eliminar este rol?')) return
    await api.eliminarRol(id)
    if (selectedRol === id) setSelectedRol(null)
    loadData()
  }

  const modulos = [...new Set(permisos.map(p => p.modulo))].sort()
  const permisosPorModulo = modulos.map(mod => ({
    modulo: mod,
    permisos: permisos.filter(p => p.modulo === mod),
  }))

  if (loading) return <div className="text-slate-400">Cargando...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Roles y Permisos</h1>
          <p className="text-slate-400 text-sm mt-1">Gestion de roles y asignacion de permisos</p>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium">
          <Plus className="w-4 h-4" />
          Nuevo Rol
        </button>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">{editingRol ? 'Editar Rol' : 'Nuevo Rol'}</h2>
              <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Nombre</label>
                <input
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={form.nombre}
                  onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))}
                  placeholder="Ej: Vendedor"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Descripcion</label>
                <input
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={form.descripcion}
                  onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
                  placeholder="Descripcion del rol"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={saveRol} className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium">
                  <Check className="w-4 h-4" />
                  Guardar
                </button>
                <button onClick={() => setShowForm(false)} className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm">
                  <X className="w-4 h-4" />
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Roles</h2>
          {roles.map(rol => (
            <div
              key={rol.id}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedRol === rol.id
                  ? 'bg-primary-600/20 border-primary-500/40 text-primary-300'
                  : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
              }`}
              onClick={() => selectRol(rol.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  <span className="font-medium">{rol.nombre}</span>
                  {rol.is_admin && <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full">ADMIN</span>}
                </div>
                <div className="flex gap-1">
                  <button onClick={e => { e.stopPropagation(); openEdit(rol) }} className="p-1 hover:bg-slate-800 rounded text-slate-500 hover:text-slate-200">
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  {!rol.is_admin && (
                    <button onClick={e => { e.stopPropagation(); deleteRol(rol.id) }} className="p-1 hover:bg-red-900/30 rounded text-slate-500 hover:text-red-400">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
              {rol.descripcion && <p className="text-xs text-slate-500 mt-1 ml-6">{rol.descripcion}</p>}
            </div>
          ))}
        </div>

        <div className="lg:col-span-2">
          {selectedRol ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                  Permisos - {roles.find(r => r.id === selectedRol)?.nombre}
                </h2>
                <button onClick={savePermisos} className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-xs font-medium">
                  <Check className="w-3.5 h-3.5" />
                  Guardar Permisos
                </button>
              </div>
              <div className="space-y-3">
                {permisosPorModulo.map(({ modulo, permisos: modPermisos }) => (
                  <div key={modulo} className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
                    <div className="px-4 py-2 bg-slate-800/50 border-b border-slate-800">
                      <h3 className="text-sm font-semibold text-slate-300">{modulo}</h3>
                    </div>
                    <div className="p-2">
                      {modPermisos.map(p => (
                        <label
                          key={p.id}
                          className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-800/50 cursor-pointer transition-colors"
                        >
                          <div
                            className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                              rolPermisos.has(p.id)
                                ? 'bg-primary-600 border-primary-600'
                                : 'border-slate-600 hover:border-slate-500'
                            }`}
                            onClick={() => togglePermiso(p.id)}
                          >
                            {rolPermisos.has(p.id) && <Check className="w-3.5 h-3.5 text-white" />}
                          </div>
                          <div>
                            <span className="text-sm text-slate-200">{p.nombre}</span>
                            <span className="text-xs text-slate-500 ml-2">({p.codigo})</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-500">
              <div className="text-center">
                <Shield className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Selecciona un rol para gestionar sus permisos</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
