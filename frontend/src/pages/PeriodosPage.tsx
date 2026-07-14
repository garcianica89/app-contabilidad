import { useState, useEffect } from 'react'
import { Search, Plus, AlertCircle, Calendar, Lock, Unlock } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'

export default function PeriodosPage() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => { load() }, [])
  async function load() {
    try { setItems(await api.getPeriodos()) } catch {}
    setLoading(false)
  }

  const filtered = items.filter((i) =>
    !search || i.codigo?.toLowerCase().includes(search.toLowerCase()) ||
    i.nombre?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Periodos Contables</h1>
          <p className="text-sm text-slate-400">Control de periodos contables y su estado</p>
        </div>
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar periodo..." />
      </div>

      {loading ? (
<Skeleton rows={5} />
      ) : filtered.length === 0 ? (
        <EmptyState message="No hay periodos registrados" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((p) => (
            <div key={p.id} className="card">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{p.codigo}</span>
              </div>
              <div className="text-xs text-slate-400 mb-1">{p.nombre}</div>
              <div className="flex gap-4 text-xs text-slate-500">
                <span>{p.fecha_inicio}</span>
                <span>→</span>
                <span>{p.fecha_fin}</span>
              </div>
              <div className="mt-3">
                {p.cerrado ? (
                  <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-red-600/20 text-red-400">
                    <Lock className="w-3 h-3" /> Cerrado
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-emerald-600/20 text-emerald-400">
                    <Unlock className="w-3 h-3" /> Abierto
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
