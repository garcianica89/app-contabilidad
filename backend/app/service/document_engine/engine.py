"""
Document Engine — Motor Central de Documentos.

CADA documento del ERP pasa por este motor.
NINGUN modulo procesa documentos directamente.
NINGUN modulo crea asientos directamente.

Pipeline:
  1.  Validate        → Schema + reglas de negocio
  2.  Pre-process     → Defaults, valores derivados
  3.  Numerar         → NumeracionEngine.asignar()
  4.  Workflow        → WorkflowEngine.transicionar()
  5.  Rules           → RuleEngine.evaluar()
  6.  Accounting      → AccountingEngine.generar_asiento() (si corresponde)
  7.  Inventory       → KardexService.registrar() (si corresponde)
  8.  CxC/CxP         → SaldoService.actualizar() (si corresponde)
  9.  Post-process    → Auditoria, notificaciones
  10. Return          → DocumentResult
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.producto import Producto


@dataclass
class DocumentAction:
    """Accion ejecutada sobre un documento."""
    action: str           # 'CREATE', 'UPDATE', 'APPROVE', 'REJECT', 'REVERSE', 'ANULAR'
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: uuid.UUID = None
    comment: str = ""


@dataclass
class DocumentResult:
    """Resultado del procesamiento de un documento."""
    success: bool
    document_type: str
    document_id: Optional[uuid.UUID] = None
    numero: Optional[str] = None
    estado: Optional[str] = None
    asiento_id: Optional[uuid.UUID] = None
    asiento_numero: Optional[str] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentEngine:
    """
    Pipeline central de procesamiento de documentos.

    Uso:
        engine = DocumentEngine(db)
        result = await engine.process(
            document_type='FAC',
            subtype_code='FAC_CONTADO',
            action='CREATE',
            data={...},
            user_id=...,
            company_id=...
        )
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._errors: list[str] = []
        self._warnings: list[str] = []

    async def process(
        self,
        document_type: str,
        subtype_code: str,
        action: str,
        data: dict[str, Any],
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        document_id: Optional[uuid.UUID] = None,
    ) -> DocumentResult:
        """
        Procesa un documento a traves del pipeline completo.
        """
        doc_action = DocumentAction(action=action, user_id=user_id)
        ctx = DocumentContext(
            document_type=document_type,
            subtype_code=subtype_code,
            action=action,
            data=data,
            user_id=user_id,
            company_id=company_id,
            document_id=document_id or uuid.uuid4(),
        )

        try:
            # 1. Validate
            await self._validate(ctx)
            if self._errors:
                return self._error_result(ctx)

            # 2. Pre-process (defaults, derived values)
            await self._pre_process(ctx)

            # 3. Numeracion
            if action in ('CREATE',):
                numero = await self._assign_number(ctx, company_id)
                ctx.data['numero'] = numero
                ctx.numero = numero

            # 4. Workflow transition
            estado = await self._execute_workflow(ctx)
            ctx.estado = estado

            # 5. Business rules
            await self._execute_rules(ctx)

            # 6. Accounting (if applicable)
            if self._generates_accounting(ctx):
                asiento = await self._generate_entry(ctx)
                if asiento:
                    ctx.asiento_id = asiento.get('asiento_id')
                    ctx.asiento_numero = asiento.get('numero_asiento')

            # 7. Inventory (if applicable)
            if self._affects_inventory(ctx):
                await self._update_inventory(ctx)

            # 8. CxC/CxP (if applicable)
            if self._affects_cxc(ctx):
                await self._update_cxc(ctx)
            if self._affects_cxp(ctx):
                await self._update_cxp(ctx)

            # 9. Post-process: audit trail
            await self._audit_log(ctx)

            return DocumentResult(
                success=True,
                document_type=document_type,
                document_id=ctx.document_id,
                numero=ctx.numero,
                estado=ctx.estado,
                asiento_id=ctx.asiento_id,
                asiento_numero=ctx.asiento_numero,
                warnings=self._warnings,
            )

        except Exception as e:
            self._errors.append(str(e))
            return self._error_result(ctx)

    async def _validate(self, ctx: 'DocumentContext'):
        """Validaciones de esquema y negocio."""
        if not ctx.data:
            self._errors.append("Document data is required")

    async def _pre_process(self, ctx: 'DocumentContext'):
        """Valores por defecto y calculos derivados."""
        now = datetime.now()
        if 'fecha' not in ctx.data:
            ctx.data['fecha'] = now.date().isoformat()
        if 'moneda_id' not in ctx.data:
            ctx.data['moneda_id'] = str(ctx.company_id)  # will resolve properly

    async def _assign_number(self, ctx: 'DocumentContext', company_id: uuid.UUID) -> Optional[str]:
        """Asigna numero usando NumeracionEngine."""
        from app.service.numeracion_service import NumeracionService
        service = NumeracionService(self.db)
        try:
            result = await service.get_next(
                company_id=company_id,
                document_type=ctx.document_type,
                subtype_code=ctx.subtype_code,
            )
            if result:
                return result.get('numero')
        except Exception as e:
            self._warnings.append(f"Could not assign number: {e}")
        return None

    async def _execute_workflow(self, ctx: 'DocumentContext') -> Optional[str]:
        """Ejecuta transicion de workflow."""
        from app.service.workflow_engine import WorkflowEngine
        engine = WorkflowEngine(self.db)
        return await engine.transition(
            document_type=ctx.document_type,
            action=ctx.action,
            company_id=ctx.company_id,
        )

    async def _execute_rules(self, ctx: 'DocumentContext'):
        """Evalua reglas de negocio."""
        from app.service.rule_engine import RuleEngine
        engine = RuleEngine(self.db)
        results = await engine.evaluate(
            module=self._get_module(ctx.document_type),
            document_type=ctx.document_type,
            action=ctx.action,
            context=ctx.data,
            company_id=ctx.company_id,
        )
        if results.get('blocks'):
            self._errors.extend(results['blocks'])
        if results.get('warnings'):
            self._warnings.extend(results['warnings'])

    def _generates_accounting(self, ctx: 'DocumentContext') -> bool:
        """Determina si el documento genera asiento contable."""
        return ctx.data.get('genera_asiento', True)

    async def _generate_entry(self, ctx: 'DocumentContext') -> Optional[dict]:
        """Genera asiento contable via AccountingEngine."""
        from app.service.asiento_service import AccountingEngine
        engine = AccountingEngine(self.db)
        return await engine.generate_from_document(ctx)

    def _affects_inventory(self, ctx: 'DocumentContext') -> bool:
        return ctx.data.get('afecta_inventario', False)

    async def _update_inventory(self, ctx: 'DocumentContext'):
        """Actualiza inventario / kardex."""
        from app.service.inventario_service import InventarioService
        service = InventarioService(self.db)
        await service.registrar_movimiento(ctx)
        lineas = ctx.data.get('lineas', [])
        doc_type = ctx.document_type
        for l in lineas:
            producto_id = uuid.UUID(l['producto_id']) if isinstance(l['producto_id'], str) else l['producto_id']
            cantidad = Decimal(str(l['cantidad']))
            precio = Decimal(str(l.get('precio_unitario', 0)))
            producto = await self.db.get(Producto, producto_id)
            if not producto:
                continue
            if doc_type in ('FAC', 'FACTURA', 'NCR'):
                producto.stock_actual -= cantidad
                producto.stock_valorado -= cantidad * (producto.costo_promedio or 0)
            elif doc_type in ('COMPRA', 'OC', 'ENTRADA'):
                costo_total_anterior = (producto.costo_promedio or 0) * producto.stock_actual
                costo_nueva = cantidad * precio
                cantidad_total = producto.stock_actual + cantidad
                if cantidad_total > 0:
                    producto.costo_promedio = (costo_total_anterior + costo_nueva) / cantidad_total
                producto.stock_actual += cantidad

    def _affects_cxc(self, ctx: 'DocumentContext') -> bool:
        return ctx.data.get('afecta_cxc', False)

    async def _update_cxc(self, ctx: 'DocumentContext'):
        """Actualiza saldos de Cuentas por Cobrar."""
        if not ctx.data.get('cliente_id') and not ctx.data.get('tercero_id'):
            return
        from app.domain.models.factura_venta import FacturaVenta, FacturaVentaLinea
        from app.domain.models.caja import MovimientoCaja
        total = Decimal(str(ctx.data.get('total', 0)))
        if total == 0:
            return
        factura = FacturaVenta(
            empresa_id=ctx.company_id,
            numero=ctx.data.get('numero', ''),
            cliente_id=ctx.data.get('cliente_id', ctx.data.get('tercero_id')),
            fecha=datetime.strptime(ctx.data.get('fecha', ''), '%Y-%m-%d').date() if ctx.data.get('fecha') else datetime.now().date(),
            fecha_vencimiento=datetime.strptime(ctx.data.get('fecha_vencimiento', ''), '%Y-%m-%d').date() if ctx.data.get('fecha_vencimiento') else None,
            tipo=ctx.data.get('tipo_pago', 'CREDITO'),
            subtotal=Decimal(str(ctx.data.get('subtotal', total))),
            descuento=Decimal(str(ctx.data.get('descuento', 0))),
            iva=Decimal(str(ctx.data.get('iva', 0))),
            total=total,
            moneda_id=ctx.data.get('moneda_id'),
            estado=ctx.estado or 'EMITIDA',
            asiento_id=ctx.asiento_id,
        )
        self.db.add(factura)
        await self.db.flush()

        lineas = ctx.data.get('lineas', [])
        for l in lineas:
            linea = FacturaVentaLinea(
                factura_id=factura.id,
                producto_id=l['producto_id'],
                cantidad=Decimal(str(l['cantidad'])),
                precio_unitario=Decimal(str(l['precio_unitario'])),
                descuento=Decimal(str(l.get('descuento', 0))),
                subtotal=Decimal(str(l['cantidad'])) * Decimal(str(l['precio_unitario'])),
            )
            self.db.add(linea)

        if ctx.data.get('tipo_pago') == 'CONTADO':
            caja_r = await self.db.execute(
                text("""
                SELECT id FROM (
                    SELECT id FROM caja WHERE empresa_id = :eid AND activa = TRUE LIMIT 1
                ) sub
                """),
                {'eid': ctx.company_id},
            )
            caja_id = caja_r.scalar_one_or_none()
            if caja_id:
                mov = MovimientoCaja(
                    empresa_id=ctx.company_id,
                    caja_id=caja_id,
                    fecha=factura.fecha,
                    tipo='FACTURA',
                    concepto=f'Cobro factura {factura.numero}',
                    entrada=total,
                    salida=0,
                    saldo=total,
                    referencia_id=factura.id,
                    asiento_id=ctx.asiento_id,
                )
                self.db.add(mov)
            factura.estado = 'COBRADA'

        ctx.data['factura_cxc_id'] = str(factura.id)

    def _affects_cxp(self, ctx: 'DocumentContext') -> bool:
        return ctx.data.get('afecta_cxp', False)

    async def _update_cxp(self, ctx: 'DocumentContext'):
        """Actualiza saldos de Cuentas por Pagar."""
        if not ctx.data.get('proveedor_id') and not ctx.data.get('tercero_id'):
            return
        from app.domain.models.factura_compra import FacturaCompra, FacturaCompraLinea
        total = Decimal(str(ctx.data.get('total', 0)))
        if total == 0:
            return
        factura = FacturaCompra(
            empresa_id=ctx.company_id,
            numero=ctx.data.get('numero', ''),
            proveedor_id=ctx.data.get('proveedor_id', ctx.data.get('tercero_id')),
            orden_id=ctx.data.get('orden_id'),
            fecha=datetime.strptime(ctx.data.get('fecha', ''), '%Y-%m-%d').date() if ctx.data.get('fecha') else datetime.now().date(),
            fecha_vencimiento=datetime.strptime(ctx.data.get('fecha_vencimiento', ''), '%Y-%m-%d').date() if ctx.data.get('fecha_vencimiento') else None,
            subtotal=Decimal(str(ctx.data.get('subtotal', total))),
            descuento=Decimal(str(ctx.data.get('descuento', 0))),
            iva=Decimal(str(ctx.data.get('iva', 0))),
            retencion_ir=Decimal(str(ctx.data.get('retencion_ir', 0))),
            total=total,
            moneda_id=ctx.data.get('moneda_id'),
            estado=ctx.estado or 'PENDIENTE',
            asiento_id=ctx.asiento_id,
        )
        self.db.add(factura)
        await self.db.flush()

        lineas = ctx.data.get('lineas', [])
        for l in lineas:
            linea = FacturaCompraLinea(
                factura_id=factura.id,
                producto_id=l['producto_id'],
                cantidad=Decimal(str(l['cantidad'])),
                precio_unitario=Decimal(str(l['precio_unitario'])),
                descuento=Decimal(str(l.get('descuento', 0))),
                subtotal=Decimal(str(l['cantidad'])) * Decimal(str(l['precio_unitario'])),
            )
            self.db.add(linea)

        ctx.data['factura_cxp_id'] = str(factura.id)

    async def _audit_log(self, ctx: 'DocumentContext'):
        """Registra auditoria."""
        from app.service.auditoria_service import AuditoriaService
        service = AuditoriaService(self.db)
        await service.registrar(
            usuario_id=ctx.user_id,
            company_id=ctx.company_id,
            documento_tipo=ctx.document_type,
            documento_id=ctx.document_id,
            accion=ctx.action,
            data=ctx.data,
        )

    def _get_module(self, document_type: str) -> str:
        """Resuelve modulo desde tipo de documento."""
        MODULE_MAP = {
            'FAC': 'facturacion', 'NCR': 'facturacion', 'NDB': 'facturacion',
            'OC': 'compras', 'RECEPCION': 'compras',
            'DEBITO': 'bancos', 'CREDITO': 'bancos', 'CHEQUE': 'bancos', 'TRANSFERENCIA': 'bancos',
            'COBRO': 'cxc', 'PAGO': 'cxp', 'RETENCION': 'cxp',
            'ENTRADA': 'inventario', 'SALIDA': 'inventario', 'AJUSTE': 'inventario', 'TRASLADO': 'inventario',
            'DEPRECIACION': 'activos_fijos',
            'NOMINA': 'nomina',
            'PRESUPUESTO': 'presupuestos',
        }
        return MODULE_MAP.get(document_type, 'admin')

    def _error_result(self, ctx: 'DocumentContext') -> DocumentResult:
        return DocumentResult(
            success=False,
            document_type=ctx.document_type,
            document_id=ctx.document_id,
            errors=self._errors,
            warnings=self._warnings,
        )


class DocumentContext:
    """Contexto de procesamiento de un documento."""

    def __init__(
        self,
        document_type: str,
        subtype_code: str,
        action: str,
        data: dict,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        document_id: uuid.UUID,
    ):
        self.document_type = document_type
        self.subtype_code = subtype_code
        self.action = action
        self.data = data
        self.user_id = user_id
        self.company_id = company_id
        self.document_id = document_id
        self.numero: Optional[str] = None
        self.estado: Optional[str] = None
        self.asiento_id: Optional[uuid.UUID] = None
        self.asiento_numero: Optional[str] = None
