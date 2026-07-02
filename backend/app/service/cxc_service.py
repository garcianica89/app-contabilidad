from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.cliente import Cliente
from app.domain.models.factura_venta import FacturaVenta
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
    ) -> FacturaVenta:
        subtotal = sum(
            Decimal(str(l["cantidad"])) * Decimal(str(l["precio_unitario"]))
            for l in lineas
        )
        total = subtotal - Decimal(str(descuento)) + Decimal(str(iva))

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
                }
                for l in lineas
            ],
            'afecta_inventario': True,
            'afecta_cxc': True,
            'genera_asiento': True,
        }

        engine = DocumentEngine(self.db)
        result = await engine.process(
            document_type='FAC',
            subtype_code='FAC_' + tipo if tipo else 'FAC_CREDITO',
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
