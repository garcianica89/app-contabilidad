from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.producto import Producto
from app.domain.models.categoria import Categoria
from app.domain.schemas import ProductoCreate, ProductoResponse
from pydantic import BaseModel

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


@router.put("/{producto_id}", response_model=ProductoResponse)
async def actualizar_producto(
    producto_id: uuid.UUID,
    data: ProductoCreate,
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
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(p, key, value)
    await db.commit()
    await db.refresh(p)
    return p


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


# ─── Categorias de Producto ──────────────────────────────────


class CategoriaCreate(BaseModel):
    nombre: str


class CategoriaResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    activa: bool

    class Config:
        from_attributes = True


@router.get("/categorias", response_model=list[CategoriaResponse])
async def listar_categorias(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Categoria).where(
            Categoria.empresa_id == current_user.empresa_id,
            Categoria.activa == True,
        ).order_by(Categoria.nombre)
    )
    return result.scalars().all()


@router.post("/categorias", response_model=CategoriaResponse, status_code=201)
async def crear_categoria(
    data: CategoriaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    cat = Categoria(empresa_id=current_user.empresa_id, nombre=data.nombre)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.put("/categorias/{categoria_id}", response_model=CategoriaResponse)
async def actualizar_categoria(
    categoria_id: uuid.UUID,
    data: CategoriaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Categoria).where(
            Categoria.id == categoria_id,
            Categoria.empresa_id == current_user.empresa_id,
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    cat.nombre = data.nombre
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/categorias/{categoria_id}", status_code=204)
async def eliminar_categoria(
    categoria_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Categoria).where(
            Categoria.id == categoria_id,
            Categoria.empresa_id == current_user.empresa_id,
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    cat.activa = False
    await db.commit()
