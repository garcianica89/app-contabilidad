from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.document_type import ModuloSistema, DocumentoTipo, DocumentoSubtipo, DocumentoEstado

router = APIRouter()


@router.get("/modulos", response_model=list[dict])
async def list_modulos(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(ModuloSistema).where(ModuloSistema.is_active == True).order_by(ModuloSistema.orden))
    modulos = result.scalars().all()
    return [{"id": str(m.id), "codigo": m.codigo, "nombre": m.nombre, "icono": m.icono, "orden": m.orden} for m in modulos]


@router.get("/modulos/{modulo_id}/documentos", response_model=list[dict])
async def list_documentos_por_modulo(
    modulo_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(DocumentoTipo).where(
            DocumentoTipo.modulo_id == modulo_id,
            DocumentoTipo.company_id == user.empresa_id,
            DocumentoTipo.is_active == True,
        )
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "codigo": d.codigo,
            "nombre": d.nombre,
            "nombre_corto": d.nombre_corto,
            "genera_asiento": d.genera_asiento,
            "afecta_inventario": d.afecta_inventario,
            "afecta_cxc": d.afecta_cxc,
            "afecta_cxp": d.afecta_cxp,
        }
        for d in docs
    ]
