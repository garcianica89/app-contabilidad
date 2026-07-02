from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.proveedor import Proveedor
from app.domain.models.factura_compra import FacturaCompra
from app.domain.models.orden_compra import OrdenCompra
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
                }
                for l in lineas
            ],
            'afecta_inventario': True,
            'afecta_cxp': True,
            'genera_asiento': True,
        }

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
