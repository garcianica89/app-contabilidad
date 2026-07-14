from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.parametro import Parametro
from app.domain.schemas import ParametroCreate, ParametroUpdate, ParametroResponse

router = APIRouter()


@router.get("/", response_model=list[ParametroResponse])
async def listar_parametros(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    grupo: str | None = None,
):
    query = select(Parametro).where(Parametro.empresa_id == current_user.empresa_id)
    if grupo:
        query = query.where(Parametro.grupo == grupo)
    query = query.order_by(Parametro.grupo, Parametro.clave)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{parametro_id}", response_model=ParametroResponse)
async def obtener_parametro(
    parametro_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Parametro).where(
            Parametro.id == parametro_id,
            Parametro.empresa_id == current_user.empresa_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Parametro no encontrado")
    return p


@router.post("/", response_model=ParametroResponse, status_code=201)
async def crear_parametro(
    data: ParametroCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(Parametro).where(
            Parametro.empresa_id == current_user.empresa_id,
            Parametro.grupo == data.grupo,
            Parametro.clave == data.clave,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un parametro con ese grupo y clave")

    p = Parametro(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@router.put("/{parametro_id}", response_model=ParametroResponse)
async def actualizar_parametro(
    parametro_id: uuid.UUID,
    data: ParametroUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Parametro).where(
            Parametro.id == parametro_id,
            Parametro.empresa_id == current_user.empresa_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Parametro no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(p, key, value)
    await db.commit()
    await db.refresh(p)
    return p


@router.delete("/{parametro_id}", status_code=204)
async def eliminar_parametro(
    parametro_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Parametro).where(
            Parametro.id == parametro_id,
            Parametro.empresa_id == current_user.empresa_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Parametro no encontrado")
    await db.delete(p)
    await db.commit()
