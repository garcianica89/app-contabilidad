from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.cliente import Cliente
from app.domain.models.factura_venta import FacturaVenta, FacturaVentaLinea
from app.domain.models.producto import Producto
from app.domain.models.caja import MovimientoCaja
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
    ) -> FacturaVenta:
        subtotal = sum(
            Decimal(str(l["cantidad"])) * Decimal(str(l["precio_unitario"]))
            for l in lineas
        )
        total = subtotal - Decimal(str(descuento)) + Decimal(str(iva))

        factura = FacturaVenta(
            empresa_id=self.empresa_id,
            numero=numero,
            cliente_id=cliente_id,
            fecha=fecha,
            fecha_vencimiento=fecha_vencimiento,
            tipo=tipo,
            subtotal=subtotal,
            descuento=Decimal(str(descuento)),
            iva=Decimal(str(iva)),
            total=total,
            moneda_id=moneda_id,
            estado="EMITIDA",
        )
        self.db.add(factura)
        await self.db.flush()

        for l in lineas:
            linea = FacturaVentaLinea(
                factura_id=factura.id,
                producto_id=l["producto_id"],
                cantidad=Decimal(str(l["cantidad"])),
                precio_unitario=Decimal(str(l["precio_unitario"])),
                descuento=Decimal(str(l.get("descuento", 0))),
                subtotal=Decimal(str(l["cantidad"])) * Decimal(str(l["precio_unitario"])),
            )
            self.db.add(linea)

            producto = await self.db.get(Producto, l["producto_id"])
            if producto:
                producto.stock_actual -= Decimal(str(l["cantidad"]))

        asiento_result = await self._generar_asiento_venta(
            factura, fecha, cliente_id
        )
        if asiento_result:
            factura.asiento_id = asiento_result.get('asiento_id')

        if tipo == "CONTADO":
            await self._registrar_cobro(factura, fecha, total, moneda_id, factura.asiento_id)

        await self.db.commit()
        await self.db.refresh(factura)
        return factura

    async def _generar_asiento_venta(
        self, factura: FacturaVenta, fecha: date, cliente_id: uuid.UUID
    ) -> Optional[dict]:
        """Genera asiento usando AccountingEngine (template-based, zero IFs)."""
        cliente = await self.db.get(Cliente, cliente_id)
        engine = AccountingEngine(self.db)
        data = {
            'fecha': fecha.isoformat(),
            'numero': factura.numero,
            'concepto': f"Factura {factura.numero}",
            'subtotal': float(factura.subtotal),
            'iva': float(factura.iva),
            'descuento': float(factura.descuento),
            'total': float(factura.total),
            'tipo_pago': factura.tipo,
            'cliente_id': str(cliente_id),
            'cliente_nombre': cliente.nombre if cliente else '',
            'moneda_id': str(factura.moneda_id),
        }
        return await engine.generate_from_event(
            event_type='FAC',
            module='facturacion',
            data=data,
            company_id=self.empresa_id,
            document_id=factura.id,
        )

    async def _registrar_cobro(
        self,
        factura: FacturaVenta,
        fecha: date,
        monto: Decimal,
        moneda_id: uuid.UUID,
        asiento_id: uuid.UUID | None,
    ):
        caja = await self.db.execute(
            text("""
            SELECT id FROM caja
            WHERE empresa_id = :empresa_id AND activa = TRUE
            LIMIT 1
            """),
            {"empresa_id": self.empresa_id},
        )
        caja_id = caja.scalar_one_or_none()

        if caja_id:
            mov = MovimientoCaja(
                empresa_id=self.empresa_id,
                caja_id=caja_id,
                fecha=fecha,
                tipo="FACTURA",
                concepto=f"Cobro factura {factura.numero}",
                entrada=monto,
                salida=0,
                saldo=monto,
                referencia_id=factura.id,
                asiento_id=asiento_id,
            )
            self.db.add(mov)

        factura.estado = "COBRADA"

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
