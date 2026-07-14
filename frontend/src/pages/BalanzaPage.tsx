import { useState, useEffect } from 'react'
import {
  Scale, Search, ChevronDown, ChevronRight, RefreshCw, FileText,
  Filter, CalendarDays, BookOpen,
} from 'lucide-react'
import { api } from '../services/api'
import type { BalanceComprobacionRow } from '../types/api'
import type { PeriodoContable } from '../types/api'

interface CuentaNode extends BalanceComprobacionRow {
  children: CuentaNode[]
  open: boolean
}

export default function BalanzaPage() {
  const [periodos, setPeriodos] = useState<PeriodoContable[]>([])
  const [periodoId, setPeriodoId] = useState('')
  const [cuentas, setCuentas] = useState<{ id: string; codigo: string; nombre: string }[]>([])
  const [cuentaId, setCuentaId] = useState('')
  const [nivelMaximo, setNivelMaximo] = useState(99)
  const [centroCostos, setCentroCostos] = useState<{ id: string; codigo: string; nombre: string }[]>([])
  const [centroCostoId, setCentroCostoId] = useState('')
  const [soloDiario, setSoloDiario] = useState(false)
  const [rows, setRows] = useState<BalanceComprobacionRow[]>([])
  const [loading, setLoading] = useState(false)
  const [recalculando, setRecalculando] = useState(false)
  const [cuentaSearch, setCuentaSearch] = useState('')

  useEffect(() => {
    api.getPeriodos().then(setPeriodos)
    api.getCentrosCosto().then(setCentroCostos)
    loadCuentas()
  }, [])

  const loadCuentas = async () => {
    try {
      const data = await api.getCuentasContables() as any[]
      setCuentas(data.map((c: any) => ({ id: c.id, codigo: c.codigo, nombre: c.nombre })))
    } catch {
      // ERP endpoint may be empty stub
    }
  }

  const consultar = async () => {
    setLoading(true)
    try {
      const data = await api.getBalanceComprobacion({
        periodo_id: periodoId || undefined,
        cuenta_id: cuentaId || undefined,
        nivel_maximo: nivelMaximo < 99 ? nivelMaximo : undefined,
        centro_costo_id: centroCostoId || undefined,
        solo_diario: soloDiario || undefined,
      })
      setRows(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const recalcular = async () => {
    if (!periodoId) return
    setRecalculando(true)
    try {
      await api.recalcularSaldos(periodoId, cuentaId || undefined, centroCostoId || undefined)
      await consultar()
    } finally {
      setRecalculando(false)
    }
  }

  const exportXlsx = async () => {
    const q = new URLSearchParams()
    if (periodoId) q.set('periodo_id', periodoId)
    if (cuentaId) q.set('cuenta_id', cuentaId)
    if (nivelMaximo < 99) q.set('nivel_maximo', String(nivelMaximo))
    if (centroCostoId) q.set('centro_costo_id', centroCostoId)
    if (soloDiario) q.set('solo_diario', 'true')
    q.set('formato', 'xlsx')

    const token = localStorage.getItem('token')
    const res = await fetch(`/api/v1/reportes/balance-comprobacion?${q.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'balance_comprobacion.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  }

  // Build tree from flat rows
  const buildTree = (flat: BalanceComprobacionRow[]): CuentaNode[] => {
    const map = new Map<string, CuentaNode>()
    const roots: CuentaNode[] = []

    for (const r of flat) {
      map.set(r.cuenta_id, { ...r, children: [], open: true })
    }

    for (const r of flat) {
      const node = map.get(r.cuenta_id)!
      if (r.padre_id && map.has(r.padre_id)) {
        map.get(r.padre_id)!.children.push(node)
      } else {
        roots.push(node)
      }
    }

    return roots
  }

  const tree = buildTree(rows)

  // Calculate subtotals
  const calcSubtotals = (nodes: CuentaNode[]): BalanceComprobacionRow => {
    let debe = 0, haber = 0, sd = 0, sa = 0, sf = 0, sa_ant = 0
    for (const n of nodes) {
      if (n.nivel <= 4) {
        const sub = calcSubtotals(n.children)
        debe += sub.debe
        haber += sub.haber
        sd += sub.saldo_deudor
        sa += sub.saldo_acreedor
        sf += sub.saldo_final
        sa_ant += sub.saldo_anterior
      } else {
        debe += n.debe
        haber += n.haber
        sd += n.saldo_deudor
        sa += n.saldo_acreedor
        sf += n.saldo_final
        sa_ant += n.saldo_anterior
      }
    }
    return { cuenta_id: '', codigo: '', nombre: 'SUBTOTAL', nivel: 0, naturaleza: '', tipo: '', padre_id: null, debe, haber, saldo_deudor: sd, saldo_acreedor: sa, saldo_final: sf, saldo_anterior: sa_ant }
  }

  const renderNode = (node: CuentaNode, depth: number) => {
    const hasChildren = node.children.length > 0
    return (
      <div key={node.cuenta_id}>
        <div
          className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm transition-colors hover:bg-slate-800/30 cursor-pointer ${
            node.nivel <= 3 ? 'font-semibold text-slate-200' : 'text-slate-400'
          }`}
          onClick={() => { node.open = !node.open; setRows([...rows]) }}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          <div className="w-5 flex-shrink-0">
            {hasChildren && (node.open ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />)}
          </div>
          <div className="w-24 text-xs font-mono text-slate-500 truncate">{node.codigo}</div>
          <div className="flex-1 truncate">{node.nombre}</div>
          <div className="w-20 text-right tabular-nums">{node.debe ? node.debe.toFixed(2) : ''}</div>
          <div className="w-20 text-right tabular-nums">{node.haber ? node.haber.toFixed(2) : ''}</div>
          <div className="w-24 text-right tabular-nums text-red-400">{node.saldo_deudor ? node.saldo_deudor.toFixed(2) : ''}</div>
          <div className="w-24 text-right tabular-nums text-green-400">{node.saldo_acreedor ? node.saldo_acreedor.toFixed(2) : ''}</div>
        </div>
        {hasChildren && node.open && (
          <div>
            {node.children.map(child => renderNode(child, depth + 1))}
            {node.nivel <= 3 && node.children.length > 0 && (
              <div className="flex items-center gap-2 px-2 py-1 text-xs font-bold text-slate-500 border-t border-slate-800/50"
                style={{ paddingLeft: `${(depth + 1) * 16 + 8}px` }}
              >
                <div className="w-24" />
                <div className="flex-1 truncate">Subtotal {node.codigo}</div>
                <div className="w-20 text-right tabular-nums">{(() => {
                  const sub = calcSubtotals(node.children)
                  return sub.debe ? sub.debe.toFixed(2) : ''
                })()}</div>
                <div className="w-20 text-right tabular-nums">{(() => {
                  const sub = calcSubtotals(node.children)
                  return sub.haber ? sub.haber.toFixed(2) : ''
                })()}</div>
                <div className="w-24 text-right tabular-nums">{(() => {
                  const sub = calcSubtotals(node.children)
                  return sub.saldo_deudor ? sub.saldo_deudor.toFixed(2) : ''
                })()}</div>
                <div className="w-24 text-right tabular-nums">{(() => {
                  const sub = calcSubtotals(node.children)
                  return sub.saldo_acreedor ? sub.saldo_acreedor.toFixed(2) : ''
                })()}</div>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const totalRow = rows.length > 0 ? calcSubtotals(tree) : null

  // Filter cuentas for search
  const filteredCuentas = cuentaSearch
    ? cuentas.filter(c =>
        c.codigo.toLowerCase().includes(cuentaSearch.toLowerCase()) ||
        c.nombre.toLowerCase().includes(cuentaSearch.toLowerCase())
      ).slice(0, 20)
    : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary-600/20 rounded-lg">
          <Scale className="w-6 h-6 text-primary-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Balanza de Comprobación</h1>
          <p className="text-slate-400 text-sm">Saldos por cuenta contable con corte a periodo o fecha</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-slate-500 mb-1 uppercase tracking-wider">Periodo</label>
            <select
              value={periodoId}
              onChange={e => setPeriodoId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Último periodo abierto</option>
              {periodos.map(p => (
                <option key={p.id} value={p.id}>
                  {p.nombre} ({p.fecha_inicio} - {p.fecha_fin})
                </option>
              ))}
            </select>
          </div>

          <div className="relative">
            <label className="block text-xs text-slate-500 mb-1 uppercase tracking-wider">Cuenta Contable</label>
            <input
              type="text"
              placeholder="Buscar cuenta..."
              value={cuentaSearch}
              onChange={e => {
                setCuentaSearch(e.target.value)
                if (!e.target.value) setCuentaId('')
              }}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-8 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <Search className="absolute left-2.5 top-[34px] w-4 h-4 text-slate-500" />
            {cuentaSearch && filteredCuentas.length > 0 && (
              <div className="absolute z-10 mt-1 w-full bg-slate-800 border border-slate-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {filteredCuentas.map(c => (
                  <button
                    key={c.id}
                    onClick={() => { setCuentaId(c.id); setCuentaSearch(`${c.codigo} - ${c.nombre}`) }}
                    className="w-full text-left px-3 py-2 text-sm text-slate-300 hover:bg-slate-700"
                  >
                    <span className="font-mono text-slate-500">{c.codigo}</span> - {c.nombre}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs text-slate-500 mb-1 uppercase tracking-wider">Nivel Máximo</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5, 6, 7, 8].map(n => (
                <button
                  key={n}
                  onClick={() => setNivelMaximo(n)}
                  className={`px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                    nivelMaximo === n
                      ? 'bg-primary-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {n}
                </button>
              ))}
              <button
                onClick={() => setNivelMaximo(99)}
                className={`px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                  nivelMaximo === 99
                    ? 'bg-primary-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                Todo
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-500 mb-1 uppercase tracking-wider">Centro de Costo</label>
            <select
              value={centroCostoId}
              onChange={e => setCentroCostoId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Todos</option>
              {centroCostos.map(cc => (
                <option key={cc.id} value={cc.id}>{cc.codigo} - {cc.nombre}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-800">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={soloDiario}
              onChange={e => setSoloDiario(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-slate-400">
              <BookOpen className="w-4 h-4 inline mr-1" />
              Solo asientos de Diario (excluye documentos)
            </span>
          </label>

          <div className="flex gap-2">
            <button
              onClick={consultar}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              <Filter className="w-4 h-4" />
              {loading ? 'Consultando...' : 'Consultar'}
            </button>
            <button
              onClick={recalcular}
              disabled={recalculando || !periodoId}
              className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-sm transition-colors disabled:opacity-50"
              title="Recalcular saldos para el periodo seleccionado"
            >
              <RefreshCw className={`w-4 h-4 ${recalculando ? 'animate-spin' : ''}`} />
              Recalcular
            </button>
            <button
              onClick={exportXlsx}
              className="flex items-center gap-2 px-3 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-sm transition-colors"
            >
              <FileText className="w-4 h-4" />
              Excel
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-800 overflow-hidden">
        {/* Column headers */}
        <div className="flex items-center gap-2 px-2 py-2.5 bg-slate-800/50 border-b border-slate-700 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          <div className="w-5 flex-shrink-0" />
          <div className="w-24">Código</div>
          <div className="flex-1">Nombre</div>
          <div className="w-20 text-right">Debe</div>
          <div className="w-20 text-right">Haber</div>
          <div className="w-24 text-right">Saldo Deudor</div>
          <div className="w-24 text-right">Saldo Acreedor</div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500">Cargando...</div>
        ) : rows.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <Scale className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Selecciona filtros y presiona Consultar</p>
          </div>
        ) : (
          <div className="max-h-[55vh] overflow-y-auto">
            {tree.map(node => renderNode(node, 0))}

            {/* Grand total */}
            {totalRow && (
              <div className="flex items-center gap-2 px-2 py-2.5 bg-slate-800/80 border-t border-slate-700 text-sm font-bold text-white sticky bottom-0">
                <div className="w-5 flex-shrink-0" />
                <div className="w-24" />
                <div className="flex-1">TOTALES</div>
                <div className="w-20 text-right tabular-nums">{totalRow.debe.toFixed(2)}</div>
                <div className="w-20 text-right tabular-nums">{totalRow.haber.toFixed(2)}</div>
                <div className="w-24 text-right tabular-nums text-red-400">{totalRow.saldo_deudor.toFixed(2)}</div>
                <div className="w-24 text-right tabular-nums text-green-400">{totalRow.saldo_acreedor.toFixed(2)}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
