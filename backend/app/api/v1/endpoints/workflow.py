from typing import Annotated
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.workflow import (
    WfWorkflow, WfStatus, WfTransition, WfDocumentHistory, WfPendingApproval
)
from app.domain.models.document_type import DocumentoTipo
from app.service.workflow_engine import WorkflowEngine

router = APIRouter()


class WfCreate(BaseModel):
    documento_tipo_id: uuid.UUID
    codigo: str
    nombre: str


class WfUpdate(BaseModel):
    nombre: str | None = None
    is_active: bool | None = None


class StatusCreate(BaseModel):
    codigo: str
    nombre: str
    es_inicial: bool = False
    es_final: bool = False
    requiere_aprobacion: bool = False
    requiere_firma: bool = False
    notificar_al_entrar: bool = False


class TransitionCreate(BaseModel):
    from_status_id: uuid.UUID
    to_status_id: uuid.UUID
    action_code: str
    nombre: str
    requiere_comentario: bool = False
    requiere_aprobacion: bool = False
    cantidad_aprobaciones: int = 1
    es_reversion: bool = False


class TransitionExecute(BaseModel):
    document_id: uuid.UUID
    action: str
    comment: str = ""


class ApproveReject(BaseModel):
    approved: bool
    comment: str = ""


# ── Workflow CRUD ────────────────────────────────────────────────
@router.get("/", response_model=list[dict])
async def list_workflows(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(WfWorkflow).where(
            WfWorkflow.company_id == current_user.empresa_id
        ).order_by(WfWorkflow.codigo)
    )
    return [
        {
            "id": str(w.id),
            "documento_tipo_id": str(w.documento_tipo_id),
            "codigo": w.codigo,
            "nombre": w.nombre,
            "is_active": w.is_active,
            "created_at": w.created_at.isoformat(),
        }
        for w in result.scalars().all()
    ]


@router.post("/", response_model=dict, status_code=201)
async def create_workflow(
    data: WfCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    existing = await db.execute(
        select(WfWorkflow).where(
            WfWorkflow.company_id == current_user.empresa_id,
            WfWorkflow.codigo == data.codigo,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Workflow ya existe con ese codigo")
    wf = WfWorkflow(
        company_id=current_user.empresa_id,
        documento_tipo_id=data.documento_tipo_id,
        codigo=data.codigo,
        nombre=data.nombre,
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return {"id": str(wf.id), "codigo": wf.codigo, "nombre": wf.nombre}


@router.get("/{workflow_id}", response_model=dict)
async def get_workflow(
    workflow_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(WfWorkflow).where(
            WfWorkflow.id == workflow_id,
            WfWorkflow.company_id == current_user.empresa_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    statuses = await db.execute(
        select(WfStatus).where(WfStatus.workflow_id == wf.id).order_by(WfStatus.codigo)
    )
    transitions = await db.execute(
        select(WfTransition).where(WfTransition.workflow_id == wf.id)
    )
    return {
        "id": str(wf.id),
        "documento_tipo_id": str(wf.documento_tipo_id),
        "codigo": wf.codigo,
        "nombre": wf.nombre,
        "is_active": wf.is_active,
        "statuses": [
            {
                "id": str(s.id),
                "codigo": s.codigo,
                "nombre": s.nombre,
                "es_inicial": s.es_inicial,
                "es_final": s.es_final,
                "requiere_aprobacion": s.requiere_aprobacion,
            }
            for s in statuses.scalars().all()
        ],
        "transitions": [
            {
                "id": str(t.id),
                "from_status_id": str(t.from_status_id),
                "to_status_id": str(t.to_status_id),
                "action_code": t.action_code,
                "nombre": t.nombre,
                "requiere_aprobacion": t.requiere_aprobacion,
            }
            for t in transitions.scalars().all()
        ],
    }


@router.put("/{workflow_id}", response_model=dict)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WfUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(WfWorkflow).where(
            WfWorkflow.id == workflow_id,
            WfWorkflow.company_id == current_user.empresa_id,
        )
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    if data.nombre is not None:
        wf.nombre = data.nombre
    if data.is_active is not None:
        wf.is_active = data.is_active
    await db.commit()
    return {"id": str(wf.id), "codigo": wf.codigo}


# ── Status CRUD ──────────────────────────────────────────────────
@router.post("/{workflow_id}/statuses", response_model=dict, status_code=201)
async def create_status(
    workflow_id: uuid.UUID,
    data: StatusCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    wf = await db.get(WfWorkflow, workflow_id)
    if not wf or wf.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    status_obj = WfStatus(
        workflow_id=workflow_id,
        **data.model_dump(),
    )
    db.add(status_obj)
    await db.commit()
    await db.refresh(status_obj)
    return {"id": str(status_obj.id), "codigo": status_obj.codigo, "nombre": status_obj.nombre}


@router.put("/statuses/{status_id}", response_model=dict)
async def update_status(
    status_id: uuid.UUID,
    data: StatusCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(WfStatus).where(WfStatus.id == status_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Status no encontrado")
    wf = await db.get(WfWorkflow, s.workflow_id)
    if not wf or wf.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Status no encontrado")
    for key, value in data.model_dump().items():
        setattr(s, key, value)
    await db.commit()
    return {"id": str(s.id), "codigo": s.codigo}


@router.delete("/statuses/{status_id}", status_code=204)
async def delete_status(
    status_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(WfStatus).where(WfStatus.id == status_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Status no encontrado")
    wf = await db.get(WfWorkflow, s.workflow_id)
    if not wf or wf.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Status no encontrado")
    await db.delete(s)
    await db.commit()


# ── Transition CRUD ──────────────────────────────────────────────
@router.post("/{workflow_id}/transitions", response_model=dict, status_code=201)
async def create_transition(
    workflow_id: uuid.UUID,
    data: TransitionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    wf = await db.get(WfWorkflow, workflow_id)
    if not wf or wf.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    transition = WfTransition(
        workflow_id=workflow_id,
        **data.model_dump(),
    )
    db.add(transition)
    await db.commit()
    await db.refresh(transition)
    return {"id": str(transition.id), "action_code": transition.action_code, "nombre": transition.nombre}


@router.delete("/transitions/{transition_id}", status_code=204)
async def delete_transition(
    transition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(select(WfTransition).where(WfTransition.id == transition_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Transicion no encontrada")
    wf = await db.get(WfWorkflow, t.workflow_id)
    if not wf or wf.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Transicion no encontrada")
    await db.delete(t)
    await db.commit()


# ── Execute transition ───────────────────────────────────────────
@router.post("/{workflow_id}/transition", response_model=dict)
async def execute_transition(
    workflow_id: uuid.UUID,
    data: TransitionExecute,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    engine = WorkflowEngine(db)
    wf = await db.get(WfWorkflow, workflow_id)
    if not wf or wf.company_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    tipo_doc = await db.get(DocumentoTipo, wf.documento_tipo_id)
    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")

    new_state = await engine.transition(
        document_type=tipo_doc.codigo,
        action=data.action,
        company_id=current_user.empresa_id,
        document_id=data.document_id,
        user_id=current_user.id,
        comment=data.comment,
    )
    return {
        "document_id": str(data.document_id),
        "action": data.action,
        "nuevo_estado": new_state,
    }


# ── History ──────────────────────────────────────────────────────
@router.get("/{workflow_id}/history", response_model=list[dict])
async def get_history(
    workflow_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    document_id: uuid.UUID | None = None,
):
    query = select(WfDocumentHistory).join(
        WfTransition, WfDocumentHistory.transition_id == WfTransition.id
    ).where(
        WfTransition.workflow_id == workflow_id,
    ).order_by(WfDocumentHistory.created_at.desc())
    if document_id:
        query = query.where(WfDocumentHistory.documento_id == document_id)
    result = await db.execute(query)
    return [
        {
            "id": str(h.id),
            "documento_id": str(h.documento_id),
            "from_status_id": str(h.from_status_id) if h.from_status_id else None,
            "to_status_id": str(h.to_status_id),
            "user_id": str(h.user_id),
            "comentario": h.comentario,
            "created_at": h.created_at.isoformat(),
        }
        for h in result.scalars().all()
    ]


# ── Pending approvals ────────────────────────────────────────────
@router.get("/pending-approvals", response_model=list[dict])
async def list_pending_approvals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(WfPendingApproval).where(
            WfPendingApproval.estado == 'PENDIENTE'
        ).order_by(WfPendingApproval.created_at.desc())
    )
    return [
        {
            "id": str(pa.id),
            "documento_tipo_id": str(pa.documento_tipo_id),
            "documento_id": str(pa.documento_id),
            "transition_id": str(pa.transition_id),
            "solicitado_por": str(pa.solicitado_por),
            "estado": pa.estado,
            "created_at": pa.created_at.isoformat(),
        }
        for pa in result.scalars().all()
    ]


@router.post("/pending-approvals/{approval_id}/resolve", response_model=dict)
async def resolve_approval(
    approval_id: uuid.UUID,
    data: ApproveReject,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    engine = WorkflowEngine(db)
    success = await engine.approve(
        approval_id=approval_id,
        user_id=current_user.id,
        approved=data.approved,
        comment=data.comment,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Aprobacion no encontrada")
    return {"mensaje": "Aprobacion resuelta", "approved": data.approved}
