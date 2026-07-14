from typing import Annotated
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.tipo_cuenta_banco import TipoCuentaBanco

router = APIRouter()


class TipoCuentaBancoOut(BaseModel):
    id: str
    codigo: str
    nombre: str
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TipoCuentaBancoCreate(BaseModel):
    codigo: str
    nombre: str


class TipoCuentaBancoUpdate(BaseModel):
    codigo: str | None = None
    nombre: str | None = None
    activo: bool | None = None


@router.get("/", response_model=list[TipoCuentaBancoOut])
async def listar_tipos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    solo_activos: bool = False,
):
    q = select(TipoCuentaBanco).where(TipoCuentaBanco.empresa_id == current_user.empresa_id)
    if solo_activos:
        q = q.where(TipoCuentaBanco.activo == True)
    q = q.order_by(TipoCuentaBanco.codigo)
    r = await db.execute(q)
    return [TipoCuentaBancoOut(id=str(t.id), codigo=t.codigo, nombre=t.nombre, activo=t.activo, created_at=t.created_at) for t in r.scalars().all()]


@router.post("/", response_model=TipoCuentaBancoOut, status_code=201)
async def crear_tipo(
    data: TipoCuentaBancoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    exist = await db.execute(select(TipoCuentaBanco).where(
        TipoCuentaBanco.empresa_id == current_user.empresa_id,
        TipoCuentaBanco.codigo == data.codigo,
    ))
    if exist.scalar_one_or_none():
        raise HTTPException(400, "Ya existe un tipo con ese codigo")
    t = TipoCuentaBanco(empresa_id=current_user.empresa_id, codigo=data.codigo, nombre=data.nombre)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return TipoCuentaBancoOut(id=str(t.id), codigo=t.codigo, nombre=t.nombre, activo=t.activo, created_at=t.created_at)


@router.put("/{tipo_id}", response_model=TipoCuentaBancoOut)
async def actualizar_tipo(
    tipo_id: uuid.UUID,
    data: TipoCuentaBancoUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    t = await db.get(TipoCuentaBanco, tipo_id)
    if not t or t.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Tipo no encontrado")
    if data.codigo is not None:
        t.codigo = data.codigo
    if data.nombre is not None:
        t.nombre = data.nombre
    if data.activo is not None:
        t.activo = data.activo
    await db.commit()
    await db.refresh(t)
    return TipoCuentaBancoOut(id=str(t.id), codigo=t.codigo, nombre=t.nombre, activo=t.activo, created_at=t.created_at)


@router.delete("/{tipo_id}", status_code=204)
async def eliminar_tipo(
    tipo_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    t = await db.get(TipoCuentaBanco, tipo_id)
    if not t or t.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Tipo no encontrado")
    await db.delete(t)
    await db.commit()
