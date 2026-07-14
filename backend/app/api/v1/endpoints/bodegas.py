from typing import Annotated
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.sucursal import Bodega

router = APIRouter()


class BodegaResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[BodegaResponse])
async def listar_bodegas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Bodega).where(
            Bodega.company_id == current_user.empresa_id,
            Bodega.is_active == True,
        ).order_by(Bodega.nombre)
    )
    return result.scalars().all()
