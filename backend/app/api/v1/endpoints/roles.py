from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.rol import Rol
from app.domain.models.permiso import Permiso
from app.domain.models.usuario import Usuario
from pydantic import BaseModel

router = APIRouter()


class RolCreate(BaseModel):
    nombre: str
    descripcion: str | None = None


class RolUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    activo: bool | None = None


class RolResponse(BaseModel):
    id: str
    nombre: str
    descripcion: str | None
    activo: bool

    class Config:
        from_attributes = True


class PermisoResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    modulo: str

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


@router.put("/{rol_id}", response_model=RolResponse)
async def actualizar_rol(
    rol_id: uuid.UUID,
    data: RolUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    rol = await db.get(Rol, rol_id)
    if not rol or rol.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rol, field, value)
    await db.commit()
    await db.refresh(rol)
    return rol


@router.delete("/{rol_id}", status_code=204)
async def eliminar_rol(
    rol_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    rol = await db.get(Rol, rol_id)
    if not rol or rol.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    await db.delete(rol)
    await db.commit()


@router.get("/{rol_id}/permisos", response_model=list[PermisoResponse])
async def get_permisos_rol(
    rol_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    rol = await db.get(Rol, rol_id)
    if not rol or rol.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol.permisos


class AsignarPermisosInput(BaseModel):
    permiso_ids: list[uuid.UUID]


@router.post("/{rol_id}/permisos")
async def asignar_permisos_rol(
    rol_id: uuid.UUID,
    data: AsignarPermisosInput,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    rol = await db.get(Rol, rol_id)
    if not rol or rol.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    await db.execute(
        text("DELETE FROM rol_permiso WHERE rol_id = :rid"),
        {"rid": rol_id},
    )

    for pid in data.permiso_ids:
        permiso = await db.get(Permiso, pid)
        if permiso:
            rol.permisos.append(permiso)

    await db.commit()
    return {"status": "ok", "permisos_asignados": len(data.permiso_ids)}
