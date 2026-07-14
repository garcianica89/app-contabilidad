from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.cliente import Cliente
from app.domain.models.factura_venta import FacturaVenta, FacturaVentaRetencion
from app.domain.models.retencion import Retencion
from app.domain.models.banco import CuentaBanco, MovimientoBanco
from app.domain.models.categoria_cliente import CategoriaCliente
from app.domain.accounting.models import Account, JournalType
from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.models.periodo import PeriodoContable
from app.service.document_engine import DocumentEngine
from app.service.accounting.accounting_engine import AccountingEngine


class CxcService:

    def __init__(self, db: AsyncSession, usuario_id: uuid.UUID, empresa_id: uuid.UUID):
        self.db = db
        self.usuario_id = usuario_id
        self.empresa_id = empresa_id

    async def crear_factura(
        self,
        numero: str,
        cliente_id: uuid.UUID,
        fecha: date,
        tipo: str,
        lineas: list[dict],
        moneda_id: uuid.UUID,
        periodo_id: uuid.UUID,
        fecha_vencimiento: Optional[date] = None,
        descuento: float = 0,
        iva: float = 0,
        aplica_iva: Optional[bool] = None,
        tasa_iva: Optional[float] = None,
    ) -> FacturaVenta:
        subtotal = sum(
            Decimal(str(l["cantidad"])) * Decimal(str(l["precio_unitario"]))
            for l in lineas
        )
        total = subtotal - Decimal(str(descuento)) + Decimal(str(iva))

        subtype = f'FAC_{tipo}' if tipo else 'FAC_CREDITO'

        data = {
            'numero': numero,
            'cliente_id': str(cliente_id),
            'fecha': fecha.isoformat(),
            'fecha_vencimiento': fecha_vencimiento.isoformat() if fecha_vencimiento else None,
            'tipo_pago': tipo,
            'subtotal': float(subtotal),
            'descuento': descuento,
            'iva': iva,
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
            document_type='FAC',
            subtype_code=subtype,
            action='CREATE',
            data=data,
            user_id=self.usuario_id,
            company_id=self.empresa_id,
        )

        if not result.success:
            raise ValueError('; '.join(result.errors))

        factura = await self.db.execute(
            select(FacturaVenta).where(FacturaVenta.id == result.document_id)
        )
        return factura.scalar_one()

    async def get_retenciones_factura(self, factura_id: uuid.UUID) -> list[dict]:
        factura = await self.db.get(FacturaVenta, factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")

        cliente = await self.db.get(Cliente, factura.cliente_id)

        overrides = {}
        saved = await self.db.execute(
            select(FacturaVentaRetencion).where(
                FacturaVentaRetencion.factura_venta_id == factura_id
            )
        )
        for sr in saved.scalars():
            overrides[sr.retencion_id] = sr

        if not cliente or not cliente.sujeto_retenciones or not cliente.retenciones:
            return []

        result = []
        for ret in cliente.retenciones:
            if not ret.is_active:
                continue

            if factura.subtotal and ret.base_imponible == 'SUBTOTAL':
                base = float(factura.subtotal) - float(factura.descuento)
            else:
                base = float(factura.total)

            monto_ret = round(base * float(ret.porcentaje) / 100, ret.redondeo or 2)

            override = overrides.get(ret.id)
            if override:
                base = float(override.base_imponible)
                monto_ret = float(override.monto_retenido)

            result.append({
                "retencion_id": str(ret.id),
                "retencion_codigo": ret.codigo,
                "retencion_nombre": ret.nombre,
                "tipo": ret.tipo,
                "porcentaje": float(ret.porcentaje),
                "naturaleza": ret.naturaleza,
                "cuenta_retencion_id": str(ret.cuenta_cobrar_id) if ret.cuenta_cobrar_id else None,
                "base_imponible_calculada": base,
                "monto_retenido": monto_ret,
                "is_override": override is not None,
            })

        return result

    async def save_retenciones_factura(
        self, factura_id: uuid.UUID, retenciones: list[dict]
    ):
        factura = await self.db.get(FacturaVenta, factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")

        await self.db.execute(
            text("DELETE FROM factura_venta_retencion WHERE factura_venta_id = :fid"),
            {"fid": factura_id},
        )

        for r in retenciones:
            fvr = FacturaVentaRetencion(
                factura_venta_id=factura_id,
                retencion_id=uuid.UUID(r["retencion_id"]),
                base_imponible=r.get("base_imponible", 0),
                monto_retenido=r.get("monto_retenido", 0),
            )
            self.db.add(fvr)

        await self.db.flush()

    async def registrar_cobro(
        self,
        factura_venta_id: uuid.UUID,
        monto: float,
        fecha: date,
        metodo_pago: str = 'EFECTIVO',
        cuenta_banco_id: Optional[uuid.UUID] = None,
        concepto: Optional[str] = None,
        retenciones: Optional[list[dict]] = None,
    ) -> dict:
        factura = await self.db.get(FacturaVenta, factura_venta_id)
        if not factura:
            raise ValueError("Factura no encontrada")
        if factura.estado == 'COBRADA':
            raise ValueError("Factura ya está cobrada")

        if retenciones:
            await self.save_retenciones_factura(factura_venta_id, retenciones)

        total_retenido = sum(r.get('monto_retenido', 0) for r in (retenciones or []))
        monto_neto = monto

        periodo = await self._get_periodo_abierto(fecha)
        if not periodo:
            raise ValueError("No hay periodo contable abierto para la fecha indicada")

        jt_result = await self.db.execute(
            select(JournalType).where(
                JournalType.company_id == self.empresa_id,
                JournalType.code == 'FA',
                JournalType.is_active == True,
            )
        )
        jt = jt_result.scalar_one_or_none()
        if not jt:
            raise ValueError("No se encontro JournalType FA activo")

        prefijo = jt.prefijo or 'CO'
        digitos = jt.digitos or 8
        old_corr = jt.correlativo_actual
        new_corr = old_corr + 1
        await self.db.execute(
            text("UPDATE journal_type SET correlativo_actual = :new WHERE id = :id AND correlativo_actual = :old"),
            {"new": new_corr, "id": jt.id, "old": old_corr},
        )
        numero_asiento = f"{prefijo}-{str(new_corr).zfill(digitos)}"

        asiento = Asiento(
            empresa_id=self.empresa_id,
            periodo_id=periodo.id,
            numero=numero_asiento,
            fecha=fecha,
            concepto=concepto or f"Cobro factura #{factura.numero}",
            journal_type_id=jt.id,
            documento_tipo='COBRO',
            documento_id=factura_venta_id,
            estado='CONTABILIZADO',
            creado_por=self.usuario_id,
        )
        self.db.add(asiento)
        await self.db.flush()

        total_factura = float(factura.total)

        cliente = await self.db.get(Cliente, factura.cliente_id)
        if not cliente or not cliente.categoria_id:
            await self.db.rollback()
            raise ValueError("El cliente debe tener una categoria configurada con cuentas contables")

        cat = await self.db.get(CategoriaCliente, cliente.categoria_id)
        if not cat:
            await self.db.rollback()
            raise ValueError(f"Categoria de cliente '{cliente.categoria_id}' no encontrada")

        cat_cuenta_tercero = cat.cuenta_tercero_id
        cat_cuenta_banco = cat.cuenta_banco_id
        cat_cuenta_caja = cat.cuenta_caja_id

        # Line 1: DEBIT Banco/Caja = monto cobrado
        if metodo_pago in ('TRANSFERENCIA', 'CHEQUE') and cuenta_banco_id:
            account_id = cat_cuenta_banco
        else:
            account_id = cat_cuenta_caja

        if not account_id:
            await self.db.rollback()
            raise ValueError(f"Cuenta contable {'de banco' if metodo_pago in ('TRANSFERENCIA','CHEQUE') else 'de caja'} no configurada en la categoria del cliente")

        cuenta = await self.db.get(Account, account_id)
        if not cuenta:
            await self.db.rollback()
            raise ValueError(f"Cuenta contable ID {account_id} no encontrada")

        linea1 = AsientoLinea(
            asiento_id=asiento.id,
            cuenta_id=cuenta.id,
            debe=monto_neto,
            haber=0,
            descripcion=concepto or f"Cobro factura #{factura.numero}",
        )
        self.db.add(linea1)

        # Line 2: CREDIT Clientes = total_factura
        if not cat_cuenta_tercero:
            await self.db.rollback()
            raise ValueError("Cuenta contable de clientes no configurada en la categoria del cliente")

        clientes_account = await self.db.get(Account, cat_cuenta_tercero)
        if not clientes_account:
            await self.db.rollback()
            raise ValueError(f"Cuenta contable ID {cat_cuenta_tercero} no encontrada")

        linea2 = AsientoLinea(
            asiento_id=asiento.id,
            cuenta_id=clientes_account.id,
            debe=0,
            haber=total_factura,
            descripcion=f"Cancelacion factura #{factura.numero}",
        )
        self.db.add(linea2)

        # Lines 3-N: Retenciones
        for r in (retenciones or []):
            monto_ret = r.get('monto_retenido', 0)
            if monto_ret <= 0:
                continue

            ret = await self.db.get(Retencion, uuid.UUID(r['retencion_id']))
            if not ret or not ret.cuenta_cobrar_id:
                continue

            # Inverso a CxP: naturaleza CREDITO en CxP (pasivo) → DEBIT en CxC (activo)
            naturaleza = r.get('naturaleza', ret.naturaleza)
            if naturaleza == 'DEBITO':
                linea = AsientoLinea(
                    asiento_id=asiento.id,
                    cuenta_id=ret.cuenta_cobrar_id,
                    debe=0,
                    haber=monto_ret,
                    descripcion=f"Retencion {ret.nombre} factura #{factura.numero}",
                )
            else:
                linea = AsientoLinea(
                    asiento_id=asiento.id,
                    cuenta_id=ret.cuenta_cobrar_id,
                    debe=monto_ret,
                    haber=0,
                    descripcion=f"Retencion {ret.nombre} factura #{factura.numero}",
                )
            self.db.add(linea)

        # MovimientoBanco for TRANSFERENCIA/CHEQUE
        mov_banco_id = None
        if metodo_pago in ('TRANSFERENCIA', 'CHEQUE') and cuenta_banco_id:
            cuenta = await self.db.get(CuentaBanco, cuenta_banco_id)
            if cuenta:
                ult_saldo = await self.db.execute(
                    select(func.coalesce(func.max(MovimientoBanco.saldo), 0)).where(
                        MovimientoBanco.cuenta_id == cuenta_banco_id
                    )
                )
                saldo_anterior = float(ult_saldo.scalar())
                saldo_nuevo = saldo_anterior + monto_neto
                mov = MovimientoBanco(
                    empresa_id=self.empresa_id,
                    cuenta_id=cuenta_banco_id,
                    fecha=fecha,
                    tipo='INGRESO',
                    concepto=concepto or f"Cobro factura #{factura.numero}",
                    entrada=monto_neto,
                    salida=0,
                    saldo=saldo_nuevo,
                    asiento_id=asiento.id,
                )
                self.db.add(mov)
                await self.db.flush()
                mov_banco_id = str(mov.id)

        factura.estado = 'COBRADA'
        factura.asiento_id = asiento.id

        await self.db.commit()

        return {
            "factura_id": str(factura.id),
            "asiento_id": str(asiento.id),
            "numero_asiento": numero_asiento,
            "movimiento_banco_id": mov_banco_id,
            "monto_cobrado": monto_neto,
            "total_retenido": total_retenido,
        }

    async def estado_cuenta_cliente(
        self, cliente_id: uuid.UUID, fecha_corte: Optional[date] = None
    ):
        query = select(FacturaVenta).where(
            FacturaVenta.cliente_id == cliente_id,
            FacturaVenta.empresa_id == self.empresa_id,
        )
        if fecha_corte:
            query = query.where(FacturaVenta.fecha <= fecha_corte)

        query = query.order_by(FacturaVenta.fecha)
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
                "debito": monto if f.estado != "COBRADA" else 0,
                "credito": monto if f.estado == "COBRADA" else 0,
                "saldo": saldo,
                "vencimiento": str(f.fecha_vencimiento) if f.fecha_vencimiento else None,
                "dias_vencido": (
                    (date.today() - f.fecha_vencimiento).days
                    if f.fecha_vencimiento and f.fecha_vencimiento < date.today()
                    else 0
                ),
            })

        return {
            "cliente_id": str(cliente_id),
            "saldo_actual": saldo,
            "movimientos": movimientos,
        }

    async def antiguedad_saldos(self):
        query = """
        SELECT
            c.id AS cliente_id,
            c.codigo,
            c.nombre,
            SUM(CASE
                WHEN fv.fecha_vencimiento < CURRENT_DATE - 90
                THEN fv.total ELSE 0 END) AS mas_90,
            SUM(CASE
                WHEN fv.fecha_vencimiento BETWEEN CURRENT_DATE - 90 AND CURRENT_DATE - 61
                THEN fv.total ELSE 0 END) AS entre_60_90,
            SUM(CASE
                WHEN fv.fecha_vencimiento BETWEEN CURRENT_DATE - 60 AND CURRENT_DATE - 31
                THEN fv.total ELSE 0 END) AS entre_30_60,
            SUM(CASE
                WHEN fv.fecha_vencimiento BETWEEN CURRENT_DATE - 30 AND CURRENT_DATE
                THEN fv.total ELSE 0 END) AS entre_0_30,
            SUM(fv.total) AS saldo_total
        FROM factura_venta fv
        JOIN cliente c ON c.id = fv.cliente_id
        WHERE fv.empresa_id = :empresa_id
            AND fv.estado NOT IN ('COBRADA', 'ANULADA')
        GROUP BY c.id, c.codigo, c.nombre
        ORDER BY c.nombre
        """

        result = await self.db.execute(
            text(query), {"empresa_id": self.empresa_id}
        )
        rows = result.fetchall()

        return [
            {
                "cliente_id": str(r.cliente_id),
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

    async def _get_periodo_abierto(self, fecha: date) -> Optional[PeriodoContable]:
        result = await self.db.execute(
            select(PeriodoContable).where(
                PeriodoContable.empresa_id == self.empresa_id,
                PeriodoContable.fecha_inicio <= fecha,
                PeriodoContable.fecha_fin >= fecha,
                PeriodoContable.cerrado == False,
            )
        )
        return result.scalar_one_or_none()
