from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.domain.models.usuario import Usuario
from app.service.permission_service import user_has_perm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Usuario:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")

    return user


# Mapeo de nombres de accion antiguos → nuevos
_OLD_ACTION_MAP = {
    'ver': 'leer',
    'editar': 'actualizar',
}


def _normalize_perm_code(raw: str) -> tuple[str, str, str]:
    lowered = raw.lower().strip()

    if '.' in lowered:
        parts = lowered.split('.', 1)
        return (parts[0], parts[1], lowered)

    if '_' in lowered:
        parts = lowered.split('_', 1)
        mod = parts[0]
        act = parts[1]
        act_normalized = _OLD_ACTION_MAP.get(act, act)
        return (mod, act_normalized, f"{mod}.{act_normalized}")

    return ('', lowered, lowered)


def require_permission(perm_codigo: str):
    """Dependency factory. Checks role-based AND direct user permissions via permission_service."""
    modulo, accion, codigo_normalizado = _normalize_perm_code(perm_codigo)

    async def _check(
        user: Annotated[Usuario, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> Usuario:
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para esta accion")

        has = await user_has_perm(db, user.id, codigo_normalizado)
        if not has:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permiso '{perm_codigo}' requerido")
        return user

    return _check


def require_entity_permission(perm_codigo: str, entity_type: str):
    """Like require_permission but also checks entity-scoped permission."""
    modulo, accion, codigo_normalizado = _normalize_perm_code(perm_codigo)

    async def _check(
        entity_id: str,
        user: Annotated[Usuario, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> Usuario:
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para esta accion")

        has = await user_has_perm(db, user.id, codigo_normalizado, entity_type, entity_id)
        if not has:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permiso '{perm_codigo}' requerido para este recurso")
        return user

    return _check
