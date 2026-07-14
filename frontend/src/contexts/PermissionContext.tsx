import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { api } from '../services/api'

interface PermissionContextType {
  permisos: string[]
  loading: boolean
  has: (codigo: string) => boolean
  hasAny: (codigos: string[]) => boolean
  hasAll: (codigos: string[]) => boolean
}

const PermissionContext = createContext<PermissionContextType>({
  permisos: [],
  loading: true,
  has: () => false,
  hasAny: () => false,
  hasAll: () => false,
})

export function PermissionProvider({ children }: { children: ReactNode }) {
  const [permisos, setPermisos] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.misPermisos()
      .then(list => setPermisos(list.map(p => p.codigo)))
      .catch(() => setPermisos([]))
      .finally(() => setLoading(false))
  }, [])

  const has = (codigo: string) => permisos.includes(codigo)
  const hasAny = (codigos: string[]) => codigos.some(c => permisos.includes(c))
  const hasAll = (codigos: string[]) => codigos.every(c => permisos.includes(c))

  return (
    <PermissionContext.Provider value={{ permisos, loading, has, hasAny, hasAll }}>
      {children}
    </PermissionContext.Provider>
  )
}

export const usePermissions = () => useContext(PermissionContext)
