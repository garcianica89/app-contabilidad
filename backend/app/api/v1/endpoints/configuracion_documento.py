from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.usuario import Usuario
from app.domain.models.document_type import DocumentoTipo, DocumentoSubtipo

router = APIRouter()


@router.get("/")
async def listar_configuracion(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Lista toda la configuracion de tipos y subtipos de documento."""
    tipos = await db.execute(
        select(DocumentoTipo).where(DocumentoTipo.company_id == current_user.empresa_id)
    )
    result = []
    for t in tipos.scalars():
        subtipos = await db.execute(
            select(DocumentoSubtipo).where(
                DocumentoSubtipo.documento_tipo_id == t.id,
                DocumentoSubtipo.company_id == current_user.empresa_id,
            )
        )
        result.append({
            "id": str(t.id),
            "codigo": t.codigo,
            "nombre": t.nombre,
            "modulo": t.modulo.codigo if t.modulo else None,
            "genera_asiento": t.genera_asiento,
            "afecta_inventario": t.afecta_inventario,
            "afecta_cxc": t.afecta_cxc,
            "afecta_cxp": t.afecta_cxp,
            "afecta_bancos": t.afecta_bancos,
            "subtipos": [
                {
                    "id": str(s.id),
                    "codigo": s.codigo,
                    "nombre": s.nombre,
                    "genera_asiento": s.genera_asiento,
                    "afecta_inventario": s.afecta_inventario,
                    "afecta_cxc": s.afecta_cxc,
                    "afecta_cxp": s.afecta_cxp,
                    "afecta_bancos": s.afecta_bancos,
                    "calcula_iva": s.calcula_iva,
                    "aplica_retenciones": s.aplica_retenciones,
                    "genera_costo_venta": s.genera_costo_venta,
                    "requiere_centros_costo": s.requiere_centros_costo,
                    "cuenta_descuentos_id": str(s.cuenta_descuentos_id) if s.cuenta_descuentos_id else None,
                    "cuenta_principal_id": str(s.cuenta_principal_id) if s.cuenta_principal_id else None,
                    "cuenta_impuestos_id": str(s.cuenta_impuestos_id) if s.cuenta_impuestos_id else None,
                    "cuenta_retencion_id": str(s.cuenta_retencion_id) if s.cuenta_retencion_id else None,
                    "cost_center_default_id": str(s.cost_center_default_id) if s.cost_center_default_id else None,
                }
                for s in subtipos.scalars()
            ],
        })
    return result


@router.put("/{tipo_id}")
async def actualizar_configuracion_tipo(
    tipo_id: uuid.UUID,
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Actualiza configuracion de un tipo de documento."""
    tipo = await db.get(DocumentoTipo, tipo_id)
    if not tipo or tipo.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")

    for field in ('genera_asiento', 'afecta_inventario', 'afecta_cxc', 'afecta_cxp', 'afecta_bancos'):
        if field in data:
            setattr(tipo, field, bool(data[field]))
    await db.commit()
    return {"status": "ok"}


@router.get("/subtipos")
async def listar_subtipos_por_tipo(
    tipo_codigo: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Lista subtipos para un tipo de documento especifico."""
    tipo = await db.execute(
        select(DocumentoTipo).where(
            DocumentoTipo.company_id == current_user.empresa_id,
            DocumentoTipo.codigo == tipo_codigo,
        )
    )
    tipo = tipo.scalar_one_or_none()
    if not tipo:
        return []

    subtipos = await db.execute(
        select(DocumentoSubtipo).where(
            DocumentoSubtipo.documento_tipo_id == tipo.id,
            DocumentoSubtipo.company_id == current_user.empresa_id,
            DocumentoSubtipo.is_active == True,
        ).order_by(DocumentoSubtipo.nombre)
    )
    return [
        {
            "id": str(s.id),
            "codigo": s.codigo,
            "nombre": s.nombre,
            "cuenta_principal_id": str(s.cuenta_principal_id) if s.cuenta_principal_id else None,
        }
        for s in subtipos.scalars()
    ]


@router.post("/subtipos")
async def crear_subtipo(
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Crea un nuevo subtipo para un tipo de documento."""
    tipo_codigo = data.get("tipo_codigo")
    codigo = data.get("codigo")
    nombre = data.get("nombre")
    if not tipo_codigo or not codigo or not nombre:
        raise HTTPException(status_code=400, detail="tipo_codigo, codigo y nombre son requeridos")

    tipo = await db.execute(
        select(DocumentoTipo).where(
            DocumentoTipo.company_id == current_user.empresa_id,
            DocumentoTipo.codigo == tipo_codigo,
        )
    )
    tipo = tipo.scalar_one_or_none()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")

    existing = await db.execute(
        select(DocumentoSubtipo).where(
            DocumentoSubtipo.company_id == current_user.empresa_id,
            DocumentoSubtipo.documento_tipo_id == tipo.id,
            DocumentoSubtipo.codigo == codigo,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un subtipo con ese codigo")

    subtipo = DocumentoSubtipo(
        company_id=current_user.empresa_id,
        documento_tipo_id=tipo.id,
        codigo=codigo,
        nombre=nombre,
        nombre_corto=data.get("nombre_corto", codigo),
        genera_asiento=data.get("genera_asiento", True),
        afecta_inventario=data.get("afecta_inventario", False),
        afecta_cxc=data.get("afecta_cxc", False),
        afecta_cxp=data.get("afecta_cxp", False),
        afecta_bancos=data.get("afecta_bancos", False),
        calcula_iva=data.get("calcula_iva", False),
        aplica_retenciones=data.get("aplica_retenciones", False),
        genera_costo_venta=data.get("genera_costo_venta", False),
        is_active=True,
    )
    cuenta_id = data.get("cuenta_principal_id")
    if cuenta_id:
        subtipo.cuenta_principal_id = uuid.UUID(cuenta_id)

    db.add(subtipo)
    await db.commit()
    return {"status": "ok", "id": str(subtipo.id)}


@router.put("/subtipo/{subtipo_id}")
async def actualizar_configuracion_subtipo(
    subtipo_id: uuid.UUID,
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Actualiza configuracion de un subtipo de documento."""
    subtipo = await db.get(DocumentoSubtipo, subtipo_id)
    if not subtipo or subtipo.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Subtipo de documento no encontrado")

    config_fields = (
        'genera_asiento', 'afecta_inventario', 'afecta_cxc', 'afecta_cxp',
        'afecta_bancos', 'calcula_iva', 'aplica_retenciones',
        'genera_costo_venta', 'requiere_centros_costo',
    )
    for field in config_fields:
        if field in data:
            setattr(subtipo, field, bool(data[field]))
    account_fields = (
        'cuenta_descuentos_id', 'cuenta_principal_id', 'cuenta_impuestos_id',
        'cuenta_retencion_id', 'cost_center_default_id',
    )
    for field in account_fields:
        if field in data:
            val = data[field]
            setattr(subtipo, field, uuid.UUID(val) if val else None)
    await db.commit()
    return {"status": "ok"}
