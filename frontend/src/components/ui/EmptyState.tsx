import { AlertCircle } from 'lucide-react'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  message?: string
  icon?: ReactNode | null
  className?: string
}

export default function EmptyState({
  message = 'No hay datos disponibles',
  icon = <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />,
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`card text-center py-12 text-slate-500 ${className}`}>
      {icon}
      {message}
    </div>
  )
}
