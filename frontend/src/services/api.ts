const API_BASE = '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options?.headers as Record<string, string>) },
  })

  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Error de conexion')
  }

  return res.json()
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  getDashboard: (periodoId?: string) =>
    request<any>(`/bi/dashboard${periodoId ? `?periodo_id=${periodoId}` : ''}`),

  getBalanceComprobacion: (periodoId: string, nivel = 4) =>
    request<any[]>(`/reportes/balance-comprobacion?periodo_id=${periodoId}&nivel=${nivel}`),

  getBalanceGeneral: (periodoId: string) =>
    request<any>(`/reportes/balance-general?periodo_id=${periodoId}`),

  getEstadoResultados: (periodoId: string) =>
    request<any>(`/reportes/estado-resultados?periodo_id=${periodoId}`),

  getFlujoEfectivo: (desde: string, hasta: string) =>
    request<any>(`/reportes/flujo-efectivo?fecha_desde=${desde}&fecha_hasta=${hasta}`),

  getAntiguedadCxC: () => request<any[]>('/cuentas-por-cobrar/antiguedad'),
  getAntiguedadCxP: () => request<any[]>('/cuentas-por-pagar/antiguedad'),

  getPeriodos: () => request<any[]>('/periodos'),

  getUsuarios: () => request<any[]>('/usuarios?solo_activos=false'),
  getRoles: () => request<any[]>('/roles'),
  crearUsuario: (data: any) =>
    request<any>('/usuarios', { method: 'POST', body: JSON.stringify(data) }),
  actualizarUsuario: (id: string, data: any) =>
    request<any>(`/usuarios/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  asignarRoles: (id: string, roles: string[]) =>
    request<any>(`/usuarios/${id}/roles`, { method: 'POST', body: JSON.stringify(roles) }),
}
