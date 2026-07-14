from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.accounting.models import JournalType
from app.domain.schemas import (
    JournalTypeCreate,
    JournalTypeUpdate,
    JournalTypeResponse,
)

router = APIRouter()


@router.get("/", response_model=list[JournalTypeResponse])
async def listar_tipos_asiento(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(JournalType)
        .where(JournalType.company_id == current_user.empresa_id)
        .order_by(JournalType.code)
    )
    return result.scalars().all()


@router.get("/{tipo_asiento_id}", response_model=JournalTypeResponse)
async def obtener_tipo_asiento(
    tipo_asiento_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(JournalType).where(
            JournalType.id == tipo_asiento_id,
            JournalType.company_id == current_user.empresa_id,
        )
    )
    jt = result.scalar_one_or_none()
    if not jt:
        raise HTTPException(status_code=404, detail="Tipo de asiento no encontrado")
    return jt


@router.post("/", response_model=JournalTypeResponse, status_code=201)
async def crear_tipo_asiento(
    data: JournalTypeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(JournalType).where(
            JournalType.company_id == current_user.empresa_id,
            JournalType.code == data.code,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un tipo de asiento con ese codigo")

    jt = JournalType(company_id=current_user.empresa_id, **data.model_dump())
    db.add(jt)
    await db.commit()
    await db.refresh(jt)
    return jt


@router.put("/{tipo_asiento_id}", response_model=JournalTypeResponse)
async def actualizar_tipo_asiento(
    tipo_asiento_id: uuid.UUID,
    data: JournalTypeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(JournalType).where(
            JournalType.id == tipo_asiento_id,
            JournalType.company_id == current_user.empresa_id,
        )
    )
    jt = result.scalar_one_or_none()
    if not jt:
        raise HTTPException(status_code=404, detail="Tipo de asiento no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(jt, key, value)
    await db.commit()
    await db.refresh(jt)
    return jt


@router.delete("/{tipo_asiento_id}", status_code=204)
async def eliminar_tipo_asiento(
    tipo_asiento_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    jt = await db.get(JournalType, tipo_asiento_id)
    if not jt or jt.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Tipo de asiento no encontrado")
    await db.delete(jt)
    await db.commit()
