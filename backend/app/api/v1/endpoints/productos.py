from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.producto import Producto
from app.domain.schemas import ProductoCreate, ProductoResponse

router = APIRouter()


@router.get("/", response_model=list[ProductoResponse])
async def listar_productos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    categoria_id: uuid.UUID | None = None,
):
    query = select(Producto).where(
        Producto.empresa_id == current_user.empresa_id,
        Producto.activo == True,
    )
    if categoria_id:
        query = query.where(Producto.categoria_id == categoria_id)
    query = query.order_by(Producto.nombre)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{producto_id}", response_model=ProductoResponse)
async def obtener_producto(
    producto_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Producto).where(
            Producto.id == producto_id,
            Producto.empresa_id == current_user.empresa_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return p


@router.post("/", response_model=ProductoResponse, status_code=201)
async def crear_producto(
    data: ProductoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    producto = Producto(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(producto)
    await db.commit()
    await db.refresh(producto)
    return producto


@router.get("/{producto_id}/kardex")
async def kardex_producto(
    producto_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    from app.domain.models.producto import KardexMovimiento

    result = await db.execute(
        select(KardexMovimiento)
        .where(
            KardexMovimiento.producto_id == producto_id,
            KardexMovimiento.empresa_id == current_user.empresa_id,
        )
        .order_by(KardexMovimiento.fecha, KardexMovimiento.created_at)
    )
    movs = result.scalars().all()
    return [
        {
            "fecha": str(m.fecha),
            "tipo": m.tipo,
            "tipo_documento": m.tipo_documento,
            "cantidad": float(m.cantidad),
            "costo_unitario": float(m.costo_unitario),
            "costo_total": float(m.costo_total),
            "saldo_cantidad": float(m.saldo_cantidad),
            "saldo_costo_promedio": float(m.saldo_costo_promedio),
            "saldo_total": float(m.saldo_total),
        }
        for m in movs
    ]
