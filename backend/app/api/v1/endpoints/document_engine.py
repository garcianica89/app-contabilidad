from typing import Annotated
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.service.document_engine.engine import DocumentEngine

router = APIRouter()


class ProcessDocumentRequest(BaseModel):
    document_type: str
    subtype_code: str
    action: str
    data: dict
    document_id: str | None = None


@router.post("/process", response_model=dict)
async def process_document(
    req: ProcessDocumentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    engine = DocumentEngine(db)
    result = await engine.process(
        document_type=req.document_type,
        subtype_code=req.subtype_code,
        action=req.action,
        data=req.data,
        user_id=current_user.id,
        company_id=current_user.empresa_id,
        document_id=uuid.UUID(req.document_id) if req.document_id else None,
    )
    return {
        "success": result.success,
        "document_type": result.document_type,
        "document_id": str(result.document_id) if result.document_id else None,
        "numero": result.numero,
        "estado": result.estado,
        "asiento_id": str(result.asiento_id) if result.asiento_id else None,
        "asiento_numero": result.asiento_numero,
        "errors": result.errors,
        "warnings": result.warnings,
        "metadata": result.metadata,
    }
