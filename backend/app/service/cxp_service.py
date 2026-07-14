from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.proveedor import Proveedor
from app.domain.models.factura_compra import FacturaCompra, FacturaCompraRetencion
from app.domain.models.retencion import Retencion
from app.domain.models.banco import CuentaBanco, MovimientoBanco
from app.domain.models.categoria_proveedor import CategoriaProveedor
from app.domain.accounting.models import Account, JournalType
from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.models.periodo import PeriodoContable
from app.service.document_engine import DocumentEngine


class CxpService:

    def __init__(self, db: AsyncSession, usuario_id: uuid.UUID, empresa_id: uuid.UUID):
        self.db = db
        self.usuario_id = usuario_id
        self.empresa_id = empresa_id

    async def crear_orden_compra(
        self,
        numero: str,
        proveedor_id: uuid.UUID,
        fecha: date,
        lineas: list[dict],
        moneda_id: uuid.UUID,
        fecha_entrega: Optional[date] = None,
    ) -> OrdenCompra:
        from app.domain.models.orden_compra import OrdenCompra
        subtotal = sum(
            Decimal(str(l["cantidad"])) * Decimal(str(l["precio_unitario"]))
            for l in lineas
        )

        orden = OrdenCompra(
            empresa_id=self.empresa_id,
            numero=numero,
            proveedor_id=proveedor_id,
            fecha=fecha,
            fecha_entrega=fecha_entrega,
            subtotal=subtotal,
            iva=0,
            total=subtotal,
            moneda_id=moneda_id,
            estado="EMITIDA",
        )
        self.db.add(orden)

        await self.db.commit()
        await self.db.refresh(orden)
        return orden

    async def crear_factura_compra(
        self,
        numero: str,
        proveedor_id: uuid.UUID,
        fecha: date,
        lineas: list[dict],
        moneda_id: uuid.UUID,
        periodo_id: uuid.UUID,
        orden_id: Optional[uuid.UUID] = None,
        fecha_vencimiento: Optional[date] = None,
        descuento: float = 0,
        iva: float = 0,
        retencion_ir: float = 0,
        aplica_iva: Optional[bool] = None,
        tasa_iva: Optional[float] = None,
    ) -> FacturaCompra:
        subtotal = sum(
            Decimal(str(l["cantidad"])) * Decimal(str(l["precio_unitario"]))
            for l in lineas
        )
        total = subtotal - Decimal(str(descuento)) + Decimal(str(iva)) - Decimal(str(retencion_ir))

        data = {
            'numero': numero,
            'proveedor_id': str(proveedor_id),
            'orden_id': str(orden_id) if orden_id else None,
            'fecha': fecha.isoformat(),
            'fecha_vencimiento': fecha_vencimiento.isoformat() if fecha_vencimiento else None,
            'subtotal': float(subtotal),
            'descuento': descuento,
            'iva': iva,
            'retencion_ir': retencion_ir,
            'total': float(total),
            'moneda_id': str(moneda_id),
            'lineas': [
                {
                    'producto_id': str(l['producto_id']),
                    'cantidad': float(l['cantidad']),
                    'precio_unitario': float(l['precio_unitario']),
                    'descuento': float(l.get('descuento', 0)),
                    'aplica_iva': l.get('aplica_iva'),
                    'tasa_iva': float(l.get('tasa_iva', 0)) if l.get('tasa_iva') else None,
                }
                for l in lineas
            ],
        }

        if aplica_iva is not None:
            data['aplica_iva'] = aplica_iva
        if tasa_iva is not None:
            data['tasa_iva'] = tasa_iva

        engine = DocumentEngine(self.db)
        result = await engine.process(
            document_type='COMPRA',
            subtype_code='COMPRA',
            action='CREATE',
            data=data,
            user_id=self.usuario_id,
            company_id=self.empresa_id,
        )

        if not result.success:
            raise ValueError('; '.join(result.errors))

        factura = await self.db.execute(
            select(FacturaCompra).where(FacturaCompra.id == result.document_id)
        )
        return factura.scalar_one()

    async def get_retenciones_factura(self, factura_id: uuid.UUID) -> list[dict]:
        """Retorna retenciones para una factura: defaults del proveedor + overrides guardados."""
        factura = await self.db.get(FacturaCompra, factura_id)
        if not factura:
            return []

        proveedor = await self.db.get(Proveedor, factura.proveedor_id)

        overrides = {}
        r = await self.db.execute(
            select(FacturaCompraRetencion).where(
                FacturaCompraRetencion.factura_compra_id == factura_id
            )
        )
        for ov in r.scalars():
            overrides[str(ov.retencion_id)] = {
                'base_imponible': float(ov.base_imponible),
                'monto_retenido': float(ov.monto_retenido),
            }

        result = []
        if proveedor and proveedor.sujeto_retenciones and proveedor.retenciones:
            for ret in proveedor.retenciones:
                base = factura.subtotal if ret.base_imponible == 'SUBTOTAL' else factura.total
                monto = float(base) * float(ret.porcentaje / 100)
                ov = overrides.get(str(ret.id))
                result.append({
                    'retencion_id': str(ret.id),
                    'retencion_codigo': ret.codigo,
                    'retencion_nombre': ret.nombre,
                    'tipo': ret.tipo,
                    'porcentaje': float(ret.porcentaje),
                    'naturaleza': ret.naturaleza,
                    'cuenta_retencion_id': str(ret.cuenta_retencion_id) if ret.cuenta_retencion_id else None,
                    'base_imponible_calculada': float(ov['base_imponible']) if ov else float(base),
                    'monto_retenido': float(ov['monto_retenido']) if ov else round(monto, int(ret.redondeo or 2)),
                    'is_override': ov is not None,
                })

        return result

    async def save_retenciones_factura(self, factura_id: uuid.UUID, retenciones: list[dict]):
        factura = await self.db.get(FacturaCompra, factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")

        await self.db.execute(
            text("DELETE FROM factura_compra_retencion WHERE factura_compra_id = :fid"),
            {'fid': factura_id},
        )

        for r in retenciones:
            fcr = FacturaCompraRetencion(
                factura_compra_id=factura_id,
                retencion_id=uuid.UUID(r['retencion_id']) if isinstance(r['retencion_id'], str) else r['retencion_id'],
                base_imponible=Decimal(str(r.get('base_imponible', 0))),
                monto_retenido=Decimal(str(r.get('monto_retenido', 0))),
            )
            self.db.add(fcr)

        await self.db.flush()

    async def registrar_pago(
        self,
        factura_compra_id: uuid.UUID,
        monto: float,
        fecha: date,
        metodo_pago: str = 'EFECTIVO',
        cuenta_banco_id: Optional[uuid.UUID] = None,
        concepto: Optional[str] = None,
        retenciones: Optional[list[dict]] = None,
    ) -> dict:
        """Procesa un pago con retenciones: crea asiento, movimiento banco, actualiza factura."""
        factura = await self.db.get(FacturaCompra, factura_compra_id)
        if not factura:
            raise ValueError("Factura no encontrada")
        if factura.estado == 'PAGADA':
            raise ValueError("Factura ya esta pagada")

        if retenciones:
            await self.save_retenciones_factura(factura_compra_id, retenciones)
            total_retenido = sum(Decimal(str(r.get('monto_retenido', 0))) for r in retenciones)
        else:
            total_retenido = Decimal('0')

        monto_pagado = Decimal(str(monto))
        total_factura = factura.total
        concepto_final = concepto or f"Pago factura {factura.numero}"

        # Obtener periodo abierto
        periodo = await self._get_periodo_abierto(fecha)
        if not periodo:
            raise ValueError("No hay periodo contable abierto para la fecha del pago")

        # Obtener journal type CP
        jt = await self.db.execute(
            select(JournalType).where(
                JournalType.company_id == self.empresa_id,
                JournalType.code == 'CP',
                JournalType.is_active == True,
            )
        )
        jt = jt.scalar_one_or_none()
        if not jt:
            raise ValueError("Journal type CP no encontrado")

        # Generar numero de asiento
        prefijo = jt.prefijo or 'CP'
        digitos = jt.digitos or 8
        correlativo = jt.correlativo_actual + 1
        await self.db.execute(
            text("UPDATE journal_type SET correlativo_actual = :corr WHERE id = :id AND correlativo_actual = :old"),
            {'corr': correlativo, 'id': jt.id, 'old': jt.correlativo_actual},
        )
        numero_asiento = f"{prefijo}{correlativo:0{digitos}d}"

        # Crear asiento
        asiento = Asiento(
            empresa_id=self.empresa_id,
            periodo_id=periodo.id,
            numero=numero_asiento,
            fecha=datetime.combine(fecha, datetime.min.time()),
            concepto=concepto_final,
            journal_type_id=jt.id,
            documento_tipo='PAGO',
            documento_id=factura_compra_id,
            estado='CONTABILIZADO',
            creado_por=self.usuario_id,
        )
        self.db.add(asiento)
        await self.db.flush()

        # Resolver cuentas desde categoria del proveedor
        proveedor = await self.db.get(Proveedor, factura.proveedor_id)
        if not proveedor or not proveedor.categoria_id:
            raise ValueError("El proveedor debe tener una categoria configurada con cuentas contables")

        cat = await self.db.get(CategoriaProveedor, proveedor.categoria_id)
        if not cat:
            raise ValueError(f"Categoria de proveedor '{proveedor.categoria_id}' no encontrada")

        cat_cuenta_tercero = cat.cuenta_tercero_id
        cat_cuenta_banco = cat.cuenta_banco_id
        cat_cuenta_caja = cat.cuenta_caja_id

        # Línea 1: DEBIT Proveedores = total_factura
        if not cat_cuenta_tercero:
            raise ValueError("Cuenta contable de proveedores no configurada en la categoria")

        prov_account = await self.db.get(Account, cat_cuenta_tercero)
        if not prov_account:
            raise ValueError(f"Cuenta contable ID {cat_cuenta_tercero} no encontrada")

        self.db.add(AsientoLinea(
            asiento_id=asiento.id,
            cuenta_id=prov_account.id,
            debe=total_factura,
            haber=0,
            descripcion=concepto_final,
        ))

        # Línea 2: CREDIT banco/caja = monto_pagado
        if metodo_pago in ('TRANSFERENCIA', 'CHEQUE') and cuenta_banco_id:
            cuenta_banco_obj = await self.db.get(CuentaBanco, cuenta_banco_id)
            if not cuenta_banco_obj:
                raise ValueError("Cuenta bancaria no encontrada")

            if not cat_cuenta_banco:
                raise ValueError("Cuenta contable de banco no configurada en la categoria del proveedor")

            banco_account = await self.db.get(Account, cat_cuenta_banco)
            if not banco_account:
                raise ValueError(f"Cuenta contable ID {cat_cuenta_banco} no encontrada")

            self.db.add(AsientoLinea(
                asiento_id=asiento.id,
                cuenta_id=banco_account.id,
                debe=0,
                haber=monto_pagado,
                descripcion=concepto_final,
            ))
        else:
            if not cat_cuenta_caja:
                raise ValueError("Cuenta contable de caja no configurada en la categoria del proveedor")

            caja_account = await self.db.get(Account, cat_cuenta_caja)
            if not caja_account:
                raise ValueError(f"Cuenta contable ID {cat_cuenta_caja} no encontrada")

            self.db.add(AsientoLinea(
                asiento_id=asiento.id,
                cuenta_id=caja_account.id,
                debe=0,
                haber=monto_pagado,
                descripcion=concepto_final,
            ))

        # Líneas de retenciones
        if retenciones and total_retenido > 0:
            for r in retenciones:
                ret = await self.db.get(Retencion, uuid.UUID(r['retencion_id']))
                if not ret or not ret.cuenta_retencion_id:
                    continue
                monto_ret = Decimal(str(r.get('monto_retenido', 0)))
                if monto_ret <= 0:
                    continue
                naturaleza = r.get('naturaleza', ret.naturaleza)
                if naturaleza == 'CREDITO':
                    self.db.add(AsientoLinea(
                        asiento_id=asiento.id,
                        cuenta_id=ret.cuenta_retencion_id,
                        debe=0,
                        haber=monto_ret,
                        descripcion=f"Retencion {ret.codigo} - {concepto_final}",
                    ))
                else:
                    self.db.add(AsientoLinea(
                        asiento_id=asiento.id,
                        cuenta_id=ret.cuenta_retencion_id,
                        debe=monto_ret,
                        haber=0,
                        descripcion=f"Retencion {ret.codigo} - {concepto_final}",
                    ))

        await self.db.flush()

        # Crear MovimientoBanco
        movimiento_banco_id = None
        if metodo_pago in ('TRANSFERENCIA', 'CHEQUE') and cuenta_banco_id:
            r = await self.db.execute(
                select(MovimientoBanco).where(
                    MovimientoBanco.cuenta_id == cuenta_banco_id,
                ).order_by(MovimientoBanco.saldo.desc()).limit(1)
            )
            ultimo = r.scalar_one_or_none()
            saldo_anterior = float(ultimo.saldo) if ultimo else 0
            saldo_nuevo = saldo_anterior - float(monto_pagado)

            mov = MovimientoBanco(
                empresa_id=self.empresa_id,
                cuenta_id=cuenta_banco_id,
                fecha=datetime.combine(fecha, datetime.min.time()),
                tipo='EGRESO',
                concepto=concepto_final,
                entrada=0,
                salida=float(monto_pagado),
                saldo=saldo_nuevo,
                numero_documento=f"PAG-{factura.numero}",
                asiento_id=asiento.id,
            )
            self.db.add(mov)
            await self.db.flush()
            movimiento_banco_id = mov.id

        # Actualizar factura
        factura.estado = 'PAGADA'
        factura.asiento_id = asiento.id
        await self.db.flush()

        return {
            'factura_id': str(factura.id),
            'asiento_id': str(asiento.id),
            'numero_asiento': numero_asiento,
            'movimiento_banco_id': str(movimiento_banco_id) if movimiento_banco_id else None,
            'monto_pagado': float(monto_pagado),
            'total_retenido': float(total_retenido),
        }

    async def estado_cuenta_proveedor(
        self, proveedor_id: uuid.UUID, fecha_corte: Optional[date] = None
    ):
        query = select(FacturaCompra).where(
            FacturaCompra.proveedor_id == proveedor_id,
            FacturaCompra.empresa_id == self.empresa_id,
        )
        if fecha_corte:
            query = query.where(FacturaCompra.fecha <= fecha_corte)
        query = query.order_by(FacturaCompra.fecha)

        result = await self.db.execute(query)
        facturas = result.scalars().all()

        saldo = 0
        movimientos = []
        for f in facturas:
            monto = float(f.total)
            saldo += monto
            movimientos.append({
                "fecha": str(f.fecha),
                "documento": f.numero,
                "tipo": "FACTURA",
                "debito": monto if f.estado == "PAGADA" else 0,
                "credito": monto if f.estado != "PAGADA" else 0,
                "saldo": saldo,
                "vencimiento": str(f.fecha_vencimiento) if f.fecha_vencimiento else None,
                "dias_vencido": (
                    (date.today() - f.fecha_vencimiento).days
                    if f.fecha_vencimiento and f.fecha_vencimiento < date.today()
                    else 0
                ),
            })

        return {
            "proveedor_id": str(proveedor_id),
            "saldo_actual": saldo,
            "movimientos": movimientos,
        }

    async def antiguedad_saldos(self):
        query = """
        SELECT
            p.id AS proveedor_id,
            p.codigo,
            p.nombre,
            SUM(CASE
                WHEN fc.fecha_vencimiento < CURRENT_DATE - 90
                THEN fc.total ELSE 0 END) AS mas_90,
            SUM(CASE
                WHEN fc.fecha_vencimiento BETWEEN CURRENT_DATE - 90 AND CURRENT_DATE - 61
                THEN fc.total ELSE 0 END) AS entre_60_90,
            SUM(CASE
                WHEN fc.fecha_vencimiento BETWEEN CURRENT_DATE - 60 AND CURRENT_DATE - 31
                THEN fc.total ELSE 0 END) AS entre_30_60,
            SUM(CASE
                WHEN fc.fecha_vencimiento BETWEEN CURRENT_DATE - 30 AND CURRENT_DATE
                THEN fc.total ELSE 0 END) AS entre_0_30,
            SUM(fc.total) AS saldo_total
        FROM factura_compra fc
        JOIN proveedor p ON p.id = fc.proveedor_id
        WHERE fc.empresa_id = :empresa_id
            AND fc.estado NOT IN ('PAGADA', 'ANULADA')
        GROUP BY p.id, p.codigo, p.nombre
        ORDER BY p.nombre
        """

        result = await self.db.execute(
            text(query), {"empresa_id": self.empresa_id}
        )
        rows = result.fetchall()

        return [
            {
                "proveedor_id": str(r.proveedor_id),
                "codigo": r.codigo,
                "nombre": r.nombre,
                "mas_90": float(r.mas_90 or 0),
                "entre_60_90": float(r.entre_60_90 or 0),
                "entre_30_60": float(r.entre_30_60 or 0),
                "entre_0_30": float(r.entre_0_30 or 0),
                "saldo_total": float(r.saldo_total or 0),
            }
            for r in rows
        ]

    async def _get_periodo_abierto(self, fecha: date):
        r = await self.db.execute(
            select(PeriodoContable).where(
                PeriodoContable.empresa_id == self.empresa_id,
                PeriodoContable.cerrado == False,
                PeriodoContable.fecha_inicio <= fecha,
                PeriodoContable.fecha_fin >= fecha,
            ).limit(1)
        )
        return r.scalar_one_or_none()
