from typing import Annotated
import uuid
import io

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.usuario import Usuario
from app.domain.models.periodo import PeriodoContable
from app.service.reporte_service import ReporteService
from app.service.balance_service import BalanceService

router = APIRouter()


class RecalcularSaldosInput(BaseModel):
    periodo_id: uuid.UUID
    cuenta_id: uuid.UUID | None = None
    centro_costo_id: uuid.UUID | None = None


async def _resolver_periodo(
    db: AsyncSession, empresa_id: uuid.UUID, periodo_id: uuid.UUID | None
) -> PeriodoContable:
    if not periodo_id:
        result = await db.execute(
            select(PeriodoContable).where(
                PeriodoContable.empresa_id == empresa_id,
                PeriodoContable.cerrado == False,
            ).order_by(PeriodoContable.fecha_fin.desc()).limit(1)
        )
        periodo = result.scalar_one_or_none()
    else:
        periodo = await db.get(PeriodoContable, periodo_id)
    if not periodo:
        raise HTTPException(status_code=404, detail="Periodo contable no encontrado")
    return periodo


def _to_xlsx(rows: list[dict], sheet_name: str = "Reporte") -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for r in rows:
            ws.append([r[h] for h in headers])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


# ── Balanza de Comprobacion ──


@router.get("/balance-comprobacion")
async def balance_comprobacion(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    cuenta_id: uuid.UUID | None = None,
    nivel_maximo: int = 99,
    centro_costo_id: uuid.UUID | None = None,
    solo_diario: bool = False,
    formato: str = "json",
):
    """
    Balanza de comprobacion con filtros:
    - periodo_id: periodo contable exacto (usa cache si existe)
    - fecha_desde/fecha_hasta: rango de fechas (alternativa a periodo)
    - cuenta_id: filtra una cuenta especifica y sus hijas
    - nivel_maximo: profundidad maxima del catalogo (1-99)
    - centro_costo_id: filtro por centro de costo
    - solo_diario: true = solo asientos tipo DIARIO
    - formato: json (default) o xlsx
    """
    svc = BalanceService(db, current_user.empresa_id)
    data = await svc.balance_comprobacion(
        periodo_id=periodo_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cuenta_id=cuenta_id,
        nivel_maximo=nivel_maximo,
        centro_costo_id=centro_costo_id,
        solo_diario=solo_diario,
    )
    if formato == "xlsx":
        xlsx = _to_xlsx(data, "Balance Comprobacion")
        return Response(
            content=xlsx,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=balance_comprobacion.xlsx"},
        )
    return data


@router.post("/recalcular-saldos")
async def recalcular_saldos(
    data: RecalcularSaldosInput,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("CONTABILIDAD_CREAR"))],
):
    """
    Recalcula y cachea los saldos de todas (o una) cuentas para un periodo.
    Toma el saldo_final del periodo anterior como base,
    suma debe/haber del periodo actual y almacena en cuenta_saldo.
    """
    svc = BalanceService(db, current_user.empresa_id)
    try:
        count = await svc.recalcular_saldos(
            periodo_id=data.periodo_id,
            cuenta_id=data.cuenta_id,
            centro_costo_id=data.centro_costo_id,
        )
        return {"mensaje": "Saldos recalculados", "periodo_id": str(data.periodo_id), "cuentas": count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Legacy endpoints (delegados al ReporteService existente) ──


@router.get("/balance-general")
async def balance_general(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID | None = None,
    formato: str = "json",
):
    periodo = await _resolver_periodo(db, current_user.empresa_id, periodo_id)
    svc = ReporteService(db, current_user.empresa_id)
    data = await svc.balance_general(fecha_corte=periodo.fecha_fin, periodo_id=periodo.id)
    if formato == "xlsx":
        rows = []
        for section in ("activo", "pasivo", "patrimonio"):
            for item in data.get(section, {}).get("cuentas", []):
                rows.append({"seccion": section, **item})
        xlsx = _to_xlsx(rows, "Balance General")
        return Response(
            content=xlsx,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=balance_general.xlsx"},
        )
    return data


@router.get("/estado-resultados")
async def estado_resultados(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID | None = None,
    formato: str = "json",
):
    periodo = await _resolver_periodo(db, current_user.empresa_id, periodo_id)
    svc = ReporteService(db, current_user.empresa_id)
    data = await svc.estado_resultados(
        fecha_inicio=periodo.fecha_inicio,
        fecha_fin=periodo.fecha_fin,
        periodo_id=periodo.id,
    )
    if formato == "xlsx":
        rows = []
        for section in ("ingresos", "costos", "gastos"):
            for item in data.get(section, {}).get("cuentas", []):
                rows.append({"seccion": section, **item})
        xlsx = _to_xlsx(rows, "Estado Resultados")
        return Response(
            content=xlsx,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=estado_resultados.xlsx"},
        )
    return data


@router.get("/mayor-general")
async def mayor_general(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    cuenta_id: uuid.UUID,
    fecha_desde: date,
    fecha_hasta: date,
    formato: str = "json",
):
    svc = ReporteService(db, current_user.empresa_id)
    data = await svc.mayor_general(cuenta_id, fecha_desde, fecha_hasta)
    if formato == "xlsx":
        xlsx = _to_xlsx(data, "Mayor General")
        return Response(
            content=xlsx,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=mayor_general.xlsx"},
        )
    return data


@router.get("/flujo-efectivo")
async def flujo_efectivo(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    fecha_desde: date,
    fecha_hasta: date,
    formato: str = "json",
):
    svc = ReporteService(db, current_user.empresa_id)
    data = await svc.flujo_efectivo(fecha_desde, fecha_hasta)
    if formato == "xlsx":
        rows = []
        for section in ("operacion", "inversion", "financiamiento"):
            for mov in data.get(f"actividades_{section}", {}).get("movimientos", []):
                rows.append({"actividad": section, **mov})
        xlsx = _to_xlsx(rows, "Flujo Efectivo")
        return Response(
            content=xlsx,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=flujo_efectivo.xlsx"},
        )
    return data
