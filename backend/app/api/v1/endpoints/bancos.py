from typing import Annotated
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.banco import CuentaBanco, MovimientoBanco

router = APIRouter()


class CuentaBancoCreate(BaseModel):
    banco: str
    numero_cuenta: str
    tipo: str = "CORRIENTE"
    moneda_id: uuid.UUID


class CuentaBancoResponse(BaseModel):
    id: uuid.UUID
    banco: str
    numero_cuenta: str
    tipo: str
    saldo: float
    activa: bool

    class Config:
        from_attributes = True


class MovimientoBancoCreate(BaseModel):
    cuenta_id: uuid.UUID
    fecha: date
    tipo: str
    concepto: str
    entrada: float = 0
    salida: float = 0
    numero_documento: str | None = None


class MovimientoBancoResponse(BaseModel):
    id: uuid.UUID
    cuenta_id: uuid.UUID
    fecha: date
    tipo: str
    concepto: str
    entrada: float
    salida: float
    saldo: float
    numero_documento: str | None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[CuentaBancoResponse])
async def listar_cuentas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(CuentaBanco).where(
            CuentaBanco.empresa_id == current_user.empresa_id,
            CuentaBanco.activa == True,
        ).order_by(CuentaBanco.banco)
    )
    return result.scalars().all()


@router.post("/", response_model=CuentaBancoResponse, status_code=201)
async def crear_cuenta(
    data: CuentaBancoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    cuenta = CuentaBanco(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(cuenta)
    await db.commit()
    await db.refresh(cuenta)
    return cuenta


@router.put("/{cuenta_id}", response_model=CuentaBancoResponse)
async def actualizar_cuenta(
    cuenta_id: uuid.UUID,
    data: CuentaBancoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(CuentaBanco).where(
            CuentaBanco.id == cuenta_id,
            CuentaBanco.empresa_id == current_user.empresa_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(c, key, value)
    await db.commit()
    await db.refresh(c)
    return c


@router.get("/movimientos", response_model=list[MovimientoBancoResponse])
async def listar_movimientos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    cuenta_id: uuid.UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(MovimientoBanco).where(
        MovimientoBanco.empresa_id == current_user.empresa_id
    )
    if cuenta_id:
        query = query.where(MovimientoBanco.cuenta_id == cuenta_id)
    if fecha_desde:
        query = query.where(MovimientoBanco.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.where(MovimientoBanco.fecha <= fecha_hasta)
    query = query.order_by(MovimientoBanco.fecha.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/movimientos", response_model=MovimientoBancoResponse, status_code=201)
async def registrar_movimiento(
    data: MovimientoBancoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    cuenta = await db.execute(
        select(CuentaBanco).where(CuentaBanco.id == data.cuenta_id).with_for_update()
    )
    c = cuenta.scalar_one_or_none()
    if not c or not c.activa:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada o inactiva")

    saldo_anterior = (
        await db.execute(
            select(func.coalesce(func.max(MovimientoBanco.saldo), 0)).where(
                MovimientoBanco.cuenta_id == data.cuenta_id
            )
        )
    ).scalar()

    saldo_nuevo = float(saldo_anterior) + data.entrada - data.salida

    mov = MovimientoBanco(
        empresa_id=current_user.empresa_id,
        cuenta_id=data.cuenta_id,
        fecha=data.fecha,
        tipo=data.tipo,
        concepto=data.concepto,
        entrada=data.entrada,
        salida=data.salida,
        saldo=saldo_nuevo,
        numero_documento=data.numero_documento,
    )
    db.add(mov)
    c.saldo = saldo_nuevo
    await db.commit()
    await db.refresh(mov)
    return mov
