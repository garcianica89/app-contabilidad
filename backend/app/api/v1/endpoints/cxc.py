from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.factura_venta import FacturaVenta
from app.service.cxc_service import CxcService
from app.service.document_engine import DocumentEngine

router = APIRouter()


class FacturaVentaCreate(BaseModel):
    numero: str
    cliente_id: uuid.UUID
    fecha: date
    tipo: str
    lineas: list[dict]
    moneda_id: uuid.UUID
    fecha_vencimiento: date | None = None
    descuento: float = 0
    iva: float = 0
    periodo_id: uuid.UUID
    aplica_iva: bool | None = None
    tasa_iva: float | None = None


@router.post("/facturas")
async def crear_factura(
    data: FacturaVentaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxcService(db, current_user.id, current_user.empresa_id)
    try:
        factura = await svc.crear_factura(
            numero=data.numero,
            cliente_id=data.cliente_id,
            fecha=data.fecha,
            tipo=data.tipo,
            lineas=[l for l in data.lineas],
            moneda_id=data.moneda_id,
            fecha_vencimiento=data.fecha_vencimiento,
            descuento=data.descuento,
            iva=data.iva,
            periodo_id=data.periodo_id,
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
    cliente_id: uuid.UUID | None = None,
    estado: str | None = None,
):
    query = select(FacturaVenta).where(
        FacturaVenta.empresa_id == current_user.empresa_id
    )
    if cliente_id:
        query = query.where(FacturaVenta.cliente_id == cliente_id)
    if estado:
        query = query.where(FacturaVenta.estado == estado)
    query = query.order_by(FacturaVenta.fecha.desc())

    conn = await db.execute(query)
    return [
        {
            "id": str(f.id),
            "numero": f.numero,
            "fecha": str(f.fecha),
            "cliente_id": str(f.cliente_id),
            "total": float(f.total),
            "estado": f.estado,
            "tipo": f.tipo,
        }
        for f in conn.scalars().all()
    ]


@router.get("/facturas/{factura_id}")
async def get_factura(
    factura_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    factura = await db.get(FacturaVenta, factura_id)
    if not factura or factura.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return {
        "id": str(factura.id),
        "numero": factura.numero,
        "cliente_id": str(factura.cliente_id),
        "fecha": str(factura.fecha),
        "subtotal": float(factura.subtotal),
        "descuento": float(factura.descuento),
        "iva": float(factura.iva),
        "total": float(factura.total),
        "estado": factura.estado,
        "tipo": factura.tipo,
    }


# ─── Retenciones por Factura ───

class RetencionFacturaInput(BaseModel):
    retencion_id: uuid.UUID
    base_imponible: float = 0
    monto_retenido: float = 0


@router.get("/facturas/{factura_id}/retenciones")
async def get_retenciones_factura(
    factura_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxcService(db, current_user.id, current_user.empresa_id)
    try:
        return await svc.get_retenciones_factura(factura_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/facturas/{factura_id}/retenciones")
async def save_retenciones_factura(
    factura_id: uuid.UUID,
    retenciones: list[RetencionFacturaInput],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxcService(db, current_user.id, current_user.empresa_id)
    try:
        await svc.save_retenciones_factura(
            factura_id,
            [r.model_dump() for r in retenciones],
        )
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Cobros ───

class CobroCreate(BaseModel):
    factura_venta_id: uuid.UUID
    monto: float
    fecha: date
    metodo_pago: str = 'EFECTIVO'
    cuenta_banco_id: uuid.UUID | None = None
    concepto: str | None = None
    retenciones: list[RetencionFacturaInput] | None = None


@router.post("/cobros")
async def registrar_cobro(
    data: CobroCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxcService(db, current_user.id, current_user.empresa_id)
    try:
        result = await svc.registrar_cobro(
            factura_venta_id=data.factura_venta_id,
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


@router.get("/estado-cuenta/{cliente_id}")
async def estado_cuenta(
    cliente_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    fecha_corte: date | None = None,
):
    svc = CxcService(db, current_user.id, current_user.empresa_id)
    return await svc.estado_cuenta_cliente(cliente_id, fecha_corte)


@router.get("/antiguedad")
async def antiguedad_saldos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = CxcService(db, current_user.id, current_user.empresa_id)
    return await svc.antiguedad_saldos()
