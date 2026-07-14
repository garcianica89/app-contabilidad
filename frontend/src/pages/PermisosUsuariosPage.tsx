import { useState, useEffect } from 'react'
import { Key, Users, Plus, X, Check, Shield, Search } from 'lucide-react'
import { api } from '../services/api'

interface Usuario {
  id: string
  username: string
  email: string
  activo: boolean
}

interface Permiso {
  id: string
  codigo: string
  nombre: string
  modulo: string
}

interface UPermiso {
  id: string
  permiso_id: string
  entity_type: string | null
  entity_id: string | null
  allow: boolean
  codigo?: string
}

export default function PermisosUsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [permisos, setPermisos] = useState<Permiso[]>([])
  const [selectedUser, setSelectedUser] = useState<string | null>(null)
  const [userPermisos, setUserPermisos] = useState<string[]>([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    api.getUsuarios().then(setUsuarios)
    api.getPermisos().then(setPermisos)
  }, [])

  const loadUserPermisos = async (userId: string) => {
    setSelectedUser(userId)
    const data = await api.getPermisosUsuario(userId) as { codigo: string }[]
    setUserPermisos(data.map(p => p.codigo))
  }

  const togglePermiso = async (permisoId: string) => {
    if (!selectedUser) return
    const hasPerm = userPermisos.includes(permisos.find(p => p.id === permisoId)?.codigo || '')
    await api.asignarPermisoUsuario(selectedUser, {
      permiso_id: permisoId,
      allow: !hasPerm,
    })
    await loadUserPermisos(selectedUser)
  }

  const filteredPermisos = permisos.filter(p =>
    p.codigo.toLowerCase().includes(search.toLowerCase()) ||
    p.nombre.toLowerCase().includes(search.toLowerCase()) ||
    p.modulo.toLowerCase().includes(search.toLowerCase())
  )

  const permisosAgrupados = filteredPermisos.reduce<Record<string, Permiso[]>>((acc, p) => {
    if (!acc[p.modulo]) acc[p.modulo] = []
    acc[p.modulo].push(p)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary-600/20 rounded-lg">
          <Key className="w-6 h-6 text-primary-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Permisos por Usuario</h1>
          <p className="text-slate-400 text-sm">Asignacion directa de permisos a usuarios</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Users list */}
        <div className="lg:col-span-1 bg-slate-900/50 rounded-xl border border-slate-800 p-4">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Users className="w-4 h-4" /> Usuarios
          </h2>
          <div className="space-y-1">
            {usuarios.map(u => (
              <button
                key={u.id}
                onClick={() => loadUserPermisos(u.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedUser === u.id
                    ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                <div className="font-medium">{u.username}</div>
                <div className="text-xs text-slate-500">{u.email}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Permissions list */}
        <div className="lg:col-span-3 bg-slate-900/50 rounded-xl border border-slate-800 p-4">
          {!selectedUser ? (
            <div className="text-center py-12 text-slate-500">
              <Shield className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Selecciona un usuario para gestionar sus permisos</p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Buscar permiso..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>

              <div className="space-y-4 max-h-[65vh] overflow-y-auto">
                {Object.entries(permisosAgrupados).map(([modulo, perms]) => (
                  <div key={modulo}>
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{modulo}</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
                      {perms.map(p => {
                        const hasPerm = userPermisos.includes(p.codigo)
                        return (
                          <button
                            key={p.id}
                            onClick={() => togglePermiso(p.id)}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                              hasPerm
                                ? 'bg-primary-600/10 text-primary-400 border border-primary-500/20'
                                : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/30'
                            }`}
                          >
                            {hasPerm
                              ? <Check className="w-4 h-4 flex-shrink-0" />
                              : <Plus className="w-4 h-4 flex-shrink-0" />
                            }
                            <span className="text-left">{p.codigo}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
