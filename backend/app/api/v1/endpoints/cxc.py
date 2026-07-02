from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
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
    from sqlalchemy import select
    from app.domain.models.factura_venta import FacturaVenta

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


# ─── Cobros ───

class CobroCreate(BaseModel):
    factura_venta_id: uuid.UUID
    monto: float
    fecha: date
    metodo_pago: str = 'EFECTIVO'
    cuenta_banco_id: uuid.UUID | None = None
    concepto: str | None = None

@router.post("/cobros")
async def registrar_cobro(
    data: CobroCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    engine = DocumentEngine(db)
    result = await engine.process(
        document_type='COBRO',
        subtype_code='COBRO',
        action='CREATE',
        data={
            'factura_venta_id': str(data.factura_venta_id),
            'monto': data.monto,
            'fecha': data.fecha.isoformat(),
            'metodo_pago': data.metodo_pago,
            'cuenta_banco_id': str(data.cuenta_banco_id) if data.cuenta_banco_id else None,
            'concepto': data.concepto or 'Cobro',
            'afecta_banking': True,
            'genera_asiento': True,
        },
        user_id=current_user.id,
        company_id=current_user.empresa_id,
    )
    if not result.success:
        raise HTTPException(status_code=400, detail='; '.join(result.errors))
    return {
        "document_id": str(result.document_id),
        "asiento_id": str(result.asiento_id) if result.asiento_id else None,
        "estado": "COBRADA",
    }
