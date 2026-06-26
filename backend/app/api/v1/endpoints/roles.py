from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.rol import Rol
from app.domain.models.usuario import Usuario
from pydantic import BaseModel

router = APIRouter()


class RolCreate(BaseModel):
    nombre: str
    descripcion: str | None = None


class RolResponse(BaseModel):
    id: str
    nombre: str
    descripcion: str | None
    activo: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[RolResponse])
async def listar_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Rol).where(Rol.empresa_id == current_user.empresa_id, Rol.activo == True)
    )
    return result.scalars().all()


@router.post("/", response_model=RolResponse, status_code=201)
async def crear_rol(
    data: RolCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    rol = Rol(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol
