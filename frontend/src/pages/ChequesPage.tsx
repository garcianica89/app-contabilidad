import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import {
  CreditCard, Plus, FileText, Printer, Eye, X, Download, Settings,
} from 'lucide-react'

interface CuentaBanco { id: string; nombre: string; numero_cuenta: string; moneda_id: string }
interface Chequera { id: string; nombre: string; cuenta_bancaria_id: string; numero_inicio: number; numero_fin: number; numero_actual: number; activa: boolean }
interface Cheque { id: string; numero: string; numero_contable?: string | null; pagadero_a: string; monto: number; fecha: string; concepto: string | null; estado: string; impreso: boolean; cuenta_bancaria_id: string; chequera_id: string | null; proveedor_id: string | null }
interface ChequeFormato { id: string; nombre: string; activo: boolean }

export default function ChequesPage() {
  const [cuentas, setCuentas] = useState<CuentaBanco[]>([])
  const [chequeras, setChequeras] = useState<Chequera[]>([])
  const [cheques, setCheques] = useState<Cheque[]>([])
  const [formatos, setFormatos] = useState<ChequeFormato[]>([])
  const [cuentaFiltro, setCuentaFiltro] = useState('')
  const [estadoFiltro, setEstadoFiltro] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [showChequeraForm, setShowChequeraForm] = useState(false)
  const [showConfigForm, setShowConfigForm] = useState(false)
  const [showPdfPreview, setShowPdfPreview] = useState<string | null>(null)
  const [tab, setTab] = useState<'cheques' | 'chequeras'>('cheques')

  const [formCuenta, setFormCuenta] = useState('')
  const [formChequera, setFormChequera] = useState('')
  const [formPagadero, setFormPagadero] = useState('')
  const [formMonto, setFormMonto] = useState('')
  const [formFecha, setFormFecha] = useState(new Date().toISOString().split('T')[0])
  const [formConcepto, setFormConcepto] = useState('')

  const [chNombre, setChNombre] = useState('')
  const [chCuenta, setChCuenta] = useState('')
  const [chDesde, setChDesde] = useState('')
  const [chHasta, setChHasta] = useState('')

  const [configCuentaId, setConfigCuentaId] = useState('')
  const [config, setConfig] = useState({
    cheque_formato_id: '',
    cheque_ultimo_numero_operativo: 0,
    cheque_ultimo_numero_contable: 0,
    cheque_prefijo: '',
    cheque_formato_numero: '{NUM}',
  })

  const load = useCallback(async () => {
    try {
      const [c, ch, qs, fmts] = await Promise.all([
        api.erpGetCuentasBancarias(),
        api.erpGetCheques(),
        api.erpGetChequeras(),
        api.erpGetFormatos(),
      ])
      setCuentas(c)
      setCheques(qs)
      setChequeras(ch)
      setFormatos(fmts)
    } catch {}
  }, [])

  useEffect(() => { load() }, [load])

  const chequesFiltrados = cheques.filter(c => {
    if (cuentaFiltro && c.cuenta_bancaria_id !== cuentaFiltro) return false
    if (estadoFiltro && c.estado !== estadoFiltro) return false
    return true
  })

  const handleCrearCheque = async () => {
    await api.erpCrearCheque({
      cuenta_bancaria_id: formCuenta,
      chequera_id: formChequera || undefined,
      pagadero_a: formPagadero,
      monto: parseFloat(formMonto),
      fecha: formFecha,
      concepto: formConcepto || undefined,
    })
    setShowForm(false)
    setFormCuenta(''); setFormChequera(''); setFormPagadero(''); setFormMonto(''); setFormConcepto('')
    await load()
  }

  const handleCrearChequera = async () => {
    await api.erpCrearChequera({
      cuenta_bancaria_id: chCuenta,
      nombre: chNombre,
      numero_inicio: parseInt(chDesde),
      numero_fin: parseInt(chHasta),
    })
    setShowChequeraForm(false)
    setChNombre(''); setChCuenta(''); setChDesde(''); setChHasta('')
    await load()
  }

  const handleAnular = async (id: string) => {
    if (!confirm('¿Anular este cheque?')) return
    await api.erpAnularCheque(id)
    await load()
  }

  const handleImprimirPdf = async (id: string) => {
    const blob = await api.erpImprimirCheque(id, 'pdf')
    const url = URL.createObjectURL(blob)
    setShowPdfPreview(url)
  }

  const handleDownloadPdf = async (id: string, numero: string) => {
    const blob = await api.erpVistaPreviaCheque(id, 'pdf')
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cheque_${numero}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const openConfig = async (cuentaId: string) => {
    try {
      const cfg = await api.erpGetChequeConfig(cuentaId)
      setConfig({
        cheque_formato_id: cfg.cheque_formato_id || '',
        cheque_ultimo_numero_operativo: cfg.cheque_ultimo_numero_operativo,
        cheque_ultimo_numero_contable: cfg.cheque_ultimo_numero_contable,
        cheque_prefijo: cfg.cheque_prefijo || '',
        cheque_formato_numero: cfg.cheque_formato_numero || '{NUM}',
      })
      setConfigCuentaId(cuentaId)
      setShowConfigForm(true)
    } catch {}
  }

  const handleSaveConfig = async () => {
    await api.erpUpdateChequeConfig(configCuentaId, {
      cheque_formato_id: config.cheque_formato_id || null,
      cheque_ultimo_numero_operativo: config.cheque_ultimo_numero_operativo,
      cheque_ultimo_numero_contable: config.cheque_ultimo_numero_contable,
      cheque_prefijo: config.cheque_prefijo,
      cheque_formato_numero: config.cheque_formato_numero,
    })
    setShowConfigForm(false)
  }

  const estadoBadge = (estado: string) => {
    const map: Record<string, string> = {
      ANULADO: 'bg-red-100 text-red-700',
      COBRADO: 'bg-green-100 text-green-700',
      EMITIDO: 'bg-yellow-100 text-yellow-700',
    }
    return `px-2 py-0.5 rounded-full text-xs font-medium ${map[estado] || 'bg-gray-100 text-gray-500'}`
  }

  function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
    return (
      <div className="fixed inset-0 bg-black/40 z-50 flex items-end md:items-center justify-center" onClick={onClose}>
        <div
          className="bg-white w-full md:max-w-md md:rounded-lg max-h-[90vh] overflow-y-auto rounded-t-2xl shadow-xl"
          onClick={e => e.stopPropagation()}
        >
          <div className="sticky top-0 bg-white border-b flex items-center justify-between p-4 md:rounded-t-lg z-10">
            <h2 className="text-lg font-bold">{title}</h2>
            <button onClick={onClose} className="p-2 -mr-2 min-w-[44px] min-h-[44px] flex items-center justify-center">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="p-4 space-y-3">
            {children}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-3 md:p-4 max-w-6xl mx-auto pb-24">
      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
          <CreditCard className="w-5 h-5 md:w-6 md:h-6" /> Cheques
        </h1>
        <div className="flex gap-2">
          <button onClick={() => setShowChequeraForm(true)}
            className="btn btn-secondary flex items-center gap-1 text-sm min-h-[44px] px-3">
            <Plus className="w-4 h-4" /><span className="hidden md:inline">Chequera</span>
          </button>
          <button onClick={() => setShowForm(true)}
            className="btn btn-primary flex items-center gap-1 text-sm min-h-[44px] px-3">
            <Plus className="w-4 h-4" /><span className="hidden md:inline">Cheque</span>
          </button>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-4 mb-4 border-b pb-2">
        <button onClick={() => setTab('cheques')}
          className={`font-medium pb-1 text-sm md:text-base min-h-[44px] ${tab === 'cheques' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>
          <CreditCard className="w-4 h-4 inline mr-1" />Cheques
        </button>
        <button onClick={() => setTab('chequeras')}
          className={`font-medium pb-1 text-sm md:text-base min-h-[44px] ${tab === 'chequeras' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>
          <FileText className="w-4 h-4 inline mr-1" />Talonarios
        </button>
      </div>

      {/* ════════════════════════════════════════ */}
      {/* TAB: CHEQUES                              */}
      {/* ════════════════════════════════════════ */}
      {tab === 'cheques' && (
        <>
          <div className="flex flex-col md:flex-row gap-2 md:gap-4 mb-4">
            <select className="input text-sm" value={cuentaFiltro} onChange={e => setCuentaFiltro(e.target.value)}>
              <option value="">Todas las cuentas</option>
              {cuentas.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            <select className="input text-sm" value={estadoFiltro} onChange={e => setEstadoFiltro(e.target.value)}>
              <option value="">Todos los estados</option>
              <option value="EMITIDO">Emitido</option>
              <option value="COBRADO">Cobrado</option>
              <option value="ANULADO">Anulado</option>
            </select>
          </div>

          {/* ── Desktop table ── */}
          <div className="hidden md:block overflow-x-auto">
            <table className="table w-full text-sm">
              <thead>
                <tr>
                  <th>No. Operativo</th>
                  <th>No. Contable</th>
                  <th>Cuenta</th>
                  <th>Pagadero a</th>
                  <th>Monto</th>
                  <th>Fecha</th>
                  <th>Estado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {chequesFiltrados.map(c => {
                  const cuenta = cuentas.find(cu => cu.id === c.cuenta_bancaria_id)
                  return (
                    <tr key={c.id}>
                      <td className="font-mono text-xs">{c.numero}</td>
                      <td className="font-mono text-xs text-gray-500">{c.numero_contable || '—'}</td>
                      <td>{cuenta?.nombre || '—'}</td>
                      <td>{c.pagadero_a}</td>
                      <td className="text-right font-mono">C$ {c.monto.toLocaleString()}</td>
                      <td>{c.fecha}</td>
                      <td><span className={estadoBadge(c.estado)}>{c.estado}</span></td>
                      <td>
                        <div className="flex gap-1">
                          <button onClick={() => handleImprimirPdf(c.id)} className="btn btn-xs btn-ghost p-2" title="Ver PDF"><FileText className="w-4 h-4" /></button>
                          <button onClick={() => handleDownloadPdf(c.id, c.numero)} className="btn btn-xs btn-ghost p-2" title="Descargar PDF"><Download className="w-4 h-4" /></button>
                          {c.estado === 'EMITIDO' && (
                            <button onClick={() => handleAnular(c.id)} className="btn btn-xs btn-ghost p-2 text-red-600" title="Anular"><X className="w-4 h-4" /></button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
                {chequesFiltrados.length === 0 && (
                  <tr><td colSpan={8} className="text-center text-gray-400 py-8">No hay cheques</td></tr>
                )}
              </tbody>
            </table>
          </div>

          {/* ── Mobile cards ── */}
          <div className="md:hidden space-y-3">
            {chequesFiltrados.map(c => {
              const cuenta = cuentas.find(cu => cu.id === c.cuenta_bancaria_id)
              return (
                <div key={c.id} className="bg-white rounded-xl shadow-sm border p-4 active:bg-gray-50">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-mono text-xs text-gray-400">#{c.numero}</div>
                      <div className="font-medium">{c.pagadero_a}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono font-bold">C$ {c.monto.toLocaleString()}</div>
                      <div className="text-xs text-gray-400">{c.fecha}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                    {cuenta && <span>{cuenta.nombre}</span>}
                    {c.numero_contable && <span className="text-gray-300">|</span>}
                    {c.numero_contable && <span className="font-mono">C: {c.numero_contable}</span>}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={estadoBadge(c.estado)}>{c.estado}</span>
                    <div className="flex gap-2">
                      <button onClick={() => handleImprimirPdf(c.id)}
                        className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg bg-gray-100 active:bg-gray-200">
                        <Eye className="w-5 h-5" />
                      </button>
                      <button onClick={() => handleDownloadPdf(c.id, c.numero)}
                        className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg bg-gray-100 active:bg-gray-200">
                        <Download className="w-5 h-5" />
                      </button>
                      {c.estado === 'EMITIDO' && (
                        <button onClick={() => handleAnular(c.id)}
                          className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg bg-red-50 active:bg-red-100 text-red-600">
                          <X className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
            {chequesFiltrados.length === 0 && (
              <div className="text-center text-gray-400 py-8">No hay cheques</div>
            )}
          </div>
        </>
      )}

      {/* ════════════════════════════════════════ */}
      {/* TAB: CHEQUERAS                            */}
      {/* ════════════════════════════════════════ */}
      {tab === 'chequeras' && (
        <>
          {/* ── Desktop table ── */}
          <div className="hidden md:block overflow-x-auto">
            <table className="table w-full text-sm">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Cuenta</th>
                  <th>Rango</th>
                  <th>Actual</th>
                  <th>Disponibles</th>
                  <th>Estado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {chequeras.map(cq => {
                  const cuenta = cuentas.find(cu => cu.id === cq.cuenta_bancaria_id)
                  const disponibles = cq.numero_fin - cq.numero_actual + 1
                  return (
                    <tr key={cq.id}>
                      <td className="font-medium">{cq.nombre}</td>
                      <td>{cuenta?.nombre || '—'}</td>
                      <td className="font-mono">{String(cq.numero_inicio).padStart(8, '0')} – {String(cq.numero_fin).padStart(8, '0')}</td>
                      <td className="font-mono">{String(cq.numero_actual).padStart(8, '0')}</td>
                      <td>
                        <span className={`font-mono font-bold ${disponibles < 10 ? 'text-red-600' : disponibles < 50 ? 'text-yellow-600' : 'text-green-600'}`}>{disponibles}</span>
                      </td>
                      <td><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cq.activa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>{cq.activa ? 'Activa' : 'Inactiva'}</span></td>
                      <td>
                        <button onClick={() => openConfig(cq.cuenta_bancaria_id)} className="btn btn-xs btn-ghost p-2" title="Configurar numeración">
                          <Settings className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
                {chequeras.length === 0 && (
                  <tr><td colSpan={7} className="text-center text-gray-400 py-8">No hay talonarios</td></tr>
                )}
              </tbody>
            </table>
          </div>

          {/* ── Mobile cards ── */}
          <div className="md:hidden space-y-3">
            {chequeras.map(cq => {
              const cuenta = cuentas.find(cu => cu.id === cq.cuenta_bancaria_id)
              const disponibles = cq.numero_fin - cq.numero_actual + 1
              return (
                <div key={cq.id} className="bg-white rounded-xl shadow-sm border p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium">{cq.nombre}</div>
                      <div className="text-xs text-gray-500">{cuenta?.nombre || '—'}</div>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cq.activa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {cq.activa ? 'Activa' : 'Inactiva'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm mb-2">
                    <span className="text-gray-500">Rango:</span>
                    <span className="font-mono">{String(cq.numero_inicio).padStart(8, '0')} – {String(cq.numero_fin).padStart(8, '0')}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm mb-3">
                    <span className="text-gray-500">Actual:</span>
                    <span className="font-mono">{String(cq.numero_actual).padStart(8, '0')}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className={`font-mono font-bold text-sm ${disponibles < 10 ? 'text-red-600' : disponibles < 50 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {disponibles} disponibles
                    </span>
                    <button onClick={() => openConfig(cq.cuenta_bancaria_id)}
                      className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg bg-gray-100 active:bg-gray-200">
                      <Settings className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              )
            })}
            {chequeras.length === 0 && (
              <div className="text-center text-gray-400 py-8">No hay talonarios</div>
            )}
          </div>
        </>
      )}

      {/* ── Modal Nuevo Cheque ── */}
      {showForm && (
        <Modal title="Nuevo Cheque" onClose={() => setShowForm(false)}>
          <select className="input text-sm" value={formCuenta} onChange={e => setFormCuenta(e.target.value)} required>
            <option value="">Seleccionar cuenta bancaria</option>
            {cuentas.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <select className="input text-sm" value={formChequera} onChange={e => setFormChequera(e.target.value)}>
            <option value="">Auto (desde config de cuenta)</option>
            {chequeras.filter(cq => cq.activa && cq.numero_actual <= cq.numero_fin).map(cq => (
              <option key={cq.id} value={cq.id}>{cq.nombre} ({String(cq.numero_actual).padStart(8, '0')})</option>
            ))}
          </select>
          <input className="input text-sm" placeholder="Pagadero a" value={formPagadero} onChange={e => setFormPagadero(e.target.value)} required />
          <div className="flex gap-2">
            <input className="input text-sm flex-1" type="number" step="0.01" placeholder="Monto C$" value={formMonto} onChange={e => setFormMonto(e.target.value)} required />
            <input className="input text-sm w-1/2" type="date" value={formFecha} onChange={e => setFormFecha(e.target.value)} required />
          </div>
          <input className="input text-sm" placeholder="Concepto (opcional)" value={formConcepto} onChange={e => setFormConcepto(e.target.value)} />
          <button onClick={handleCrearCheque} className="btn btn-primary w-full min-h-[44px] text-sm">Emitir Cheque</button>
        </Modal>
      )}

      {/* ── Modal Nueva Chequera ── */}
      {showChequeraForm && (
        <Modal title="Nuevo Talonario" onClose={() => setShowChequeraForm(false)}>
          <input className="input text-sm" placeholder="Nombre (ej: BBVA 2026)" value={chNombre} onChange={e => setChNombre(e.target.value)} required />
          <select className="input text-sm" value={chCuenta} onChange={e => setChCuenta(e.target.value)} required>
            <option value="">Seleccionar cuenta bancaria</option>
            {cuentas.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <div className="flex gap-2">
            <input className="input text-sm flex-1" type="number" placeholder="No. inicial" value={chDesde} onChange={e => setChDesde(e.target.value)} required />
            <input className="input text-sm flex-1" type="number" placeholder="No. final" value={chHasta} onChange={e => setChHasta(e.target.value)} required />
          </div>
          <button onClick={handleCrearChequera} className="btn btn-primary w-full min-h-[44px] text-sm">Crear Talonario</button>
        </Modal>
      )}

      {/* ── Modal Config Cheque por Cuenta ── */}
      {showConfigForm && (
        <Modal title="Config. Cheques" onClose={() => setShowConfigForm(false)}>
          <div>
            <label className="label text-xs">Formato de impresión</label>
            <select className="input text-sm" value={config.cheque_formato_id} onChange={e => setConfig({ ...config, cheque_formato_id: e.target.value })}>
              <option value="">Default (activo de empresa)</option>
              {formatos.map(f => <option key={f.id} value={f.id}>{f.nombre} {f.activo ? '(activo)' : ''}</option>)}
            </select>
          </div>
          <div>
            <label className="label text-xs">Prefijo (ej: A-)</label>
            <input className="input text-sm" value={config.cheque_prefijo} onChange={e => setConfig({ ...config, cheque_prefijo: e.target.value })} maxLength={10} />
          </div>
          <div>
            <label className="label text-xs">Formato número</label>
            <input className="input text-sm" value={config.cheque_formato_numero} onChange={e => setConfig({ ...config, cheque_formato_numero: e.target.value })} maxLength={30} />
            <p className="text-xs text-gray-400 mt-1">Ej: {config.cheque_prefijo || '{PREF}'}{'{NUM}'} → {config.cheque_prefijo}00000001</p>
          </div>
          <div>
            <label className="label text-xs">Último número operativo</label>
            <input className="input text-sm" type="number" value={config.cheque_ultimo_numero_operativo} onChange={e => setConfig({ ...config, cheque_ultimo_numero_operativo: parseInt(e.target.value) || 0 })} />
          </div>
          <div>
            <label className="label text-xs">Último número contable</label>
            <input className="input text-sm" type="number" value={config.cheque_ultimo_numero_contable} onChange={e => setConfig({ ...config, cheque_ultimo_numero_contable: parseInt(e.target.value) || 0 })} />
          </div>
          <button onClick={handleSaveConfig} className="btn btn-primary w-full min-h-[44px] text-sm">Guardar Configuración</button>
        </Modal>
      )}

      {/* ── Modal Vista Previa PDF ── */}
      {showPdfPreview && (
        <div className="fixed inset-0 bg-black z-50 flex flex-col" onClick={() => { setShowPdfPreview(null); URL.revokeObjectURL(showPdfPreview) }}>
          <div className="bg-white flex items-center justify-between px-4 py-3 border-b shadow-sm" onClick={e => e.stopPropagation()}>
            <h2 className="font-bold text-sm">Vista Previa PDF</h2>
            <div className="flex gap-2">
              <button onClick={() => { const w = window.open(showPdfPreview!); w?.print() }}
                className="btn btn-primary btn-sm min-h-[44px] flex items-center gap-1">
                <Printer className="w-4 h-4" /> Imprimir
              </button>
              <button onClick={() => { setShowPdfPreview(null); URL.revokeObjectURL(showPdfPreview) }}
                className="min-w-[44px] min-h-[44px] flex items-center justify-center">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          <iframe src={showPdfPreview} className="flex-1 w-full bg-gray-200" title="PDF" />
        </div>
      )}
    </div>
  )
}
