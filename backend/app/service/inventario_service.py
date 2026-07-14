"""
InventarioService — Servicio central de inventario.

UNICO servicio autorizado para:
- Registrar movimientos de inventario (entradas, salidas, ajustes, traslados)
- Actualizar Kardex
- Calcular costos (promedio, FIFO, LIFO, especifico)

Ningun modulo de negocio escribe en kardex_movimiento directamente.
"""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.producto import Producto, KardexMovimiento
from app.service.document_engine.engine import DocumentContext


class InventarioService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def registrar_movimiento(self, ctx: DocumentContext) -> Optional[dict]:
        """Registra movimiento de inventario desde un contexto de documento.

        Soporta: ENTRADA, SALIDA, AJUSTE, TRASLADO, CONSUMO
        """
        movimiento_tipo = ctx.data.get('movimiento_tipo', 'SALIDA')
        lineas = ctx.data.get('lineas', ctx.data.get('items', []))
        bodega_id = ctx.data.get('bodega_id')
        bodega_destino_id = ctx.data.get('bodega_destino_id')

        resultados = []
        for linea in lineas:
            producto_id = linea.get('producto_id')
            cantidad = Decimal(str(linea.get('cantidad', 0)))
            if cantidad == 0 or not producto_id:
                continue

            producto = await self.db.get(Producto, uuid.UUID(producto_id) if isinstance(producto_id, str) else producto_id)
            if not producto:
                continue

            costo_unitario = Decimal(str(linea.get('costo_unitario', linea.get('precio_unitario', 0))))
            if costo_unitario == 0:
                costo_unitario = producto.costo_promedio or Decimal('0')

            if movimiento_tipo in ('SALIDA', 'CONSUMO', 'AJUSTE_NEGATIVO'):
                cantidad = -abs(cantidad)
            elif movimiento_tipo == 'ENTRADA':
                cantidad = abs(cantidad)

            kardex = KardexMovimiento(
                producto_id=producto.id,
                tipo_movimiento=movimiento_tipo,
                cantidad=cantidad,
                costo_unitario=costo_unitario,
                costo_total=costo_unitario * abs(cantidad),
                bodega_id=uuid.UUID(bodega_id) if isinstance(bodega_id, str) and bodega_id else None,
                bodega_destino_id=uuid.UUID(bodega_destino_id) if isinstance(bodega_destino_id, str) and bodega_destino_id else None,
                documento_tipo=ctx.document_type,
                documento_id=ctx.document_id,
                referencia=ctx.data.get('numero', ''),
                created_by=ctx.user_id,
            )
            self.db.add(kardex)

            producto.stock_actual += cantidad
            if movimiento_tipo == 'ENTRADA' and cantidad > 0 and producto.costo_promedio:
                costo_total_anterior = producto.costo_promedio * (producto.stock_actual - cantidad)
                costo_nuevo = costo_unitario * cantidad
                nueva_cantidad = producto.stock_actual
                if nueva_cantidad > 0:
                    producto.costo_promedio = (costo_total_anterior + costo_nuevo) / nueva_cantidad

            resultados.append({
                "producto_id": str(producto.id),
                "producto": producto.nombre,
                "cantidad": float(cantidad),
                "stock_resultante": float(producto.stock_actual),
            })

        await self.db.flush()
        return {
            "movimiento_tipo": movimiento_tipo,
            "documento_id": str(ctx.document_id),
            "items": resultados,
        }
