from typing import Annotated
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.permiso import Permiso, UsuarioPermiso
from app.service.permission_service import get_user_permissions, user_has_perm
from pydantic import BaseModel

router = APIRouter()


class PermisoCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None
    modulo: str


class PermisoUpdate(BaseModel):
    codigo: str | None = None
    nombre: str | None = None
    descripcion: str | None = None
    modulo: str | None = None


class PermisoResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    descripcion: str | None
    modulo: str

    class Config:
        from_attributes = True


class AsignarPermisoUsuario(BaseModel):
    permiso_id: uuid.UUID
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    allow: bool = True


@router.get("/", response_model=list[PermisoResponse])
async def listar_permisos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    modulo: str | None = None,
):
    query = select(Permiso)
    if modulo:
        query = query.where(Permiso.modulo == modulo)
    query = query.order_by(Permiso.modulo, Permiso.codigo)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/mis-permisos")
async def mis_permisos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Returns all permission codes the current user has (role + direct)."""
    codes = await get_user_permissions(db, current_user.id)
    return [{"codigo": c} for c in codes]


@router.get("/mis-permisos/entidad/{entity_type}/{entity_id}")
async def mis_permisos_entidad(
    entity_type: str,
    entity_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Returns permissions scoped to a specific entity (e.g., a cuenta_contable or asiento)."""
    codes = await get_user_permissions(db, current_user.id, entity_type, entity_id)
    return [{"codigo": c} for c in codes]


@router.get("/usuario/{usuario_id}/permisos")
async def listar_permisos_usuario(
    usuario_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
):
    """Admin: list effective permissions for a specific user (role + direct)."""
    codes = await get_user_permissions(db, usuario_id, entity_type, entity_id)
    return [{"codigo": c} for c in codes]


@router.post("/usuario/{usuario_id}/permisos", status_code=201)
async def asignar_permiso_usuario(
    usuario_id: uuid.UUID,
    data: AsignarPermisoUsuario,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Assign a direct permission to a user, optionally scoped to an entity."""
    existing = await db.execute(
        select(UsuarioPermiso).where(
            UsuarioPermiso.usuario_id == usuario_id,
            UsuarioPermiso.permiso_id == data.permiso_id,
            UsuarioPermiso.entity_type == data.entity_type,
            UsuarioPermiso.entity_id == data.entity_id,
        )
    )
    up = existing.scalar_one_or_none()
    if up:
        up.allow = data.allow
    else:
        up = UsuarioPermiso(
            usuario_id=usuario_id,
            permiso_id=data.permiso_id,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            allow=data.allow,
        )
        db.add(up)
    await db.commit()
    return {"mensaje": "Permiso asignado"}


@router.delete("/usuario/{usuario_id}/permisos/{up_id}", status_code=204)
async def eliminar_permiso_usuario(
    usuario_id: uuid.UUID,
    up_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    up = await db.get(UsuarioPermiso, up_id)
    if not up or up.usuario_id != usuario_id:
        raise HTTPException(404, "Asignacion no encontrada")
    await db.delete(up)
    await db.commit()


@router.post("/", response_model=PermisoResponse, status_code=201)
async def crear_permiso(
    data: PermisoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(select(Permiso).where(Permiso.codigo == data.codigo))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Permiso con este codigo ya existe")

    permiso = Permiso(**data.model_dump())
    db.add(permiso)
    await db.commit()
    await db.refresh(permiso)
    return permiso


@router.put("/{permiso_id}", response_model=PermisoResponse)
async def actualizar_permiso(
    permiso_id: uuid.UUID,
    data: PermisoUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(Permiso).where(Permiso.id == permiso_id))
    permiso = result.scalar_one_or_none()
    if not permiso:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(permiso, key, value)

    await db.commit()
    await db.refresh(permiso)
    return permiso


@router.delete("/{permiso_id}", status_code=204)
async def eliminar_permiso(
    permiso_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(Permiso).where(Permiso.id == permiso_id))
    permiso = result.scalar_one_or_none()
    if not permiso:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")

    await db.delete(permiso)
    await db.commit()
