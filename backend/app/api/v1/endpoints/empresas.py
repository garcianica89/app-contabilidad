from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.models.empresa import Empresa
from app.domain.schemas import EmpresaCreate, EmpresaResponse

router = APIRouter()


@router.get("/", response_model=list[EmpresaResponse])
async def listar_empresas(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Empresa).where(Empresa.activo == True))
    return result.scalars().all()


@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obtener_empresa(
    empresa_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Empresa).where(Empresa.id == empresa_id, Empresa.activo == True)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa


@router.post("/", response_model=EmpresaResponse, status_code=201)
async def crear_empresa(
    data: EmpresaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    empresa = Empresa(**data.model_dump())
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa
