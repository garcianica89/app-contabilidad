from typing import Annotated
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.retencion import Retencion

router = APIRouter()


class RetencionCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None
    tipo: str
    porcentaje: float
    aplica_a: str = 'NACIONAL'
    monto_minimo: float | None = None
    base_imponible: str = 'SUBTOTAL'
    prioridad: int = 10
    redondeo: int = 2
    naturaleza: str = 'CREDITO'
    cuenta_retencion_id: str | None = None
    cuenta_pagar_id: str | None = None
    cuenta_cobrar_id: str | None = None
    centro_costo_id: str | None = None
    vigencia_desde: date
    vigencia_hasta: date | None = None


class RetencionUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    tipo: str | None = None
    porcentaje: float | None = None
    aplica_a: str | None = None
    monto_minimo: float | None = None
    base_imponible: str | None = None
    prioridad: int | None = None
    redondeo: int | None = None
    naturaleza: str | None = None
    cuenta_retencion_id: str | None = None
    cuenta_pagar_id: str | None = None
    cuenta_cobrar_id: str | None = None
    centro_costo_id: str | None = None
    vigencia_desde: date | None = None
    vigencia_hasta: date | None = None
    is_active: bool | None = None


def _to_dict(r: Retencion) -> dict:
    return {
        "id": str(r.id),
        "codigo": r.codigo,
        "nombre": r.nombre,
        "descripcion": r.descripcion,
        "tipo": r.tipo,
        "porcentaje": float(r.porcentaje),
        "aplica_a": r.aplica_a,
        "monto_minimo": float(r.monto_minimo) if r.monto_minimo else None,
        "base_imponible": r.base_imponible,
        "prioridad": r.prioridad,
        "redondeo": r.redondeo,
        "naturaleza": r.naturaleza,
        "cuenta_retencion_id": str(r.cuenta_retencion_id) if r.cuenta_retencion_id else None,
        "cuenta_pagar_id": str(r.cuenta_pagar_id) if r.cuenta_pagar_id else None,
        "cuenta_cobrar_id": str(r.cuenta_cobrar_id) if r.cuenta_cobrar_id else None,
        "centro_costo_id": str(r.centro_costo_id) if r.centro_costo_id else None,
        "vigencia_desde": r.vigencia_desde.isoformat(),
        "vigencia_hasta": r.vigencia_hasta.isoformat() if r.vigencia_hasta else None,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat(),
    }


@router.get("/")
async def list_retenciones(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    activo: bool | None = None,
):
    query = select(Retencion).where(
        Retencion.company_id == current_user.empresa_id
    ).order_by(Retencion.prioridad, Retencion.codigo)
    if activo is not None:
        query = query.where(Retencion.is_active == activo)
    result = await db.execute(query)
    return [_to_dict(r) for r in result.scalars().all()]


@router.post("/", status_code=201)
async def create_retencion(
    data: RetencionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(Retencion).where(
            Retencion.company_id == current_user.empresa_id,
            Retencion.codigo == data.codigo,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe una retencion con ese codigo")
    ret = Retencion(
        company_id=current_user.empresa_id,
        codigo=data.codigo,
        nombre=data.nombre,
        descripcion=data.descripcion,
        tipo=data.tipo,
        porcentaje=data.porcentaje,
        aplica_a=data.aplica_a,
        monto_minimo=data.monto_minimo,
        base_imponible=data.base_imponible,
        prioridad=data.prioridad,
        redondeo=data.redondeo,
        naturaleza=data.naturaleza,
        cuenta_retencion_id=uuid.UUID(data.cuenta_retencion_id) if data.cuenta_retencion_id else None,
        cuenta_pagar_id=uuid.UUID(data.cuenta_pagar_id) if data.cuenta_pagar_id else None,
        cuenta_cobrar_id=uuid.UUID(data.cuenta_cobrar_id) if data.cuenta_cobrar_id else None,
        centro_costo_id=uuid.UUID(data.centro_costo_id) if data.centro_costo_id else None,
        vigencia_desde=data.vigencia_desde,
        vigencia_hasta=data.vigencia_hasta,
    )
    db.add(ret)
    await db.commit()
    await db.refresh(ret)
    return _to_dict(ret)


@router.get("/{retencion_id}")
async def get_retencion(
    retencion_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Retencion).where(
            Retencion.id == retencion_id,
            Retencion.company_id == current_user.empresa_id,
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Retencion no encontrada")
    return _to_dict(r)


@router.put("/{retencion_id}")
async def update_retencion(
    retencion_id: uuid.UUID,
    data: RetencionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Retencion).where(
            Retencion.id == retencion_id,
            Retencion.company_id == current_user.empresa_id,
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Retencion no encontrada")
    update_data = data.model_dump(exclude_unset=True)
    for field in ('cuenta_retencion_id', 'cuenta_pagar_id', 'cuenta_cobrar_id', 'centro_costo_id'):
        if field in update_data and update_data[field]:
            update_data[field] = uuid.UUID(update_data[field])
    for key, value in update_data.items():
        if hasattr(r, key):
            setattr(r, key, value)
    await db.commit()
    await db.refresh(r)
    return _to_dict(r)


@router.delete("/{retencion_id}", status_code=204)
async def delete_retencion(
    retencion_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Retencion).where(
            Retencion.id == retencion_id,
            Retencion.company_id == current_user.empresa_id,
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Retencion no encontrada")
    r.is_active = False
    await db.commit()
