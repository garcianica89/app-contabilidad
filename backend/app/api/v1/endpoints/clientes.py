from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.cliente import Cliente
from app.domain.schemas import ClienteCreate, ClienteResponse

router = APIRouter()


@router.get("/", response_model=list[ClienteResponse])
async def listar_clientes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Cliente).where(
            Cliente.empresa_id == current_user.empresa_id,
            Cliente.activo == True,
        ).order_by(Cliente.nombre)
    )
    return result.scalars().all()


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obtener_cliente(
    cliente_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.empresa_id == current_user.empresa_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return c


@router.post("/", response_model=ClienteResponse, status_code=201)
async def crear_cliente(
    data: ClienteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    cliente = Cliente(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente
