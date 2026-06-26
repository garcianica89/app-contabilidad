from typing import Annotated
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.periodo import PeriodoContable

router = APIRouter()


@router.get("/")
async def listar_periodos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(PeriodoContable)
        .where(PeriodoContable.empresa_id == current_user.empresa_id)
        .order_by(PeriodoContable.codigo.desc())
    )
    return [
        {
            "id": str(p.id),
            "codigo": p.codigo,
            "nombre": p.nombre,
            "fecha_inicio": str(p.fecha_inicio),
            "fecha_fin": str(p.fecha_fin),
            "cerrado": p.cerrado,
        }
        for p in result.scalars().all()
    ]
