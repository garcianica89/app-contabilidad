from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.impuesto import Impuesto
from app.domain.schemas import ImpuestoCreate, ImpuestoUpdate, ImpuestoResponse

router = APIRouter()


@router.get("/", response_model=list[ImpuestoResponse])
async def listar_impuestos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    tipo: str | None = None,
):
    query = select(Impuesto).where(Impuesto.empresa_id == current_user.empresa_id)
    if tipo:
        query = query.where(Impuesto.tipo == tipo)
    query = query.order_by(Impuesto.codigo)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{impuesto_id}", response_model=ImpuestoResponse)
async def obtener_impuesto(
    impuesto_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Impuesto).where(
            Impuesto.id == impuesto_id,
            Impuesto.empresa_id == current_user.empresa_id,
        )
    )
    i = result.scalar_one_or_none()
    if not i:
        raise HTTPException(status_code=404, detail="Impuesto no encontrado")
    return i


@router.post("/", response_model=ImpuestoResponse, status_code=201)
async def crear_impuesto(
    data: ImpuestoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(Impuesto).where(
            Impuesto.empresa_id == current_user.empresa_id,
            Impuesto.codigo == data.codigo,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un impuesto con ese codigo")

    i = Impuesto(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(i)
    await db.commit()
    await db.refresh(i)
    return i


@router.put("/{impuesto_id}", response_model=ImpuestoResponse)
async def actualizar_impuesto(
    impuesto_id: uuid.UUID,
    data: ImpuestoUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Impuesto).where(
            Impuesto.id == impuesto_id,
            Impuesto.empresa_id == current_user.empresa_id,
        )
    )
    i = result.scalar_one_or_none()
    if not i:
        raise HTTPException(status_code=404, detail="Impuesto no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(i, key, value)
    await db.commit()
    await db.refresh(i)
    return i


@router.delete("/{impuesto_id}", status_code=204)
async def eliminar_impuesto(
    impuesto_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Impuesto).where(
            Impuesto.id == impuesto_id,
            Impuesto.empresa_id == current_user.empresa_id,
        )
    )
    i = result.scalar_one_or_none()
    if not i:
        raise HTTPException(status_code=404, detail="Impuesto no encontrado")
    await db.delete(i)
    await db.commit()
