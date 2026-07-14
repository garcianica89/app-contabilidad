from typing import Annotated
import uuid
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.producto import Producto, KardexMovimiento
from app.domain.models.asiento import Asiento
from app.service.document_engine.engine import DocumentEngine

router = APIRouter()


class SalidaLinea(BaseModel):
    producto_id: uuid.UUID
    cantidad: float


class SalidaInventarioCreate(BaseModel):
    fecha: date
    subtype_code: str
    bodega_id: uuid.UUID
    motivo: str
    lineas: list[SalidaLinea]


class SalidaInventarioResponse(BaseModel):
    success: bool
    documento_id: str | None = None
    numero: str | None = None
    estado: str | None = None
    asiento_id: str | None = None
    asiento_numero: str | None = None
    errors: list[str] = []


class SalidaListadoItem(BaseModel):
    id: str
    fecha: date | None = None
    numero: str
    concepto: str
    documento_id: str
    asiento_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[SalidaListadoItem])
async def listar_salidas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    asientos = await db.execute(
        select(Asiento).where(
            Asiento.empresa_id == current_user.empresa_id,
            Asiento.documento_tipo == 'SALIDA_INV',
        ).order_by(Asiento.fecha.desc(), Asiento.created_at.desc())
    )
    resultados = []
    for a in asientos.scalars():
        resultados.append(SalidaListadoItem(
            id=str(a.id),
            fecha=a.fecha if hasattr(a, 'fecha') else None,
            numero=str(a.numero),
            concepto=str(a.concepto),
            documento_id=str(a.documento_id) if a.documento_id else '',
            asiento_id=str(a.id),
            created_at=a.created_at,
        ))
    return resultados


@router.get("/{documento_id}", response_model=SalidaInventarioResponse)
async def obtener_salida(
    documento_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    asiento = await db.execute(
        select(Asiento).where(
            Asiento.empresa_id == current_user.empresa_id,
            Asiento.documento_tipo == 'SALIDA_INV',
            Asiento.documento_id == documento_id,
        )
    )
    a = asiento.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Salida no encontrada")

    return SalidaInventarioResponse(
        success=True,
        documento_id=str(documento_id),
        numero=a.numero,
        estado=a.estado,
        asiento_id=str(a.id),
        asiento_numero=a.numero,
    )


@router.post("/", response_model=SalidaInventarioResponse)
async def crear_salida(
    data: SalidaInventarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    company_id = current_user.empresa_id

    costo_total = Decimal('0')
    lineas_data = []
    for l in data.lineas:
        producto = await db.get(Producto, l.producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto {l.producto_id} no encontrado")
        cantidad = Decimal(str(l.cantidad))
        costo_unitario = producto.costo_promedio or Decimal('0')
        costo_total += cantidad * costo_unitario
        lineas_data.append({
            "producto_id": str(l.producto_id),
            "cantidad": float(cantidad),
            "costo_unitario": float(costo_unitario),
        })

    doc_data = {
        "fecha": data.fecha.isoformat(),
        "bodega_id": str(data.bodega_id),
        "motivo": data.motivo,
        "subtype_code": data.subtype_code,
        "lineas": lineas_data,
        "costo_total": float(costo_total),
        "concepto": f"Salida de inventario: {data.motivo}",
        "afecta_cxc": False,
        "afecta_cxp": False,
        "afecta_bancos": False,
    }

    engine = DocumentEngine(db)
    result = await engine.process(
        document_type='SALIDA_INV',
        subtype_code=data.subtype_code,
        action='CREATE',
        data=doc_data,
        user_id=current_user.id,
        company_id=company_id,
    )

    await db.commit()

    return SalidaInventarioResponse(
        success=result.success,
        documento_id=str(result.document_id) if result.document_id else None,
        numero=result.numero,
        estado=result.estado,
        asiento_id=str(result.asiento_id) if result.asiento_id else None,
        asiento_numero=result.asiento_numero,
        errors=result.errors,
    )
