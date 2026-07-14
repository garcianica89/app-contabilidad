from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.accounting.models import JournalTemplate, JournalTemplateLine, JournalType
from app.domain.schemas import (
    JournalTemplateCreate,
    JournalTemplateUpdate,
    JournalTemplateResponse,
    JournalTemplateLineCreate,
    JournalTemplateLineResponse,
)

router = APIRouter()


@router.get("/", response_model=list[JournalTemplateResponse])
async def listar_plantillas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    journal_type_id: uuid.UUID | None = None,
):
    query = (
        select(JournalTemplate)
        .where(JournalTemplate.company_id == current_user.empresa_id)
        .options(selectinload(JournalTemplate.lines))
        .order_by(JournalTemplate.priority.desc(), JournalTemplate.name)
    )
    if journal_type_id:
        query = query.where(JournalTemplate.journal_type_id == journal_type_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{plantilla_id}", response_model=JournalTemplateResponse)
async def obtener_plantilla(
    plantilla_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(JournalTemplate)
        .where(
            JournalTemplate.id == plantilla_id,
            JournalTemplate.company_id == current_user.empresa_id,
        )
        .options(selectinload(JournalTemplate.lines))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return t


@router.post("/", response_model=JournalTemplateResponse, status_code=201)
async def crear_plantilla(
    data: JournalTemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    jt = await db.get(JournalType, data.journal_type_id)
    if not jt or jt.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Tipo de asiento no encontrado")

    template = JournalTemplate(
        journal_type_id=data.journal_type_id,
        company_id=current_user.empresa_id,
        name=data.name,
        priority=data.priority,
        condition_expr=data.condition_expr,
        is_active=data.is_active,
    )
    db.add(template)
    await db.flush()

    for line_data in data.lines:
        line = JournalTemplateLine(
            template_id=template.id,
            **line_data.model_dump(),
        )
        db.add(line)

    await db.commit()
    await db.refresh(template)
    result = await db.execute(
        select(JournalTemplate)
        .where(JournalTemplate.id == template.id)
        .options(selectinload(JournalTemplate.lines))
    )
    return result.scalar_one()


@router.put("/{plantilla_id}", response_model=JournalTemplateResponse)
async def actualizar_plantilla(
    plantilla_id: uuid.UUID,
    data: JournalTemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(JournalTemplate)
        .where(
            JournalTemplate.id == plantilla_id,
            JournalTemplate.company_id == current_user.empresa_id,
        )
        .options(selectinload(JournalTemplate.lines))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(t, key, value)
    await db.commit()
    await db.refresh(t)
    return t


@router.delete("/{plantilla_id}", status_code=204)
async def eliminar_plantilla(
    plantilla_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    t = await db.get(JournalTemplate, plantilla_id)
    if not t or t.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    await db.delete(t)
    await db.commit()


@router.post("/{plantilla_id}/lineas", response_model=JournalTemplateLineResponse, status_code=201)
async def agregar_linea(
    plantilla_id: uuid.UUID,
    data: JournalTemplateLineCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    t = await db.get(JournalTemplate, plantilla_id)
    if not t or t.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    line = JournalTemplateLine(template_id=plantilla_id, **data.model_dump())
    db.add(line)
    await db.commit()
    await db.refresh(line)
    return line


@router.put("/lineas/{linea_id}", response_model=JournalTemplateLineResponse)
async def actualizar_linea(
    linea_id: uuid.UUID,
    data: JournalTemplateLineCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    line = await db.get(JournalTemplateLine, linea_id)
    if not line:
        raise HTTPException(status_code=404, detail="Linea no encontrada")
    t = await db.get(JournalTemplate, line.template_id)
    if not t or t.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(line, key, value)
    await db.commit()
    await db.refresh(line)
    return line


@router.delete("/lineas/{linea_id}", status_code=204)
async def eliminar_linea(
    linea_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    line = await db.get(JournalTemplateLine, linea_id)
    if not line:
        raise HTTPException(status_code=404, detail="Linea no encontrada")
    t = await db.get(JournalTemplate, line.template_id)
    if not t or t.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    await db.delete(line)
    await db.commit()
