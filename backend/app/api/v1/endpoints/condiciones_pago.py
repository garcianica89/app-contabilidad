from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.condicion_pago import CondicionPago
from app.domain.schemas import CondicionPagoCreate, CondicionPagoUpdate, CondicionPagoResponse

router = APIRouter()


@router.get("/", response_model=list[CondicionPagoResponse])
async def listar_condiciones_pago(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(CondicionPago).where(
            CondicionPago.empresa_id == current_user.empresa_id,
        ).order_by(CondicionPago.codigo)
    )
    return result.scalars().all()


@router.get("/{condicion_pago_id}", response_model=CondicionPagoResponse)
async def obtener_condicion_pago(
    condicion_pago_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(CondicionPago).where(
            CondicionPago.id == condicion_pago_id,
            CondicionPago.empresa_id == current_user.empresa_id,
        )
    )
    cp = result.scalar_one_or_none()
    if not cp:
        raise HTTPException(status_code=404, detail="Condicion de pago no encontrada")
    return cp


@router.post("/", response_model=CondicionPagoResponse, status_code=201)
async def crear_condicion_pago(
    data: CondicionPagoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(CondicionPago).where(
            CondicionPago.empresa_id == current_user.empresa_id,
            CondicionPago.codigo == data.codigo,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe una condicion de pago con ese codigo")

    cp = CondicionPago(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(cp)
    await db.commit()
    await db.refresh(cp)
    return cp


@router.put("/{condicion_pago_id}", response_model=CondicionPagoResponse)
async def actualizar_condicion_pago(
    condicion_pago_id: uuid.UUID,
    data: CondicionPagoUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(CondicionPago).where(
            CondicionPago.id == condicion_pago_id,
            CondicionPago.empresa_id == current_user.empresa_id,
        )
    )
    cp = result.scalar_one_or_none()
    if not cp:
        raise HTTPException(status_code=404, detail="Condicion de pago no encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cp, key, value)
    await db.commit()
    await db.refresh(cp)
    return cp


@router.delete("/{condicion_pago_id}", status_code=204)
async def eliminar_condicion_pago(
    condicion_pago_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(CondicionPago).where(
            CondicionPago.id == condicion_pago_id,
            CondicionPago.empresa_id == current_user.empresa_id,
        )
    )
    cp = result.scalar_one_or_none()
    if not cp:
        raise HTTPException(status_code=404, detail="Condicion de pago no encontrada")
    await db.delete(cp)
    await db.commit()
