from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.domain.models.usuario import Usuario
from app.domain.schemas import LoginRequest, TokenResponse, UsuarioCreate, UsuarioResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Usuario).where(Usuario.username == data.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    token = create_access_token({"sub": str(user.id), "empresa_id": str(user.empresa_id)})
    return TokenResponse(access_token=token)


@router.post("/register", response_model=UsuarioResponse, status_code=201)
async def register(
    data: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(
        select(Usuario).where(
            (Usuario.username == data.username) | (Usuario.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username o email ya existe",
        )

    user = Usuario(
        empresa_id=data.empresa_id,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        nombre_completo=data.nombre_completo,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
