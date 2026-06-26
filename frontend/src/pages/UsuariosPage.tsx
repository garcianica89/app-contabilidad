import { useState, useEffect } from 'react'
import { UserPlus, ToggleLeft, ToggleRight, Shield, Pencil } from 'lucide-react'

interface Usuario {
  id: string
  username: string
  email: string
  nombre_completo: string
  activo: boolean
  roles: { id: string; nombre: string }[]
  ultimo_acceso: string | null
  created_at: string
}

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({ username: '', email: '', password: '', nombre_completo: '' })
  const [roles, setRoles] = useState<{ id: string; nombre: string }[]>([])
  const [selectedRoles, setSelectedRoles] = useState<string[]>([])

  useEffect(() => {
    Promise.all([
      fetch('/api/v1/usuarios?solo_activos=false').then((r) => r.json()),
      fetch('/api/v1/roles').then((r) => r.json()),
    ]).then(([users, r]) => {
      setUsuarios(users)
      setRoles(r)
    }).finally(() => setLoading(false))
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const method = editId ? 'PUT' : 'POST'
    const url = editId ? `/api/v1/usuarios/${editId}` : '/api/v1/usuarios'
    const body: any = { ...form }
    if (!body.password) delete body.password

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
      body: JSON.stringify(body),
    })

    if (res.ok) {
      const updated = await res.json()
      setUsuarios((prev) =>
        editId ? prev.map((u) => (u.id === editId ? updated : u)) : [...prev, updated]
      )
      if (editId && selectedRoles.length > 0) {
        await fetch(`/api/v1/usuarios/${editId}/roles`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
          body: JSON.stringify(selectedRoles),
        })
      }
      resetForm()
    }
  }

  function editUser(u: Usuario) {
    setEditId(u.id)
    setForm({ username: u.username, email: u.email, password: '', nombre_completo: u.nombre_completo })
    setSelectedRoles(u.roles.map((r) => r.id))
    setShowForm(true)
  }

  function resetForm() {
    setShowForm(false)
    setEditId(null)
    setForm({ username: '', email: '', password: '', nombre_completo: '' })
    setSelectedRoles([])
  }

  async function toggleActivo(u: Usuario) {
    const res = await fetch(`/api/v1/usuarios/${u.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
      body: JSON.stringify({ activo: !u.activo }),
    })
    if (res.ok) {
      const updated = await res.json()
      setUsuarios((prev) => prev.map((p) => (p.id === u.id ? updated : p)))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Administracion de Usuarios</h1>
          <p className="text-sm text-slate-400">Gestion de usuarios, roles y permisos</p>
        </div>
        <button onClick={() => { resetForm(); setShowForm(true) }} className="btn-primary flex items-center gap-2">
          <UserPlus className="w-4 h-4" />
          Nuevo Usuario
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4 max-w-lg">
          <h3 className="text-sm font-semibold text-white">{editId ? 'Editar Usuario' : 'Nuevo Usuario'}</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Usuario</label>
              <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })}
                className="input-filter w-full" required disabled={!!editId} />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre Completo</label>
              <input value={form.nombre_completo} onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })}
                className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="input-filter w-full" required />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">{editId ? 'Nueva Contrasena (opcional)' : 'Contrasena'}</label>
              <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="input-filter w-full" required={!editId} />
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-2">Roles</label>
            <div className="flex flex-wrap gap-2">
              {roles.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => setSelectedRoles((prev) =>
                    prev.includes(r.id) ? prev.filter((x) => x !== r.id) : [...prev, r.id]
                  )}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    selectedRoles.includes(r.id)
                      ? 'bg-primary-600/20 border-primary-500 text-primary-400'
                      : 'bg-slate-700/50 border-slate-600 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {r.nombre}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button type="submit" className="btn-primary">Guardar</button>
            <button type="button" onClick={resetForm} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="card overflow-hidden !p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Usuario</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Nombre</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Email</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Roles</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Estado</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {usuarios.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/30">
                  <td className="px-4 py-3">
                    <span className="text-white font-medium">{u.username}</span>
                    <span className="text-slate-500 text-xs block">{u.ultimo_acceso ? `Ultimo: ${u.ultimo_acceso.slice(0, 10)}` : 'Nunca'}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{u.nombre_completo}</td>
                  <td className="px-4 py-3 text-slate-300">{u.email}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1 flex-wrap">
                      {u.roles.map((r) => (
                        <span key={r.id} className="px-2 py-0.5 bg-primary-600/20 text-primary-400 rounded text-xs">
                          {r.nombre}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      u.activo ? 'bg-emerald-600/20 text-emerald-400' : 'bg-red-600/20 text-red-400'
                    }`}>
                      {u.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => editUser(u)} className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white">
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button onClick={() => toggleActivo(u)} className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white">
                        {u.activo ? <ToggleRight className="w-4 h-4 text-emerald-400" /> : <ToggleLeft className="w-4 h-4 text-red-400" />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
