import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, Field
from datetime import date
from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.departamento import Departamento
from app.domain.models.empleado import Cargo, Empleado
from app.domain.models.usuario import Usuario

router = APIRouter()

# ─── Schemas ───
class DepartamentoCreate(BaseModel):
    codigo: str = Field(max_length=20)
    nombre: str = Field(max_length=100)
    activo: bool = True

class DepartamentoResponse(DepartamentoCreate):
    id: str
    class Config: from_attributes = True

class CargoCreate(BaseModel):
    codigo: str = Field(max_length=20)
    nombre: str = Field(max_length=100)
    activo: bool = True

class CargoResponse(CargoCreate):
    id: str
    class Config: from_attributes = True

class EmpleadoCreate(BaseModel):
    codigo: str = Field(max_length=20)
    nombre: str = Field(max_length=200)
    cedula: str | None = None
    fecha_nacimiento: date | None = None
    fecha_contratacion: date
    departamento_id: str | None = None
    cargo_id: str | None = None
    salario_base: float = Field(gt=0)
    tipo_contrato: str = "INDEFINIDO"
    estado: str = "ACTIVO"
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None

class EmpleadoResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    cedula: str | None
    fecha_nacimiento: date | None
    fecha_contratacion: date
    departamento_id: str | None
    cargo_id: str | None
    salario_base: float
    tipo_contrato: str
    estado: str
    direccion: str | None
    telefono: str | None
    email: str | None
    class Config: from_attributes = True


# ─── Departamentos ───
@router.get("/departamentos", response_model=list[DepartamentoResponse])
async def list_departamentos(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
    activo: bool | None = Query(None),
):
    q = select(Departamento).where(Departamento.empresa_id == user.empresa_id)
    if activo is not None:
        q = q.where(Departamento.activo == activo)
    q = q.order_by(Departamento.codigo)
    r = await db.execute(q)
    return r.scalars().all()

@router.post("/departamentos", response_model=DepartamentoResponse, status_code=201)
async def create_departamento(
    data: DepartamentoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    obj = Departamento(empresa_id=user.empresa_id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/departamentos/{id}", response_model=DepartamentoResponse)
async def update_departamento(
    id: uuid.UUID,
    data: DepartamentoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_EDITAR"))],
):
    r = await db.execute(select(Departamento).where(Departamento.id == id, Departamento.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/departamentos/{id}", status_code=204)
async def delete_departamento(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_ELIMINAR"))],
):
    r = await db.execute(select(Departamento).where(Departamento.id == id, Departamento.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()

# ─── Cargos ───
@router.get("/cargos", response_model=list[CargoResponse])
async def list_cargos(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
    activo: bool | None = Query(None),
):
    q = select(Cargo).where(Cargo.empresa_id == user.empresa_id)
    if activo is not None:
        q = q.where(Cargo.activo == activo)
    q = q.order_by(Cargo.codigo)
    r = await db.execute(q)
    return r.scalars().all()

@router.post("/cargos", response_model=CargoResponse, status_code=201)
async def create_cargo(
    data: CargoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    obj = Cargo(empresa_id=user.empresa_id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/cargos/{id}", response_model=CargoResponse)
async def update_cargo(
    id: uuid.UUID,
    data: CargoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_EDITAR"))],
):
    r = await db.execute(select(Cargo).where(Cargo.id == id, Cargo.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/cargos/{id}", status_code=204)
async def delete_cargo(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_ELIMINAR"))],
):
    r = await db.execute(select(Cargo).where(Cargo.id == id, Cargo.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()

# ─── Empleados ───
@router.get("", response_model=list[EmpleadoResponse])
async def list_empleados(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
    activo: bool | None = Query(None),
    departamento_id: str | None = Query(None),
):
    q = select(Empleado).where(Empleado.empresa_id == user.empresa_id)
    if activo is not None:
        estado = "ACTIVO" if activo else "INACTIVO"
        q = q.where(Empleado.estado == estado)
    if departamento_id:
        q = q.where(Empleado.departamento_id == departamento_id)
    q = q.order_by(Empleado.codigo)
    r = await db.execute(q)
    return r.scalars().all()

@router.post("", response_model=EmpleadoResponse, status_code=201)
async def create_empleado(
    data: EmpleadoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    if data.cedula:
        r = await db.execute(select(Empleado).where(Empleado.cedula == data.cedula))
        if r.scalar():
            raise HTTPException(400, "Cedula ya registrada")
    obj = Empleado(empresa_id=user.empresa_id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get("/{id}", response_model=EmpleadoResponse)
async def get_empleado(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(select(Empleado).where(Empleado.id == id, Empleado.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    return obj

@router.put("/{id}", response_model=EmpleadoResponse)
async def update_empleado(
    id: uuid.UUID,
    data: EmpleadoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_EDITAR"))],
):
    r = await db.execute(select(Empleado).where(Empleado.id == id, Empleado.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{id}", status_code=204)
async def delete_empleado(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_ELIMINAR"))],
):
    r = await db.execute(select(Empleado).where(Empleado.id == id, Empleado.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()
