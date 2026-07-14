import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.presupuesto import PresupuestoCabecera as Presupuesto, PresupuestoDetalle as PresupuestoPartida
from app.domain.models.centro_costo import CentroCosto
from app.domain.models.usuario import Usuario

router = APIRouter()

# ─── Schemas Presupuesto ───
class PresupuestoCreate(BaseModel):
    anio: int = Field(ge=2000, le=2100)
    nombre: str = Field(max_length=200)

class PresupuestoResponse(BaseModel):
    id: str
    anio: int
    nombre: str
    version: int
    estado: str
    class Config: from_attributes = True

class PresupuestoPartidaCreate(BaseModel):
    cuenta_contable_id: str
    centro_costo_id: str | None = None
    mes: int = Field(ge=1, le=12)
    monto_presupuestado: float = Field(gt=0)

class PresupuestoPartidaResponse(BaseModel):
    id: str
    cuenta_contable_id: str
    centro_costo_id: str | None
    mes: int
    monto_presupuestado: float
    class Config: from_attributes = True

class PresupuestoDetalleResponse(PresupuestoResponse):
    partidas: list[PresupuestoPartidaResponse] = []

class CentroCostoCreate(BaseModel):
    codigo: str = Field(max_length=20)
    nombre: str = Field(max_length=200)
    padre_id: str | None = None

class CentroCostoResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    padre_id: str | None
    activo: bool
    class Config: from_attributes = True

# ─── Centro Costo ───
@router.get("/centros-costo", response_model=list[CentroCostoResponse])
async def list_centros_costo(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(
        select(CentroCosto).where(CentroCosto.empresa_id == user.empresa_id).order_by(CentroCosto.codigo)
    )
    return r.scalars().all()

@router.post("/centros-costo", response_model=CentroCostoResponse, status_code=201)
async def create_centro_costo(
    data: CentroCostoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    obj = CentroCosto(empresa_id=user.empresa_id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/centros-costo/{id}", response_model=CentroCostoResponse)
async def update_centro_costo(
    id: uuid.UUID,
    data: CentroCostoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_EDITAR"))],
):
    r = await db.execute(select(CentroCosto).where(CentroCosto.id == id, CentroCosto.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/centros-costo/{id}", status_code=204)
async def delete_centro_costo(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_ELIMINAR"))],
):
    r = await db.execute(select(CentroCosto).where(CentroCosto.id == id, CentroCosto.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()

# ─── Presupuestos ───
@router.get("", response_model=list[PresupuestoResponse])
async def list_presupuestos(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
    anio: int | None = Query(None),
    estado: str | None = Query(None),
):
    q = select(Presupuesto).where(Presupuesto.empresa_id == user.empresa_id)
    if anio:
        q = q.where(Presupuesto.anio == anio)
    if estado:
        q = q.where(Presupuesto.estado == estado)
    q = q.order_by(Presupuesto.anio.desc(), Presupuesto.nombre)
    r = await db.execute(q)
    return r.scalars().all()

@router.post("", response_model=PresupuestoResponse, status_code=201)
async def create_presupuesto(
    data: PresupuestoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    obj = Presupuesto(empresa_id=user.empresa_id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get("/{id}", response_model=PresupuestoDetalleResponse)
async def get_presupuesto(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(
        select(Presupuesto).where(Presupuesto.id == id, Presupuesto.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    return obj

@router.put("/{id}", response_model=PresupuestoResponse)
async def update_presupuesto(
    id: uuid.UUID,
    data: PresupuestoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_EDITAR"))],
):
    r = await db.execute(
        select(Presupuesto).where(Presupuesto.id == id, Presupuesto.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.post("/{id}/aprobar", response_model=PresupuestoResponse)
async def aprobar_presupuesto(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_EDITAR"))],
):
    r = await db.execute(
        select(Presupuesto).where(Presupuesto.id == id, Presupuesto.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    if obj.estado != "BORRADOR":
        raise HTTPException(400, "Solo se puede aprobar presupuestos en BORRADOR")
    obj.estado = "APROBADO"
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{id}", status_code=204)
async def delete_presupuesto(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_ELIMINAR"))],
):
    r = await db.execute(
        select(Presupuesto).where(Presupuesto.id == id, Presupuesto.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()

# ─── Partidas ───
@router.get("/{id}/partidas", response_model=list[PresupuestoPartidaResponse])
async def list_partidas(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(
        select(PresupuestoPartida).where(
            PresupuestoPartida.presupuesto_id == id,
            Presupuesto.id == PresupuestoPartida.presupuesto_id,
            Presupuesto.empresa_id == user.empresa_id,
        ).join(Presupuesto).order_by(PresupuestoPartida.mes)
    )
    return r.scalars().all()

@router.post("/{id}/partidas", response_model=PresupuestoPartidaResponse, status_code=201)
async def create_partida(
    id: uuid.UUID,
    data: PresupuestoPartidaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    r = await db.execute(select(Presupuesto).where(Presupuesto.id == id, Presupuesto.empresa_id == user.empresa_id))
    pres = r.scalar_one_or_none()
    if not pres:
        raise HTTPException(404)
    if pres.estado != "BORRADOR":
        raise HTTPException(400, "Solo se puede agregar partidas a presupuestos en BORRADOR")
    obj = PresupuestoPartida(presupuesto_id=id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/{presupuesto_id}/partidas/{id}", response_model=PresupuestoPartidaResponse)
async def update_partida(
    presupuesto_id: uuid.UUID,
    id: uuid.UUID,
    data: PresupuestoPartidaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_EDITAR"))],
):
    r = await db.execute(
        select(PresupuestoPartida).where(
            PresupuestoPartida.id == id,
            PresupuestoPartida.presupuesto_id == presupuesto_id,
        )
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{presupuesto_id}/partidas/{id}", status_code=204)
async def delete_partida(
    presupuesto_id: uuid.UUID,
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_ELIMINAR"))],
):
    r = await db.execute(
        select(PresupuestoPartida).where(
            PresupuestoPartida.id == id,
            PresupuestoPartida.presupuesto_id == presupuesto_id,
        )
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()
