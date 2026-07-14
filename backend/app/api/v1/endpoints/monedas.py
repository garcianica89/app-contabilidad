from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.moneda import Moneda
from app.domain.schemas import MonedaCreate, MonedaUpdate, MonedaResponse

router = APIRouter()


@router.get("", response_model=list[MonedaResponse])
async def listar_monedas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(Moneda).order_by(Moneda.codigo))
    return result.scalars().all()


@router.get("/{moneda_id}", response_model=MonedaResponse)
async def obtener_moneda(
    moneda_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(Moneda).where(Moneda.id == moneda_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")
    return m


@router.post("", response_model=MonedaResponse, status_code=201)
async def crear_moneda(
    data: MonedaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(select(Moneda).where(Moneda.codigo == data.codigo))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe una moneda con ese codigo")

    m = Moneda(**data.model_dump())
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


@router.put("/{moneda_id}", response_model=MonedaResponse)
async def actualizar_moneda(
    moneda_id: uuid.UUID,
    data: MonedaUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(Moneda).where(Moneda.id == moneda_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(m, key, value)
    await db.commit()
    await db.refresh(m)
    return m


@router.delete("/{moneda_id}", status_code=204)
async def eliminar_moneda(
    moneda_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(Moneda).where(Moneda.id == moneda_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")
    await db.delete(m)
    await db.commit()
