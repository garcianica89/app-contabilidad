from typing import Annotated
import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.ejercicio import EjercicioFiscal

router = APIRouter()


@router.get("")
async def listar_ejercicios(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(EjercicioFiscal)
        .where(EjercicioFiscal.company_id == current_user.empresa_id)
        .order_by(EjercicioFiscal.codigo.desc())
    )
    return [
        {
            "id": str(e.id),
            "codigo": e.codigo,
            "nombre": e.nombre,
            "fecha_inicio": str(e.fecha_inicio),
            "fecha_fin": str(e.fecha_fin),
            "cerrado": e.cerrado,
        }
        for e in result.scalars().all()
    ]
