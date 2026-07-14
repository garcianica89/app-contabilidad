"""
Workflow Engine — Motor de Workflow.

Cada documento tiene estados definidos en wf_workflow.
Las transiciones estan configuradas en wf_transition.
Cada transicion puede requerir aprobacion, reglas, firmas.
"""
import uuid
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.workflow import (
    WfWorkflow, WfStatus, WfTransition, WfDocumentHistory, WfPendingApproval
)
from app.domain.models.document_type import DocumentoTipo


class WorkflowEngine:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def transition(
        self,
        document_type: str,
        action: str,
        company_id: uuid.UUID,
        document_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        comment: str = "",
    ) -> Optional[str]:
        """
        Ejecuta una transicion de workflow.

        Returns el codigo del nuevo estado, o None si no hay workflow.
        """
        # 1. Obtener el tipo de documento
        tipo_doc = await self._get_document_type(document_type, company_id)
        if not tipo_doc:
            return 'BORRADOR'

        # 2. Obtener el workflow activo
        workflow = await self._get_workflow(tipo_doc.id, company_id)
        if not workflow:
            return 'BORRADOR'

        # 3. Obtener estado actual (o inicial)
        current_status = await self._get_current_status(workflow.id, document_id)
        if not current_status and document_id:
            current_status = await self._get_initial_status(workflow.id)

        # 4. Buscar transicion valida
        if not current_status:
            return 'BORRADOR'

        transition = await self._find_transition(workflow.id, current_status.id, action)
        if not transition:
            return current_status.codigo

        # 5. Verificar reglas de aprobacion
        if transition.requiere_aprobacion:
            if user_id:
                await self._create_pending_approval(
                    tipo_doc.id, document_id, transition.id, user_id
                )
            return 'PENDIENTE_APROBACION'

        # 6. Registrar historial
        await self._record_history(
            tipo_doc.id, document_id,
            current_status.id, transition.to_status_id,
            transition.id, user_id, comment
        )

        # 7. Retornar nuevo estado
        target_status = await self._get_status_by_id(transition.to_status_id)
        return target_status.codigo if target_status else 'BORRADOR'

    async def _get_document_type(self, code: str, company_id: uuid.UUID) -> Optional[DocumentoTipo]:
        q = select(DocumentoTipo).where(
            DocumentoTipo.codigo == code,
            DocumentoTipo.company_id == company_id,
            DocumentoTipo.is_active == True,
        )
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def _get_workflow(self, tipo_doc_id: uuid.UUID, company_id: uuid.UUID) -> Optional[WfWorkflow]:
        q = select(WfWorkflow).where(
            WfWorkflow.documento_tipo_id == tipo_doc_id,
            WfWorkflow.company_id == company_id,
            WfWorkflow.is_active == True,
        )
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def _get_current_status(self, workflow_id: uuid.UUID, document_id: Optional[uuid.UUID]) -> Optional[WfStatus]:
        if not document_id:
            return await self._get_initial_status(workflow_id)
        q = (
            select(WfStatus)
            .join(WfDocumentHistory, WfDocumentHistory.to_status_id == WfStatus.id)
            .where(
                WfDocumentHistory.documento_id == document_id,
                WfStatus.workflow_id == workflow_id,
            )
            .order_by(WfDocumentHistory.created_at.desc())
            .limit(1)
        )
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def _get_initial_status(self, workflow_id: uuid.UUID) -> Optional[WfStatus]:
        q = select(WfStatus).where(
            WfStatus.workflow_id == workflow_id,
            WfStatus.es_inicial == True,
        )
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def _find_transition(
        self, workflow_id: uuid.UUID, from_status_id: uuid.UUID, action: str
    ) -> Optional[WfTransition]:
        q = select(WfTransition).where(
            WfTransition.workflow_id == workflow_id,
            WfTransition.from_status_id == from_status_id,
            WfTransition.action_code == action,
            WfTransition.is_active == True,
        )
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def _create_pending_approval(
        self, tipo_doc_id: uuid.UUID, document_id: Optional[uuid.UUID],
        transition_id: uuid.UUID, user_id: uuid.UUID,
    ):
        if not document_id:
            return
        pa = WfPendingApproval(
            documento_tipo_id=tipo_doc_id,
            documento_id=document_id,
            transition_id=transition_id,
            solicitado_por=user_id,
            estado='PENDIENTE',
        )
        self.db.add(pa)
        await self.db.flush()

    async def _record_history(
        self, tipo_doc_id: uuid.UUID, document_id: Optional[uuid.UUID],
        from_status_id: Optional[uuid.UUID], to_status_id: uuid.UUID,
        transition_id: Optional[uuid.UUID], user_id: Optional[uuid.UUID],
        comment: str,
    ):
        if not document_id:
            return
        h = WfDocumentHistory(
            documento_tipo_id=tipo_doc_id,
            documento_id=document_id,
            from_status_id=from_status_id,
            to_status_id=to_status_id,
            transition_id=transition_id,
            user_id=user_id or uuid.uuid4(),
            comentario=comment,
        )
        self.db.add(h)
        await self.db.flush()

    async def _get_status_by_id(self, status_id: uuid.UUID) -> Optional[WfStatus]:
        q = select(WfStatus).where(WfStatus.id == status_id)
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def approve(
        self,
        approval_id: uuid.UUID,
        user_id: uuid.UUID,
        approved: bool,
        comment: str = "",
    ) -> bool:
        """Aprueba o rechaza una aprobacion pendiente."""
        q = select(WfPendingApproval).where(WfPendingApproval.id == approval_id)
        r = await self.db.execute(q)
        pa = r.scalar_one_or_none()
        if not pa:
            return False

        pa.aprobado_por = user_id
        pa.estado = 'APPROVED' if approved else 'REJECTED'
        pa.comentario = comment
        pa.resolved_at = datetime.now()
        await self.db.flush()

        if approved:
            transition = await self._get_transition_by_id(pa.transition_id)
            if transition:
                current_status = await self._get_status_by_id(transition.from_status_id)
                target_status = await self._get_status_by_id(transition.to_status_id)
                if current_status and target_status:
                    await self._record_history(
                        pa.documento_tipo_id, pa.documento_id,
                        current_status.id, target_status.id,
                        transition.id, user_id, f"Approved: {comment}",
                    )
        return True

    async def _get_transition_by_id(self, transition_id: uuid.UUID) -> Optional[WfTransition]:
        q = select(WfTransition).where(WfTransition.id == transition_id)
        r = await self.db.execute(q)
        return r.scalar_one_or_none()
