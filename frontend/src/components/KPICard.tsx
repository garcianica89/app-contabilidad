import { ReactNode } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface KPICardProps {
  title: string
  value: string
  subtitle?: string
  icon: ReactNode
  trend?: { value: string; up: boolean }
  color?: 'primary' | 'emerald' | 'amber' | 'red' | 'blue' | 'purple'
}

const colorMap = {
  primary: 'from-primary-600/20 to-primary-600/5 border-primary-500/30',
  emerald: 'from-emerald-600/20 to-emerald-600/5 border-emerald-500/30',
  amber: 'from-amber-600/20 to-amber-600/5 border-amber-500/30',
  red: 'from-red-600/20 to-red-600/5 border-red-500/30',
  blue: 'from-blue-600/20 to-blue-600/5 border-blue-500/30',
  purple: 'from-purple-600/20 to-purple-600/5 border-purple-500/30',
}

export default function KPICard({ title, value, subtitle, icon, trend, color = 'primary' }: KPICardProps) {
  return (
    <div className={`card bg-gradient-to-br ${colorMap[color]}`}>
      <div className="flex items-start justify-between mb-2">
        <span className="card-header">{title}</span>
        <div className={`p-2 rounded-lg bg-${color === 'primary' ? 'primary' : color}-600/20`}>
          {icon}
        </div>
      </div>
      <div className="kpi-value">{value}</div>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
      {trend && (
        <div className="flex items-center gap-1 mt-2">
          {trend.up ? (
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-400" />
          )}
          <span className={trend.up ? 'kpi-trend-up' : 'kpi-trend-down'}>{trend.value}</span>
        </div>
      )}
    </div>
  )
}
