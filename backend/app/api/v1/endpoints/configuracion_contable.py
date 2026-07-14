import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.domain.accounting.models import ModuleAccountingConfig
from app.api.deps import get_current_user

router = APIRouter()


class ConfigContableResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    module: str
    concept_code: str
    concept_name: str
    account_id: Optional[uuid.UUID] = None
    auxiliary_account_id: Optional[uuid.UUID] = None
    cost_center_id: Optional[uuid.UUID] = None
    is_active: bool

    class Config:
        from_attributes = True


class ConfigContableUpdate(BaseModel):
    account_id: Optional[uuid.UUID] = None
    auxiliary_account_id: Optional[uuid.UUID] = None
    cost_center_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


@router.get("", response_model=list[ConfigContableResponse])
async def listar_config(
    module: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    q = select(ModuleAccountingConfig).where(
        ModuleAccountingConfig.company_id == usuario["empresa_id"]
    )
    if module:
        q = q.where(ModuleAccountingConfig.module == module)
    q = q.order_by(ModuleAccountingConfig.module, ModuleAccountingConfig.concept_code)
    r = await db.execute(q)
    return r.scalars().all()


@router.put("/{config_id}", response_model=ConfigContableResponse)
async def actualizar_config(
    config_id: uuid.UUID,
    data: ConfigContableUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    cfg = await db.get(ModuleAccountingConfig, config_id)
    if not cfg or cfg.company_id != usuario["empresa_id"]:
        raise HTTPException(404, "Configuracion no encontrada")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cfg, k, v)
    await db.commit()
    await db.refresh(cfg)
    return cfg
