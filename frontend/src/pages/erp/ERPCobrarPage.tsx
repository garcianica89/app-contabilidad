import { useState, useEffect } from 'react'
import { Search, Plus, Pencil, X, Check, AlertCircle, DollarSign, FileText, TrendingUp } from 'lucide-react'
import { api } from '../../services/api'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { useNotification } from '../../contexts/NotificationContext'

type Tab = 'documentos' | 'cobros'

export default function ERPCobrarPage() {
  const [tab, setTab] = useState<Tab>('documentos')
  const [documentos, setDocumentos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<'documento' | 'cobro'>('documento')
  const [form, setForm] = useState<any>({ cliente: '', monto: '', tipo: 'FACTURA' })
  const [saving, setSaving] = useState(false)
  const { notify } = useNotification()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const docs = await api.erpGetDocumentosCC().catch(() => [])
      setDocumentos(docs)
    } catch {}
    setLoading(false)
  }

  const filtered = documentos.filter((i: any) =>
    !search || i.cliente_nombre?.toLowerCase().includes(search.toLowerCase()) || i.numero?.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate(mode: 'documento' | 'cobro') {
    setFormMode(mode)
    setForm({ cliente: '', monto: '', tipo: 'FACTURA', referencia: '' })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true)
    try {
      if (formMode === 'documento') {
        const data = await api.erpCrearDocumentoCC(form)
        setDocumentos((prev) => [...prev, data])
      } else {
        await api.erpRegistrarCobro(form)
        notify('Cobro registrado')
      }
      setShowForm(false)
    } catch (err: any) { notify(err.message) }
    setSaving(false)
  }

  const mostrar = formMode === 'documento' ? documentos : documentos.filter((d: any) => d.saldo > 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Cuentas por Cobrar</h1>
          <p className="text-sm text-slate-400">Documentos y cobros</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => openCreate('documento')} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Nuevo Documento
          </button>
          <button onClick={() => openCreate('cobro')} className="btn-secondary flex items-center gap-2">
            <DollarSign className="w-4 h-4" /> Registrar Cobro
          </button>
        </div>
      </div>

      <div className="flex gap-1 bg-slate-800 rounded-lg p-1 w-fit">
        <button onClick={() => setTab('documentos')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm ${tab === 'documentos' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}>
          <FileText className="w-4 h-4" /> Documentos
        </button>
        <button onClick={() => setTab('cobros')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm ${tab === 'cobros' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}>
          <TrendingUp className="w-4 h-4" /> Cobros
        </button>
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar..." />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{formMode === 'documento' ? 'Nuevo Documento CC' : 'Registrar Cobro'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          {formMode === 'documento' ? (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Cliente *</label>
                <input value={form.cliente} onChange={(e) => setForm({ ...form, cliente: e.target.value })} className="input-filter w-full" required placeholder="Nombre del cliente" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Monto *</label>
                <input type="number" step="0.01" value={form.monto} onChange={(e) => setForm({ ...form, monto: e.target.value })} className="input-filter w-full" required placeholder="0.00" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Tipo</label>
                <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-filter w-full">
                  <option value="FACTURA">Factura</option>
                  <option value="NOTA_CREDITO">Nota de Credito</option>
                  <option value="RECIBO">Recibo</option>
                </select>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Referencia Documento *</label>
                <input value={form.referencia} onChange={(e) => setForm({ ...form, referencia: e.target.value })} className="input-filter w-full" required placeholder="Doc-001" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Monto Cobro *</label>
                <input type="number" step="0.01" value={form.monto} onChange={(e) => setForm({ ...form, monto: e.target.value })} className="input-filter w-full" required placeholder="0.00" />
              </div>
            </>
          )}
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary"><Check className="w-4 h-4" /> {formMode === 'documento' ? 'Crear' : 'Registrar'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <Skeleton rows={6} />
      ) : tab === 'cobros' ? (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-700/50">
                <th className="py-2 px-3">Cliente</th>
                <th className="py-2 px-3">Documento</th>
                <th className="py-2 px-3 text-right">Total</th>
                <th className="py-2 px-3 text-right">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {documentos.filter((d: any) => d.saldo > 0).length === 0 ? (
                <tr><td colSpan={4} className="py-8 text-center text-slate-500">No hay documentos pendientes de cobro</td></tr>
              ) : (
                documentos.filter((d: any) => d.saldo > 0).map((i: any) => (
                  <tr key={i.id} className="border-b border-slate-700/30 hover:bg-slate-700/20">
                    <td className="py-2 px-3 text-white">{i.cliente_nombre || i.cliente}</td>
                    <td className="py-2 px-3 text-slate-300">{i.numero || i.id}</td>
                    <td className="py-2 px-3 text-right text-white">{i.monto?.toFixed(2)}</td>
                    <td className="py-2 px-3 text-right text-yellow-400 font-semibold">{i.saldo?.toFixed(2)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState message="No hay documentos registrados" />
      ) : (
        <div className="card divide-y divide-slate-700/50">
          {filtered.map((i: any) => (
            <div key={i.id} className="flex items-center justify-between py-3 px-4">
              <div>
                <p className="text-sm font-semibold text-white">{i.cliente_nombre || i.cliente}</p>
                <p className="text-xs text-slate-400">{i.numero || i.id} - {i.tipo}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-white">C${i.monto?.toFixed(2)}</p>
                <p className={`text-xs ${i.saldo > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                  Saldo: C${i.saldo?.toFixed(2)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
