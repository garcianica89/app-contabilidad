from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.proveedor import Proveedor
from pydantic import BaseModel

router = APIRouter()


class ProveedorCreate(BaseModel):
    codigo: str | None = None
    nombre: str
    ruc: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    plazo_credito: int = 30


class ProveedorResponse(BaseModel):
    id: uuid.UUID
    codigo: str | None
    nombre: str
    saldo: float
    activo: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ProveedorResponse])
async def listar_proveedores(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Proveedor).where(
            Proveedor.empresa_id == current_user.empresa_id,
            Proveedor.activo == True,
        ).order_by(Proveedor.nombre)
    )
    return result.scalars().all()


@router.get("/{proveedor_id}", response_model=ProveedorResponse)
async def obtener_proveedor(
    proveedor_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Proveedor).where(
            Proveedor.id == proveedor_id,
            Proveedor.empresa_id == current_user.empresa_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return p


@router.post("/", response_model=ProveedorResponse, status_code=201)
async def crear_proveedor(
    data: ProveedorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    proveedor = Proveedor(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(proveedor)
    await db.commit()
    await db.refresh(proveedor)
    return proveedor
