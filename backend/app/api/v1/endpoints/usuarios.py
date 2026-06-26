from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.rol import Rol
from app.domain.schemas import UsuarioCreate, UsuarioResponse
from pydantic import BaseModel

router = APIRouter()


class UsuarioUpdate(BaseModel):
    nombre_completo: str | None = None
    email: str | None = None
    password: str | None = None
    activo: bool | None = None


class UsuarioDetailResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    nombre_completo: str
    activo: bool
    roles: list[dict]
    ultimo_acceso: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=list[UsuarioDetailResponse])
async def listar_usuarios(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    solo_activos: bool = True,
):
    query = select(Usuario).where(
        Usuario.empresa_id == current_user.empresa_id,
    )
    if solo_activos:
        query = query.where(Usuario.activo == True)
    query = query.order_by(Usuario.nombre_completo)
    result = await db.execute(query)
    users = result.scalars().all()

    response = []
    for u in users:
        roles_q = await db.execute(
            text("""
            SELECT r.id, r.nombre FROM rol r
            JOIN usuario_rol ur ON ur.rol_id = r.id
            WHERE ur.usuario_id = :uid
            """),
            {"uid": u.id},
        )
        roles = [{"id": str(r.id), "nombre": r.nombre} for r in roles_q.fetchall()]
        response.append(UsuarioDetailResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            nombre_completo=u.nombre_completo,
            activo=u.activo,
            roles=roles,
            ultimo_acceso=str(u.ultimo_acceso) if u.ultimo_acceso else None,
            created_at=str(u.created_at),
        ))

    return response


@router.get("/{usuario_id}", response_model=UsuarioDetailResponse)
async def obtener_usuario(
    usuario_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    roles_q = await db.execute(
        text("""
        SELECT r.id, r.nombre FROM rol r
        JOIN usuario_rol ur ON ur.rol_id = r.id
        WHERE ur.usuario_id = :uid
        """),
        {"uid": user.id},
    )
    return UsuarioDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nombre_completo=user.nombre_completo,
        activo=user.activo,
        roles=[{"id": str(r.id), "nombre": r.nombre} for r in roles_q.fetchall()],
        ultimo_acceso=str(user.ultimo_acceso) if user.ultimo_acceso else None,
        created_at=str(user.created_at),
    )


@router.post("/", response_model=UsuarioDetailResponse, status_code=201)
async def crear_usuario(
    data: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(Usuario).where(
            (Usuario.username == data.username) | (Usuario.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username o email ya existe")

    user = Usuario(
        empresa_id=current_user.empresa_id,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        nombre_completo=data.nombre_completo,
    )
    db.add(user)
    await db.flush()

    roles_q = await db.execute(
        text("""
        SELECT r.id, r.nombre FROM rol r
        JOIN usuario_rol ur ON ur.rol_id = r.id
        WHERE ur.usuario_id = :uid
        """),
        {"uid": user.id},
    )
    await db.commit()
    await db.refresh(user)

    return UsuarioDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nombre_completo=user.nombre_completo,
        activo=user.activo,
        roles=[{"id": str(r.id), "nombre": r.nombre} for r in roles_q.fetchall()],
        ultimo_acceso=None,
        created_at=str(user.created_at),
    )


@router.put("/{usuario_id}", response_model=UsuarioDetailResponse)
async def actualizar_usuario(
    usuario_id: uuid.UUID,
    data: UsuarioUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.nombre_completo is not None:
        user.nombre_completo = data.nombre_completo
    if data.email is not None:
        user.email = data.email
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.activo is not None:
        user.activo = data.activo

    await db.commit()
    await db.refresh(user)

    roles_q = await db.execute(
        text("""
        SELECT r.id, r.nombre FROM rol r
        JOIN usuario_rol ur ON ur.rol_id = r.id
        WHERE ur.usuario_id = :uid
        """),
        {"uid": user.id},
    )
    return UsuarioDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nombre_completo=user.nombre_completo,
        activo=user.activo,
        roles=[{"id": str(r.id), "nombre": r.nombre} for r in roles_q.fetchall()],
        ultimo_acceso=str(user.ultimo_acceso) if user.ultimo_acceso else None,
        created_at=str(user.created_at),
    )


@router.post("/{usuario_id}/roles")
async def asignar_roles(
    usuario_id: uuid.UUID,
    rol_ids: list[uuid.UUID],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    await db.execute(
        text("DELETE FROM usuario_rol WHERE usuario_id = :uid"),
        {"uid": usuario_id},
    )

    for rid in rol_ids:
        await db.execute(
            text("INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (:uid, :rid) ON CONFLICT DO NOTHING"),
            {"uid": usuario_id, "rid": rid},
        )

    await db.commit()
    return {"mensaje": "Roles asignados exitosamente"}
