import { useState, useEffect } from 'react'
import { Search, PiggyBank, Pencil, X, Check, AlertCircle, Plus, ArrowRight, ArrowLeft, Settings } from 'lucide-react'
import { api } from '../services/api'
import Skeleton from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import type { TipoCuentaBanco } from '../types/api'

interface CuentaBanco {
  id: string
  banco: string
  numero_cuenta: string
  tipo: string
  saldo: number
  activa: boolean
  tipo_cuenta_banco_id?: string
  cuenta_contable_id?: string
}

interface Movimiento {
  id: string
  cuenta_id: string
  fecha: string
  tipo: string
  concepto: string
  entrada: number
  salida: number
  saldo: number
  numero_documento?: string | null
}

export default function BancosPage() {
  const [cuentas, setCuentas] = useState<CuentaBanco[]>([])
  const [movimientos, setMovimientos] = useState<Movimiento[]>([])
  const [tiposCuentaBanco, setTiposCuentaBanco] = useState<TipoCuentaBanco[]>([])
  const [cuentasContables, setCuentasContables] = useState<any[]>([])
  const [monedas, setMonedas] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({ banco: '', numero_cuenta: '', tipo: 'CORRIENTE', moneda_id: '', tipo_cuenta_banco_id: '', cuenta_contable_id: '' })
  const [saving, setSaving] = useState(false)

  const [showMovForm, setShowMovForm] = useState(false)
  const [movForm, setMovForm] = useState({
    cuenta_id: '', fecha: new Date().toISOString().split('T')[0],
    tipo: 'INGRESO', concepto: '', entrada: 0, salida: 0, numero_documento: '',
  })
  const [selectedCuenta, setSelectedCuenta] = useState<string | null>(null)
  const [showConfigMov, setShowConfigMov] = useState(false)
  const [subtiposMOV, setSubtiposMOV] = useState<any[]>([])
  const [configMovForm, setConfigMovForm] = useState({
    subtype_code: '', cuenta_id: '', fecha: new Date().toISOString().split('T')[0],
    monto: 0, concepto: '', tipo: 'EGRESO', numero_documento: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    loadSubtiposMOV()
    loadTiposCuenta()
    loadCuentasContables()
    loadMonedas()
  }, [])

  async function loadSubtiposMOV() {
    try {
      const list = await api.getSubtiposPorTipo('MOV_BANCO')
      setSubtiposMOV(list)
    } catch {}
  }

  async function loadTiposCuenta() {
    try {
      const list = await api.getTiposCuentaBanco(true)
      setTiposCuentaBanco(list)
    } catch {}
  }

  async function loadCuentasContables() {
    try {
      const list = await api.getCuentasContables()
      setCuentasContables(list)
    } catch {}
  }

  async function loadMonedas() {
    try {
      const list = await api.getMonedas()
      setMonedas(list)
    } catch {}
  }

  async function loadData() {
    try {
      const [c, m] = await Promise.all([
        api.getCuentasBanco(),
        api.getMovimientosBanco(),
      ])
      setCuentas(c)
      setMovimientos(m)
    } catch {}
    setLoading(false)
  }

  const movFiltrados = selectedCuenta
    ? movimientos.filter((m) => m.cuenta_id === selectedCuenta)
    : movimientos

  function openCreate() {
    setEditId(null)
    setForm({ banco: '', numero_cuenta: '', tipo: 'CORRIENTE', moneda_id: '', tipo_cuenta_banco_id: '', cuenta_contable_id: '' })
    setShowForm(true)
  }

  function openEdit(c: CuentaBanco) {
    setEditId(c.id)
    setForm({
      banco: c.banco, numero_cuenta: c.numero_cuenta, tipo: c.tipo,
      moneda_id: c.moneda_id, tipo_cuenta_banco_id: c.tipo_cuenta_banco_id || '',
      cuenta_contable_id: c.cuenta_contable_id || '',
    })
    setShowForm(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload: any = {
        banco: form.banco,
        numero_cuenta: form.numero_cuenta,
        tipo: form.tipo,
      }
      if (form.moneda_id) payload.moneda_id = form.moneda_id
      if (form.tipo_cuenta_banco_id) payload.tipo_cuenta_banco_id = form.tipo_cuenta_banco_id
      if (form.cuenta_contable_id) payload.cuenta_contable_id = form.cuenta_contable_id

      const updated = editId
        ? await api.actualizarCuentaBanco(editId, payload)
        : await api.crearCuentaBanco(payload)
      setCuentas((prev) => editId ? prev.map((c) => (c.id === editId ? updated : c)) : [...prev, updated])
      setShowForm(false)
    } catch {}
    setSaving(false)
  }

  async function handleMovSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const m = await api.crearMovimientoBanco({
        ...movForm,
        entrada: movForm.tipo === 'INGRESO' ? Number(movForm.entrada) : 0,
        salida: movForm.tipo === 'EGRESO' ? Number(movForm.salida) : 0,
      })
      setMovimientos((prev) => [m, ...prev])
      loadData()
      setShowMovForm(false)
    } catch {}
    setSaving(false)
  }

  async function handleConfigMovSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const result = await api.crearMovimientoBancoConfigurable({
        ...configMovForm,
        numero_documento: configMovForm.numero_documento || undefined,
      })
      loadData()
      setShowConfigMov(false)
    } catch {}
    setSaving(false)
  }

  const cuentaActual = cuentas.find((c) => c.id === selectedCuenta)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Bancos</h1>
          <p className="text-sm text-slate-400">Cuentas bancarias y movimientos</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { setShowMovForm(true); setMovForm({ ...movForm, cuenta_id: selectedCuenta || '' }) }}
            className="btn-secondary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" /> Movimiento
          </button>
          <button onClick={() => { setShowConfigMov(true); setConfigMovForm({ ...configMovForm, cuenta_id: selectedCuenta || '' }) }}
            className="btn-secondary flex items-center gap-2 text-sm">
            <Settings className="w-4 h-4" /> Mov. Configurable
          </button>
          <button onClick={openCreate} className="btn-primary flex items-center gap-2">
            <PiggyBank className="w-4 h-4" /> Nueva Cuenta
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">{editId ? 'Editar Cuenta' : 'Nueva Cuenta Bancaria'}</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Banco *</label>
              <input value={form.banco} onChange={(e) => setForm({ ...form, banco: e.target.value })} className="input-filter w-full" required placeholder="BAC Credomatic" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Numero Cuenta *</label>
              <input value={form.numero_cuenta} onChange={(e) => setForm({ ...form, numero_cuenta: e.target.value })} className="input-filter w-full" required placeholder="000-000-000" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-filter w-full">
                <option value="CORRIENTE">Corriente</option>
                <option value="AHORRO">Ahorro</option>
                <option value="CREDITO">Credito</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Moneda *</label>
              <select value={form.moneda_id} onChange={(e) => setForm({ ...form, moneda_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar moneda</option>
                {monedas.map((m: any) => <option key={m.id} value={m.id}>{m.codigo} - {m.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo de Cuenta (configurable)</label>
              <select value={form.tipo_cuenta_banco_id} onChange={(e) => setForm({ ...form, tipo_cuenta_banco_id: e.target.value })} className="input-filter w-full">
                <option value="">-- Seleccionar --</option>
                {tiposCuentaBanco.map((t) => <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta Contable</label>
              <select value={form.cuenta_contable_id} onChange={(e) => setForm({ ...form, cuenta_contable_id: e.target.value })} className="input-filter w-full">
                <option value="">-- Seleccionar --</option>
                {cuentasContables.map((cc: any) => <option key={cc.id} value={cc.id}>{cc.codigo} - {cc.nombre}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> {editId ? 'Actualizar' : 'Crear'} Cuenta</>}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {showMovForm && (
        <form onSubmit={handleMovSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Nuevo Movimiento Bancario</h3>
            <button type="button" onClick={() => setShowMovForm(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta</label>
              <select value={movForm.cuenta_id} onChange={(e) => setMovForm({ ...movForm, cuenta_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar cuenta</option>
                {cuentas.map((c) => <option key={c.id} value={c.id}>{c.banco} - {c.numero_cuenta}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha</label>
              <input type="date" value={movForm.fecha} onChange={(e) => setMovForm({ ...movForm, fecha: e.target.value })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo</label>
              <select value={movForm.tipo} onChange={(e) => setMovForm({ ...movForm, tipo: e.target.value, entrada: 0, salida: 0 })} className="input-filter w-full">
                <option value="INGRESO">Ingreso</option>
                <option value="EGRESO">Egreso</option>
                <option value="TRANSFERENCIA">Transferencia</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Monto (C$)</label>
              <input type="number" step="0.01" value={movForm.tipo === 'INGRESO' ? movForm.entrada : movForm.salida}
                onChange={(e) => movForm.tipo === 'INGRESO'
                  ? setMovForm({ ...movForm, entrada: Number(e.target.value) })
                  : setMovForm({ ...movForm, salida: Number(e.target.value) })
                } className="input-filter w-full" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Concepto *</label>
              <input value={movForm.concepto} onChange={(e) => setMovForm({ ...movForm, concepto: e.target.value })} className="input-filter w-full" required placeholder="Descripcion del movimiento" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">No. Documento</label>
              <input value={movForm.numero_documento} onChange={(e) => setMovForm({ ...movForm, numero_documento: e.target.value })} className="input-filter w-full" placeholder="Cheque / Transf." />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> Registrar Movimiento</>}
            </button>
            <button type="button" onClick={() => setShowMovForm(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      {showConfigMov && (
        <form onSubmit={handleConfigMovSubmit} className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Movimiento Bancario Configurable (MOV_BANCO)</h3>
            <button type="button" onClick={() => setShowConfigMov(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Subtipo</label>
              <select value={configMovForm.subtype_code} onChange={(e) => setConfigMovForm({ ...configMovForm, subtype_code: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar subtipo...</option>
                {subtiposMOV.map((s: any) => <option key={s.codigo} value={s.codigo}>{s.nombre}</option>)}
              </select>
              {subtiposMOV.length === 0 && (
                <p className="text-xs text-yellow-400 mt-1">No hay subtipos. Cree uno en Configuracion Documentos.</p>
              )}
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Cuenta</label>
              <select value={configMovForm.cuenta_id} onChange={(e) => setConfigMovForm({ ...configMovForm, cuenta_id: e.target.value })} className="input-filter w-full" required>
                <option value="">Seleccionar cuenta...</option>
                {cuentas.map((c) => <option key={c.id} value={c.id}>{c.banco} - {c.numero_cuenta}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha</label>
              <input type="date" value={configMovForm.fecha} onChange={(e) => setConfigMovForm({ ...configMovForm, fecha: e.target.value })} className="input-filter w-full" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo</label>
              <select value={configMovForm.tipo} onChange={(e) => setConfigMovForm({ ...configMovForm, tipo: e.target.value })} className="input-filter w-full">
                <option value="INGRESO">Ingreso</option>
                <option value="EGRESO">Egreso</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Monto</label>
              <input type="number" step="0.01" value={configMovForm.monto}
                onChange={(e) => setConfigMovForm({ ...configMovForm, monto: Number(e.target.value) })} className="input-filter w-full" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-400 mb-1">Concepto *</label>
              <input value={configMovForm.concepto} onChange={(e) => setConfigMovForm({ ...configMovForm, concepto: e.target.value })} className="input-filter w-full" required placeholder="Descripcion del movimiento" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">No. Documento</label>
              <input value={configMovForm.numero_documento} onChange={(e) => setConfigMovForm({ ...configMovForm, numero_documento: e.target.value })} className="input-filter w-full" placeholder="Cheque / Ref." />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? 'Guardando...' : <><Check className="w-4 h-4" /> Registrar</>}
            </button>
            <button type="button" onClick={() => setShowConfigMov(false)} className="btn-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cuentas.map((c) => (
          <div key={c.id}
            onClick={() => setSelectedCuenta(c.id === selectedCuenta ? null : c.id)}
            className={`card cursor-pointer transition-all hover:border-slate-600 ${selectedCuenta === c.id ? 'ring-1 ring-primary-500 border-primary-500/50' : ''}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-white">{c.banco}</span>
              <button onClick={(e) => { e.stopPropagation(); openEdit(c) }} className="p-1 text-slate-500 hover:text-white">
                <Pencil className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="text-xs text-slate-500 font-mono">{c.numero_cuenta}</div>
            <div className="text-lg font-bold text-emerald-400 mt-2 font-mono">
              C$ {c.saldo.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-500 mt-1">{c.tipo}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="input-filter w-full pl-10" placeholder="Buscar movimiento..." />
        </div>
        {cuentaActual && <span className="text-xs text-primary-400">Filtrando: {cuentaActual.banco}</span>}
        <span className="text-xs text-slate-500">{movFiltrados.length} movimientos</span>
      </div>

      {loading ? (
<Skeleton rows={5} />
      ) : movFiltrados.length === 0 ? (
        <EmptyState message="No hay movimientos registrados" />
      ) : (
        <div className="card overflow-hidden !p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Concepto</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">Tipo</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Entrada</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Salida</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-400">Saldo</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-slate-400">No. Doc</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {movFiltrados.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 text-slate-400 text-xs">{m.fecha}</td>
                    <td className="px-4 py-3"><span className="text-slate-300">{m.concepto}</span></td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded ${
                        m.tipo === 'INGRESO' ? 'bg-emerald-600/20 text-emerald-400' :
                        m.tipo === 'EGRESO' ? 'bg-red-600/20 text-red-400' : 'bg-slate-600/20 text-slate-400'
                      }`}>
                        {m.tipo === 'INGRESO' ? <ArrowRight className="w-3 h-3" /> :
                         m.tipo === 'EGRESO' ? <ArrowLeft className="w-3 h-3" /> : null}
                        {m.tipo}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-emerald-400">
                      {m.entrada > 0 ? `C$ ${m.entrada.toLocaleString('es-NI', { minimumFractionDigits: 2 })}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-red-400">
                      {m.salida > 0 ? `C$ ${m.salida.toLocaleString('es-NI', { minimumFractionDigits: 2 })}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-white">
                      C$ {m.saldo.toLocaleString('es-NI', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-center text-slate-500 text-xs">{m.numero_documento || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
