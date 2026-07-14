import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Trash2, TrendingUp, AlertCircle, BarChart3 } from 'lucide-react'

const tipos = [
  { value: 'PREDICCION', label: 'Prediccion', icon: TrendingUp },
  { value: 'RECOMENDACION', label: 'Recomendacion', icon: AlertCircle },
  { value: 'ANOMALIA', label: 'Anomalia', icon: AlertCircle },
]

export default function IAPage() {
  const [analisis, setAnalisis] = useState<any[]>([])
  const [filter, setFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newItem, setNewItem] = useState({ tipo: 'PREDICCION', modulo: '', titulo: '', descripcion: '' })

  const load = async () => {
    setAnalisis(await api.getAnalisisIA(filter || undefined))
  }
  useEffect(() => { load() }, [filter])

  const create = async () => {
    await api.crearAnalisisIA(newItem)
    setNewItem({ tipo: 'PREDICCION', modulo: '', titulo: '', descripcion: '' })
    setShowCreate(false)
    load()
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        <BarChart3 className="w-7 h-7 text-primary-400" /> Analisis IA</h1>

      <div className="flex gap-2 mb-4 flex-wrap">
        <button onClick={() => setFilter('')}
          className={`px-3 py-1.5 rounded-lg text-sm ${!filter ? 'bg-primary-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Todos</button>
        {tipos.map(t => (
          <button key={t.value} onClick={() => setFilter(t.value)}
            className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1 ${filter === t.value ? 'bg-primary-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
            <t.icon className="w-4 h-4" /> {t.label}</button>
        ))}
        <div className="flex-1" />
        <button onClick={() => setShowCreate(true)}
          className="bg-primary-600 text-white px-4 py-1.5 rounded-lg flex items-center gap-2 hover:bg-primary-700">
          <Plus className="w-4 h-4" /> Nuevo</button>
      </div>

      <div className="grid gap-3">
        {analisis.map((a: any) => {
          const Icon = tipos.find(t => t.value === a.tipo)?.icon || BarChart3
          return (
            <div key={a.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Icon className="w-5 h-5 text-primary-400" />
                  <p className="text-white font-medium">{a.titulo || a.tipo}</p>
                  <span className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400">{a.tipo}</span>
                  {a.modulo && <span className="text-xs text-slate-500">· {a.modulo}</span>}
                </div>
                <div className="flex gap-1">
                  {!a.resultado && (
                    <button onClick={async () => { await api.ejecutarAnalisisIA(a.id); load() }}
                      className="p-2 text-green-400 hover:text-green-300">▶</button>
                  )}
                  <button onClick={async () => { await api.eliminarAnalisisIA(a.id); load() }}
                    className="p-2 text-red-400 hover:text-red-300"><Trash2 className="w-4 h-4" /></button>
                </div>
              </div>
              {a.descripcion && <p className="text-sm text-slate-400 mb-2">{a.descripcion}</p>}
              {a.resultado && (
                <div className="bg-slate-800 rounded p-3 mt-2">
                  <p className="text-xs text-slate-500 mb-1">Resultado:</p>
                  <pre className="text-sm text-green-400 font-mono">{JSON.stringify(a.resultado, null, 2)}</pre>
                </div>
              )}
            </div>
          )
        })}
        {analisis.length === 0 && (
          <p className="text-center text-slate-500 py-12">Sin analisis IA</p>
        )}
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold text-white mb-4">Nuevo Analisis IA</h2>
            <select value={newItem.tipo} onChange={e => setNewItem({...newItem, tipo: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-3">
              {tipos.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
            <input placeholder="Modulo (ej: ventas, finanzas)" value={newItem.modulo} onChange={e => setNewItem({...newItem, modulo: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-3" />
            <input placeholder="Titulo" value={newItem.titulo} onChange={e => setNewItem({...newItem, titulo: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-3" />
            <textarea placeholder="Descripcion" value={newItem.descripcion} onChange={e => setNewItem({...newItem, descripcion: e.target.value})}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-4" rows={3} />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-slate-400 hover:text-white">Cancelar</button>
              <button onClick={create}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">Crear</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
