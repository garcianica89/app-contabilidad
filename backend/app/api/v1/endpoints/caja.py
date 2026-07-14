from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.caja import Caja, MovimientoCaja, ArqueoCaja
from app.domain.schemas import MovimientoCajaCreate
from app.service.accounting.accounting_engine import AccountingEngine
from pydantic import BaseModel

router = APIRouter()


class CajaResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    saldo_actual: float
    activa: bool

    class Config:
        from_attributes = True


class MovimientoCajaResponse(BaseModel):
    id: uuid.UUID
    fecha: date
    tipo: str
    concepto: str
    entrada: float
    salida: float
    saldo: float
    referencia_id: str | None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[CajaResponse])
async def listar_cajas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Caja).where(
            Caja.empresa_id == current_user.empresa_id,
            Caja.activa == True,
        )
    )
    return result.scalars().all()


@router.post("/movimientos", response_model=MovimientoCajaResponse, status_code=201)
async def registrar_movimiento(
    data: MovimientoCajaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    caja_row = await db.execute(
        select(Caja).where(Caja.id == data.caja_id).with_for_update()
    )
    caja = caja_row.scalar_one_or_none()
    if not caja or not caja.activa:
        raise HTTPException(status_code=404, detail="Caja no encontrada o inactiva")

    saldo_anterior = (
        await db.execute(
            select(func.coalesce(func.max(MovimientoCaja.saldo), 0)).where(
                MovimientoCaja.caja_id == data.caja_id
            )
        )
    ).scalar()

    saldo_nuevo = float(saldo_anterior) + data.entrada - data.salida

    mov = MovimientoCaja(
        empresa_id=current_user.empresa_id,
        caja_id=data.caja_id,
        fecha=data.fecha,
        tipo=data.tipo,
        concepto=data.concepto,
        entrada=data.entrada,
        salida=data.salida,
        saldo=saldo_nuevo,
        usuario_id=current_user.id,
    )
    db.add(mov)
    caja.saldo_actual = saldo_nuevo

    await db.flush()

    if data.entrada > 0 or data.salida > 0:
        engine = AccountingEngine(db)
        asiento_result = await engine.generate_from_event(
            event_type='CAJA',
            module='bancos',
            data={
                'caja_id': str(data.caja_id),
                'caja_nombre': caja.nombre,
                'fecha': data.fecha.isoformat(),
                'concepto': data.concepto,
                'entrada': data.entrada,
                'salida': data.salida,
                'movimiento_id': str(mov.id),
                'tipo': data.tipo,
            },
            company_id=current_user.empresa_id,
            document_id=mov.id,
            user_id=current_user.id,
        )
        if asiento_result:
            mov.asiento_id = asiento_result.get('asiento_id')

    await db.commit()
    await db.refresh(mov)
    return mov


@router.get("/movimientos")
async def listar_movimientos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    caja_id: uuid.UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(MovimientoCaja).where(
        MovimientoCaja.empresa_id == current_user.empresa_id
    )
    if caja_id:
        query = query.where(MovimientoCaja.caja_id == caja_id)
    if fecha_desde:
        query = query.where(MovimientoCaja.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.where(MovimientoCaja.fecha <= fecha_hasta)
    query = query.order_by(MovimientoCaja.fecha.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return [
        {
            "id": str(m.id),
            "caja_id": str(m.caja_id),
            "fecha": str(m.fecha),
            "tipo": m.tipo,
            "concepto": m.concepto,
            "entrada": float(m.entrada),
            "salida": float(m.salida),
            "saldo": float(m.saldo),
        }
        for m in result.scalars().all()
    ]
