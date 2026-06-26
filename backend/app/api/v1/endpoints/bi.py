from typing import Annotated
from datetime import date, datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario

router = APIRouter()


@router.get("/dashboard")
async def dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID | None = None,
):
    empresa_id = current_user.empresa_id

    if not periodo_id:
        result = await db.execute(
            text("""
            SELECT id FROM periodo_contable
            WHERE empresa_id = :empresa_id AND cerrado = FALSE
            ORDER BY fecha_fin DESC LIMIT 1
            """),
            {"empresa_id": empresa_id},
        )
        row = result.scalar_one_or_none()
        if row:
            periodo_id = row

    ventas = await db.execute(
        text("""
        SELECT COALESCE(SUM(total), 0) AS total
        FROM factura_venta
        WHERE empresa_id = :empresa_id
          AND (:periodo_id IS NULL OR
            fecha BETWEEN (SELECT fecha_inicio FROM periodo_contable WHERE id = :periodo_id2)
                    AND (SELECT fecha_fin FROM periodo_contable WHERE id = :periodo_id3))
          AND estado != 'ANULADA'
        """),
        {"empresa_id": empresa_id, "periodo_id": periodo_id,
         "periodo_id2": periodo_id, "periodo_id3": periodo_id},
    )
    ventas_total = float(ventas.scalar() or 0)

    gastos = await db.execute(
        text("""
        SELECT COALESCE(SUM(total), 0) AS total
        FROM factura_compra
        WHERE empresa_id = :empresa_id
          AND (:periodo_id IS NULL OR
            fecha BETWEEN (SELECT fecha_inicio FROM periodo_contable WHERE id = :periodo_id2)
                    AND (SELECT fecha_fin FROM periodo_contable WHERE id = :periodo_id3))
          AND estado != 'ANULADA'
        """),
        {"empresa_id": empresa_id, "periodo_id": periodo_id,
         "periodo_id2": periodo_id, "periodo_id3": periodo_id},
    )
    gastos_total = float(gastos.scalar() or 0)

    utilidad = ventas_total - gastos_total
    margen = round((utilidad / ventas_total * 100), 1) if ventas_total > 0 else 0

    caja = await db.execute(
        text("SELECT COALESCE(SUM(saldo_actual), 0) FROM caja WHERE empresa_id = :empresa_id"),
        {"empresa_id": empresa_id},
    )
    saldo_caja = float(caja.scalar() or 0)

    cxc = await db.execute(
        text("""
        SELECT COALESCE(SUM(total), 0) FROM factura_venta
        WHERE empresa_id = :empresa_id AND estado NOT IN ('COBRADA', 'ANULADA')
        """),
        {"empresa_id": empresa_id},
    )
    cxc_pendiente = float(cxc.scalar() or 0)

    cxp = await db.execute(
        text("""
        SELECT COALESCE(SUM(total), 0) FROM factura_compra
        WHERE empresa_id = :empresa_id AND estado NOT IN ('PAGADA', 'ANULADA')
        """),
        {"empresa_id": empresa_id},
    )
    cxp_pendiente = float(cxp.scalar() or 0)

    inventario = await db.execute(
        text("""
        SELECT
            COALESCE(SUM(stock_actual * costo_promedio), 0) AS valor_total,
            COUNT(*) AS items
        FROM producto WHERE empresa_id = :empresa_id AND activo = TRUE
        """),
        {"empresa_id": empresa_id},
    )
    inv = inventario.fetchone()
    inventario_valor = float(inv.valor_total or 0)
    inventario_items = inv.items or 0

    clientes = await db.execute(
        text("""
        SELECT COUNT(*) FROM cliente
        WHERE empresa_id = :empresa_id AND activo = TRUE
        """),
        {"empresa_id": empresa_id},
    )
    clientes_activos = clientes.scalar() or 0

    meses_data = await db.execute(
        text("""
        SELECT
            CAST(EXTRACT(MONTH FROM f.fecha) AS INTEGER) AS mes_num,
            COALESCE(SUM(CASE WHEN f.tipo = 'VENTA' THEN f.total ELSE 0 END), 0) AS ingresos,
            COALESCE(SUM(CASE WHEN f.tipo = 'COMPRA' THEN f.total ELSE 0 END), 0) AS gastos
        FROM (
            SELECT fecha, total, 'VENTA' AS tipo FROM factura_venta
            WHERE empresa_id = :empresa_id AND estado != 'ANULADA'
            UNION ALL
            SELECT fecha, total, 'COMPRA' AS tipo FROM factura_compra
            WHERE empresa_id = :empresa_id AND estado != 'ANULADA'
        ) f
        WHERE (:periodo_id IS NULL OR
            f.fecha BETWEEN (SELECT fecha_inicio FROM periodo_contable WHERE id = :pid)
                     AND (SELECT fecha_fin FROM periodo_contable WHERE id = :pid2))
        GROUP BY mes_num
        ORDER BY mes_num
        """),
        {"empresa_id": empresa_id, "pid": periodo_id, "pid2": periodo_id},
    )
    meses = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
             7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
    ventas_mes = []
    ingresos_vs_gastos = []
    for r in meses_data.fetchall():
        label = meses.get(r.mes_num, str(r.mes_num))
        ventas_mes.append({"mes": label, "ventas": float(r.ingresos or 0)})
        ingresos_vs_gastos.append({
            "mes": label,
            "ingresos": float(r.ingresos or 0),
            "gastos": float(r.gastos or 0),
        })

    top_clientes = await db.execute(
        text("""
        SELECT c.nombre, COALESCE(SUM(fv.total), 0) AS total
        FROM factura_venta fv
        JOIN cliente c ON c.id = fv.cliente_id
        WHERE fv.empresa_id = :empresa_id AND fv.estado != 'ANULADA'
        GROUP BY c.nombre
        ORDER BY total DESC
        LIMIT 10
        """),
        {"empresa_id": empresa_id},
    )
    top_c = [
        {"nombre": r.nombre, "total": float(r.total or 0)}
        for r in top_clientes.fetchall()
    ]

    antiguedad_cxc = await db.execute(
        text("""
        SELECT c.nombre,
            COALESCE(SUM(CASE WHEN fv.fecha_vencimiento < CURRENT_DATE - 90 THEN fv.total ELSE 0 END), 0) AS mas_90,
            COALESCE(SUM(CASE WHEN fv.fecha_vencimiento BETWEEN CURRENT_DATE - 90 AND CURRENT_DATE - 61 THEN fv.total ELSE 0 END), 0) AS entre_60_90,
            COALESCE(SUM(CASE WHEN fv.fecha_vencimiento BETWEEN CURRENT_DATE - 60 AND CURRENT_DATE - 31 THEN fv.total ELSE 0 END), 0) AS entre_30_60,
            COALESCE(SUM(CASE WHEN fv.fecha_vencimiento BETWEEN CURRENT_DATE - 30 AND CURRENT_DATE THEN fv.total ELSE 0 END), 0) AS entre_0_30,
            COALESCE(SUM(fv.total), 0) AS saldo_total
        FROM factura_venta fv
        JOIN cliente c ON c.id = fv.cliente_id
        WHERE fv.empresa_id = :empresa_id AND fv.estado NOT IN ('COBRADA', 'ANULADA')
        GROUP BY c.nombre
        ORDER BY saldo_total DESC
        LIMIT 10
        """),
        {"empresa_id": empresa_id},
    )
    ant_cxc = [
        {
            "nombre": r.nombre,
            "mas_90": float(r.mas_90 or 0),
            "entre_60_90": float(r.entre_60_90 or 0),
            "entre_30_60": float(r.entre_30_60 or 0),
            "entre_0_30": float(r.entre_0_30 or 0),
            "saldo_total": float(r.saldo_total or 0),
        }
        for r in antiguedad_cxc.fetchall()
    ]

    ultimos_mov = await db.execute(
        text("""
        SELECT fecha, concepto, tipo, entrada, salida
        FROM movimiento_caja
        WHERE empresa_id = :empresa_id
        ORDER BY created_at DESC
        LIMIT 10
        """),
        {"empresa_id": empresa_id},
    )
    ult_mov = [
        {
            "fecha": str(r.fecha.date()) if hasattr(r.fecha, 'date') else str(r.fecha),
            "concepto": r.concepto,
            "tipo": r.tipo,
            "entrada": float(r.entrada or 0),
            "salida": float(r.salida or 0),
        }
        for r in ultimos_mov.fetchall()
    ]

    return {
        "kpis": {
            "ventas_totales": ventas_total,
            "gastos_totales": gastos_total,
            "utilidad_neta": utilidad,
            "margen": margen,
            "saldo_caja": saldo_caja,
            "cxc_pendiente": cxc_pendiente,
            "cxp_pendiente": cxp_pendiente,
            "inventario_valor": inventario_valor,
            "inventario_items": inventario_items,
            "clientes_activos": clientes_activos,
        },
        "ventas_por_mes": ventas_mes,
        "ingresos_vs_gastos": ingresos_vs_gastos,
        "gastos_por_categoria": [],
        "top_clientes": top_c,
        "antiguedad_cxc": ant_cxc,
        "ultimos_movimientos": ult_mov,
    }
