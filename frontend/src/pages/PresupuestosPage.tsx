import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Pencil, Trash2 } from 'lucide-react'

export default function PresupuestosPage() {
  const [presupuestos, setPresupuestos] = useState<any[]>([])
  const [centros, setCentros] = useState<any[]>([])
  const [cuentas, setCuentas] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [edit, setEdit] = useState<any>(null)
  const [tab, setTab] = useState<'presupuestos' | 'centros'>('presupuestos')

  const load = async () => {
    const [p, c, cu] = await Promise.all([
      api.getPresupuestos(),
      api.getCentrosCosto(),
      api.getCuentasContables(),
    ])
    setPresupuestos(p)
    setCentros(c)
    setCuentas(cu)
  }
  useEffect(() => { load() }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Presupuestos</h1>
      <div className="flex gap-2 mb-4">
        <button onClick={() => setTab('presupuestos')}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === 'presupuestos' ? 'bg-primary-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Presupuestos</button>
        <button onClick={() => setTab('centros')}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === 'centros' ? 'bg-primary-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Centros de Costo</button>
      </div>

      {tab === 'presupuestos' && (
        <>
          {selected && <DetallePresupuesto presupuesto={selected} onBack={() => setSelected(null)} onRefresh={load} cuentas={cuentas} centros={centros} />}
          {!selected && (
            <>
              <div className="flex gap-2 mb-4">
                <button onClick={() => setEdit({})}
                  className="bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-700">
                  <Plus className="w-4 h-4" /> Nuevo Presupuesto</button>
              </div>
              <div className="grid gap-3">
                {presupuestos.map((p: any) => (
                  <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-center justify-between">
                    <div>
                      <p className="text-white font-medium">{p.nombre}</p>
                      <p className="text-sm text-slate-400">{p.anio} · v{p.version}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        p.estado === 'APROBADO' ? 'bg-green-900 text-green-400' :
                        p.estado === 'CERRADO' ? 'bg-red-900 text-red-400' :
                        'bg-slate-800 text-slate-400'}`}>{p.estado}</span>
                      <button onClick={() => setSelected(p)} className="p-2 text-slate-400 hover:text-white">Ver</button>
                      {p.estado === 'BORRADOR' && (
                        <button onClick={() => setEdit(p)} className="p-2 text-slate-400 hover:text-white"><Pencil className="w-4 h-4" /></button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {tab === 'centros' && (
        <div>
          <button onClick={async () => {
            const c = prompt('Codigo:')
            if (!c) return
            const n = prompt('Nombre:')
            if (!n) return
            await api.crearCentroCosto({ codigo: c, nombre: n })
            load()
          }} className="mb-4 bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-700">
            <Plus className="w-4 h-4" /> Nuevo Centro Costo</button>
          <div className="grid gap-2">
            {centros.map((c: any) => (
              <div key={c.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">{c.nombre}</p>
                  <p className="text-sm text-slate-400">{c.codigo}</p>
                </div>
                <button onClick={async () => { await api.eliminarCentroCosto(c.id); load() }} className="p-2 text-red-400"><Trash2 className="w-4 h-4" /></button>
              </div>
            ))}
          </div>
        </div>
      )}

      {edit && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setEdit(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold text-white mb-4">{edit.id ? 'Editar' : 'Nuevo'} Presupuesto</h2>
            <input placeholder="Nombre" value={edit.nombre || ''} onChange={(e: any) => setEdit({...edit, nombre: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-3" />
            <input type="number" placeholder="Año" value={edit.anio || ''} onChange={(e: any) => setEdit({...edit, anio: parseInt(e.target.value) || 0})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-4" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setEdit(null)} className="px-4 py-2 text-slate-400 hover:text-white">Cancelar</button>
              <button onClick={async () => {
                if (edit.id) await api.actualizarPresupuesto(edit.id, edit)
                else await api.crearPresupuesto(edit)
                setEdit(null); load()
              }} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">Guardar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DetallePresupuesto({ presupuesto, onBack, onRefresh, cuentas, centros }: any) {
  const [partidas, setPartidas] = useState<any[]>([])
  const [editPartida, setEditPartida] = useState<any>(null)

  const loadPartidas = async () => {
    setPartidas(await api.getPartidasPresupuesto(presupuesto.id))
  }
  useEffect(() => { loadPartidas() }, [presupuesto.id])

  const cuentaMap = Object.fromEntries(cuentas.map((c: any) => [c.id, `${c.codigo} - ${c.nombre}`]))
  const centroMap = Object.fromEntries(centros.map((c: any) => [c.id, c.nombre]))
  const meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

  const totales = meses.map((_, i) => ({
    mes: i + 1,
    total: partidas.filter(p => p.mes === i + 1).reduce((s, p) => s + Number(p.monto_presupuestado), 0)
  }))

  return (
    <div>
      <button onClick={onBack} className="text-sm text-primary-400 hover:text-primary-300 mb-4">← Volver</button>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-white">{presupuesto.nombre}</h2>
          <p className="text-sm text-slate-400">{presupuesto.anio} · v{presupuesto.version} · {presupuesto.estado}</p>
        </div>
        <div className="flex gap-2">
          {presupuesto.estado === 'BORRADOR' && (
            <>
              <button onClick={async () => { await api.aprobarPresupuesto(presupuesto.id); onRefresh(); loadPartidas() }}
                className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-green-700">
                Aprobar</button>
              <button onClick={() => setEditPartida({})}
                className="bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-700">
                <Plus className="w-4 h-4" /> Agregar Partida</button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        {totales.map(t => (
          <div key={t.mes} className="bg-slate-900 border border-slate-800 rounded-lg p-3">
            <p className="text-xs text-slate-400">{meses[t.mes - 1]}</p>
            <p className="text-lg text-white font-medium">C$ {t.total.toLocaleString()}</p>
          </div>
        ))}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-800 text-slate-400">
            <th className="text-left p-3">Cuenta</th>
            <th className="text-left p-3">Centro Costo</th>
            <th className="text-left p-3">Mes</th>
            <th className="text-right p-3">Monto</th>
            {presupuesto.estado === 'BORRADOR' && <th className="p-3"></th>}
          </tr></thead>
          <tbody>
            {partidas.length === 0 && (
              <tr><td colSpan={5} className="p-6 text-center text-slate-500">Sin partidas</td></tr>
            )}
            {partidas.map((p: any) => (
              <tr key={p.id} className="border-b border-slate-800 text-white">
                <td className="p-3">{cuentaMap[p.cuenta_contable_id] || p.cuenta_contable_id}</td>
                <td className="p-3 text-slate-400">{centroMap[p.centro_costo_id] || '-'}</td>
                <td className="p-3">{meses[p.mes - 1]}</td>
                <td className="p-3 text-right">C$ {Number(p.monto_presupuestado).toLocaleString()}</td>
                {presupuesto.estado === 'BORRADOR' && (
                  <td className="p-3">
                    <button onClick={async () => { await api.eliminarPartidaPresupuesto(presupuesto.id, p.id); loadPartidas() }}
                      className="p-1 text-red-400"><Trash2 className="w-4 h-4" /></button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editPartida !== null && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setEditPartida(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold text-white mb-4">Nueva Partida</h2>
            <select value={editPartida.cuenta_contable_id || ''} onChange={(e: any) => setEditPartida({...editPartida, cuenta_contable_id: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-3">
              <option value="">Seleccionar Cuenta</option>
              {cuentas.map((c: any) => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
            </select>
            <select value={editPartida.centro_costo_id || ''} onChange={(e: any) => setEditPartida({...editPartida, centro_costo_id: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-3">
              <option value="">Sin Centro Costo</option>
              {centros.map((c: any) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            <select value={editPartida.mes || 1} onChange={(e: any) => setEditPartida({...editPartida, mes: parseInt(e.target.value)})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-3">
              {['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'].map((m, i) => (
                <option key={i+1} value={i+1}>{m}</option>
              ))}
            </select>
            <input type="number" placeholder="Monto" value={editPartida.monto_presupuestado || ''}
              onChange={(e: any) => setEditPartida({...editPartida, monto_presupuestado: parseFloat(e.target.value) || 0})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-4" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setEditPartida(null)} className="px-4 py-2 text-slate-400 hover:text-white">Cancelar</button>
              <button onClick={async () => {
                await api.crearPartidaPresupuesto(presupuesto.id, editPartida)
                setEditPartida(null); loadPartidas()
              }} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">Guardar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
