from typing import Annotated
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.orden_compra import OrdenCompra, OrdenCompraLinea
from app.domain.models.proveedor import Proveedor

router = APIRouter()


class LineaCreate(BaseModel):
    producto_id: uuid.UUID
    cantidad: float
    precio_unitario: float
    descuento: float = 0
    aplica_iva: bool | None = None
    tasa_iva: float | None = None
    centro_costo_id: uuid.UUID | None = None
    cuenta_contable_id: uuid.UUID | None = None


class OrdenCompraCreate(BaseModel):
    numero: str
    proveedor_id: uuid.UUID
    fecha: date
    lineas: list[LineaCreate]
    moneda_id: uuid.UUID
    fecha_entrega: date | None = None
    bodega_id: uuid.UUID | None = None
    condicion_pago_id: uuid.UUID | None = None
    descuento: float = 0
    retencion_ir: float = 0


class LineaResponse(BaseModel):
    id: str
    producto_id: str
    cantidad: float
    precio_unitario: float
    descuento: float
    aplica_iva: bool | None
    tasa_iva: float | None
    subtotal: float

    class Config:
        from_attributes = True


class OrdenCompraResponse(BaseModel):
    id: str
    numero: str
    proveedor_id: str
    proveedor_nombre: str | None = None
    fecha: date
    fecha_entrega: date | None = None
    bodega_id: str | None = None
    condicion_pago_id: str | None = None
    subtotal: float
    descuento: float
    iva: float
    retencion_ir: float
    total: float
    estado: str
    lineas: list[LineaResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[OrdenCompraResponse])
async def listar_ordenes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    proveedor_id: uuid.UUID | None = None,
    estado: str | None = None,
):
    query = select(OrdenCompra).where(OrdenCompra.empresa_id == current_user.empresa_id)
    if proveedor_id:
        query = query.where(OrdenCompra.proveedor_id == proveedor_id)
    if estado:
        query = query.where(OrdenCompra.estado == estado)
    query = query.order_by(OrdenCompra.fecha.desc())

    result = await db.execute(query)
    ordenes = result.scalars().all()

    response = []
    for o in ordenes:
        prov = await db.get(Proveedor, o.proveedor_id)
        response.append(OrdenCompraResponse(
            id=str(o.id),
            numero=o.numero,
            proveedor_id=str(o.proveedor_id),
            proveedor_nombre=prov.nombre if prov else None,
            fecha=o.fecha,
            fecha_entrega=o.fecha_entrega,
            bodega_id=str(o.bodega_id) if o.bodega_id else None,
            condicion_pago_id=str(o.condicion_pago_id) if o.condicion_pago_id else None,
            subtotal=float(o.subtotal),
            descuento=float(o.descuento),
            iva=float(o.iva),
            retencion_ir=float(o.retencion_ir),
            total=float(o.total),
            estado=o.estado,
            lineas=[LineaResponse(
                id=str(l.id),
                producto_id=str(l.producto_id),
                cantidad=float(l.cantidad),
                precio_unitario=float(l.precio_unitario),
                descuento=float(l.descuento),
                aplica_iva=l.aplica_iva,
                tasa_iva=float(l.tasa_iva) if l.tasa_iva else None,
                subtotal=float(l.subtotal),
            ) for l in o.lineas],
            created_at=o.created_at,
        ))
    return response


@router.get("/{orden_id}", response_model=OrdenCompraResponse)
async def obtener_orden(
    orden_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(OrdenCompra).where(
            OrdenCompra.id == orden_id,
            OrdenCompra.empresa_id == current_user.empresa_id,
        )
    )
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    prov = await db.get(Proveedor, o.proveedor_id)
    return OrdenCompraResponse(
        id=str(o.id),
        numero=o.numero,
        proveedor_id=str(o.proveedor_id),
        proveedor_nombre=prov.nombre if prov else None,
        fecha=o.fecha,
        fecha_entrega=o.fecha_entrega,
        bodega_id=str(o.bodega_id) if o.bodega_id else None,
        condicion_pago_id=str(o.condicion_pago_id) if o.condicion_pago_id else None,
        subtotal=float(o.subtotal),
        descuento=float(o.descuento),
        iva=float(o.iva),
        retencion_ir=float(o.retencion_ir),
        total=float(o.total),
        estado=o.estado,
        lineas=[LineaResponse(
            id=str(l.id),
            producto_id=str(l.producto_id),
            cantidad=float(l.cantidad),
            precio_unitario=float(l.precio_unitario),
            descuento=float(l.descuento),
            aplica_iva=l.aplica_iva,
            tasa_iva=float(l.tasa_iva) if l.tasa_iva else None,
            subtotal=float(l.subtotal),
        ) for l in o.lineas],
        created_at=o.created_at,
    )


@router.post("/", response_model=OrdenCompraResponse, status_code=201)
async def crear_orden(
    data: OrdenCompraCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    prov = await db.get(Proveedor, data.proveedor_id)
    if not prov or prov.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    line_subtotal = sum(
        float(l.cantidad) * float(l.precio_unitario) for l in data.lineas
    )
    total = line_subtotal - data.descuento - data.retencion_ir

    orden = OrdenCompra(
        empresa_id=current_user.empresa_id,
        numero=data.numero,
        proveedor_id=data.proveedor_id,
        fecha=data.fecha,
        fecha_entrega=data.fecha_entrega,
        bodega_id=data.bodega_id,
        condicion_pago_id=data.condicion_pago_id,
        subtotal=line_subtotal,
        descuento=data.descuento,
        iva=0,
        retencion_ir=data.retencion_ir,
        total=total,
        moneda_id=data.moneda_id,
        estado="EMITIDA",
    )
    db.add(orden)
    await db.flush()

    for l in data.lineas:
        line_total = float(l.cantidad) * float(l.precio_unitario)
        linea = OrdenCompraLinea(
            orden_id=orden.id,
            producto_id=l.producto_id,
            cantidad=float(l.cantidad),
            precio_unitario=float(l.precio_unitario),
            descuento=float(l.descuento),
            aplica_iva=l.aplica_iva,
            tasa_iva=float(l.tasa_iva) if l.tasa_iva else None,
            subtotal=line_total,
            centro_costo_id=l.centro_costo_id,
            cuenta_contable_id=l.cuenta_contable_id,
        )
        db.add(linea)

    await db.commit()
    await db.refresh(orden)

    return OrdenCompraResponse(
        id=str(orden.id),
        numero=orden.numero,
        proveedor_id=str(orden.proveedor_id),
        proveedor_nombre=prov.nombre if prov else None,
        fecha=orden.fecha,
        fecha_entrega=orden.fecha_entrega,
        bodega_id=str(orden.bodega_id) if orden.bodega_id else None,
        condicion_pago_id=str(orden.condicion_pago_id) if orden.condicion_pago_id else None,
        subtotal=float(orden.subtotal),
        descuento=float(orden.descuento),
        iva=float(orden.iva),
        retencion_ir=float(orden.retencion_ir),
        total=float(orden.total),
        estado=orden.estado,
        lineas=[LineaResponse(
            id=str(l.id),
            producto_id=str(l.producto_id),
            cantidad=float(l.cantidad),
            precio_unitario=float(l.precio_unitario),
            descuento=float(l.descuento),
            aplica_iva=l.aplica_iva,
            tasa_iva=float(l.tasa_iva) if l.tasa_iva else None,
            subtotal=float(l.subtotal),
        ) for l in orden.lineas],
        created_at=orden.created_at,
    )


@router.post("/{orden_id}/aprobar")
async def aprobar_orden(
    orden_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(OrdenCompra).where(
            OrdenCompra.id == orden_id,
            OrdenCompra.empresa_id == current_user.empresa_id,
        )
    )
    orden = result.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado != "EMITIDA":
        raise HTTPException(status_code=400, detail=f"Orden en estado {orden.estado}. No se puede aprobar")

    orden.estado = "APROBADA"
    await db.commit()
    return {"mensaje": "Orden aprobada", "estado": "APROBADA"}


@router.post("/{orden_id}/anular")
async def anular_orden(
    orden_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(OrdenCompra).where(
            OrdenCompra.id == orden_id,
            OrdenCompra.empresa_id == current_user.empresa_id,
        )
    )
    orden = result.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado in ("ANULADA", "RECIBIDA"):
        raise HTTPException(status_code=400, detail=f"Orden en estado {orden.estado}")

    orden.estado = "ANULADA"
    await db.commit()
    return {"mensaje": "Orden anulada", "estado": "ANULADA"}
