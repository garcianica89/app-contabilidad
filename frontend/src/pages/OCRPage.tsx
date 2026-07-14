import { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'
import { Trash2, FileText, Plus } from 'lucide-react'

export default function OCRPage() {
  const [docs, setDocs] = useState<any[]>([])
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const load = async () => setDocs(await api.getDocumentosOCR())
  useEffect(() => { load() }, [])

  const upload = async (file: File) => {
    setUploading(true)
    try {
      await api.uploadDocumentoOCR(file)
      load()
    } finally { setUploading(false) }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">OCR — Documentos</h1>
      <div className="mb-6">
        <input ref={fileRef} type="file" accept=".pdf,.jpg,.jpeg,.png" className="hidden"
          onChange={e => { if (e.target.files?.[0]) upload(e.target.files[0]); e.target.value = '' }} />
        <button onClick={() => fileRef.current?.click()} disabled={uploading}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-700 disabled:opacity-50">
          <Plus className="w-4 h-4" /> {uploading ? 'Subiendo...' : 'Subir Documento'}</button>
      </div>
      <div className="grid gap-3">
        {docs.map((d: any) => (
          <div key={d.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-6 h-6 text-slate-400" />
              <div>
                <p className="text-white font-medium">{d.filename}</p>
                <p className="text-sm text-slate-400">{d.content_type} · {(d.file_size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                d.estado === 'PROCESADO' ? 'bg-green-900 text-green-400' :
                d.estado === 'ERROR' ? 'bg-red-900 text-red-400' :
                'bg-yellow-900 text-yellow-400'}`}>{d.estado}</span>
              <button onClick={async () => { await api.eliminarDocumentoOCR(d.id); load() }}
                className="p-2 text-red-400 hover:text-red-300"><Trash2 className="w-4 h-4" /></button>
            </div>
          </div>
        ))}
        {docs.length === 0 && (
          <p className="text-center text-slate-500 py-12">No hay documentos OCR</p>
        )}
      </div>
    </div>
  )
}
