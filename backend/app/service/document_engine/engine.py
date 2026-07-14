"""
Document Engine — Motor Central de Documentos.

CADA documento del ERP pasa por este motor.
NINGUN modulo procesa documentos directamente.
NINGUN modulo crea asientos directamente.

Pipeline:
  1.  Validate        → Schema + reglas de negocio
  2.  LoadConfig      → Lee config desde DocumentoTipo/Subtipo (BD)
  3.  Pre-process     → Defaults, valores derivados
  4.  Numerar         → NumeracionEngine.asignar()
  5.  Workflow        → WorkflowEngine.transicionar()
  6.  Rules           → RuleEngine.evaluar()
  7.  Accounting      → AccountingEngine.generar_asiento() (si genera_asiento)
  8.  Cost of Sale   → Asiento de costo de venta (si genera_costo_venta)
  9.  Inventory       → KardexService.registrar() (si afecta_inventario)
  10. CxC/CxP         → SaldoService.actualizar() (si afecta_cxc/cxp)
  11. Post-process    → Auditoria, notificaciones
  12. Return          → DocumentResult
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.producto import Producto


@dataclass
class DocumentAction:
    """Accion ejecutada sobre un documento."""
    action: str
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
    asiento_costo_id: Optional[uuid.UUID] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentConfig:
    """Configuracion de comportamiento resuelta desde DB + overrides."""
    genera_asiento: bool = True
    afecta_inventario: bool = False
    afecta_cxc: bool = False
    afecta_cxp: bool = False
    afecta_bancos: bool = False
    afecta_saldo: bool = True
    calcula_iva: bool = True
    aplica_retenciones: bool = False
    genera_costo_venta: bool = False
    requiere_centros_costo: bool = False

    documento_tipo_id: Optional[uuid.UUID] = None
    documento_subtipo_id: Optional[uuid.UUID] = None
    journal_type_id: Optional[uuid.UUID] = None
    journal_template_id: Optional[uuid.UUID] = None
    cuenta_costo_venta_id: Optional[uuid.UUID] = None
    cuenta_descuentos_id: Optional[uuid.UUID] = None
    cost_center_default_id: Optional[uuid.UUID] = None


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
        self._config: Optional[DocumentConfig] = None

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

            # 2. Load config from DB (DocumentoTipo / DocumentoSubtipo)
            await self._load_config(ctx)

            # 3. Pre-process (defaults, derived values)
            await self._pre_process(ctx)

            # 4. Numeracion
            if action in ('CREATE',):
                numero = await self._assign_number(ctx, company_id)
                ctx.data['numero'] = numero or f"SYS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                ctx.numero = ctx.data['numero']

            # 5. Workflow transition
            estado = await self._execute_workflow(ctx)
            ctx.estado = estado

            # 6. Business rules
            await self._execute_rules(ctx)

            # 7. Accounting entry (if configured)
            if self._generates_accounting(ctx):
                asiento = await self._generate_entry(ctx)
                if asiento:
                    ctx.asiento_id = asiento.get('asiento_id')
                    ctx.asiento_numero = asiento.get('numero_asiento')

            # 8. Cost of sale entry (if configured)
            if self._generates_costo_venta(ctx):
                asiento_costo = await self._generate_costo_venta(ctx)
                if asiento_costo:
                    ctx.asiento_costo_id = asiento_costo.get('asiento_id')

            # 9. Inventory (if configured)
            if self._affects_inventory(ctx):
                await self._update_inventory(ctx)

            # 10. CxC/CxP (if configured)
            if self._affects_cxc(ctx):
                await self._update_cxc(ctx)
            if self._affects_cxp(ctx):
                await self._update_cxp(ctx)

            # 11. Banking (cobros/pagos)
            if self._affects_banking(ctx):
                await self._update_banking(ctx)

            # 12. Post-process: audit trail
            await self._audit_log(ctx)

            return DocumentResult(
                success=True,
                document_type=document_type,
                document_id=ctx.document_id,
                numero=ctx.numero,
                estado=ctx.estado,
                asiento_id=ctx.asiento_id,
                asiento_numero=ctx.asiento_numero,
                asiento_costo_id=ctx.asiento_costo_id,
                warnings=self._warnings,
            )

        except Exception as e:
            self._errors.append(str(e))
            return self._error_result(ctx)

    async def _load_config(self, ctx: 'DocumentContext'):
        """Carga configuracion desde DocumentoTipo y DocumentoSubtipo en BD."""
        from app.domain.models.document_type import DocumentoTipo, DocumentoSubtipo

        # Buscar DocumentoTipo por codigo + company_id
        tipo_result = await self.db.execute(
            select(DocumentoTipo).where(
                DocumentoTipo.codigo == ctx.document_type,
                DocumentoTipo.company_id == ctx.company_id,
            )
        )
        doc_tipo = tipo_result.scalar_one_or_none()

        sub_tipo = None
        if doc_tipo and ctx.subtype_code:
            sub_result = await self.db.execute(
                select(DocumentoSubtipo).where(
                    DocumentoSubtipo.documento_tipo_id == doc_tipo.id,
                    DocumentoSubtipo.codigo == ctx.subtype_code,
                    DocumentoSubtipo.company_id == ctx.company_id,
                )
            )
            sub_tipo = sub_result.scalar_one_or_none()

        config = DocumentConfig()

        if doc_tipo:
            config.documento_tipo_id = doc_tipo.id
            config.genera_asiento = doc_tipo.genera_asiento
            config.afecta_inventario = doc_tipo.afecta_inventario
            config.afecta_cxc = doc_tipo.afecta_cxc
            config.afecta_cxp = doc_tipo.afecta_cxp
            config.afecta_bancos = doc_tipo.afecta_bancos

        if sub_tipo:
            config.documento_subtipo_id = sub_tipo.id
            config.genera_asiento = sub_tipo.genera_asiento
            config.afecta_inventario = sub_tipo.afecta_inventario
            config.afecta_cxc = sub_tipo.afecta_cxc
            config.afecta_cxp = sub_tipo.afecta_cxp
            config.afecta_bancos = sub_tipo.afecta_bancos
            config.afecta_saldo = sub_tipo.afecta_saldo
            config.calcula_iva = sub_tipo.calcula_iva
            config.aplica_retenciones = sub_tipo.aplica_retenciones
            config.genera_costo_venta = sub_tipo.genera_costo_venta
            config.requiere_centros_costo = sub_tipo.requiere_centros_costo
            config.journal_type_id = sub_tipo.journal_type_id
            config.journal_template_id = sub_tipo.journal_template_id
            config.cuenta_costo_venta_id = sub_tipo.cuenta_costo_venta_id
            config.cuenta_descuentos_id = sub_tipo.cuenta_descuentos_id
            config.cost_center_default_id = sub_tipo.cost_center_default_id

        # Permitir override via ctx.data (document-level flexibility)
        for flag in ('genera_asiento', 'afecta_inventario', 'afecta_cxc',
                     'afecta_cxp', 'afecta_bancos', 'calcula_iva',
                     'aplica_retenciones', 'genera_costo_venta', 'requiere_centros_costo'):
            if flag in ctx.data:
                setattr(config, flag, bool(ctx.data[flag]))

        self._config = config

    async def _validate(self, ctx: 'DocumentContext'):
        if not ctx.data:
            self._errors.append("Document data is required")

    async def _pre_process(self, ctx: 'DocumentContext'):
        now = datetime.now()
        if 'fecha' not in ctx.data:
            ctx.data['fecha'] = now.date().isoformat()
        if 'moneda_id' not in ctx.data:
            ctx.data['moneda_id'] = str(ctx.company_id)

    async def _assign_number(self, ctx: 'DocumentContext', company_id: uuid.UUID) -> Optional[str]:
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
        from app.service.workflow_engine import WorkflowEngine
        engine = WorkflowEngine(self.db)
        return await engine.transition(
            document_type=ctx.document_type,
            action=ctx.action,
            company_id=ctx.company_id,
        )

    async def _execute_rules(self, ctx: 'DocumentContext'):
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

    # ── Configuration checks ──────────────────────────────────────

    def _generates_accounting(self, ctx: 'DocumentContext') -> bool:
        return self._config.genera_asiento if self._config else ctx.data.get('genera_asiento', True)

    def _generates_costo_venta(self, ctx: 'DocumentContext') -> bool:
        return self._config.genera_costo_venta if self._config else ctx.data.get('genera_costo_venta', False)

    def _affects_inventory(self, ctx: 'DocumentContext') -> bool:
        return self._config.afecta_inventario if self._config else ctx.data.get('afecta_inventario', False)

    def _affects_cxc(self, ctx: 'DocumentContext') -> bool:
        return self._config.afecta_cxc if self._config else ctx.data.get('afecta_cxc', False)

    def _affects_cxp(self, ctx: 'DocumentContext') -> bool:
        return self._config.afecta_cxp if self._config else ctx.data.get('afecta_cxp', False)

    def _affects_banking(self, ctx: 'DocumentContext') -> bool:
        return self._config.afecta_bancos if self._config else ctx.data.get('afecta_bancos', False)

    def _calculates_iva(self, ctx: 'DocumentContext') -> bool:
        return self._config.calcula_iva if self._config else ctx.data.get('calcula_iva', True)

    # ── Accounting ────────────────────────────────────────────────

    async def _generate_entry(self, ctx: 'DocumentContext') -> Optional[dict]:
        from app.service.accounting.accounting_engine import AccountingEngine
        engine = AccountingEngine(self.db)
        return await engine.generate_from_document(ctx)

    async def _generate_costo_venta(self, ctx: 'DocumentContext') -> Optional[dict]:
        """Genera asiento de costo de venta mediante AccountingEngine."""
        from app.service.accounting.accounting_engine import AccountingEngine
        engine = AccountingEngine(self.db)

        costo_total = Decimal('0')
        lineas = ctx.data.get('lineas', [])
        for l in lineas:
            producto_id = uuid.UUID(l['producto_id']) if isinstance(l['producto_id'], str) else l['producto_id']
            producto = await self.db.get(Producto, producto_id)
            if not producto:
                continue
            cantidad = Decimal(str(l['cantidad']))
            costo_unitario = producto.costo_promedio or Decimal('0')
            costo_total += cantidad * costo_unitario

        ctx.data['_tipo_asiento'] = 'COSTO_VENTA'
        ctx.data['_costo_venta_total'] = float(costo_total)
        ctx.data['_cuenta_costo_venta_id'] = str(self._config.cuenta_costo_venta_id) if self._config and self._config.cuenta_costo_venta_id else None

        return await engine.generate_from_document(ctx)

    # ── Inventory ─────────────────────────────────────────────────

    async def _update_inventory(self, ctx: 'DocumentContext'):
        from app.service.inventario_service import InventarioService
        doc_type = ctx.document_type
        ctx.data['movimiento_tipo'] = 'ENTRADA' if doc_type in ('COMPRA', 'OC', 'ENTRADA') else 'SALIDA'
        service = InventarioService(self.db)
        await service.registrar_movimiento(ctx)
        lineas = ctx.data.get('lineas', [])
        for l in lineas:
            producto_id = uuid.UUID(l['producto_id']) if isinstance(l['producto_id'], str) else l['producto_id']
            cantidad = Decimal(str(l['cantidad']))
            producto = await self.db.get(Producto, producto_id)
            if not producto:
                continue
            if doc_type in ('FAC', 'FACTURA', 'NCR'):
                producto.stock_valorado -= cantidad * (producto.costo_promedio or 0)

    # ── CxC ───────────────────────────────────────────────────────

    async def _update_cxc(self, ctx: 'DocumentContext'):
        if not ctx.data.get('cliente_id') and not ctx.data.get('tercero_id'):
            return
        from app.domain.models.factura_venta import FacturaVenta, FacturaVentaLinea
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
            aplica_iva=ctx.data.get('aplica_iva'),
            tasa_iva=Decimal(str(ctx.data.get('tasa_iva', 0))) if ctx.data.get('tasa_iva') else None,
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
                aplica_iva=l.get('aplica_iva'),
                tasa_iva=Decimal(str(l['tasa_iva'])) if l.get('tasa_iva') else None,
            )
            self.db.add(linea)

        ctx.data['factura_cxc_id'] = str(factura.id)

    # ── CxP ───────────────────────────────────────────────────────

    async def _update_cxp(self, ctx: 'DocumentContext'):
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
            aplica_iva=ctx.data.get('aplica_iva'),
            tasa_iva=Decimal(str(ctx.data.get('tasa_iva', 0))) if ctx.data.get('tasa_iva') else None,
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
                aplica_iva=l.get('aplica_iva'),
                tasa_iva=Decimal(str(l['tasa_iva'])) if l.get('tasa_iva') else None,
            )
            self.db.add(linea)

        ctx.data['factura_cxp_id'] = str(factura.id)

    # ── Banking ───────────────────────────────────────────────────

    async def _update_banking(self, ctx: 'DocumentContext'):
        from app.domain.models.caja import MovimientoCaja
        from app.domain.models.factura_venta import FacturaVenta
        from app.domain.models.factura_compra import FacturaCompra
        from app.domain.models.banco import MovimientoBanco
        from sqlalchemy import func

        doc_type = ctx.document_type
        monto = Decimal(str(ctx.data.get('monto', 0)))
        if monto == 0:
            return

        if doc_type == 'COBRO':
            factura_id = ctx.data.get('factura_venta_id')
            if factura_id:
                factura = await self.db.get(FacturaVenta, factura_id)
                if factura:
                    factura.estado = 'COBRADA'
                    factura.asiento_id = ctx.asiento_id
            concepto = ctx.data.get('concepto', f'Cobro FACT #{ctx.data.get("numero", "")}')
            ingreso = monto
            egreso = 0

        elif doc_type == 'PAGO':
            factura_id = ctx.data.get('factura_compra_id')
            if factura_id:
                factura = await self.db.get(FacturaCompra, factura_id)
                if factura:
                    factura.estado = 'PAGADA'
                    factura.asiento_id = ctx.asiento_id
            concepto = ctx.data.get('concepto', f'Pago FACT #{ctx.data.get("numero", "")}')
            ingreso = 0
            egreso = monto

        elif doc_type == 'MOV_BANCO':
            concepto = ctx.data.get('concepto', 'Movimiento Bancario')
            tipo = ctx.data.get('tipo', 'EGRESO')
            cuenta_banco_id = ctx.data.get('cuenta_banco_id')
            if cuenta_banco_id:
                if isinstance(cuenta_banco_id, str):
                    cuenta_banco_id = uuid.UUID(cuenta_banco_id)
                result = await self.db.execute(
                    select(func.coalesce(func.max(MovimientoBanco.saldo), 0)).where(
                        MovimientoBanco.cuenta_id == cuenta_banco_id
                    )
                )
                saldo_anterior = result.scalar()
                ingreso = monto if tipo == 'INGRESO' else 0
                egreso = monto if tipo == 'EGRESO' else 0
                saldo_nuevo = float(saldo_anterior) + float(ingreso) - float(egreso)
                mov = MovimientoBanco(
                    empresa_id=ctx.company_id,
                    cuenta_id=cuenta_banco_id,
                    fecha=datetime.strptime(ctx.data.get('fecha', ''), '%Y-%m-%d').date() if ctx.data.get('fecha') else datetime.now().date(),
                    tipo=tipo,
                    concepto=concepto,
                    entrada=ingreso,
                    salida=egreso,
                    saldo=saldo_nuevo,
                    numero_documento=ctx.data.get('numero_documento', ''),
                    asiento_id=ctx.asiento_id,
                )
                self.db.add(mov)
            return

        else:
            return

        metodo = ctx.data.get('metodo_pago', 'EFECTIVO')
        if metodo == 'EFECTIVO':
            from sqlalchemy import text as sa_text
            r = await self.db.execute(
                sa_text("""
                SELECT id FROM caja
                WHERE empresa_id = :eid AND activa = TRUE
                LIMIT 1
                """),
                {'eid': ctx.company_id},
            )
            caja_id = r.scalar_one_or_none()
            if caja_id:
                from app.domain.models.caja import MovimientoCaja
                r_saldo = await self.db.execute(
                    select(func.coalesce(func.max(MovimientoCaja.saldo), 0)).where(
                        MovimientoCaja.caja_id == caja_id
                    )
                )
                saldo_anterior = r_saldo.scalar()
                saldo_nuevo = float(saldo_anterior) + float(ingreso) - float(egreso)
                mov = MovimientoCaja(
                    empresa_id=ctx.company_id,
                    caja_id=caja_id,
                    fecha=datetime.strptime(ctx.data.get('fecha', ''), '%Y-%m-%d').date() if ctx.data.get('fecha') else datetime.now().date(),
                    tipo='COBRO' if doc_type == 'COBRO' else 'PAGO',
                    concepto=concepto,
                    entrada=ingreso,
                    salida=egreso,
                    saldo=saldo_nuevo,
                    referencia_id=factura_id,
                    asiento_id=ctx.asiento_id,
                )
                self.db.add(mov)

        elif metodo == 'TRANSFERENCIA' or metodo == 'CHEQUE':
            cuenta_banco_id = ctx.data.get('cuenta_banco_id')
            if cuenta_banco_id:
                from app.domain.models.banco import MovimientoBanco
                if isinstance(cuenta_banco_id, str):
                    cuenta_banco_id = uuid.UUID(cuenta_banco_id)
                result = await self.db.execute(
                    select(func.coalesce(func.max(MovimientoBanco.saldo), 0)).where(
                        MovimientoBanco.cuenta_id == cuenta_banco_id
                    )
                )
                saldo_anterior = result.scalar()
                saldo_nuevo = float(saldo_anterior) + float(ingreso) - float(egreso)
                mov = MovimientoBanco(
                    empresa_id=ctx.company_id,
                    cuenta_id=cuenta_banco_id,
                    fecha=datetime.strptime(ctx.data.get('fecha', ''), '%Y-%m-%d').date() if ctx.data.get('fecha') else datetime.now().date(),
                    tipo='DEPOSITO' if doc_type == 'COBRO' else 'EGRESO',
                    concepto=concepto,
                    entrada=ingreso,
                    salida=egreso,
                    saldo=saldo_nuevo,
                    asiento_id=ctx.asiento_id,
                )
                self.db.add(mov)

    async def _audit_log(self, ctx: 'DocumentContext'):
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
        MODULE_MAP = {
            'FAC': 'facturacion', 'NCR': 'facturacion', 'NDB': 'facturacion',
            'OC': 'compras', 'RECEPCION': 'compras', 'COMPRA': 'compras',
            'DEBITO': 'bancos', 'CREDITO': 'bancos', 'CHEQUE': 'bancos', 'TRANSFERENCIA': 'bancos', 'MOV_BANCO': 'bancos',
            'COBRO': 'cxc', 'PAGO': 'cxp', 'RETENCION': 'cxp',
            'ENTRADA': 'inventario', 'SALIDA': 'inventario', 'SALIDA_INV': 'inventario', 'AJUSTE': 'inventario', 'TRASLADO': 'inventario',
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
        self.asiento_costo_id: Optional[uuid.UUID] = None
