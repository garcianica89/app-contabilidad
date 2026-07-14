import type {
  TokenResponse,
  DashboardResponse,
  BalanceComprobacionRow,
  BalanceGeneralResponse,
  EstadoResultadosResponse,
  FlujoEfectivoResponse,
  AntiguedadRow,
  PeriodoContable,
  Cliente,
  Usuario,
  Rol,
  Proveedor,
  Producto,
  FacturaVenta,
  FacturaVentaLinea,
  CuentaBanco,
  TipoCuentaBanco,
  MovimientoBanco,
  Bodega,
  Categoria,
  Numeracion,
  NextCorrelativoResponse,
  OrdenCompra,
  FacturaCompra,
  ActivoFijo,
  CategoriaActivo,
  DepreciacionLinea,
  CuentaContable,
  TipoAsiento,
  Plantilla,
  SalidaInventarioCreate,
  SalidaInventarioResponse,
  SalidaInventarioListadoItem,
  ConciliacionBancaria,
  PartidaConciliacion,
  Parametro,
  Moneda,
  TipoCambioHist,
  CondicionPago,
  Impuesto,
  Empleado,
  Departamento,
  Cargo,
  NominaPeriodo,
  NominaConfig,
  DocumentoOCR,
  AnalisisIA,
  Presupuesto,
  CentroCosto,
  PresupuestoDetalle,
  Permiso,
  Tercero,
  Workflow,
  WorkflowStatus,
  WorkflowTransition,
  WfDocumentHistory,
  WfPendingApproval,
  Retencion,
  EjercicioFiscal,
  Empresa,
  CierreMensual,
  CierreFiscal,
  ModuloSistema,
} from '../types/api'

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

  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  login: (username: string, password: string) =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  getDashboard: (periodoId?: string) =>
    request<DashboardResponse>(`/bi/dashboard${periodoId ? `?periodo_id=${periodoId}` : ''}`),

  getBalanceComprobacion: (params?: {
    periodo_id?: string
    fecha_desde?: string
    fecha_hasta?: string
    cuenta_id?: string
    nivel_maximo?: number
    centro_costo_id?: string
    solo_diario?: boolean
  }) => {
    const q = new URLSearchParams()
    if (params?.periodo_id) q.set('periodo_id', params.periodo_id)
    if (params?.fecha_desde) q.set('fecha_desde', params.fecha_desde)
    if (params?.fecha_hasta) q.set('fecha_hasta', params.fecha_hasta)
    if (params?.cuenta_id) q.set('cuenta_id', params.cuenta_id)
    if (params?.nivel_maximo) q.set('nivel_maximo', String(params.nivel_maximo))
    if (params?.centro_costo_id) q.set('centro_costo_id', params.centro_costo_id)
    if (params?.solo_diario) q.set('solo_diario', 'true')
    const qs = q.toString() ? `?${q.toString()}` : ''
    return request<BalanceComprobacionRow[]>(`/reportes/balance-comprobacion${qs}`)
  },
  recalcularSaldos: (periodo_id: string, cuenta_id?: string, centro_costo_id?: string) =>
    request<{ mensaje: string; periodo_id: string; cuentas: number }>(
      '/reportes/recalcular-saldos',
      { method: 'POST', body: JSON.stringify({ periodo_id, cuenta_id, centro_costo_id }) },
    ),

  getBalanceGeneral: (periodoId: string) =>
    request<BalanceGeneralResponse>(`/reportes/balance-general?periodo_id=${periodoId}`),

  getEstadoResultados: (periodoId: string) =>
    request<EstadoResultadosResponse>(`/reportes/estado-resultados?periodo_id=${periodoId}`),

  getFlujoEfectivo: (desde: string, hasta: string) =>
    request<FlujoEfectivoResponse>(`/reportes/flujo-efectivo?fecha_desde=${desde}&fecha_hasta=${hasta}`),

  getAntiguedadCxC: () => request<AntiguedadRow[]>('/cuentas-por-cobrar/antiguedad'),
  getAntiguedadCxP: () => request<AntiguedadRow[]>('/cuentas-por-pagar/antiguedad'),

  getPeriodos: () => request<PeriodoContable[]>('/periodos'),

  getClientes: () => request<Cliente[]>('/clientes'),
  crearCliente: (data: Partial<Cliente>) =>
    request<Cliente>('/clientes', { method: 'POST', body: JSON.stringify(data) }),
  actualizarCliente: (id: string, data: Partial<Cliente>) =>
    request<Cliente>(`/clientes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getUsuarios: () => request<Usuario[]>('/usuarios?solo_activos=false'),
  getRoles: () => request<Rol[]>('/roles'),
  crearUsuario: (data: Partial<Usuario>) =>
    request<Usuario>('/usuarios', { method: 'POST', body: JSON.stringify(data) }),
  actualizarUsuario: (id: string, data: Partial<Usuario>) =>
    request<Usuario>(`/usuarios/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  asignarRoles: (id: string, roles: string[]) =>
    request<void>(`/usuarios/${id}/roles`, { method: 'POST', body: JSON.stringify(roles) }),

  getProveedores: () => request<Proveedor[]>('/proveedores'),
  crearProveedor: (data: Partial<Proveedor>) =>
    request<Proveedor>('/proveedores', { method: 'POST', body: JSON.stringify(data) }),
  actualizarProveedor: (id: string, data: Partial<Proveedor>) =>
    request<Proveedor>(`/proveedores/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getProductos: () => request<Producto[]>('/productos'),
  getProducto: (id: string) => request<Producto>(`/productos/${id}`),
  crearProducto: (data: Partial<Producto>) =>
    request<Producto>('/productos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarProducto: (id: string, data: Partial<Producto>) =>
    request<Producto>(`/productos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getFacturas: (params?: { cliente_id?: string; estado?: string }) => {
    const q = new URLSearchParams()
    if (params?.cliente_id) q.set('cliente_id', params.cliente_id)
    if (params?.estado) q.set('estado', params.estado)
    const qs = q.toString()
    return request<FacturaVenta[]>(`/cuentas-por-cobrar/facturas${qs ? `?${qs}` : ''}`)
  },
  crearFactura: (data: Partial<FacturaVenta> & { lineas?: FacturaVentaLinea[] }) =>
    request<FacturaVenta>('/cuentas-por-cobrar/facturas', { method: 'POST', body: JSON.stringify(data) }),

  // ── CxC Retenciones / Cobros ──────────────────────────
  getFacturaVenta: (id: string) =>
    request<any>(`/cuentas-por-cobrar/facturas/${id}`),
  getRetencionesFacturaCxC: (facturaId: string) =>
    request<any[]>(`/cuentas-por-cobrar/facturas/${facturaId}/retenciones`),
  saveRetencionesFacturaCxC: (facturaId: string, retenciones: { retencion_id: string; base_imponible: number; monto_retenido: number }[]) =>
    request<any>(`/cuentas-por-cobrar/facturas/${facturaId}/retenciones`, {
      method: 'PUT',
      body: JSON.stringify(retenciones),
    }),
  registrarCobro: (data: any) =>
    request<any>('/cuentas-por-cobrar/cobros', { method: 'POST', body: JSON.stringify(data) }),

  getCuentasBanco: () => request<CuentaBanco[]>('/bancos'),
  crearCuentaBanco: (data: Partial<CuentaBanco>) =>
    request<CuentaBanco>('/bancos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarCuentaBanco: (id: string, data: Partial<CuentaBanco>) =>
    request<CuentaBanco>(`/bancos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getMovimientosBanco: (cuenta_id?: string) => {
    const q = cuenta_id ? `?cuenta_id=${cuenta_id}` : ''
    return request<MovimientoBanco[]>(`/bancos/movimientos${q}`)
  },
  crearMovimientoBanco: (data: Partial<MovimientoBanco>) =>
    request<MovimientoBanco>('/bancos/movimientos', { method: 'POST', body: JSON.stringify(data) }),
  crearMovimientoBancoConfigurable: (data: any) =>
    request<any>('/bancos/movimientos-configurables', { method: 'POST', body: JSON.stringify(data) }),

  getTiposCuentaBanco: (solo_activos?: boolean) => {
    const q = solo_activos ? '?solo_activos=true' : ''
    return request<TipoCuentaBanco[]>(`/tipos-cuenta-banco${q}`)
  },
  crearTipoCuentaBanco: (data: { codigo: string; nombre: string }) =>
    request<TipoCuentaBanco>('/tipos-cuenta-banco', { method: 'POST', body: JSON.stringify(data) }),
  actualizarTipoCuentaBanco: (id: string, data: Partial<TipoCuentaBanco>) =>
    request<TipoCuentaBanco>(`/tipos-cuenta-banco/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarTipoCuentaBanco: (id: string) =>
    request<void>(`/tipos-cuenta-banco/${id}`, { method: 'DELETE' }),

  getCategorias: () => request<Categoria[]>('/productos/categorias'),
  crearCategoria: (data: Partial<Categoria>) =>
    request<Categoria>('/productos/categorias', { method: 'POST', body: JSON.stringify(data) }),
  actualizarCategoria: (id: string, data: Partial<Categoria>) =>
    request<Categoria>(`/productos/categorias/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarCategoria: (id: string) =>
    request<void>(`/productos/categorias/${id}`, { method: 'DELETE' }),

  getNumeraciones: (tipo?: string) => {
    const q = tipo ? `?tipo_documento=${tipo}` : ''
    return request<Numeracion[]>(`/numeraciones${q}`)
  },
  getNextCorrelativo: (id: string) =>
    request<NextCorrelativoResponse>(`/numeraciones/${id}/next`, { method: 'POST' }),

  getOrdenesCompra: (params?: { estado?: string }) => {
    const q = params?.estado ? `?estado=${params.estado}` : ''
    return request<OrdenCompra[]>(`/ordenes-compra${q}`)
  },
  crearOrdenCompra: (data: Record<string, any>) =>
    request<OrdenCompra>('/ordenes-compra', { method: 'POST', body: JSON.stringify(data) }),
  aprobarOrdenCompra: (id: string) =>
    request<OrdenCompra>(`/ordenes-compra/${id}/aprobar`, { method: 'POST' }),
  anularOrdenCompra: (id: string) =>
    request<OrdenCompra>(`/ordenes-compra/${id}/anular`, { method: 'POST' }),

  getFacturasCompra: (params?: { proveedor_id?: string; estado?: string }) => {
    const q = new URLSearchParams()
    if (params?.proveedor_id) q.set('proveedor_id', params.proveedor_id)
    if (params?.estado) q.set('estado', params.estado)
    const qs = q.toString()
    return request<FacturaCompra[]>(`/cuentas-por-pagar/facturas${qs ? `?${qs}` : ''}`)
  },
  crearFacturaCompra: (data: Record<string, any>) =>
    request<FacturaCompra>('/cuentas-por-pagar/facturas', { method: 'POST', body: JSON.stringify(data) }),

  getActivosFijos: () => request<ActivoFijo[]>('/activos-fijos'),
  getCategoriasActivo: () => request<CategoriaActivo[]>('/activos-fijos/categorias'),
  getDepreciacionesActivo: (id: string) =>
    request<DepreciacionLinea[]>(`/activos-fijos/${id}/depreciaciones`),
  crearActivoFijo: (data: Partial<ActivoFijo>) =>
    request<ActivoFijo>('/activos-fijos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarActivoFijo: (id: string, data: Partial<ActivoFijo>) =>
    request<ActivoFijo>(`/activos-fijos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarActivoFijo: (id: string) =>
    request<void>(`/activos-fijos/${id}`, { method: 'DELETE' }),
  crearCategoriaActivo: (data: Partial<CategoriaActivo>) =>
    request<CategoriaActivo>('/activos-fijos/categorias', { method: 'POST', body: JSON.stringify(data) }),
  depreciarActivo: (id: string, data?: Partial<unknown>) =>
    request<DepreciacionLinea>(`/activos-fijos/${id}/depreciar`, { method: 'POST', body: JSON.stringify(data || {}) }),
  darBajaActivo: (id: string, data?: Partial<ActivoFijo>) =>
    request<ActivoFijo>(`/activos-fijos/${id}/dar-baja`, { method: 'POST', body: JSON.stringify(data || {}) }),

  getCuentasContables: () => request<CuentaContable[]>('/cuentas-contables'),
  getCuentasArbol: () => request<CuentaContable[]>('/cuentas-contables/arbol'),
  crearCuentaContable: (data: Partial<CuentaContable>) =>
    request<CuentaContable>('/cuentas-contables', { method: 'POST', body: JSON.stringify(data) }),
  actualizarCuentaContable: (id: string, data: Partial<CuentaContable>) =>
    request<CuentaContable>(`/cuentas-contables/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getTiposAsiento: () => request<TipoAsiento[]>('/tipos-asiento'),
  crearTipoAsiento: (data: Partial<TipoAsiento>) =>
    request<TipoAsiento>('/tipos-asiento', { method: 'POST', body: JSON.stringify(data) }),
  actualizarTipoAsiento: (id: string, data: Partial<TipoAsiento>) =>
    request<TipoAsiento>(`/tipos-asiento/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarTipoAsiento: (id: string) =>
    request<void>(`/tipos-asiento/${id}`, { method: 'DELETE' }),

  getPlantillas: () => request<Plantilla[]>('/plantillas'),
  crearPlantilla: (data: Partial<Plantilla>) =>
    request<Plantilla>('/plantillas', { method: 'POST', body: JSON.stringify(data) }),
  actualizarPlantilla: (id: string, data: Partial<Plantilla>) =>
    request<Plantilla>(`/plantillas/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarPlantilla: (id: string) =>
    request<void>(`/plantillas/${id}`, { method: 'DELETE' }),

  getConciliaciones: (params?: { cuenta_id?: string }) => {
    const q = params?.cuenta_id ? `?cuenta_id=${params.cuenta_id}` : ''
    return request<ConciliacionBancaria[]>(`/conciliaciones${q}`)
  },
  getConciliacion: (id: string) => request<ConciliacionBancaria>(`/conciliaciones/${id}`),
  crearConciliacion: (data: Partial<ConciliacionBancaria>) =>
    request<ConciliacionBancaria>('/conciliaciones', { method: 'POST', body: JSON.stringify(data) }),
  cerrarConciliacion: (id: string) =>
    request<ConciliacionBancaria>(`/conciliaciones/${id}/cerrar`, { method: 'POST' }),
  conciliarPartidas: (id: string, data: { partida_ids: string[], conciliado: boolean }) =>
    request<ConciliacionBancaria>(`/conciliaciones/${id}/conciliar`, { method: 'POST', body: JSON.stringify(data) }),

  getParametros: () => request<Parametro[]>('/parametros'),
  crearParametro: (data: Partial<Parametro>) =>
    request<Parametro>('/parametros', { method: 'POST', body: JSON.stringify(data) }),
  actualizarParametro: (id: string, data: Partial<Parametro>) =>
    request<Parametro>(`/parametros/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarParametro: (id: string) =>
    request<void>(`/parametros/${id}`, { method: 'DELETE' }),

  getMonedas: () => request<Moneda[]>('/monedas'),
  crearMoneda: (data: Partial<Moneda>) =>
    request<Moneda>('/monedas', { method: 'POST', body: JSON.stringify(data) }),
  actualizarMoneda: (id: string, data: Partial<Moneda>) =>
    request<Moneda>(`/monedas/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarMoneda: (id: string) =>
    request<void>(`/monedas/${id}`, { method: 'DELETE' }),

  getTiposCambio: () => request<TipoCambioHist[]>('/tipos-cambio'),
  crearTipoCambio: (data: Partial<TipoCambioHist>) =>
    request<TipoCambioHist>('/tipos-cambio', { method: 'POST', body: JSON.stringify(data) }),
  eliminarTipoCambio: (id: string) =>
    request<void>(`/tipos-cambio/${id}`, { method: 'DELETE' }),

  getBodegas: () => request<Bodega[]>('/bodegas'),
  getCondicionesPago: () => request<CondicionPago[]>('/condiciones-pago'),
  crearCondicionPago: (data: Partial<CondicionPago>) =>
    request<CondicionPago>('/condiciones-pago', { method: 'POST', body: JSON.stringify(data) }),
  actualizarCondicionPago: (id: string, data: Partial<CondicionPago>) =>
    request<CondicionPago>(`/condiciones-pago/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarCondicionPago: (id: string) =>
    request<void>(`/condiciones-pago/${id}`, { method: 'DELETE' }),

  getImpuestos: () => request<Impuesto[]>('/impuestos'),
  crearImpuesto: (data: Partial<Impuesto>) =>
    request<Impuesto>('/impuestos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarImpuesto: (id: string, data: Partial<Impuesto>) =>
    request<Impuesto>(`/impuestos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarImpuesto: (id: string) =>
    request<void>(`/impuestos/${id}`, { method: 'DELETE' }),

  getEmpleados: (params?: { activo?: boolean }) => {
    const q = params?.activo !== undefined ? `?activo=${params.activo}` : ''
    return request<Empleado[]>(`/empleados${q}`)
  },
  crearEmpleado: (data: Partial<Empleado>) =>
    request<Empleado>('/empleados', { method: 'POST', body: JSON.stringify(data) }),
  actualizarEmpleado: (id: string, data: Partial<Empleado>) =>
    request<Empleado>(`/empleados/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarEmpleado: (id: string) =>
    request<void>(`/empleados/${id}`, { method: 'DELETE' }),

  getDepartamentos: () => request<Departamento[]>('/empleados/departamentos'),
  crearDepartamento: (data: Partial<Departamento>) =>
    request<Departamento>('/empleados/departamentos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarDepartamento: (id: string, data: Partial<Departamento>) =>
    request<Departamento>(`/empleados/departamentos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarDepartamento: (id: string) =>
    request<void>(`/empleados/departamentos/${id}`, { method: 'DELETE' }),

  getCargos: () => request<Cargo[]>('/empleados/cargos'),
  crearCargo: (data: Partial<Cargo>) =>
    request<Cargo>('/empleados/cargos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarCargo: (id: string, data: Partial<Cargo>) =>
    request<Cargo>(`/empleados/cargos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarCargo: (id: string) =>
    request<void>(`/empleados/cargos/${id}`, { method: 'DELETE' }),

  getPeriodosNomina: () => request<NominaPeriodo[]>('/nomina/periodos'),
  getPeriodoNomina: (id: string) => request<NominaPeriodo>(`/nomina/periodos/${id}`),
  crearPeriodoNomina: (data: Partial<NominaPeriodo>) =>
    request<NominaPeriodo>('/nomina/periodos', { method: 'POST', body: JSON.stringify(data) }),
  getNominaConfig: () => request<NominaConfig>('/nomina/config'),
  actualizarNominaConfig: (data: Partial<NominaConfig>) =>
    request<NominaConfig>('/nomina/config', { method: 'PUT', body: JSON.stringify(data) }),
  procesarNomina: (periodoId: string, data?: Partial<unknown>) =>
    request<NominaPeriodo>(`/nomina/periodos/${periodoId}/procesar`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  pagarNomina: (periodoId: string, data?: Partial<unknown>) =>
    request<NominaPeriodo>(`/nomina/periodos/${periodoId}/pagar`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),

  getDocumentosOCR: () => request<DocumentoOCR[]>('/ocr'),
  uploadDocumentoOCR: (data: FormData | Partial<DocumentoOCR>) =>
    request<DocumentoOCR>('/ocr/upload', { method: 'POST', body: JSON.stringify(data) }),
  eliminarDocumentoOCR: (id: string) =>
    request<void>(`/ocr/${id}`, { method: 'DELETE' }),

  getAnalisisIA: (tipo?: string) => {
    const q = tipo ? `?tipo=${tipo}` : ''
    return request<AnalisisIA[]>(`/ia${q}`)
  },
  crearAnalisisIA: (data: Partial<AnalisisIA>) =>
    request<AnalisisIA>('/ia', { method: 'POST', body: JSON.stringify(data) }),
  ejecutarAnalisisIA: (id: string) =>
    request<AnalisisIA>(`/ia/${id}/ejecutar`, { method: 'POST' }),
  eliminarAnalisisIA: (id: string) =>
    request<void>(`/ia/${id}`, { method: 'DELETE' }),

  getPresupuestos: () => request<Presupuesto[]>('/presupuestos'),
  crearPresupuesto: (data: Partial<Presupuesto>) =>
    request<Presupuesto>('/presupuestos', { method: 'POST', body: JSON.stringify(data) }),
  actualizarPresupuesto: (id: string, data: Partial<Presupuesto>) =>
    request<Presupuesto>(`/presupuestos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  aprobarPresupuesto: (id: string) =>
    request<Presupuesto>(`/presupuestos/${id}/aprobar`, { method: 'POST' }),
  getCentrosCosto: () => request<CentroCosto[]>('/presupuestos/centros-costo'),
  crearCentroCosto: (data: Partial<CentroCosto>) =>
    request<CentroCosto>('/presupuestos/centros-costo', { method: 'POST', body: JSON.stringify(data) }),
  eliminarCentroCosto: (id: string) =>
    request<void>(`/presupuestos/centros-costo/${id}`, { method: 'DELETE' }),
  getPartidasPresupuesto: (id: string) =>
    request<PresupuestoDetalle[]>(`/presupuestos/${id}/partidas`),
  crearPartidaPresupuesto: (presupuestoId: string, data: Partial<PresupuestoDetalle>) =>
    request<PresupuestoDetalle>(`/presupuestos/${presupuestoId}/partidas`, { method: 'POST', body: JSON.stringify(data) }),
  eliminarPartidaPresupuesto: (presupuestoId: string, partidaId: string) =>
    request<void>(`/presupuestos/${presupuestoId}/partidas/${partidaId}`, { method: 'DELETE' }),

  getPermisos: () => request<Permiso[]>('/permisos'),
  getPermisosRol: (rolId: string) => request<Permiso[]>(`/roles/${rolId}/permisos`),
  asignarPermisosRol: (rolId: string, permisos: string[]) =>
    request<void>(`/roles/${rolId}/permisos`, { method: 'POST', body: JSON.stringify({ permiso_ids: permisos }) }),
  misPermisos: () => request<{ codigo: string }[]>('/permisos/mis-permisos'),
  misPermisosEntidad: (entityType: string, entityId: string) =>
    request<{ codigo: string }[]>(`/permisos/mis-permisos/entidad/${entityType}/${entityId}`),
  getPermisosUsuario: (usuarioId: string, entityType?: string, entityId?: string) => {
    const q = new URLSearchParams()
    if (entityType) q.set('entity_type', entityType)
    if (entityId) q.set('entity_id', entityId)
    const qs = q.toString() ? `?${q.toString()}` : ''
    return request<{ codigo: string }[]>(`/permisos/usuario/${usuarioId}/permisos${qs}`)
  },
  asignarPermisoUsuario: (usuarioId: string, data: { permiso_id: string; entity_type?: string; entity_id?: string; allow?: boolean }) =>
    request<any>(`/permisos/usuario/${usuarioId}/permisos`, { method: 'POST', body: JSON.stringify(data) }),
  eliminarPermisoUsuario: (usuarioId: string, upId: string) =>
    request<void>(`/permisos/usuario/${usuarioId}/permisos/${upId}`, { method: 'DELETE' }),
  crearRol: (data: Partial<Rol>) =>
    request<Rol>('/roles', { method: 'POST', body: JSON.stringify(data) }),
  actualizarRol: (id: string, data: Partial<Rol>) =>
    request<Rol>(`/roles/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarRol: (id: string) =>
    request<void>(`/roles/${id}`, { method: 'DELETE' }),

  // ── Terceros (Catálogo Único) ─────────────────────────────
  getTerceros: (params?: { rol?: string; search?: string }) => {
    const q = new URLSearchParams()
    if (params?.rol) q.set('rol', params.rol)
    if (params?.search) q.set('search', params.search)
    const qs = q.toString()
    return request<Tercero[]>(`/terceros${qs ? `?${qs}` : ''}`)
  },
  getTercero: (id: string) => request<Tercero>(`/terceros/${id}`),
  crearTercero: (data: Partial<Tercero>) =>
    request<Tercero>('/terceros', { method: 'POST', body: JSON.stringify(data) }),
  actualizarTercero: (id: string, data: Partial<Tercero>) =>
    request<Tercero>(`/terceros/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarTercero: (id: string) =>
    request<void>(`/terceros/${id}`, { method: 'DELETE' }),

  // ── Workflow ──────────────────────────────────────────────
  getWorkflows: () => request<Workflow[]>('/workflow'),
  getWorkflow: (id: string) => request<Workflow>(`/workflow/${id}`),
  crearWorkflow: (data: Partial<Workflow>) =>
    request<Workflow>('/workflow', { method: 'POST', body: JSON.stringify(data) }),
  actualizarWorkflow: (id: string, data: Partial<Workflow>) =>
    request<Workflow>(`/workflow/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  crearStatus: (workflowId: string, data: Partial<WorkflowStatus>) =>
    request<WorkflowStatus>(`/workflow/${workflowId}/statuses`, { method: 'POST', body: JSON.stringify(data) }),
  actualizarStatus: (statusId: string, data: Partial<WorkflowStatus>) =>
    request<WorkflowStatus>(`/workflow/statuses/${statusId}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarStatus: (statusId: string) =>
    request<void>(`/workflow/statuses/${statusId}`, { method: 'DELETE' }),
  crearTransicion: (workflowId: string, data: Partial<WorkflowTransition>) =>
    request<WorkflowTransition>(`/workflow/${workflowId}/transitions`, { method: 'POST', body: JSON.stringify(data) }),
  eliminarTransicion: (transitionId: string) =>
    request<void>(`/workflow/transitions/${transitionId}`, { method: 'DELETE' }),
  ejecutarTransicion: (workflowId: string, data: { transition_id: string; comentario?: string; documento_id: string }) =>
    request<void>(`/workflow/${workflowId}/transition`, { method: 'POST', body: JSON.stringify(data) }),
  getHistory: (workflowId: string, documentId?: string) => {
    const q = documentId ? `?document_id=${documentId}` : ''
    return request<WfDocumentHistory[]>(`/workflow/${workflowId}/history${q}`)
  },
  getPendingApprovals: () => request<WfPendingApproval[]>('/workflow/pending-approvals'),
  resolveApproval: (approvalId: string, data: { estado: string; comentario?: string }) =>
    request<WfPendingApproval>(`/workflow/pending-approvals/${approvalId}/resolve`, { method: 'POST', body: JSON.stringify(data) }),

  // ── Retenciones ───────────────────────────────────────────
  getRetenciones: (activo?: boolean) => {
    const q = activo !== undefined ? `?activo=${activo}` : ''
    return request<Retencion[]>(`/retenciones${q}`)
  },
  getRetencion: (id: string) => request<Retencion>(`/retenciones/${id}`),
  crearRetencion: (data: Partial<Retencion>) =>
    request<Retencion>('/retenciones', { method: 'POST', body: JSON.stringify(data) }),
  actualizarRetencion: (id: string, data: Partial<Retencion>) =>
    request<Retencion>(`/retenciones/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarRetencion: (id: string) =>
    request<void>(`/retenciones/${id}`, { method: 'DELETE' }),

  // ── Document Engine ───────────────────────────────────────
  procesarDocumento: (data: Record<string, unknown>) =>
    request<Record<string, unknown>>('/document-engine/process', { method: 'POST', body: JSON.stringify(data) }),

  // ── Ejercicios Fiscales ──────────────────────────────────
  getEjercicios: () => request<EjercicioFiscal[]>('/ejercicios'),

  // ── Empresas ──────────────────────────────────────────────
  getEmpresas: () => request<Empresa[]>('/empresas'),
  getEmpresa: (id: string) => request<Empresa>(`/empresas/${id}`),
  crearEmpresa: (data: Partial<Empresa>) =>
    request<Empresa>('/empresas', { method: 'POST', body: JSON.stringify(data) }),

  // ── Cierre Mensual / Fiscal ──────────────────────────────
  getCierresMensuales: () => request<CierreMensual[]>('/cierre/mensual'),
  crearCierreMensual: (data: { periodo_id: string; observaciones?: string }) =>
    request<CierreMensual>('/cierre/mensual', { method: 'POST', body: JSON.stringify(data) }),
  reabrirCierreMensual: (id: string) =>
    request<CierreMensual>(`/cierre/mensual/${id}/reabrir`, { method: 'POST' }),
  getCierresFiscales: () => request<CierreFiscal[]>('/cierre/fiscal'),
  crearCierreFiscal: (data: { ejercicio_id: string; cuenta_resultado_id: string; cuenta_utilidad_id: string; observaciones?: string }) =>
    request<CierreFiscal>('/cierre/fiscal', { method: 'POST', body: JSON.stringify(data) }),

  // ── Modulos del Sistema ───────────────────────────────────
  getModulos: () => request<ModuloSistema[]>('/modulos'),
  getModulo: (id: string) => request<ModuloSistema>(`/modulos/${id}`),

  // ── ERP - Contabilidad General ─────────────────────────
  erpGetCuentas: () => request<any[]>('/erp/cg/cuentas'),
  erpGetCuentasArbol: () => request<any[]>('/erp/cg/cuentas/arbol'),
  erpCrearCuenta: (data: any) => request<any>('/erp/cg/cuentas', { method: 'POST', body: JSON.stringify(data) }),
  erpGetPeriodos: () => request<any[]>('/erp/cg/periodos'),
  erpCrearPeriodo: (data: any) => request<any>('/erp/cg/periodos', { method: 'POST', body: JSON.stringify(data) }),
  erpGetPaquetes: () => request<any[]>('/erp/cg/paquetes'),
  erpGetAsientos: () => request<any[]>('/erp/cg/asientos'),
  erpCrearAsiento: (data: any) => request<any>('/erp/cg/asientos', { method: 'POST', body: JSON.stringify(data) }),
  erpGetAsientoLines: (id: string) => request<any[]>(`/erp/cg/asientos/${id}/lines`),
  erpMayorizarAsiento: (id: string) => request<any>(`/erp/cg/asientos/${id}/mayorizar`, { method: 'POST' }),
  erpGetBalanceComprobacion: (periodoId: string) => request<any[]>(`/erp/cg/balance-comprobacion?periodo_id=${periodoId}`),

  // ── ERP - Inventario ──────────────────────────────────
  erpGetBodegas: () => request<any[]>('/erp/ci/bodegas'),
  erpCrearBodega: (data: any) => request<any>('/erp/ci/bodegas', { method: 'POST', body: JSON.stringify(data) }),
  erpGetArticulos: () => request<any[]>('/erp/ci/articulos'),
  erpCrearArticulo: (data: any) => request<any>('/erp/ci/articulos', { method: 'POST', body: JSON.stringify(data) }),
  erpGetExistencias: () => request<any[]>('/erp/ci/existencias'),
  erpGetTransacciones: () => request<any[]>('/erp/ci/transacciones'),
  erpCrearTransaccion: (data: any) => request<any>('/erp/ci/transacciones', { method: 'POST', body: JSON.stringify(data) }),
  erpRecalcularCostos: (fechaDesde: string) => request<any>(`/erp/ci/costos/recalcular?fecha_desde=${fechaDesde}`, { method: 'POST' }),
  erpValidarCostos: () => request<any>('/erp/ci/costos/validar'),

  // ── ERP - Cuentas por Cobrar ──────────────────────────
  erpGetDocumentosCC: () => request<any[]>('/erp/cc/documentos'),
  erpCrearDocumentoCC: (data: any) => request<any>('/erp/cc/documentos', { method: 'POST', body: JSON.stringify(data) }),
  erpRegistrarCobro: (data: any) => request<any>('/erp/cc/cobros', { method: 'POST', body: JSON.stringify(data) }),
  erpGetAuxiliarCC: (documentoId: string) => request<any[]>(`/erp/cc/auxiliar/${documentoId}`),

  // ── ERP - Tesoreria ───────────────────────────────────
  erpGetCuentasBancarias: () => request<any[]>('/erp/cb/cuentas'),
  erpCrearCuentaBancaria: (data: any) => request<any>('/erp/cb/cuentas', { method: 'POST', body: JSON.stringify(data) }),
  erpGetCheques: (params?: string) => request<any[]>(`/erp/cb/cheques${params || ''}`),
  erpCrearCheque: (data: any) => request<any>('/erp/cb/cheques', { method: 'POST', body: JSON.stringify(data) }),
  erpAnularCheque: (chequeId: string) => request<any>(`/erp/cb/cheques/${chequeId}/anular`, { method: 'POST' }),
  erpImprimirCheque: (chequeId: string, formato: string = 'pdf') =>
    request<any>(`/erp/cb/cheques/${chequeId}/imprimir?formato=${formato}`),
  erpVistaPreviaCheque: (chequeId: string, formato: string = 'html') =>
    request<any>(`/erp/cb/cheques/${chequeId}/vista-previa?formato=${formato}`),
  erpGetChequeras: (cuentaId?: string) =>
    request<any[]>(`/erp/cb/chequeras${cuentaId ? `?cuenta_id=${cuentaId}` : ''}`),
  erpCrearChequera: (data: any) => request<any>('/erp/cb/chequeras', { method: 'POST', body: JSON.stringify(data) }),
  erpGetFormatos: () => request<any[]>('/erp/cb/formatos'),
  erpCrearFormato: (data: any) => request<any>('/erp/cb/formatos', { method: 'POST', body: JSON.stringify(data) }),
  erpActualizarFormato: (id: string, data: any) => request<any>(`/erp/cb/formatos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  erpActivarFormato: (id: string) => request<any>(`/erp/cb/formatos/${id}/activar`, { method: 'POST' }),
  erpGetChequeConfig: (cuentaId: string) => request<any>(`/erp/cb/cuentas/${cuentaId}/cheque-config`),
  erpUpdateChequeConfig: (cuentaId: string, data: any) =>
    request<any>(`/erp/cb/cuentas/${cuentaId}/cheque-config`, { method: 'PUT', body: JSON.stringify(data) }),
  erpGetMovBancos: () => request<any[]>('/erp/cb/movimientos'),
  erpCrearMovBanco: (data: any) => request<any>('/erp/cb/movimientos', { method: 'POST', body: JSON.stringify(data) }),

  // ── ERP - Activos Fijos ──────────────────────────────
  erpGetTiposActivo: () => request<any[]>('/erp/af/tipos'),
  erpCrearTipoActivo: (data: any) => request<any>('/erp/af/tipos', { method: 'POST', body: JSON.stringify(data) }),
  erpGetActivosFijos: () => request<any[]>('/erp/af/activos'),
  erpCrearActivoFijo: (data: any) => request<any>('/erp/af/activos', { method: 'POST', body: JSON.stringify(data) }),
  erpActualizarActivoFijo: (id: string, data: any) => request<any>(`/erp/af/activos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  erpDepreciarActivo: (id: string) => request<any>(`/erp/af/activos/${id}/depreciar`, { method: 'POST' }),
  erpGetDepreciaciones: (id: string) => request<any[]>(`/erp/af/activos/${id}/depreciaciones`),
  erpDarBajaActivo: (id: string, data: any) => request<any>(`/erp/af/activos/${id}/dar-baja`, { method: 'POST', body: JSON.stringify(data) }),
  erpGetAccionesActivo: (id: string) => request<any[]>(`/erp/af/acciones/${id}`),

  // ── ERP - Facturacion ─────────────────────────────────
  erpGetClientes: () => request<any[]>('/erp/fa/clientes'),
  erpCrearCliente: (data: any) => request<any>('/erp/fa/clientes', { method: 'POST', body: JSON.stringify(data) }),
  erpActualizarCliente: (id: string, data: any) => request<any>(`/erp/fa/clientes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  erpGetFacturas: () => request<any[]>('/erp/fa/facturas'),
  erpCrearFactura: (data: any) => request<any>('/erp/fa/facturas', { method: 'POST', body: JSON.stringify(data) }),
  erpGetAntiguedadFA: () => request<any[]>('/erp/fa/antiguedad'),

  // ── ERP - Compras ────────────────────────────────────
  erpGetProveedores: () => request<any[]>('/erp/co/proveedores'),
  erpCrearProveedor: (data: any) => request<any>('/erp/co/proveedores', { method: 'POST', body: JSON.stringify(data) }),
  erpGetOrdenesCompra: () => request<any[]>('/erp/co/ordenes-compra'),
  erpGetOCLines: (id: string) => request<any[]>(`/erp/co/ordenes-compra/${id}/lines`),
  erpCrearOrdenCompra: (data: any) => request<any>('/erp/co/ordenes-compra', { method: 'POST', body: JSON.stringify(data) }),
  erpAprobarOrdenCompra: (id: string) => request<any>(`/erp/co/ordenes-compra/${id}/aprobar`, { method: 'POST' }),
  erpAnularOrdenCompra: (id: string) => request<any>(`/erp/co/ordenes-compra/${id}/anular`, { method: 'POST' }),
  erpGetDocumentosCP: () => request<any[]>('/erp/co/documentos-cp'),
  erpCrearDocumentoCP: (data: any) => request<any>('/erp/co/documentos-cp', { method: 'POST', body: JSON.stringify(data) }),
  erpGetAntiguedadCO: () => request<any[]>('/erp/co/antiguedad'),

  // ── ERP - Pedidos y Presupuestos ──────────────────────
  erpGetPedidos: () => request<any[]>('/erp/pe/pedidos'),
  erpGetPedidoLines: (id: string) => request<any[]>(`/erp/pe/pedidos/${id}/lines`),
  erpCrearPedido: (data: any) => request<any>('/erp/pe/pedidos', { method: 'POST', body: JSON.stringify(data) }),
  erpAprobarPedido: (id: string) => request<any>(`/erp/pe/pedidos/${id}/aprobar`, { method: 'POST' }),
  erpAnularPedido: (id: string) => request<any>(`/erp/pe/pedidos/${id}/anular`, { method: 'POST' }),
  erpGetPresupuestos: () => request<any[]>('/erp/pe/presupuestos'),
  erpCrearPresupuesto: (data: any) => request<any>('/erp/pe/presupuestos', { method: 'POST', body: JSON.stringify(data) }),
  erpAprobarPresupuesto: (id: string) => request<any>(`/erp/pe/presupuestos/${id}/aprobar`, { method: 'POST' }),

  // ── ERP - RRHH / Nomina ──────────────────────────────
  erpGetDepartamentos: () => request<any[]>('/erp/rh/departamentos'),
  erpCrearDepartamento: (data: any) => request<any>('/erp/rh/departamentos', { method: 'POST', body: JSON.stringify(data) }),
  erpGetPuestos: () => request<any[]>('/erp/rh/puestos'),
  erpCrearPuesto: (data: any) => request<any>('/erp/rh/puestos', { method: 'POST', body: JSON.stringify(data) }),
  erpGetEmpleados: () => request<any[]>('/erp/rh/empleados'),
  erpCrearEmpleado: (data: any) => request<any>('/erp/rh/empleados', { method: 'POST', body: JSON.stringify(data) }),
  erpActualizarEmpleado: (id: string, data: any) => request<any>(`/erp/rh/empleados/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  erpEliminarEmpleado: (id: string) => request<any>(`/erp/rh/empleados/${id}`, { method: 'DELETE' }),
  erpGetNominas: () => request<any[]>('/erp/rh/nominas'),
  erpCrearNomina: (data: any) => request<any>('/erp/rh/nominas', { method: 'POST', body: JSON.stringify(data) }),
  erpGetConceptosNomina: () => request<any[]>('/erp/rh/conceptos'),
  erpGetPeriodosNomina: () => request<any[]>('/erp/rh/periodos'),
  erpGetPeriodoNomina: (id: string) => request<any>(`/erp/rh/periodos/${id}`),
  erpCrearPeriodoNomina: (data: any) => request<any>('/erp/rh/periodos', { method: 'POST', body: JSON.stringify(data) }),
  erpProcesarNomina: (periodoId: string) => request<any>(`/erp/rh/periodos/${periodoId}/procesar`, { method: 'POST' }),
  erpPagarNomina: (periodoId: string) => request<any>(`/erp/rh/periodos/${periodoId}/pagar`, { method: 'POST' }),

  // ── CxP Retenciones / Pagos ──────────────────────────
  getFacturaCompra: (id: string) =>
    request<any>(`/cuentas-por-pagar/facturas/${id}`),
  getRetencionesFactura: (facturaId: string) =>
    request<any[]>(`/cuentas-por-pagar/facturas/${facturaId}/retenciones`),
  saveRetencionesFactura: (facturaId: string, retenciones: { retencion_id: string; base_imponible: number; monto_retenido: number }[]) =>
    request<any>(`/cuentas-por-pagar/facturas/${facturaId}/retenciones`, {
      method: 'PUT',
      body: JSON.stringify(retenciones),
    }),
  registrarPago: (data: any) =>
    request<any>('/cuentas-por-pagar/pagos', { method: 'POST', body: JSON.stringify(data) }),

  // ── Salidas de Inventario ──────────────────────────────
  listarSalidasInventario: () => request<SalidaInventarioListadoItem[]>('/inventario/salidas'),
  getSalidaInventario: (id: string) => request<SalidaInventarioResponse>(`/inventario/salidas/${id}`),
  crearSalidaInventario: (data: SalidaInventarioCreate) =>
    request<SalidaInventarioResponse>('/inventario/salidas', { method: 'POST', body: JSON.stringify(data) }),

  // ── Configuracion de Documentos ─────────────────────────
  getConfiguracionDocumentos: () => request<any[]>('/configuracion-documento'),
  actualizarConfigTipoDocumento: (tipoId: string, data: any) =>
    request<any>(`/configuracion-documento/${tipoId}`, { method: 'PUT', body: JSON.stringify(data) }),
  actualizarConfigSubtipoDocumento: (subtipoId: string, data: any) =>
    request<any>(`/configuracion-documento/subtipo/${subtipoId}`, { method: 'PUT', body: JSON.stringify(data) }),
  getSubtiposPorTipo: (tipoCodigo: string) => request<any[]>(`/configuracion-documento/subtipos?tipo_codigo=${tipoCodigo}`),
  crearSubtipoDocumento: (data: any) =>
    request<any>('/configuracion-documento/subtipos', { method: 'POST', body: JSON.stringify(data) }),

  // ── Cargador de Movimientos ──────────────────────────────
  previewCargador: (cuentaBancoId: string, archivo: File) => {
    const form = new FormData()
    form.append('cuenta_banco_id', cuentaBancoId)
    form.append('archivo', archivo)
    return request<any>('/cargador/preview', { method: 'POST', body: form })
  },
  clasificarMovimientos: (data: any) =>
    request<any[]>('/cargador/clasificar', { method: 'POST', body: JSON.stringify(data) }),
  importarMovimientos: (data: any) =>
    request<any>('/cargador/importar', { method: 'POST', body: JSON.stringify(data) }),
  autoMatchConciliacion: (conciliacionId: string) =>
    request<any[]>('/cargador/auto-match', { method: 'POST', body: JSON.stringify({ conciliacion_id: conciliacionId }) }),
  aplicarAutoMatch: (conciliacionId: string, matches: any[]) =>
    request<any>('/cargador/auto-match/aplicar', { method: 'POST', body: JSON.stringify({ conciliacion_id: conciliacionId, matches }) }),
  crearAjusteConciliacion: (data: any) =>
    request<any>('/cargador/ajustes', { method: 'POST', body: JSON.stringify(data) }),
  getMovimientosSinClasificar: (cuentaId?: string) =>
    request<any[]>(`/cargador/movimientos-sin-clasificar${cuentaId ? `?cuenta_id=${cuentaId}` : ''}`),
  vincularPartidaCargador: (data: any) =>
    request<any>('/cargador/vincular-partida', { method: 'POST', body: JSON.stringify(data) }),
}
