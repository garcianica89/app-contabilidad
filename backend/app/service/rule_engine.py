"""
Rule Engine — Motor de Reglas de Negocio.

Evalua condiciones configurables y ejecuta acciones.
Utilizado por: DocumentEngine, WorkflowEngine, TemplateEngine.

Ejemplos de reglas:
  - Si cliente.saldo > cliente.limite_credito → bloquear venta
  - Si monto > 10000 → requiere aprobacion
  - Si proveedor.tipo == 'EXTRANJERO' → retencion_ir = 15%
"""
import uuid
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.accounting.models import AccountingRule, AccountingRuleLog
from app.service.accounting.expression_evaluator import ExpressionEvaluator


class RuleEngine:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evaluator = ExpressionEvaluator()

    async def evaluate(
        self,
        module: str,
        document_type: str,
        action: str,
        context: dict,
        company_id: uuid.UUID,
    ) -> dict[str, list[str]]:
        """
        Evalua todas las reglas activas para un modulo/documento.

        Returns:
            { "errors": [], "warnings": [], "blocks": [], "approvals": [] }
        """
        rules = await self._get_active_rules(module, company_id)
        result = {
            'errors': [],
            'warnings': [],
            'blocks': [],
            'approvals': [],
        }

        if not rules:
            return result

        enriched = self._enrich_context(context)

        for rule in rules:
            try:
                rule_passed = self.evaluator.evaluate_condition(
                    rule.condition_expression, enriched
                )
                passed = rule_passed
            except Exception:
                passed = False

            if passed:
                action_result = self._execute_action(rule, enriched)
                if rule.action_type == 'BLOCK':
                    result['blocks'].append(
                        rule.error_message or f"Rule '{rule.code}' blocked"
                    )
                elif rule.action_type == 'WARN':
                    result['warnings'].append(
                        rule.error_message or f"Rule '{rule.code}' warning"
                    )
                elif rule.action_type == 'APPROVAL_REQUIRED':
                    result['approvals'].append(rule.code)

                await self._log_execution(rule, document_type, str(context), passed)

        return result

    async def evaluate_one(
        self,
        rule_id: uuid.UUID,
        context: dict,
        document_type: str = "",
    ) -> bool:
        """Evalua una regla especifica."""
        q = select(AccountingRule).where(
            AccountingRule.id == rule_id,
            AccountingRule.is_active == True,
        )
        r = await self.db.execute(q)
        rule = r.scalar_one_or_none()
        if not rule:
            return True

        try:
            enriched = self._enrich_context(context)
            passed = self.evaluator.evaluate_condition(rule.condition_expression, enriched)
            await self._log_execution(rule, document_type, str(context), passed)
            return passed
        except Exception:
            await self._log_execution(rule, document_type, str(context), False)
            return True

    async def _get_active_rules(self, module: str, company_id: uuid.UUID) -> list[AccountingRule]:
        q = select(AccountingRule).where(
            AccountingRule.company_id == company_id,
            AccountingRule.is_active == True,
            and_(
                (AccountingRule.module == module) | (AccountingRule.module == 'all')
            )
        ).order_by(AccountingRule.priority.asc())
        r = await self.db.execute(q)
        return list(r.scalars().all())

    def _enrich_context(self, context: dict) -> dict:
        """Enriquece contexto con valores calculados."""
        return context

    def _execute_action(self, rule, context: dict) -> Any:
        """Ejecuta la accion de una regla.

        Actions supported: BLOCK, WARN, APPROVAL_REQUIRED, SET_FIELD, UPDATE_DOCUMENT.
        Estas acciones son decorativas por ahora; la logica de bloqueo/aprobacion
        se maneja en el llamador (DocumentEngine/WorkflowEngine).
        """
        import logging
        logger = logging.getLogger(__name__)
        if rule.action_type in ('BLOCK', 'WARN', 'APPROVAL_REQUIRED'):
            logger.info("Rule %s (%s) triggered on context", rule.code, rule.action_type)
        elif rule.action_type == 'SET_FIELD' and rule.action_config:
            field = rule.action_config.get('field')
            value = rule.action_config.get('value')
            if field:
                context[field] = value
        return None

    async def _log_execution(
        self, rule, document_type: str, context_summary: str, passed: bool,
    ):
        log = AccountingRuleLog(
            rule_id=rule.id,
            document_type=document_type,
            context_summary=context_summary,
            result='PASS' if passed else 'FAIL',
            execution_time_ms=0,
        )
        self.db.add(log)
        await self.db.flush()
