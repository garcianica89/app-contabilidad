import { usePermissions } from '../contexts/PermissionContext'

interface CanProps {
  permiso: string
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function Can({ permiso, children, fallback = null }: CanProps) {
  const { has } = usePermissions()
  return has(permiso) ? <>{children}</> : <>{fallback}</>
}
