import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Pencil, Trash2 } from 'lucide-react'

export default function EmpleadosPage() {
  const [empleados, setEmpleados] = useState<any[]>([])
  const [departamentos, setDepartamentos] = useState<any[]>([])
  const [cargos, setCargos] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [edit, setEdit] = useState<any>(null)
  const [tab, setTab] = useState<'empleados' | 'departamentos' | 'cargos'>('empleados')
  const [filter, setFilter] = useState('')

  const load = async () => {
    const [emp, dep, car] = await Promise.all([
      api.getEmpleados(),
      api.getDepartamentos(),
      api.getCargos(),
    ])
    setEmpleados(emp)
    setDepartamentos(dep)
    setCargos(car)
  }

  useEffect(() => { load() }, [])

  const depMap = Object.fromEntries(departamentos.map(d => [d.id, d.nombre]))
  const carMap = Object.fromEntries(cargos.map(c => [c.id, c.nombre]))

  const filteredEmpleados = empleados.filter(e =>
    e.nombre.toLowerCase().includes(filter.toLowerCase()) ||
    e.codigo.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Empleados</h1>
      <div className="flex gap-2 mb-4">
        {(['empleados', 'departamentos', 'cargos'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t ? 'bg-primary-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}>{t === 'empleados' ? 'Empleados' : t === 'departamentos' ? 'Departamentos' : 'Cargos'}</button>
        ))}
      </div>

      {tab === 'empleados' && (
        <>
          <div className="flex gap-2 mb-4">
            <input placeholder="Buscar..." value={filter} onChange={e => setFilter(e.target.value)}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white" />
            <button onClick={() => setEdit({})}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-700">
              <Plus className="w-4 h-4" /> Nuevo</button>
          </div>
          <div className="grid gap-3">
            {filteredEmpleados.map(e => (
              <div key={e.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">{e.nombre}</p>
                  <p className="text-sm text-slate-400">{e.codigo} · {depMap[e.departamento_id] || '-'} · {carMap[e.cargo_id] || '-'}</p>
                  <p className="text-sm text-slate-500">C$ {Number(e.salario_base).toLocaleString()} · {e.estado}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setEdit(e)} className="p-2 text-slate-400 hover:text-white"><Pencil className="w-4 h-4" /></button>
                  <button onClick={async () => { await api.eliminarEmpleado(e.id); load() }} className="p-2 text-red-400 hover:text-red-300"><Trash2 className="w-4 h-4" /></button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {tab === 'departamentos' && <CrudSubItems items={departamentos} onDelete={api.eliminarDepartamento} onRefresh={load} label="Departamento" onSave={(d: any) => d.id ? api.actualizarDepartamento(d.id, d) : api.crearDepartamento(d)} />}
      {tab === 'cargos' && <CrudSubItems items={cargos} onDelete={api.eliminarCargo} onRefresh={load} label="Cargo" onSave={(d: any) => d.id ? api.actualizarCargo(d.id, d) : api.crearCargo(d)} />}

      {(edit || tab !== 'empleados') && <ModalEdit empleado={edit} setEdit={setEdit} reload={load} />}
    </div>
  )
}

function CrudSubItems({ items, onDelete, onRefresh, label, onSave }: any) {
  const [editing, setEditing] = useState<any>(null)
  return (
    <div>
      <button onClick={() => setEditing({})} className="mb-4 bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-700">
        <Plus className="w-4 h-4" /> Nuevo {label}</button>
      <div className="grid gap-2">
        {items.map((i: any) => (
          <div key={i.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
            <div>
              <p className="text-white font-medium">{i.nombre}</p>
              <p className="text-sm text-slate-400">{i.codigo}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setEditing(i)} className="p-2 text-slate-400 hover:text-white"><Pencil className="w-4 h-4" /></button>
              <button onClick={async () => { await onDelete(i.id); onRefresh() }} className="p-2 text-red-400 hover:text-red-300"><Trash2 className="w-4 h-4" /></button>
            </div>
          </div>
        ))}
      </div>
      {editing !== null && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setEditing(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold text-white mb-4">{editing.id ? 'Editar' : 'Nuevo'} {label}</h2>
            <input placeholder="Codigo" value={editing.codigo || ''} onChange={e => setEditing({...editing, codigo: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-3" />
            <input placeholder="Nombre" value={editing.nombre || ''} onChange={e => setEditing({...editing, nombre: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-4" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setEditing(null)} className="px-4 py-2 text-slate-400 hover:text-white">Cancelar</button>
              <button onClick={async () => { await onSave(editing); setEditing(null); onRefresh() }} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">Guardar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ModalEdit({ empleado, setEdit, reload }: { empleado: any; setEdit: any; reload: any }) {
  const [form, setForm] = useState(empleado || {})
  const [departamentos, setDepartamentos] = useState<any[]>([])
  const [cargos, setCargos] = useState<any[]>([])

  useEffect(() => {
    api.getDepartamentos().then(setDepartamentos)
    api.getCargos().then(setCargos)
  }, [])

  const save = async () => {
    if (form.id) await api.actualizarEmpleado(form.id, form)
    else await api.crearEmpleado(form)
    setEdit(null)
    reload()
  }

  if (!empleado) return null
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setEdit(null)}>
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-white mb-4">{form.id ? 'Editar' : 'Nuevo'} Empleado</h2>
        <div className="grid grid-cols-2 gap-3">
          <input placeholder="Codigo" value={form.codigo || ''} onChange={e => setForm({...form, codigo: e.target.value})}
            className="col-span-2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
          <input placeholder="Nombre" value={form.nombre || ''} onChange={e => setForm({...form, nombre: e.target.value})}
            className="col-span-2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
          <input placeholder="Cedula" value={form.cedula || ''} onChange={e => setForm({...form, cedula: e.target.value})}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
          <input type="date" placeholder="Fecha Contratacion" value={form.fecha_contratacion || ''} onChange={e => setForm({...form, fecha_contratacion: e.target.value})}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
          <select value={form.departamento_id || ''} onChange={e => setForm({...form, departamento_id: e.target.value})}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white">
            <option value="">Sin Departamento</option>
            {departamentos.map(d => <option key={d.id} value={d.id}>{d.nombre}</option>)}
          </select>
          <select value={form.cargo_id || ''} onChange={e => setForm({...form, cargo_id: e.target.value})}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white">
            <option value="">Sin Cargo</option>
            {cargos.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <input type="number" placeholder="Salario Base" value={form.salario_base || ''} onChange={e => setForm({...form, salario_base: parseFloat(e.target.value) || 0})}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
          <select value={form.tipo_contrato || 'INDEFINIDO'} onChange={e => setForm({...form, tipo_contrato: e.target.value})}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white">
            <option value="INDEFINIDO">Indefinido</option>
            <option value="FIJO">Fijo</option>
            <option value="TEMPORAL">Temporal</option>
          </select>
          <input placeholder="Telefono" value={form.telefono || ''} onChange={e => setForm({...form, telefono: e.target.value})}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
          <input placeholder="Email" value={form.email || ''} onChange={e => setForm({...form, email: e.target.value})}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
        </div>
        <div className="flex gap-2 justify-end mt-4">
          <button onClick={() => setEdit(null)} className="px-4 py-2 text-slate-400 hover:text-white">Cancelar</button>
          <button onClick={save} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">Guardar</button>
        </div>
      </div>
    </div>
  )
}
