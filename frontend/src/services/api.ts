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

  getClientes: () => request<any[]>('/clientes'),
  crearCliente: (data: any) =>
    request<any>('/clientes', { method: 'POST', body: JSON.stringify(data) }),
  actualizarCliente: (id: string, data: any) =>
    request<any>(`/clientes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getUsuarios: () => request<any[]>('/usuarios?solo_activos=false'),
  getRoles: () => request<any[]>('/roles'),
  crearUsuario: (data: any) =>
    request<any>('/usuarios', { method: 'POST', body: JSON.stringify(data) }),
  actualizarUsuario: (id: string, data: any) =>
    request<any>(`/usuarios/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  asignarRoles: (id: string, roles: string[]) =>
    request<any>(`/usuarios/${id}/roles`, { method: 'POST', body: JSON.stringify(roles) }),

  getProveedores: () => request<any[]>('/proveedores'),
  crearProveedor: (data: any) =>
    request<any>('/proveedores', { method: 'POST', body: JSON.stringify(data) }),
  actualizarProveedor: (id: string, data: any) =>
    request<any>(`/proveedores/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getProductos: () => request<any[]>('/productos'),
  getProducto: (id: string) => request<any>(`/productos/${id}`),
  crearProducto: (data: any) =>
    request<any>('/productos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarProducto: (id: string, data: any) =>
    request<any>(`/productos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getFacturas: (params?: { cliente_id?: string; estado?: string }) => {
    const q = new URLSearchParams()
    if (params?.cliente_id) q.set('cliente_id', params.cliente_id)
    if (params?.estado) q.set('estado', params.estado)
    const qs = q.toString()
    return request<any[]>(`/cuentas-por-cobrar/facturas${qs ? `?${qs}` : ''}`)
  },
  crearFactura: (data: any) =>
    request<any>('/cuentas-por-cobrar/facturas', { method: 'POST', body: JSON.stringify(data) }),

  getCuentasBanco: () => request<any[]>('/bancos'),
  crearCuentaBanco: (data: any) =>
    request<any>('/bancos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarCuentaBanco: (id: string, data: any) =>
    request<any>(`/bancos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getMovimientosBanco: (cuenta_id?: string) => {
    const q = cuenta_id ? `?cuenta_id=${cuenta_id}` : ''
    return request<any[]>(`/bancos/movimientos${q}`)
  },
  crearMovimientoBanco: (data: any) =>
    request<any>('/bancos/movimientos', { method: 'POST', body: JSON.stringify(data) }),
}
