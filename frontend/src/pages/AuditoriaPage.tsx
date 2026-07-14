import { useState, useEffect } from 'react'
import { Shield, Search, Filter } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'

interface AuditEntry {
  id: string
  usuario_id: string | null
  usuario_nombre: string | null
  tabla: string
  registro_id: string
  accion: string
  valor_anterior: Record<string, unknown> | null
  valor_nuevo: Record<string, unknown> | null
  created_at: string
}

export default function AuditoriaPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [tablaFilter, setTablaFilter] = useState('')
  const [accionFilter, setAccionFilter] = useState('')
  const [selected, setSelected] = useState<AuditEntry | null>(null)

  useEffect(() => {
    loadData()
  }, [tablaFilter, accionFilter])

  async function loadData() {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (tablaFilter) params.tabla = tablaFilter
      if (accionFilter) params.accion = accionFilter
      params.limit = '100'
      const q = '?' + new URLSearchParams(params).toString()
      const data = await api.request<any[]>(`/auditoria${q}`)
      setEntries(data)
    } catch { /* ignore */ }
    setLoading(false)
  }

  function badgeAccion(accion: string) {
    const map: Record<string, string> = {
      CREAR: 'bg-emerald-900/50 text-emerald-300 border-emerald-700',
      ACTUALIZAR: 'bg-amber-900/50 text-amber-300 border-amber-700',
      ELIMINAR: 'bg-red-900/50 text-red-300 border-red-700',
    }
    return map[accion] || 'bg-slate-700 text-slate-300 border-slate-600'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-cyan-400" />
          Auditoria
        </h1>
      </div>

      <div className="flex gap-3 items-end">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Tabla</label>
          <select value={tablaFilter} onChange={e => setTablaFilter(e.target.value)}
            className="input-filter">
            <option value="">Todas</option>
            {['asiento', 'factura_compra', 'factura_venta', 'producto', 'cliente', 'proveedor', 'usuario'].map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Accion</label>
          <select value={accionFilter} onChange={e => setAccionFilter(e.target.value)}
            className="input-filter">
            <option value="">Todas</option>
            <option value="CREAR">Crear</option>
            <option value="ACTUALIZAR">Actualizar</option>
            <option value="ELIMINAR">Eliminar</option>
          </select>
        </div>
        <button onClick={loadData} className="btn-primary flex items-center gap-1">
          <Filter className="w-4 h-4" /> Filtrar
        </button>
      </div>

      {loading ? (
        <Skeleton rows={8} />
      ) : entries.length === 0 ? (
        <EmptyState message="No se encontraron registros de auditoria" />
      ) : (
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Usuario</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Tabla</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Accion</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Detalle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {entries.map(e => (
                  <tr key={e.id}
                    onClick={() => setSelected(selected?.id === e.id ? null : e)}
                    className="hover:bg-slate-700/30 transition-colors cursor-pointer">
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {new Date(e.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-white">{e.usuario_nombre || e.usuario_id?.slice(0, 8) || 'Sistema'}</td>
                    <td className="px-4 py-3 text-sm text-slate-300 font-mono">{e.tabla}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs border ${badgeAccion(e.accion)}`}>
                        {e.accion}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {e.accion === 'CREAR' ? 'Registro creado' :
                       e.accion === 'ELIMINAR' ? 'Registro eliminado' :
                       'Valores modificados'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selected && (
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Detalle de cambios</h3>
            <button onClick={() => setSelected(null)} className="text-slate-500 hover:text-white text-xs">Cerrar</button>
          </div>
          {selected.valor_anterior && (
            <div>
              <h4 className="text-xs text-slate-400 mb-1">Valor Anterior</h4>
              <pre className="text-xs text-slate-300 bg-slate-900 rounded p-2 overflow-x-auto">
                {JSON.stringify(selected.valor_anterior, null, 2)}
              </pre>
            </div>
          )}
          {selected.valor_nuevo && (
            <div>
              <h4 className="text-xs text-slate-400 mb-1">Valor Nuevo</h4>
              <pre className="text-xs text-slate-300 bg-slate-900 rounded p-2 overflow-x-auto">
                {JSON.stringify(selected.valor_nuevo, null, 2)}
              </pre>
            </div>
          )}
          {!selected.valor_anterior && !selected.valor_nuevo && (
            <p className="text-xs text-slate-500">Sin datos de cambios disponibles</p>
          )}
        </div>
      )}
    </div>
  )
}
