from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.tercero import Tercero

router = APIRouter()


@router.get("/", response_model=list[dict])
async def list_terceros(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
    rol: str | None = None,
    search: str | None = None,
):
    query = select(Tercero).where(Tercero.company_id == user.empresa_id, Tercero.is_active == True)

    if rol == 'cliente':
        query = query.where(Tercero.es_cliente == True)
    elif rol == 'proveedor':
        query = query.where(Tercero.es_proveedor == True)
    elif rol == 'empleado':
        query = query.where(Tercero.es_empleado == True)

    if search:
        query = query.where(
            or_(
                Tercero.nombre_legal.ilike(f"%{search}%"),
                Tercero.codigo.ilike(f"%{search}%"),
                Tercero.numero_documento.ilike(f"%{search}%"),
            )
        )

    result = await db.execute(query)
    return [
        {
            "id": str(t.id),
            "codigo": t.codigo,
            "tipo_documento": t.tipo_documento,
            "numero_documento": t.numero_documento,
            "nombre_legal": t.nombre_legal,
            "nombre_comercial": t.nombre_comercial,
            "telefono": t.telefono,
            "email": t.email,
            "es_cliente": t.es_cliente,
            "es_proveedor": t.es_proveedor,
            "es_empleado": t.es_empleado,
            "limite_credito": float(t.limite_credito) if t.limite_credito else None,
            "salario_base": float(t.salario_base) if t.salario_base else None,
        }
        for t in result.scalars().all()
    ]


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_tercero(
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(Tercero).where(
            Tercero.company_id == user.empresa_id,
            Tercero.codigo == data.get('codigo'),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un tercero con ese codigo")

    tercero = Tercero(
        company_id=user.empresa_id,
        codigo=data.get('codigo'),
        tipo_documento=data.get('tipo_documento', 'RUC'),
        numero_documento=data.get('numero_documento', ''),
        nombre_legal=data.get('nombre_legal', ''),
        nombre_comercial=data.get('nombre_comercial'),
        direccion=data.get('direccion'),
        telefono=data.get('telefono'),
        email=data.get('email'),
        es_cliente=data.get('es_cliente', False),
        es_proveedor=data.get('es_proveedor', False),
        es_empleado=data.get('es_empleado', False),
        limite_credito=data.get('limite_credito'),
        condicion_pago_id=data.get('condicion_pago_id'),
        tipo_proveedor=data.get('tipo_proveedor', 'NACIONAL'),
        aplica_iva=data.get('aplica_iva', True),
    )
    db.add(tercero)
    await db.commit()
    await db.refresh(tercero)
    return {"id": str(tercero.id), "codigo": tercero.codigo, "nombre_legal": tercero.nombre_legal}


@router.get("/{tercero_id}", response_model=dict)
async def get_tercero(
    tercero_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Tercero).where(
            Tercero.id == tercero_id,
            Tercero.company_id == user.empresa_id,
        )
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")
    return {
        "id": str(t.id),
        "codigo": t.codigo,
        "tipo_documento": t.tipo_documento,
        "numero_documento": t.numero_documento,
        "nombre_legal": t.nombre_legal,
        "nombre_comercial": t.nombre_comercial,
        "direccion": t.direccion,
        "telefono": t.telefono,
        "email": t.email,
        "es_cliente": t.es_cliente,
        "es_proveedor": t.es_proveedor,
        "es_empleado": t.es_empleado,
        "limite_credito": float(t.limite_credito) if t.limite_credito else None,
        "condicion_pago_id": str(t.condicion_pago_id) if t.condicion_pago_id else None,
        "tipo_proveedor": t.tipo_proveedor,
        "aplica_iva": t.aplica_iva,
        "salario_base": float(t.salario_base) if t.salario_base else None,
    }


@router.put("/{tercero_id}", response_model=dict)
async def update_tercero(
    tercero_id: str,
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Tercero).where(
            Tercero.id == tercero_id,
            Tercero.company_id == user.empresa_id,
        )
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")
    for key, value in data.items():
        if hasattr(t, key) and key not in ('id', 'company_id', 'created_at'):
            setattr(t, key, value)
    await db.commit()
    return {"id": str(t.id), "codigo": t.codigo}


@router.delete("/{tercero_id}", status_code=204)
async def delete_tercero(
    tercero_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Tercero).where(
            Tercero.id == tercero_id,
            Tercero.company_id == user.empresa_id,
        )
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")
    t.is_active = False
    await db.commit()
