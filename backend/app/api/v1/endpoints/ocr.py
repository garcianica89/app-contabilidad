import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.ocr import DocumentoOCR
from app.domain.models.usuario import Usuario

router = APIRouter()

class DocumentoOCRResponse(BaseModel):
    id: str
    filename: str
    content_type: str | None
    file_size: int | None
    estado: str
    texto_extraido: str | None
    datos_procesados: dict | None
    class Config: from_attributes = True

@router.get("", response_model=list[DocumentoOCRResponse])
async def list_documentos(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(
        select(DocumentoOCR).where(DocumentoOCR.empresa_id == user.empresa_id)
        .order_by(DocumentoOCR.created_at.desc())
    )
    return r.scalars().all()

@router.post("/upload", response_model=DocumentoOCRResponse, status_code=201)
async def upload_documento(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
    file: UploadFile = File(...),
):
    content = await file.read()
    obj = DocumentoOCR(
        empresa_id=user.empresa_id,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        estado="PENDIENTE",
        texto_extraido="",
        datos_procesados={"filename": file.filename, "size": len(content)},
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get("/{id}", response_model=DocumentoOCRResponse)
async def get_documento(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(
        select(DocumentoOCR).where(DocumentoOCR.id == id, DocumentoOCR.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    return obj

@router.delete("/{id}", status_code=204)
async def delete_documento(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_ELIMINAR"))],
):
    r = await db.execute(
        select(DocumentoOCR).where(DocumentoOCR.id == id, DocumentoOCR.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()
