from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.cuenta_contable import CuentaContable
from app.domain.schemas import CuentaContableCreate, CuentaContableResponse

router = APIRouter()


@router.get("/", response_model=list[CuentaContableResponse])
async def listar_cuentas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    tipo: str | None = None,
):
    query = select(CuentaContable).where(
        CuentaContable.empresa_id == current_user.empresa_id,
        CuentaContable.activa == True,
    )
    if tipo:
        query = query.where(CuentaContable.tipo == tipo)
    query = query.order_by(CuentaContable.codigo)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/arbol")
async def arbol_cuentas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(CuentaContable)
        .where(
            CuentaContable.empresa_id == current_user.empresa_id,
            CuentaContable.activa == True,
        )
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()

    def build_tree(padre_id=None):
        hijos = [c for c in cuentas if c.padre_id == padre_id]
        return [
            {
                "id": str(c.id),
                "codigo": c.codigo,
                "nombre": c.nombre,
                "tipo": c.tipo,
                "nivel": c.nivel,
                "acepta_datos": c.acepta_datos,
                "hijos": build_tree(c.id),
            }
            for c in hijos
        ]

    return build_tree()


@router.post("/", response_model=CuentaContableResponse, status_code=201)
async def crear_cuenta(
    data: CuentaContableCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(CuentaContable).where(
            CuentaContable.empresa_id == current_user.empresa_id,
            CuentaContable.codigo == data.codigo,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El codigo ya existe")

    cuenta = CuentaContable(
        empresa_id=current_user.empresa_id,
        **data.model_dump(),
    )
    db.add(cuenta)
    await db.commit()
    await db.refresh(cuenta)
    return cuenta
