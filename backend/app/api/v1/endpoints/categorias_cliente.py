import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.domain.models.categoria_cliente import CategoriaCliente
from app.api.deps import get_current_user

router = APIRouter()


class CategoriaClienteCreate(BaseModel):
    nombre: str
    cuenta_tercero_id: Optional[uuid.UUID] = None
    cuenta_banco_id: Optional[uuid.UUID] = None
    cuenta_caja_id: Optional[uuid.UUID] = None


class CategoriaClienteResponse(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    nombre: str
    cuenta_tercero_id: Optional[uuid.UUID] = None
    cuenta_banco_id: Optional[uuid.UUID] = None
    cuenta_caja_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


@router.get("", response_model=list[CategoriaClienteResponse])
async def listar_categorias(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    empresa_id = usuario["empresa_id"]
    result = await db.execute(
        select(CategoriaCliente).where(CategoriaCliente.empresa_id == empresa_id)
    )
    return result.scalars().all()


@router.post("", response_model=CategoriaClienteResponse)
async def crear_categoria(
    data: CategoriaClienteCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    cat = CategoriaCliente(empresa_id=usuario["empresa_id"], **data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.put("/{categoria_id}", response_model=CategoriaClienteResponse)
async def actualizar_categoria(
    categoria_id: uuid.UUID,
    data: CategoriaClienteCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    cat = await db.get(CategoriaCliente, categoria_id)
    if not cat or cat.empresa_id != usuario["empresa_id"]:
        raise HTTPException(404, "Categoria no encontrada")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/{categoria_id}")
async def eliminar_categoria(
    categoria_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    cat = await db.get(CategoriaCliente, categoria_id)
    if not cat or cat.empresa_id != usuario["empresa_id"]:
        raise HTTPException(404, "Categoria no encontrada")
    await db.delete(cat)
    await db.commit()
    return {"ok": True}
