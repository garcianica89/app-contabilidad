from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.factura_compra import FacturaCompra
from app.service.cxp_service import CxpService
from app.service.document_engine import DocumentEngine

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
    aplica_iva: bool | None = None
    tasa_iva: float | None = None


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
            aplica_iva=data.aplica_iva,
            tasa_iva=data.tasa_iva,
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
            "subtotal": float(f.subtotal),
            "descuento": float(f.descuento),
            "iva": float(f.iva),
            "total": float(f.total),
            "estado": f.estado,
            "fecha_vencimiento": str(f.fecha_vencimiento) if f.fecha_vencimiento else None,
        }
        for f in conn.scalars().all()
    ]


@router.get("/facturas/{factura_id}")
async def get_factura(
    factura_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    factura = await db.get(FacturaCompra, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if factura.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return {
        "id": str(factura.id),
        "numero": factura.numero,
        "proveedor_id": str(factura.proveedor_id),
        "fecha": str(factura.fecha),
        "fecha_vencimiento": str(factura.fecha_vencimiento) if factura.fecha_vencimiento else None,
        "subtotal": float(factura.subtotal),
        "descuento": float(factura.descuento),
        "iva": float(factura.iva),
        "retencion_ir": float(factura.retencion_ir),
        "total": float(factura.total),
        "estado": factura.estado,
        "moneda_id": str(factura.moneda_id),
        "asiento_id": str(factura.asiento_id) if factura.asiento_id else None,
    }


# ─── Retenciones por Factura ───

@router.get("/facturas/{factura_id}/retenciones")
async def get_retenciones_factura(
    factura_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxpService(db, current_user.id, current_user.empresa_id)
    return await svc.get_retenciones_factura(factura_id)


class RetencionFacturaInput(BaseModel):
    retencion_id: uuid.UUID
    base_imponible: float = 0
    monto_retenido: float = 0


@router.put("/facturas/{factura_id}/retenciones")
async def save_retenciones_factura(
    factura_id: uuid.UUID,
    data: list[RetencionFacturaInput],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxpService(db, current_user.id, current_user.empresa_id)
    try:
        await svc.save_retenciones_factura(
            factura_id,
            [r.model_dump() for r in data],
        )
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Pagos ───

class PagoCreate(BaseModel):
    factura_compra_id: uuid.UUID
    monto: float
    fecha: date
    metodo_pago: str = 'EFECTIVO'
    cuenta_banco_id: uuid.UUID | None = None
    concepto: str | None = None
    retenciones: list[RetencionFacturaInput] | None = None


@router.post("/pagos")
async def registrar_pago(
    data: PagoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxpService(db, current_user.id, current_user.empresa_id)
    try:
        result = await svc.registrar_pago(
            factura_compra_id=data.factura_compra_id,
            monto=data.monto,
            fecha=data.fecha,
            metodo_pago=data.metodo_pago,
            cuenta_banco_id=data.cuenta_banco_id,
            concepto=data.concepto,
            retenciones=[r.model_dump() for r in data.retenciones] if data.retenciones else None,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
