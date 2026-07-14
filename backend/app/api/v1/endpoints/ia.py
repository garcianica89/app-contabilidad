import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.ia import AnalisisIA
from app.domain.models.usuario import Usuario

router = APIRouter()

class AnalisisIAResponse(BaseModel):
    id: str
    tipo: str
    modulo: str | None
    titulo: str | None
    descripcion: str | None
    datos_entrada: dict | None
    resultado: dict | None
    class Config: from_attributes = True

class AnalisisIACreate(BaseModel):
    tipo: str = Field(max_length=30)
    modulo: str | None = None
    titulo: str | None = Field(max_length=200)
    descripcion: str | None = None
    datos_entrada: dict | None = None

@router.get("", response_model=list[AnalisisIAResponse])
async def list_analisis(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
    tipo: str | None = Query(None),
):
    q = select(AnalisisIA).where(AnalisisIA.empresa_id == user.empresa_id)
    if tipo:
        q = q.where(AnalisisIA.tipo == tipo)
    q = q.order_by(AnalisisIA.created_at.desc())
    r = await db.execute(q)
    return r.scalars().all()

@router.post("", response_model=AnalisisIAResponse, status_code=201)
async def create_analisis(
    data: AnalisisIACreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    obj = AnalisisIA(empresa_id=user.empresa_id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get("/{id}", response_model=AnalisisIAResponse)
async def get_analisis(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(
        select(AnalisisIA).where(AnalisisIA.id == id, AnalisisIA.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    return obj

@router.post("/{id}/ejecutar", response_model=AnalisisIAResponse)
async def ejecutar_analisis(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    r = await db.execute(
        select(AnalisisIA).where(AnalisisIA.id == id, AnalisisIA.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    obj.resultado = {"status": "simulado", "mensaje": f"Analisis {obj.titulo or obj.tipo} ejecutado exitosamente"}
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{id}", status_code=204)
async def delete_analisis(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_ELIMINAR"))],
):
    r = await db.execute(
        select(AnalisisIA).where(AnalisisIA.id == id, AnalisisIA.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()
