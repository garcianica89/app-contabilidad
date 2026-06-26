from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.service.cxp_service import CxpService

router = APIRouter()


class FacturaCompraCreate(BaseModel):
    numero: str
    proveedor_id: uuid.UUID
    fecha: date
    lineas: list[dict]
    moneda_id: uuid.UUID
    periodo_id: uuid.UUID
    orden_id: uuid.UUID | None = None
    fecha_vencimiento: date | None = None
    descuento: float = 0
    iva: float = 0
    retencion_ir: float = 0


@router.post("/facturas")
async def crear_factura(
    data: FacturaCompraCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxpService(db, current_user.id, current_user.empresa_id)
    try:
        factura = await svc.crear_factura_compra(
            numero=data.numero,
            proveedor_id=data.proveedor_id,
            fecha=data.fecha,
            lineas=[l for l in data.lineas],
            moneda_id=data.moneda_id,
            periodo_id=data.periodo_id,
            orden_id=data.orden_id,
            fecha_vencimiento=data.fecha_vencimiento,
            descuento=data.descuento,
            iva=data.iva,
            retencion_ir=data.retencion_ir,
        )
        return {
            "id": str(factura.id),
            "numero": factura.numero,
            "total": float(factura.total),
            "estado": factura.estado,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/facturas")
async def listar_facturas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    proveedor_id: uuid.UUID | None = None,
    estado: str | None = None,
):
    from sqlalchemy import select
    from app.domain.models.factura_compra import FacturaCompra

    query = select(FacturaCompra).where(
        FacturaCompra.empresa_id == current_user.empresa_id
    )
    if proveedor_id:
        query = query.where(FacturaCompra.proveedor_id == proveedor_id)
    if estado:
        query = query.where(FacturaCompra.estado == estado)
    query = query.order_by(FacturaCompra.fecha.desc())

    conn = await db.execute(query)
    return [
        {
            "id": str(f.id),
            "numero": f.numero,
            "fecha": str(f.fecha),
            "proveedor_id": str(f.proveedor_id),
            "total": float(f.total),
            "estado": f.estado,
        }
        for f in conn.scalars().all()
    ]


@router.get("/estado-cuenta/{proveedor_id}")
async def estado_cuenta(
    proveedor_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    fecha_corte: date | None = None,
):
    svc = CxpService(db, current_user.id, current_user.empresa_id)
    return await svc.estado_cuenta_proveedor(proveedor_id, fecha_corte)


@router.get("/antiguedad")
async def antiguedad_saldos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxpService(db, current_user.id, current_user.empresa_id)
    return await svc.antiguedad_saldos()
