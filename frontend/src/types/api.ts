// ── Auth ─────────────────────────────────────────────────
export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// ── Empresa ───────────────────────────────────────────────
export interface Empresa {
  id: string
  nombre: string
  nombre_legal?: string
  ruc?: string
  direccion?: string
  telefono?: string
  email?: string
  moneda_local_id?: string
  activo: boolean
  created_at: string
}

// ── Usuario ───────────────────────────────────────────────
export interface Usuario {
  id: string
  empresa_id: string
  username: string
  email: string
  nombre_completo: string
  activo: boolean
  ultimo_acceso?: string
  created_at: string
  updated_at?: string
}

// ── Sucursal ──────────────────────────────────────────────
export interface Sucursal {
  id: string
  company_id: string
  codigo: string
  nombre: string
  direccion?: string
  telefono?: string
  is_active: boolean
  created_at: string
}

// ── Bodega ────────────────────────────────────────────────
export interface Bodega {
  id: string
  company_id: string
  sucursal_id?: string
  codigo: string
  nombre: string
  is_active: boolean
  created_at: string
}

// ── Cliente ───────────────────────────────────────────────
export interface Cliente {
  id: string
  empresa_id: string
  codigo?: string
  nombre: string
  ruc?: string
  tipo_documento?: string
  direccion?: string
  telefono?: string
  email?: string
  saldo: number
  limite_credito: number
  plazo_credito?: number
  tipo_fiscal?: string
  sujeto_retenciones?: boolean
  activo: boolean
  created_at: string
}

// ── Proveedor ─────────────────────────────────────────────
export interface Proveedor {
  id: string
  empresa_id: string
  codigo?: string
  nombre: string
  ruc?: string
  direccion?: string
  telefono?: string
  email?: string
  saldo: number
  plazo_credito: number
  aplica_iva: boolean
  tasa_iva: number
  tipo_fiscal: string
  sujeto_retenciones: boolean
  activo: boolean
  retenciones?: { id: string; codigo: string; nombre: string; porcentaje: number; tipo: string }[]
  created_at: string
}

// ── Producto ──────────────────────────────────────────────
export interface Producto {
  id: string
  empresa_id: string
  codigo?: string
  nombre: string
  descripcion?: string
  categoria_id?: string
  unidad_medida: string
  costo_promedio: number
  precio_venta: number
  moneda_id?: string
  aplica_iva: boolean
  cuenta_compra_id?: string
  cuenta_venta_id?: string
  cuenta_inventario_id?: string
  stock_actual: number
  stock_minimo: number
  activo: boolean
  created_at: string
}

// ── Categoria ─────────────────────────────────────────────
export interface Categoria {
  id: string
  empresa_id: string
  nombre: string
  padre_id?: string
  activa: boolean
}

// ── KardexMovimiento ──────────────────────────────────────
export interface KardexMovimiento {
  id: string
  empresa_id: string
  producto_id: string
  fecha: string
  tipo: string
  tipo_documento?: string
  documento_id?: string
  cantidad: number
  costo_unitario: number
  costo_total: number
  saldo_cantidad: number
  saldo_costo_promedio: number
  saldo_total: number
  created_at: string
}

// ── PeriodoContable ───────────────────────────────────────
export interface PeriodoContable {
  id: string
  empresa_id: string
  codigo: string
  nombre?: string
  fecha_inicio: string
  fecha_fin: string
  cerrado: boolean
  cerrado_por?: string
  cerrado_en?: string
  created_at: string
}

// ── CuentaContable ────────────────────────────────────────
export interface CuentaContable {
  id: string
  empresa_id: string
  codigo: string
  nombre: string
  tipo: string
  nivel: number
  padre_id?: string
  acepta_datos: boolean
  moneda_id?: string
  activa: boolean
  indice?: string
  created_at: string
  hijos?: CuentaContable[]
}

// ── Asiento ───────────────────────────────────────────────
export interface Asiento {
  id: string
  empresa_id: string
  numero: string
  fecha: string
  periodo_id: string
  tipo: string
  concepto: string
  journal_type_id?: string
  documento_tipo?: string
  documento_id?: string
  estado: string
  origen_modulo?: string
  origen_documento_id?: string
  creado_por: string
  aprobado_por?: string
  reversado: boolean
  asiento_reversa_id?: string
  created_at: string
  lineas?: AsientoLinea[]
}

export interface AsientoLinea {
  id: string
  asiento_id: string
  cuenta_id: string
  centro_costo_id?: string
  descripcion?: string
  debe: number
  haber: number
  debe_local: number
  haber_local: number
  debe_dolar: number
  haber_dolar: number
  orden: number
}

// ── FacturaVenta (CxC) ────────────────────────────────────
export interface FacturaVenta {
  id: string
  empresa_id: string
  numero: string
  cliente_id: string
  fecha: string
  fecha_vencimiento?: string
  tipo: string
  subtotal: number
  descuento: number
  iva: number
  total: number
  moneda_id: string
  asiento_id?: string
  estado: string
  created_at: string
  aplica_iva?: boolean
  tasa_iva?: number
}

export interface FacturaVentaLinea {
  id: string
  factura_id: string
  producto_id: string
  cantidad: number
  precio_unitario: number
  descuento: number
  subtotal: number
  aplica_iva?: boolean
  tasa_iva?: number
}

// ── OrdenCompra ──────────────────────────────────────────
export interface OrdenCompra {
  id: string
  empresa_id: string
  numero: string
  proveedor_id: string
  proveedor_nombre?: string
  fecha: string
  fecha_entrega?: string
  bodega_id?: string
  condicion_pago_id?: string
  subtotal: number
  descuento: number
  iva: number
  retencion_ir: number
  total: number
  moneda_id: string
  estado: string
  created_at: string
  lineas?: OrdenCompraLinea[]
}

export interface OrdenCompraLinea {
  id: string
  orden_id: string
  producto_id: string
  cantidad: number
  precio_unitario: number
  descuento: number
  aplica_iva?: boolean
  tasa_iva?: number
  subtotal: number
}

// ── FacturaCompra (CxP) ───────────────────────────────────
export interface FacturaCompra {
  id: string
  empresa_id: string
  numero: string
  proveedor_id: string
  orden_id?: string
  fecha: string
  fecha_vencimiento?: string
  subtotal: number
  descuento: number
  iva: number
  retencion_ir: number
  total: number
  moneda_id: string
  asiento_id?: string
  estado: string
  created_at: string
  aplica_iva?: boolean
  tasa_iva?: number
}

export interface FacturaCompraLinea {
  id: string
  factura_id: string
  producto_id: string
  cantidad: number
  precio_unitario: number
  descuento: number
  subtotal: number
  aplica_iva?: boolean
  tasa_iva?: number
}

// ── CuentaBanco ───────────────────────────────────────────
export interface CuentaBanco {
  id: string
  empresa_id: string
  banco: string
  numero_cuenta: string
  tipo: string
  moneda_id: string
  saldo: number
  activa: boolean
  tipo_cuenta_banco_id?: string
  cuenta_contable_id?: string
  created_at: string
}

export interface TipoCuentaBanco {
  id: string
  codigo: string
  nombre: string
  activo: boolean
  created_at: string
}

export interface MovimientoBanco {
  id: string
  empresa_id: string
  cuenta_id: string
  fecha: string
  tipo: string
  numero_documento?: string
  concepto: string
  entrada: number
  salida: number
  saldo: number
  conciliado: boolean
  asiento_id?: string
  origen?: string
  subtipo_id?: string
  numero_subtipo?: number
  created_at: string
}

// ── Caja ──────────────────────────────────────────────────
export interface Caja {
  id: string
  empresa_id: string
  nombre: string
  moneda_id: string
  saldo_actual: number
  activa: boolean
  created_at: string
}

export interface MovimientoCaja {
  id: string
  empresa_id: string
  caja_id: string
  fecha: string
  tipo: string
  concepto: string
  entrada: number
  salida: number
  saldo: number
  referencia_id?: string
  asiento_id?: string
  usuario_id?: string
  created_at: string
}

export interface ArqueoCaja {
  id: string
  empresa_id: string
  caja_id: string
  fecha: string
  saldo_esperado: number
  saldo_real: number
  diferencia: number
  observaciones?: string
  realizado_por: string
  created_at: string
}

// ── Conciliacion Bancaria ─────────────────────────────────
export interface ConciliacionBancaria {
  id: string
  company_id: string
  cuenta_banco_id: string
  periodo_id: string
  fecha_inicio: string
  fecha_fin: string
  saldo_inicial_banco: number
  saldo_final_banco: number
  saldo_inicial_libro: number
  saldo_final_libro: number
  diferencia: number
  estado: string
  creada_por: string
  created_at: string
}

export interface PartidaConciliacion {
  id: string
  conciliacion_id: string
  movimiento_banco_id?: string
  tipo: string
  concepto: string
  referencia?: string
  fecha: string
  monto: number
  conciliado: boolean
  observacion?: string
  created_at: string
}

// ── Activo Fijo ───────────────────────────────────────────
export interface CategoriaActivo {
  id: string
  empresa_id: string
  codigo: string
  nombre: string
  vida_util_default?: number
  metodo_depreciacion_default?: string
  activa: boolean
  created_at: string
}

export interface ActivoFijo {
  id: string
  empresa_id: string
  categoria_id: string
  categoria_nombre?: string
  codigo: string
  nombre: string
  descripcion?: string
  fecha_adquisicion: string
  costo_adquisicion: number
  valor_residual: number
  vida_util_anos: number
  metodo_depreciacion: string
  estado: string
  valor_libros: number
  depreciacion_acumulada: number
  fecha_baja?: string
  motivo_baja?: string
  cuenta_contable_id?: string
  cuenta_depreciacion_gasto_id?: string
  cuenta_depreciacion_acumulada_id?: string
  cuenta_baja_id?: string
  ubicacion?: string
  created_at: string
}

export interface DepreciacionLinea {
  id: string
  activo_id: string
  periodo_id: string
  fecha_depreciacion: string
  monto_depreciacion: number
  depreciacion_acumulada: number
  valor_libros_despues: number
  created_at: string
}

// ── Empleado / RRHH ─────────────────────────────────────
export interface Departamento {
  id: string
  company_id: string
  codigo: string
  nombre: string
  is_active: boolean
  created_at: string
}

export interface Cargo {
  id: string
  empresa_id: string
  codigo: string
  nombre: string
  activo: boolean
  created_at: string
}

export interface Empleado {
  id: string
  empresa_id: string
  departamento_id?: string
  cargo_id?: string
  codigo: string
  nombre: string
  cedula?: string
  fecha_nacimiento?: string
  fecha_contratacion: string
  salario_base: number
  tipo_contrato: string
  estado: string
  direccion?: string
  telefono?: string
  email?: string
  created_at: string
}

// ── Nomina ────────────────────────────────────────────────
export interface NominaConfig {
  id: string
  empresa_id: string
  salario_minimo: number
  inss_patronal_rate: number
  inss_laboral_rate: number
  ir_tramos?: Record<string, unknown>
  aguinaldo_dias: number
}

export interface NominaPeriodo {
  id: string
  empresa_id: string
  codigo: string
  fecha_inicio: string
  fecha_fin: string
  fecha_pago: string
  estado: string
  total_devengado: number
  total_deducciones: number
  total_neto: number
  asiento_id?: string
  created_at: string
  detalles?: NominaDetalle[]
}

export interface NominaDetalle {
  id: string
  nomina_periodo_id: string
  empleado_id: string
  dias_trabajados: number
  salario_base: number
  horas_extra: number
  bonos: number
  comisiones: number
  total_devengado: number
  inss_laboral: number
  ir: number
  otras_deducciones: number
  total_deducciones: number
  neto: number
  created_at: string
}

// ── Presupuesto ───────────────────────────────────────────
export interface Presupuesto {
  id: string
  company_id: string
  codigo: string
  nombre: string
  ejercicio_id: string
  centro_costo_id?: string
  moneda_id: string
  tipo: string
  estado: string
  created_at: string
}

export interface PresupuestoDetalle {
  id: string
  presupuesto_id: string
  cuenta_id: string
  mes_01: number
  mes_02: number
  mes_03: number
  mes_04: number
  mes_05: number
  mes_06: number
  mes_07: number
  mes_08: number
  mes_09: number
  mes_10: number
  mes_11: number
  mes_12: number
  total: number
}

export interface PresupuestoEjecucion {
  id: string
  presupuesto_id: string
  cuenta_id: string
  mes: number
  presupuestado: number
  ejecutado: number
  variacion: number
  porcentaje_ejecucion: number
}

// ── Centro de Costo ───────────────────────────────────────
export interface CentroCosto {
  id: string
  empresa_id: string
  codigo: string
  nombre: string
  padre_id?: string
  activo: boolean
}

// ── Moneda ────────────────────────────────────────────────
export interface Moneda {
  id: string
  codigo: string
  nombre: string
  simbolo: string
  tasa_cambio: number
  es_base: boolean
  activa: boolean
}

// ── TipoCambioHist ────────────────────────────────────────
export interface TipoCambioHist {
  id: string
  empresa_id: string
  moneda_id: string
  fecha: string
  tasa_compra: number
  tasa_venta: number
  created_at: string
}

// ── CondicionPago ─────────────────────────────────────────
export interface CondicionPago {
  id: string
  empresa_id: string
  codigo: string
  nombre: string
  dias_neto: number
  descuento_contado: number
  activa: boolean
  created_at: string
}

// ── Impuesto ──────────────────────────────────────────────
export interface Impuesto {
  id: string
  empresa_id: string
  codigo: string
  nombre: string
  tipo: string
  tasa: number
  cuenta_contable_id?: string
  activo: boolean
}

// ── Parametro ─────────────────────────────────────────────
export interface Parametro {
  id: string
  empresa_id: string
  grupo: string
  clave: string
  valor?: string
  tipo_dato: string
  created_at: string
}

// ── Numeracion ────────────────────────────────────────────
export interface Numeracion {
  id: string
  company_id: string
  sucursal_id?: string
  serie: string
  nombre: string
  tipo_documento: string
  mascara: string
  correlativo_actual: number
  prefijo?: string
  sufijo?: string
  digitos: number
  reinicio: string
  numeracion_manual: boolean
  permite_reserva: boolean
  is_active: boolean
  created_at: string
}

export interface NextCorrelativoResponse {
  numero: string
  correlativo: number
}

// ── TipoAsiento (JournalType) ─────────────────────────────
export interface TipoAsiento {
  id: string
  empresa_id?: string
  codigo: string
  nombre: string
  modulo: string
  naturaleza: string
  activo: boolean
  prefijo?: string
  digitos?: number
  created_at?: string
}

export interface JournalType {
  id: string
  company_id: string
  code: string
  name: string
  module?: string
  nature: string
  affects_inventory: boolean
  affects_receivable: boolean
  affects_payable: boolean
  affects_cash: boolean
  affects_bank: boolean
  requires_approval: boolean
  approval_max_amount?: number
  is_active: boolean
  prefijo: string
  digitos: number
  correlativo_actual: number
  created_at: string
}

// ── Plantillas / JournalTemplate ──────────────────────────
export interface Plantilla {
  id: string
  codigo: string
  nombre: string
  tipo_asiento_id: string
  es_defecto?: boolean
  activo?: boolean
}

export interface PlantillaLinea {
  id: string
  plantilla_id?: string
  orden: number
  cuenta_id: string
  debe: boolean
  formula?: string
  porcentaje?: number
}

export interface JournalTemplate {
  id: string
  journal_type_id: string
  company_id: string
  name: string
  priority: number
  condition_expr?: string
  is_active: boolean
  created_at: string
}

export interface JournalTemplateLine {
  id: string
  template_id: string
  line_order: number
  nature: string
  account_source: string
  account_code?: string
  account_param_concept?: string
  account_context_var?: string
  amount_expression: string
  description_expression?: string
  cost_center_source: string
  cost_center_id?: string
  cost_center_context_var?: string
  condition_expr?: string
  invert_in_banking: boolean
  is_mandatory: boolean
  created_at: string
}

// ── Rol / Permiso ─────────────────────────────────────────
export interface Rol {
  id: string
  empresa_id: string
  nombre: string
  descripcion?: string
  created_at: string
}

export interface Permiso {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  modulo: string
  module_id?: string
  action_type?: string
  scope?: string
}

// ── Workflow ──────────────────────────────────────────────
export interface Workflow {
  id: string
  company_id: string
  documento_tipo_id: string
  codigo: string
  nombre: string
  is_active: boolean
  created_at: string
}

export interface WorkflowStatus {
  id: string
  workflow_id: string
  codigo: string
  nombre: string
  es_inicial: boolean
  es_final: boolean
  requiere_aprobacion: boolean
  requiere_firma: boolean
  notificar_al_entrar: boolean
}

export interface WorkflowTransition {
  id: string
  workflow_id: string
  from_status_id: string
  to_status_id: string
  action_code: string
  nombre: string
  requiere_comentario: boolean
  requiere_aprobacion: boolean
  cantidad_aprobaciones: number
  condition_rule_id?: string
  es_reversion: boolean
  is_active: boolean
}

export interface WfDocumentHistory {
  id: string
  documento_tipo_id: string
  documento_id: string
  from_status_id?: string
  to_status_id: string
  transition_id?: string
  user_id: string
  comentario?: string
  created_at: string
}

export interface WfPendingApproval {
  id: string
  documento_tipo_id: string
  documento_id: string
  transition_id: string
  solicitado_por: string
  aprobado_por?: string
  estado: string
  comentario?: string
  created_at: string
  resolved_at?: string
}

// ── Tercero ───────────────────────────────────────────────
export interface Tercero {
  id: string
  company_id: string
  codigo: string
  tipo_documento: string
  numero_documento: string
  nombre_legal: string
  nombre_comercial?: string
  direccion?: string
  telefono?: string
  email?: string
  ciudad?: string
  pais?: string
  es_cliente: boolean
  es_proveedor: boolean
  es_empleado: boolean
  es_transportista: boolean
  es_banco: boolean
  limite_credito?: number
  condicion_pago_id?: string
  lista_precio?: string
  cobrador_id?: string
  dias_gracia: number
  tipo_proveedor: string
  aplica_iva: boolean
  tasa_iva: number
  plazo_entrega: number
  fecha_nacimiento?: string
  fecha_ingreso?: string
  salario_base?: number
  tipo_contrato?: string
  departamento_id?: string
  is_active: boolean
  created_at: string
}

// ── Retencion ─────────────────────────────────────────────
export interface Retencion {
  id: string
  company_id: string
  codigo: string
  nombre: string
  descripcion?: string
  tipo: string
  porcentaje: number
  aplica_a: string
  monto_minimo?: number
  base_imponible: string
  prioridad: number
  redondeo: number
  naturaleza: string
  cuenta_retencion_id?: string
  cuenta_pagar_id?: string
  cuenta_cobrar_id?: string
  centro_costo_id?: string
  vigencia_desde: string
  vigencia_hasta?: string
  is_active: boolean
  created_at: string
}

// ── OCR / IA ──────────────────────────────────────────────
export interface DocumentoOCR {
  id: string
  empresa_id: string
  filename: string
  content_type: string
  file_size: number
  estado: string
  texto_extraido?: string
  datos_procesados?: Record<string, unknown>
  created_at: string
}

export interface AnalisisIA {
  id: string
  empresa_id: string
  tipo: string
  modulo?: string
  titulo: string
  descripcion?: string
  datos_entrada?: Record<string, unknown>
  resultado?: Record<string, unknown>
  created_at: string
}

// ── Modulo Sistema / DocumentoTipo ────────────────────────
export interface ModuloSistema {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  icono?: string
  orden: number
  is_active: boolean
}

export interface DocumentoTipo {
  id: string
  company_id: string
  modulo_id: string
  codigo: string
  nombre: string
  nombre_corto?: string
  genera_asiento: boolean
  afecta_inventario: boolean
  afecta_cxc: boolean
  afecta_cxp: boolean
  afecta_bancos: boolean
  workflow_id?: string
  is_active: boolean
  created_at: string
}

export interface DocumentoSubtipo {
  id: string
  company_id: string
  documento_tipo_id: string
  codigo: string
  nombre: string
  nombre_corto?: string
  numeracion_id?: string
  accounting_event_id?: string
  genera_asiento: boolean
  afecta_inventario: boolean
  afecta_cxc: boolean
  afecta_cxp: boolean
  afecta_bancos: boolean
  afecta_saldo: boolean
  permite_saldo_negativo: boolean
  permite_reversion: boolean
  max_dias_reversion?: number
  requiere_aprobacion: boolean
  cantidad_aprobaciones: number
  workflow_id?: string
  validation_rule_id?: string
  journal_type_id?: string
  journal_template_id?: string
  cuenta_principal_id?: string
  cuenta_contrapartida_id?: string
  cuenta_impuestos_id?: string
  cuenta_descuentos_id?: string
  cuenta_intereses_id?: string
  cuenta_retencion_id?: string
  cuenta_retencion_iva_id?: string
  cuenta_retencion_ir_id?: string
  cuenta_mora_id?: string
  cuenta_puente_id?: string
  cost_center_default_id?: string
  is_active: boolean
  observaciones?: string
  created_at: string
}

// ── Ejercicio Fiscal ──────────────────────────────────────
export interface EjercicioFiscal {
  id: string
  company_id: string
  codigo: string
  nombre: string
  fecha_inicio: string
  fecha_fin: string
  cerrado: boolean
  created_at: string
}

// ── Cierre Mensual / Fiscal ───────────────────────────────
export interface CierreMensual {
  id: string
  empresa_id: string
  periodo_id: string
  estado: string
  cerrado_por?: string
  cerrado_en?: string
  reabierto_por?: string
  reabierto_en?: string
  observaciones?: string
  created_at: string
}

export interface CierreFiscal {
  id: string
  empresa_id: string
  ejercicio_id: string
  estado: string
  resultado_ejercicio?: number
  cuenta_resultado_id?: string
  cuenta_utilidad_id?: string
  asiento_cierre_id?: string
  asiento_apertura_id?: string
  cerrado_por?: string
  cerrado_en?: string
  observaciones?: string
  created_at: string
}

// ── Auditoria ─────────────────────────────────────────────
export interface Auditoria {
  id: string
  usuario_id?: string
  empresa_id?: string
  tabla: string
  registro_id: string
  accion: string
  valor_anterior?: Record<string, unknown>
  valor_nuevo?: Record<string, unknown>
  direccion_ip?: string
  user_agent?: string
  created_at: string
}

// ── UnidadMedida ──────────────────────────────────────────
export interface UnidadMedida {
  id: string
  company_id: string
  codigo: string
  nombre: string
  is_active: boolean
  created_at: string
}

// ── FeatureFlag ───────────────────────────────────────────
export interface FeatureFlag {
  id: string
  company_id: string
  codigo: string
  nombre: string
  descripcion?: string
  activo: boolean
  created_at: string
}

// ── Accounting / New Schema ──────────────────────────────
export interface Account {
  id: string
  company_id: string
  parent_id?: string
  code: string
  name: string
  level: number
  account_type_id: string
  accepts_entries: boolean
  is_control_account: boolean
  is_auxiliary: boolean
  currency_id?: string
  requires_cost_center: boolean
  requires_dimension_2: boolean
  requires_dimension_3: boolean
  financial_classification_id?: string
  tax_classification_id?: string
  ifrs_classification_id?: string
  is_active: boolean
  valid_from?: string
  valid_to?: string
  observations?: string
  created_at: string
  updated_at?: string
}

export interface AccountType {
  id: string
  code: string
  name: string
  nature: string
  financial_statement?: string
  display_order: number
  is_system: boolean
}

export interface AccountingEvent {
  id: string
  company_id: string
  code: string
  name: string
  module: string
  journal_type_resolution: string
  journal_type_id?: string
  journal_type_rule_id?: string
  journal_type_param_key?: string
  requires_approval: boolean
  is_active: boolean
  observaciones?: string
  created_at: string
}

export interface AccountingRule {
  id: string
  company_id: string
  code: string
  name: string
  description?: string
  module?: string
  priority: number
  rule_type: string
  condition_expression: string
  action_type: string
  action_config?: Record<string, unknown>
  error_message?: string
  is_active: boolean
  created_at: string
}

// ── Dashboard ─────────────────────────────────────────────
export interface DashboardKPI {
  ventas_totales: number
  gastos_totales: number
  utilidad_neta: number
  margen: number
  saldo_caja: number
  cxc_pendiente: number
  cxp_pendiente: number
  inventario_valor: number
  inventario_items: number
  clientes_activos: number
}

export interface DashboardVentasMes {
  mes: string
  ventas: number
}

export interface DashboardIngresosVsGastos {
  mes: string
  ingresos: number
  gastos: number
}

export interface DashboardTopCliente {
  nombre: string
  total: number
}

export interface DashboardAntiguedadCxC {
  nombre: string
  mas_90: number
  entre_60_90: number
  entre_30_60: number
  entre_0_30: number
  saldo_total: number
}

export interface DashboardUltimoMovimiento {
  fecha: string
  concepto: string
  tipo: string
  entrada: number
  salida: number
}

export interface DashboardResponse {
  kpis: DashboardKPI
  ventas_por_mes: DashboardVentasMes[]
  ingresos_vs_gastos: DashboardIngresosVsGastos[]
  gastos_por_categoria: unknown[]
  top_clientes: DashboardTopCliente[]
  antiguedad_cxc: DashboardAntiguedadCxC[]
  ultimos_movimientos: DashboardUltimoMovimiento[]
}

// ── Reportes ──────────────────────────────────────────────
export interface BalanceComprobacionRow {
  cuenta_id: string
  codigo: string
  nombre: string
  nivel: number
  naturaleza: string
  tipo: string
  padre_id: string | null
  saldo_anterior: number
  debe: number
  haber: number
  saldo_final: number
  saldo_deudor: number
  saldo_acreedor: number
}

export interface BalanceGeneralResponse {
  activo: { total: number; cuentas: unknown[] }
  pasivo: { total: number; cuentas: unknown[] }
  patrimonio: { total: number; cuentas: unknown[] }
  total_activo: number
  total_pasivo_patrimonio: number
}

export interface EstadoResultadosResponse {
  ventas: number
  costo_ventas: number
  utilidad_bruta: number
  gastos_operativos: number
  utilidad_operativa: number
  otros_ingresos: number
  otros_gastos: number
  utilidad_neta: number
}

export interface FlujoEfectivoResponse {
  operativo: { ingresos: number; egresos: number; neto: number }
  inversion: { ingresos: number; egresos: number; neto: number }
  financiamiento: { ingresos: number; egresos: number; neto: number }
  saldo_inicial: number
  saldo_final: number
  variacion_neta: number
}

// ── Salidas de Inventario ────────────────────────────────
export interface SalidaInventarioLinea {
  producto_id: string
  cantidad: number
}

export interface SalidaInventarioCreate {
  fecha: string
  subtype_code: string
  bodega_id: string
  motivo: string
  lineas: SalidaInventarioLinea[]
}

export interface SalidaInventarioResponse {
  success: boolean
  documento_id?: string
  numero?: string
  estado?: string
  asiento_id?: string
  asiento_numero?: string
  errors: string[]
}

export interface SalidaInventarioListadoItem {
  id: string
  fecha?: string
  numero: string
  concepto: string
  documento_id: string
  asiento_id?: string
  created_at: string
}

// ── CxP Retenciones / Pago ─────────────────────────────
export interface RetencionFacturaItem {
  retencion_id: string
  retencion_codigo: string
  retencion_nombre: string
  tipo: string
  porcentaje: number
  naturaleza: string
  cuenta_retencion_id: string | null
  base_imponible_calculada: number
  monto_retenido: number
  is_override: boolean
}

export interface PagoRequest {
  factura_compra_id: string
  monto: number
  fecha: string
  metodo_pago: string
  cuenta_banco_id?: string
  concepto?: string
  retenciones?: { retencion_id: string; base_imponible: number; monto_retenido: number }[]
}

export interface PagoResponse {
  factura_id: string
  asiento_id: string
  numero_asiento: string
  movimiento_banco_id: string | null
  monto_pagado: number
  total_retenido: number
}

export interface CobroResponse {
  factura_id: string
  asiento_id: string
  numero_asiento: string
  movimiento_banco_id: string | null
  monto_cobrado: number
  total_retenido: number
}

// ── Antiguedad ────────────────────────────────────────────
export interface AntiguedadRow {
  cliente_id?: string
  proveedor_id?: string
  nombre: string
  facturas: number
  saldo_total: number
  vencido: number
  por_vencer: number
  rango_0_30: number
  rango_31_60: number
  rango_61_90: number
  rango_91_mas: number
}
