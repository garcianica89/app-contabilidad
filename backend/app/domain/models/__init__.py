from app.domain.models.asociaciones import usuario_rol, rol_permiso
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario
from app.domain.models.rol import Rol
from app.domain.models.permiso import Permiso
from app.domain.models.permiso import Permiso, UsuarioPermiso
from app.domain.models.cuenta_contable import CuentaContable
from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.models.producto import Producto
from app.domain.models.factura_venta import FacturaVenta, FacturaVentaLinea
from app.domain.models.factura_compra import FacturaCompra, FacturaCompraLinea
from app.domain.models.orden_compra import OrdenCompra, OrdenCompraLinea
from app.domain.models.cliente import Cliente
from app.domain.models.proveedor import Proveedor
from app.domain.models.caja import Caja, MovimientoCaja, ArqueoCaja
from app.domain.models.banco import CuentaBanco, MovimientoBanco
from app.domain.models.tipo_cuenta_banco import TipoCuentaBanco
from app.domain.models.periodo import PeriodoContable
from app.domain.models.moneda import Moneda
from app.domain.models.categoria import Categoria
from app.domain.models.parametro import Parametro
from app.domain.models.categoria_cliente import CategoriaCliente
from app.domain.models.categoria_proveedor import CategoriaProveedor
from app.domain.models.centro_costo import CentroCosto
from app.domain.models.auditoria import Auditoria
from app.domain.models.tipo_cambio_hist import TipoCambioHist
from app.domain.models.condicion_pago import CondicionPago
from app.domain.models.empleado import Empleado, Cargo

# Nuevos modelos v3.0
from app.domain.models.tercero import Tercero
from app.domain.models.departamento import Departamento
from app.domain.models.sucursal import Sucursal, Bodega
from app.domain.models.unidad_medida import UnidadMedida
from app.domain.models.feature_flag import FeatureFlag
from app.domain.models.document_type import ModuloSistema, DocumentoTipo, DocumentoSubtipo, DocumentoEstado
from app.domain.models.ejercicio import EjercicioFiscal
from app.domain.models.retencion import Retencion
from app.domain.models.conciliacion import ConciliacionBancaria, PartidaConciliacion
from app.domain.models.presupuesto import PresupuestoCabecera, PresupuestoDetalle, PresupuestoEjecucion
from app.domain.models.workflow import WfWorkflow, WfStatus, WfTransition, WfDocumentHistory, WfPendingApproval

# Modelos faltantes (Base)
from app.domain.models.activo_fijo import CategoriaActivo, ActivoFijo, DepreciacionLinea
from app.domain.models.nomina import NominaConfig, NominaPeriodo, NominaDetalle
from app.domain.models.ia import AnalisisIA
from app.domain.models.ocr import DocumentoOCR

# Modelos contables (accounting)
from app.domain.accounting import *
from app.domain.accounting.models import *

# Cheques
from app.domain.models.cheque import Chequera, Cheque, ChequeFormato
