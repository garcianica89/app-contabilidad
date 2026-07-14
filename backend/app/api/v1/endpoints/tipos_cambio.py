from typing import Annotated
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.tipo_cambio_hist import TipoCambioHist
from app.domain.schemas import TipoCambioHistCreate, TipoCambioHistResponse

router = APIRouter()


@router.get("/", response_model=list[TipoCambioHistResponse])
async def listar_tipos_cambio(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    moneda_id: uuid.UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
):
    query = select(TipoCambioHist).where(
        TipoCambioHist.empresa_id == current_user.empresa_id,
    )
    if moneda_id:
        query = query.where(TipoCambioHist.moneda_id == moneda_id)
    if fecha_desde:
        query = query.where(TipoCambioHist.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.where(TipoCambioHist.fecha <= fecha_hasta)
    query = query.order_by(TipoCambioHist.fecha.desc(), TipoCambioHist.moneda_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{tipo_cambio_id}", response_model=TipoCambioHistResponse)
async def obtener_tipo_cambio(
    tipo_cambio_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(TipoCambioHist).where(
            TipoCambioHist.id == tipo_cambio_id,
            TipoCambioHist.empresa_id == current_user.empresa_id,
        )
    )
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="Tipo de cambio no encontrado")
    return tc


@router.post("/", response_model=TipoCambioHistResponse, status_code=201)
async def crear_tipo_cambio(
    data: TipoCambioHistCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(TipoCambioHist).where(
            TipoCambioHist.empresa_id == current_user.empresa_id,
            TipoCambioHist.moneda_id == data.moneda_id,
            TipoCambioHist.fecha == data.fecha,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un tipo de cambio para esa moneda y fecha")

    tc = TipoCambioHist(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return tc


@router.delete("/{tipo_cambio_id}", status_code=204)
async def eliminar_tipo_cambio(
    tipo_cambio_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(TipoCambioHist).where(
            TipoCambioHist.id == tipo_cambio_id,
            TipoCambioHist.empresa_id == current_user.empresa_id,
        )
    )
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="Tipo de cambio no encontrado")
    await db.delete(tc)
    await db.commit()
