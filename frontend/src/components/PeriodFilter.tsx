import { useEffect, useState } from 'react'

interface Periodo {
  id: string
  codigo: string
  nombre: string
}

export default function PeriodFilter({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  const [periodos, setPeriodos] = useState<Periodo[]>([])

  useEffect(() => {
    fetch('/api/v1/periodos')
      .then((r) => r.json())
      .then(setPeriodos)
      .catch(() => {})
  }, [])

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="input-filter min-w-[160px]"
    >
      <option value="">Seleccionar periodo</option>
      {periodos.map((p) => (
        <option key={p.id} value={p.id}>
          {p.nombre || p.codigo}
        </option>
      ))}
    </select>
  )
}
