import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, Landmark, Banknote, ArrowLeftRight, Ban } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

type Tab = 'cuentas' | 'cheques' | 'movimientos'

export default function ERPTesoreriaPage() {
  const [tab, setTab] = useState<Tab>('cuentas')
  const [cuentas, setCuentas] = useState<any[]>([])
  const [cheques, setCheques] = useState<any[]>([])
  const [movimientos, setMovimientos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<'cuenta' | 'cheque' | 'movimiento'>('cuenta')
  const [form, setForm] = useState<any>({})
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [ctas, chqs, movs] = await Promise.all([
        api.erpGetCuentasBancarias().catch(() => []),
        api.erpGetCheques().catch(() => []),
        api.erpGetMovBancos().catch(() => []),
      ])
      setCuentas(ctas); setCheques(chqs); setMovimientos(movs)
    } catch {}
    setLoading(false)
  }

  function getItems() {
    if (tab === 'cuentas') return cuentas
    if (tab === 'cheques') return cheques
    return movimientos
  }

  const filtered = getItems().filter((i: any) =>
    !search || i.nombre?.toLowerCase().includes(search.toLowerCase()) || i.numero?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate(mode: 'cuenta' | 'cheque' | 'movimiento') {
    setFormMode(mode)
    setForm({})
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      if (formMode === 'cuenta') {
        const data = await api.erpCrearCuentaBancaria(form)
        setCuentas((prev) => [...prev, data])
      } else if (formMode === 'cheque') {
        const data = await api.erpCrearCheque(form)
        setCheques((prev) => [...prev, data])
      } else {
        const data = await api.erpCrearMovBanco(form)
        setMovimientos((prev) => [...prev, data])
      }
      setShowForm(false)
      notify('Creado exitosamente')
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  async function handleAnularCheque(id: string) {
    if (!confirm('Anular este cheque?')) return
    try {
      await api.erpAnularCheque(id)
      setCheques((prev) => prev.map((c) => c.id === id ? { ...c, estado: 'ANULADO' } : c))
      notify('Cheque anulado')
    } catch (err: any) { notify(err.message) }
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'cuentas', label: 'Cuentas Bancarias', icon: Landmark },
    { key: 'cheques', label: 'Cheques', icon: Banknote },
    { key: 'movimientos', label: 'Movimientos', icon: ArrowLeftRight },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Tesorería</h1>
          <p className="text-sm text-slate-400">Cuentas bancarias, cheques y movimientos</p>
        </div>
        <div className="flex gap-2">
          {tab === 'cuentas' && <button onClick={() => openCreate('cuenta')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nueva Cuenta</button>}
          {tab === 'cheques' && <button onClick={() => openCreate('cheque')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Cheque</button>}
          {tab === 'movimientos' && <button onClick={() => openCreate('movimiento')} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Nuevo Movimiento</button>}
        </div>
      </div>

      <div className="flex gap-1 bg-slate-800 rounded-lg p-1 w-fit">
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
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nuevo {formMode === 'cuenta' ? 'Cuenta Bancaria' : formMode === 'cheque' ? 'Cheque' : 'Movimiento'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          {formMode === 'cuenta' && (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Nombre *</label>
                <input value={form.nombre || ''} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-filter w-full" required placeholder="Banco Nacional" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Numero de Cuenta</label>
                <input value={form.numero || ''} onChange={(e) => setForm({ ...form, numero: e.target.value })} className="input-filter w-full" placeholder="191-123456-7" />
              </div>
            </>
          )}
          {formMode === 'cheque' && (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Numero Cheque *</label>
                <input value={form.numero || ''} onChange={(e) => setForm({ ...form, numero: e.target.value })} className="input-filter w-full" required placeholder="0001" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Monto *</label>
                <input type="number" step="0.01" value={form.monto || ''} onChange={(e) => setForm({ ...form, monto: e.target.value })} className="input-filter w-full" required placeholder="0.00" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Beneficiario</label>
                <input value={form.beneficiario || ''} onChange={(e) => setForm({ ...form, beneficiario: e.target.value })} className="input-filter w-full" placeholder="Nombre" />
              </div>
            </>
          )}
          {formMode === 'movimiento' && (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Cuenta Bancaria ID *</label>
                <input value={form.cuenta_bancaria_id || ''} onChange={(e) => setForm({ ...form, cuenta_bancaria_id: e.target.value })} className="input-filter w-full" required />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Monto *</label>
                <input type="number" step="0.01" value={form.monto || ''} onChange={(e) => setForm({ ...form, monto: e.target.value })} className="input-filter w-full" required placeholder="0.00" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Tipo</label>
                <select value={form.tipo || 'DEPOSITO'} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-filter w-full">
                  <option value="DEPOSITO">Deposito</option>
                  <option value="RETIRO">Retiro</option>
                  <option value="TRANSFERENCIA">Transferencia</option>
                </select>
              </div>
            </>
          )}
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> Crear</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <Skeleton rows={6} />
      ) : filtered.length === 0 ? (
        <EmptyState message={`No hay ${tab} registrados`} />
      ) : tab === 'cheques' ? (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Banknote className="w-4 h-4 text-primary-400" />
                  <span className="text-sm font-semibold text-white">Cheque #{i.numero}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    i.estado === 'ANULADO' ? 'bg-red-900/40 text-red-400' :
                    i.estado === 'EMITIDO' ? 'bg-yellow-900/40 text-yellow-400' :
                    'bg-green-900/40 text-green-400'
                  }`}>{i.estado || 'EMITIDO'}</span>
                </div>
                {i.estado !== 'ANULADO' && (
                  <button onClick={() => handleAnularCheque(i.id)} className="p-1 text-slate-500 hover:text-red-400"><Ban className="w-4 h-4" /></button>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1">C${i.monto?.toFixed(2)} - {i.beneficiario || '—'}</p>
            </div>
          ))}
        </div>
      ) : tab === 'cuentas' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((i: any) => (
            <div key={i.id} className="card">
              <div className="flex items-center gap-2 mb-1">
                <Landmark className="w-4 h-4 text-primary-400" />
                <span className="text-sm font-semibold text-white">{i.nombre}</span>
              </div>
              <p className="text-xs text-slate-400">{i.numero}</p>
              <p className="text-sm text-white mt-2">Saldo: C${i.saldo?.toFixed(2)}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-700/50">
                <th className="py-2 px-3">Cuenta</th>
                <th className="py-2 px-3">Tipo</th>
                <th className="py-2 px-3 text-right">Monto</th>
                <th className="py-2 px-3">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((i: any) => (
                <tr key={i.id} className="border-b border-slate-700/30 hover:bg-slate-700/20">
                  <td className="py-2 px-3 text-white">{i.cuenta_nombre || i.cuenta_bancaria_id}</td>
                  <td className="py-2 px-3 text-slate-300">{i.tipo}</td>
                  <td className={`py-2 px-3 text-right font-semibold ${i.tipo === 'DEPOSITO' ? 'text-green-400' : 'text-red-400'}`}>
                    {i.tipo === 'DEPOSITO' ? '+' : '-'}C${Math.abs(i.monto)?.toFixed(2)}
                  </td>
                  <td className="py-2 px-3 text-slate-400">{i.fecha || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
