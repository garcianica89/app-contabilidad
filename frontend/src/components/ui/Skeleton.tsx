interface SkeletonProps {
  rows?: number
  barHeight?: string
  className?: string
}

export default function Skeleton({ rows = 4, barHeight = 'h-12', className = '' }: SkeletonProps) {
  return (
    <div className={`card animate-pulse space-y-3 ${className}`}>
      {[...Array(rows)].map((_, i) => (
        <div key={i} className={`${barHeight} bg-slate-700/50 rounded`} />
      ))}
    </div>
  )
}
