import { useState, useEffect, useRef } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, Search, ChevronDown, ChevronUp, Loader2, Download } from 'lucide-react'
import { api } from '../services/api'

interface MovimientoPreview {
  idx: number
  fecha: string
  concepto: string
  monto: number
  referencia: string | null
  saldo: number | null
  tipo: string | null
  subtipo_codigo: string | null
  abs_monto: number
  es_ingreso: boolean
  hash: string
  duplicado?: boolean
}

interface Clasificacion {
  movimiento_idx: number
  modulo: string
  confianza: number
  entidad_id: string | null
  entidad_tipo: string | null
  entidad_descripcion: string | null
  regla: string | null
}

interface PreviewData {
  cuenta: { id: string; nombre: string }
  formato: string
  total_movimientos: number
  duplicados: number
  total_ingresos: number
  total_egresos: number
  movimientos: MovimientoPreview[]
}

export default function CargadorMovimientosPage() {
  const [cuentas, setCuentas] = useState<any[]>([])
  const [cuentaId, setCuentaId] = useState('')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [preview, setPreview] = useState<PreviewData | null>(null)
  const [clasificaciones, setClasificaciones] = useState<Clasificacion[]>([])
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [resultado, setResultado] = useState<any>(null)
  const [error, setError] = useState('')
  const [crearConciliacion, setCrearConciliacion] = useState(true)
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.getCuentasBanco().then(setCuentas).catch(() => {})
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setArchivo(file)
      setPreview(null)
      setClasificaciones([])
      setResultado(null)
      setError('')
    }
  }

  const handlePreview = async () => {
    if (!cuentaId || !archivo) return
    setLoading(true)
    setError('')
    setResultado(null)
    try {
      const data = await api.previewCargador(cuentaId, archivo)
      setPreview(data)
      const clasif = await api.clasificarMovimientos({ movimientos: data.movimientos })
      setClasificaciones(clasif)
    } catch (err: any) {
      setError(err.message || 'Error al procesar archivo')
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async () => {
    if (!preview || !cuentaId) return
    setImporting(true)
    setError('')
    try {
      const result = await api.importarMovimientos({
        cuenta_banco_id: cuentaId,
        movimientos: preview.movimientos,
        clasificaciones: clasificaciones.map(c => ({
          movimiento_idx: c.movimiento_idx,
          modulo: c.modulo,
          entidad_id: c.entidad_id,
          entidad_tipo: c.entidad_tipo,
        })),
        auto_match: true,
        crear_conciliacion: crearConciliacion,
      })
      setResultado(result)
      setArchivo(null)
      setPreview(null)
      if (fileRef.current) fileRef.current.value = ''
    } catch (err: any) {
      setError(err.message || 'Error al importar')
    } finally {
      setImporting(false)
    }
  }

  const getClasificacion = (idx: number) => clasificaciones.find(c => c.movimiento_idx === idx)

  const confianzaColor = (conf: number) => {
    if (conf >= 0.8) return 'text-green-400'
    if (conf >= 0.5) return 'text-yellow-400'
    return 'text-slate-400'
  }

  const toggleRow = (idx: number) => {
    setExpandedRows(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Cargador de Movimientos Bancarios</h1>
          <p className="text-slate-400 text-sm mt-1">Sube archivos CSV u OFX para importar movimientos bancarios</p>
        </div>
      </div>

      {/* Step 1: Seleccionar Cuenta y Archivo */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-primary-400" />
          1. Seleccionar Cuenta y Archivo
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Cuenta Bancaria</label>
            <select
              value={cuentaId}
              onChange={e => setCuentaId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
            >
              <option value="">Seleccionar cuenta...</option>
              {cuentas.map(c => (
                <option key={c.id} value={c.id}>{c.banco} - {c.numero_cuenta}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Archivo (CSV / OFX)</label>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,.ofx,.qfx,.txt,.xlsx,.xls"
              onChange={handleFileChange}
              className="w-full text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-600 file:text-white hover:file:bg-primary-500"
            />
          </div>
        </div>
        {archivo && (
          <div className="mt-4 flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={crearConciliacion}
                onChange={e => setCrearConciliacion(e.target.checked)}
                className="rounded border-slate-600"
              />
              Crear conciliacion automatica
            </label>
            <button
              onClick={handlePreview}
              disabled={loading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              {loading ? 'Procesando...' : 'Previsualizar'}
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Step 2: Preview y Clasificacion */}
      {preview && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-400" />
            2. Vista Previa y Clasificacion
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Total Movimientos</p>
              <p className="text-xl font-bold text-white">{preview.total_movimientos}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Duplicados</p>
              <p className={`text-xl font-bold ${preview.duplicados > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                {preview.duplicados}
              </p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Total Ingresos</p>
              <p className="text-xl font-bold text-green-400">C${preview.total_ingresos.toFixed(2)}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Total Egresos</p>
              <p className="text-xl font-bold text-red-400">C${preview.total_egresos.toFixed(2)}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Formato</p>
              <p className="text-xl font-bold text-white uppercase">{preview.formato}</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-slate-400">
                  <th className="text-left py-2 px-2">#</th>
                  <th className="text-left py-2 px-2">Fecha</th>
                  <th className="text-left py-2 px-2">Concepto</th>
                  <th className="text-center py-2 px-2">Subtipo</th>
                  <th className="text-right py-2 px-2">Monto</th>
                  <th className="text-center py-2 px-2">Clasificacion</th>
                  <th className="text-center py-2 px-2">Confianza</th>
                </tr>
              </thead>
              <tbody>
                {preview.movimientos.map((mov) => {
                  const clasif = getClasificacion(mov.idx)
                  const expanded = expandedRows.has(mov.idx)
                  return (
                    <tr key={mov.idx} className="border-b border-slate-800 hover:bg-slate-800/30">
                      <td className="py-2 px-2 text-slate-400">{mov.idx + 1}</td>
                      <td className="py-2 px-2 text-white">{mov.fecha}</td>
                      <td className="py-2 px-2 text-white max-w-xs truncate">
                        <button
                          onClick={() => toggleRow(mov.idx)}
                          className="flex items-center gap-1 hover:text-primary-400"
                        >
                          {mov.concepto}
                          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </button>
                        {expanded && (
                          <div className="mt-1 text-xs text-slate-400 space-y-1">
                            {mov.referencia && <p>Ref: {mov.referencia}</p>}
                            {mov.saldo !== null && <p>Saldo: C${mov.saldo.toFixed(2)}</p>}
                            {mov.tipo && <p>Tipo: {mov.tipo}</p>}
                            {mov.duplicado && <p className="text-yellow-400">⚠ Posible duplicado</p>}
                          </div>
                        )}
                      </td>
                      <td className="py-2 px-2 text-center">
                        {mov.subtipo_codigo ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-purple-900/50 text-purple-300">
                            {mov.subtipo_codigo}
                          </span>
                        ) : (
                          <span className="text-slate-600 text-xs">-</span>
                        )}
                      </td>
                      <td className={`py-2 px-2 text-right font-mono ${mov.monto >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        C${Math.abs(mov.monto).toFixed(2)}
                      </td>
                      <td className="py-2 px-2 text-center">
                        {clasif ? (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                            clasif.modulo === 'CXP' ? 'bg-orange-900/50 text-orange-300' :
                            clasif.modulo === 'CXC' ? 'bg-green-900/50 text-green-300' :
                            'bg-blue-900/50 text-blue-300'
                          }`}>
                            {clasif.modulo}
                          </span>
                        ) : (
                          <span className="text-slate-500 text-xs">Sin clasificar</span>
                        )}
                      </td>
                      <td className="py-2 px-2 text-center">
                        {clasif ? (
                          <span className={`text-xs font-mono ${confianzaColor(clasif.confianza)}`}>
                            {(clasif.confianza * 100).toFixed(0)}%
                          </span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <div className="text-sm text-slate-400">
              {preview.duplicados > 0 && (
                <span className="text-yellow-400">⚠ {preview.duplicados} movimiento(s) duplicado(s) seran omitidos</span>
              )}
            </div>
            <button
              onClick={handleImport}
              disabled={importing}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 disabled:opacity-50 flex items-center gap-2"
            >
              {importing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              {importing ? 'Importando...' : `Importar ${preview.total_movimientos - preview.duplicados} Movimientos`}
            </button>
          </div>
        </div>
      )}

      {/* Resultado Importacion */}
      {resultado && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            3. Resultado de Importacion
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-green-900/20 border border-green-800/30 rounded-lg p-4">
              <p className="text-sm text-green-400">Movimientos Creados</p>
              <p className="text-2xl font-bold text-white">{resultado.movimientos_creados}</p>
            </div>
            {resultado.conciliacion_id && (
              <div className="bg-blue-900/20 border border-blue-800/30 rounded-lg p-4">
                <p className="text-sm text-blue-400">Conciliacion Creada</p>
                <p className="text-sm text-white font-mono mt-1">{resultado.conciliacion_id.slice(0, 8)}...</p>
                <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded ${
                  resultado.conciliacion_estado === 'CONCILIADA' ? 'bg-green-900/50 text-green-300' : 'bg-yellow-900/50 text-yellow-300'
                }`}>
                  {resultado.conciliacion_estado}
                </span>
              </div>
            )}
            {resultado.vinculaciones?.length > 0 && (
              <div className="bg-purple-900/20 border border-purple-800/30 rounded-lg p-4">
                <p className="text-sm text-purple-400">Vinculaciones</p>
                <p className="text-2xl font-bold text-white">{resultado.vinculaciones.length}</p>
              </div>
            )}
          </div>
          {resultado.errores?.length > 0 && (
            <div className="mt-4 bg-red-900/20 border border-red-800/30 rounded-lg p-4">
              <p className="text-sm text-red-400 font-medium">Errores:</p>
              {resultado.errores.map((e: any, i: number) => (
                <p key={i} className="text-xs text-red-300 mt-1">{e.error || 'Error desconocido'}</p>
              ))}
            </div>
          )}
          <button
            onClick={() => { setResultado(null); setPreview(null); setArchivo(null) }}
            className="mt-4 px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700"
          >
            Importar otro archivo
          </button>
        </div>
      )}

      {/* Leyenda */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <div className="flex flex-wrap gap-6 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-orange-900/50 border border-orange-700"></span> CxP - Cuentas por Pagar
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-green-900/50 border border-green-700"></span> CxC - Cuentas por Cobrar
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-blue-900/50 border border-blue-700"></span> BANCO - Movimiento Bancario
          </span>
          <span className="flex items-center gap-1 text-yellow-400">
            <AlertCircle className="w-3 h-3" /> Duplicado (ya existe en el sistema)
          </span>
        </div>
      </div>
    </div>
  )
}
