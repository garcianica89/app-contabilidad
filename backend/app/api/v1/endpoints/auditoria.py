from typing import Annotated
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.auditoria import Auditoria

router = APIRouter()


class AuditoriaResponse(BaseModel):
    id: str
    usuario_id: str | None
    usuario_nombre: str | None = None
    tabla: str
    registro_id: str
    accion: str
    valor_anterior: dict | None
    valor_nuevo: dict | None
    created_at: datetime


@router.get("/")
async def listar_auditoria(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    tabla: str | None = None,
    accion: str | None = None,
    usuario_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = select(Auditoria).where(
        Auditoria.empresa_id == current_user.empresa_id
    )

    if tabla:
        query = query.where(Auditoria.tabla == tabla)
    if accion:
        query = query.where(Auditoria.accion == accion)
    if usuario_id:
        query = query.where(Auditoria.usuario_id == usuario_id)
    if desde:
        query = query.where(Auditoria.created_at >= datetime.combine(desde, datetime.min.time()))
    if hasta:
        query = query.where(Auditoria.created_at <= datetime.combine(hasta, datetime.max.time()))

    query = query.order_by(Auditoria.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.scalars().all()

    response = []
    for r in rows:
        usuario_nombre = None
        if r.usuario_id:
            u = await db.get(Usuario, r.usuario_id)
            if u:
                usuario_nombre = u.nombre_completo
        response.append(AuditoriaResponse(
            id=str(r.id),
            usuario_id=str(r.usuario_id) if r.usuario_id else None,
            usuario_nombre=usuario_nombre,
            tabla=r.tabla,
            registro_id=str(r.registro_id),
            accion=r.accion,
            valor_anterior=r.valor_anterior,
            valor_nuevo=r.valor_nuevo,
            created_at=r.created_at,
        ))

    return response
