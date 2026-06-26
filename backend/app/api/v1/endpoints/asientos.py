from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.schemas import AsientoCreate, AsientoResponse
from app.service.asiento_service import AsientoService

router = APIRouter()


@router.post("/", response_model=AsientoResponse, status_code=201)
async def crear_asiento(
    data: AsientoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = AsientoService(db, current_user.id, current_user.empresa_id)
    try:
        asiento = await svc.crear_asiento(
            fecha=data.fecha,
            periodo_id=data.periodo_id,
            tipo=data.tipo,
            concepto=data.concepto,
            lineas_data=[l.model_dump() for l in data.lineas],
        )
        return asiento
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[AsientoResponse])
async def listar_asientos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    tipo: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    svc = AsientoService(db, current_user.id, current_user.empresa_id)
    return await svc.listar_asientos(
        periodo_id=periodo_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo=tipo,
        limit=limit,
        offset=offset,
    )


@router.get("/{asiento_id}")
async def obtener_asiento(
    asiento_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = AsientoService(db, current_user.id, current_user.empresa_id)
    asiento = await svc.obtener_asiento(asiento_id)
    if not asiento:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")

    return {
        "id": str(asiento.id),
        "numero": asiento.numero,
        "fecha": str(asiento.fecha),
        "tipo": asiento.tipo,
        "concepto": asiento.concepto,
        "reversado": asiento.reversado,
        "lineas": [
            {
                "cuenta_id": str(l.cuenta_id),
                "descripcion": l.descripcion,
                "debe_local": float(l.debe_local),
                "haber_local": float(l.haber_local),
                "debe_dolar": float(l.debe_dolar),
                "haber_dolar": float(l.haber_dolar),
            }
            for l in asiento.lineas
        ],
    }


@router.post("/{asiento_id}/reversar")
async def reversar_asiento(
    asiento_id: uuid.UUID,
    motivo: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = AsientoService(db, current_user.id, current_user.empresa_id)
    try:
        reversa = await svc.reversar_asiento(asiento_id, motivo)
        return {"mensaje": "Asiento reversado exitosamente", "reversa_id": str(reversa.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
