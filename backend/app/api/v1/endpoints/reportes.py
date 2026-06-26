from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.periodo import PeriodoContable
from app.service.reporte_service import ReporteService

router = APIRouter()


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


@router.get("/balance-comprobacion")
async def balance_comprobacion(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID | None = None,
    nivel: int = 4,
):
    svc = ReporteService(db, current_user.empresa_id)
    return await svc.balance_comprobacion(periodo_id=periodo_id, incluir_ceros=True)


@router.get("/balance-general")
async def balance_general(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID | None = None,
):
    periodo = await _resolver_periodo(db, current_user.empresa_id, periodo_id)
    svc = ReporteService(db, current_user.empresa_id)
    return await svc.balance_general(fecha_corte=periodo.fecha_fin, periodo_id=periodo.id)


@router.get("/estado-resultados")
async def estado_resultados(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID | None = None,
):
    periodo = await _resolver_periodo(db, current_user.empresa_id, periodo_id)
    svc = ReporteService(db, current_user.empresa_id)
    return await svc.estado_resultados(
        fecha_inicio=periodo.fecha_inicio,
        fecha_fin=periodo.fecha_fin,
        periodo_id=periodo.id,
    )


@router.get("/mayor-general")
async def mayor_general(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    cuenta_id: uuid.UUID,
    fecha_desde: date,
    fecha_hasta: date,
):
    svc = ReporteService(db, current_user.empresa_id)
    return await svc.mayor_general(cuenta_id, fecha_desde, fecha_hasta)


@router.get("/flujo-efectivo")
async def flujo_efectivo(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    fecha_desde: date,
    fecha_hasta: date,
):
    svc = ReporteService(db, current_user.empresa_id)
    return await svc.flujo_efectivo(fecha_desde, fecha_hasta)
