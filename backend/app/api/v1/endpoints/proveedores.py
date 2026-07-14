from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.proveedor import Proveedor
from app.domain.models.asociaciones import proveedor_retencion
from pydantic import BaseModel

router = APIRouter()


class ProveedorCreate(BaseModel):
    codigo: str | None = None
    nombre: str
    ruc: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    plazo_credito: int = 30
    aplica_iva: bool = True
    tasa_iva: float = 15.00
    tipo_fiscal: str = 'NORMAL'
    sujeto_retenciones: bool = True
    categoria_id: str | None = None
    retenciones: list[str] = []


async def _proveedor_to_dict(p: Proveedor) -> dict:
    return {
        "id": str(p.id),
        "codigo": p.codigo,
        "nombre": p.nombre,
        "ruc": p.ruc,
        "direccion": p.direccion,
        "telefono": p.telefono,
        "email": p.email,
        "saldo": float(p.saldo),
        "plazo_credito": p.plazo_credito,
        "aplica_iva": p.aplica_iva,
        "tasa_iva": float(p.tasa_iva),
        "tipo_fiscal": p.tipo_fiscal,
        "sujeto_retenciones": p.sujeto_retenciones,
        "activo": p.activo,
        "categoria_id": str(p.categoria_id) if p.categoria_id else None,
        "retenciones": [{"id": str(r.id), "codigo": r.codigo, "nombre": r.nombre,
                         "porcentaje": float(r.porcentaje), "tipo": r.tipo}
                        for r in p.retenciones],
        "created_at": p.created_at.isoformat(),
    }


@router.get("/")
async def listar_proveedores(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Proveedor)
        .options(selectinload(Proveedor.retenciones))
        .where(
            Proveedor.empresa_id == current_user.empresa_id,
            Proveedor.activo == True,
        ).order_by(Proveedor.nombre)
    )
    return [_proveedor_to_dict(p) for p in result.scalars().all()]


@router.get("/{proveedor_id}")
async def obtener_proveedor(
    proveedor_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Proveedor)
        .options(selectinload(Proveedor.retenciones))
        .where(
            Proveedor.id == proveedor_id,
            Proveedor.empresa_id == current_user.empresa_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return _proveedor_to_dict(p)


@router.post("/", status_code=201)
async def crear_proveedor(
    data: ProveedorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    from app.domain.models.retencion import Retencion
    retencion_ids = [uuid.UUID(rid) for rid in data.retenciones]
    retenciones = []
    if retencion_ids:
        result = await db.execute(
            select(Retencion).where(Retencion.id.in_(retencion_ids))
        )
        retenciones = result.scalars().all()
    proveedor = Proveedor(
        empresa_id=current_user.empresa_id,
        codigo=data.codigo,
        nombre=data.nombre,
        ruc=data.ruc,
        direccion=data.direccion,
        telefono=data.telefono,
        email=data.email,
        plazo_credito=data.plazo_credito,
        aplica_iva=data.aplica_iva,
        tasa_iva=data.tasa_iva,
        tipo_fiscal=data.tipo_fiscal,
        sujeto_retenciones=data.sujeto_retenciones,
        categoria_id=uuid.UUID(data.categoria_id) if data.categoria_id else None,
        retenciones=retenciones,
    )
    db.add(proveedor)
    await db.commit()
    await db.refresh(proveedor)
    return _proveedor_to_dict(proveedor)


@router.put("/{proveedor_id}")
async def actualizar_proveedor(
    proveedor_id: uuid.UUID,
    data: ProveedorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    from app.domain.models.retencion import Retencion
    result = await db.execute(
        select(Proveedor)
        .options(selectinload(Proveedor.retenciones))
        .where(
            Proveedor.id == proveedor_id,
            Proveedor.empresa_id == current_user.empresa_id,
        )
    )
    prov = result.scalar_one_or_none()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    prov.codigo = data.codigo
    prov.nombre = data.nombre
    prov.ruc = data.ruc
    prov.direccion = data.direccion
    prov.telefono = data.telefono
    prov.email = data.email
    prov.plazo_credito = data.plazo_credito
    prov.aplica_iva = data.aplica_iva
    prov.tasa_iva = data.tasa_iva
    prov.tipo_fiscal = data.tipo_fiscal
    prov.sujeto_retenciones = data.sujeto_retenciones
    prov.categoria_id = uuid.UUID(data.categoria_id) if data.categoria_id else None

    retencion_ids = [uuid.UUID(rid) for rid in data.retenciones]
    if retencion_ids:
        r_result = await db.execute(
            select(Retencion).where(Retencion.id.in_(retencion_ids))
        )
        prov.retenciones = r_result.scalars().all()
    else:
        prov.retenciones = []

    await db.commit()
    await db.refresh(prov)
    return _proveedor_to_dict(prov)
