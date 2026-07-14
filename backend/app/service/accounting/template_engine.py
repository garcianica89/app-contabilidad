"""
Template engine for configurable journal entry generation.

Flow:
1. Resolve journal type by code (or from document subtype)
2. Find active templates ordered by priority
3. Evaluate template condition_expr
4. For each line: resolve account, evaluate amount, description, condition
5. Validate double entry
6. Return JournalEntryLineDTO list
"""
import uuid
from decimal import Decimal
from typing import Optional

from app.repository.accounting.repositories import (
    AccountRepository,
    JournalTypeRepository,
    ModuleAccountingConfigRepository,
)
from app.service.accounting.expression_evaluator import ExpressionEvaluator


class AccountResolutionError(Exception):
    pass


class TemplateMatchError(Exception):
    pass


class DoubleEntryError(Exception):
    pass


class JournalEntryLineDTO:
    def __init__(
        self,
        account_id: uuid.UUID,
        nature: str,
        amount: Decimal,
        description: str = "",
        cost_center_id: Optional[uuid.UUID] = None,
    ):
        self.account_id = account_id
        self.nature = nature
        self.amount = amount
        self.description = description
        self.cost_center_id = cost_center_id


class TemplateEngine:
    ACCOUNT_SOURCES = {'FIXED', 'PARAM', 'CONTEXT', 'SUBTYPE'}
    NATURES = {'DEBIT', 'CREDIT'}

    def __init__(
        self,
        account_repo: AccountRepository,
        journal_type_repo: JournalTypeRepository,
        config_repo: ModuleAccountingConfigRepository,
        evaluator: Optional[ExpressionEvaluator] = None,
    ):
        self.account_repo = account_repo
        self.journal_type_repo = journal_type_repo
        self.config_repo = config_repo
        self.evaluator = evaluator or ExpressionEvaluator()

    async def generate(
        self,
        journal_type_code: str,
        context: dict,
        company_id: uuid.UUID,
        module: str = "",
        document_subtype=None,
    ) -> list[JournalEntryLineDTO]:
        journal_type = await self.journal_type_repo.get_by_code(company_id, journal_type_code)
        if not journal_type:
            raise TemplateMatchError(f"Journal type '{journal_type_code}' not found or inactive")

        templates = await self.journal_type_repo.get_active_templates(journal_type.id)
        if not templates:
            raise TemplateMatchError(f"No active templates for journal type '{journal_type_code}'")

        subtype = document_subtype

        errors = []
        for template in templates:
            try:
                lines = await self._evaluate_template(template, context, company_id, module, subtype)
                if lines:
                    self._validate_double_entry(lines)
                    return lines
            except Exception as e:
                errors.append(f"Template '{template.name}': {e}")
                continue

        raise TemplateMatchError(
            f"No template could be evaluated for journal type '{journal_type_code}': {'; '.join(errors)}"
        )

    async def _evaluate_template(
        self,
        template,
        context: dict,
        company_id: uuid.UUID,
        module: str,
        subtype,
    ) -> list[JournalEntryLineDTO]:
        if template.condition_expr:
            condition = self.evaluator.evaluate_condition(template.condition_expr, context)
            if not condition:
                raise TemplateMatchError(f"Condition '{template.condition_expr}' not met")

        lines_to_add = []
        template_lines = await self.journal_type_repo.get_template_lines(template.id)

        for tpl_line in template_lines:
            if tpl_line.condition_expr:
                line_condition = self.evaluator.evaluate_condition(tpl_line.condition_expr, context)
                if not line_condition:
                    if tpl_line.is_mandatory:
                        raise TemplateMatchError(
                            f"Mandatory line {tpl_line.line_order} condition not met"
                        )
                    continue

            account_id = await self._resolve_account(tpl_line, context, company_id, module, subtype)
            amount = self.evaluator.evaluate(tpl_line.amount_expression, context)
            description = self.evaluator.evaluate_description(tpl_line.description_expression or "", context)
            cost_center_id = await self._resolve_cost_center(tpl_line, context, subtype)

            if amount == Decimal('0') and not tpl_line.is_mandatory:
                continue

            nature = tpl_line.nature
            if tpl_line.invert_in_banking:
                doc_type = context.get('document_type', '').upper()
                if doc_type == 'MOV_BANCO':
                    tipo = context.get('tipo', 'EGRESO')
                    if tipo.upper() == 'INGRESO':
                        nature = 'CREDIT' if nature == 'DEBIT' else 'DEBIT'
                else:
                    nature = 'CREDIT' if nature == 'DEBIT' else 'DEBIT'

            lines_to_add.append(JournalEntryLineDTO(
                account_id=account_id,
                nature=nature,
                amount=amount,
                description=description,
                cost_center_id=cost_center_id,
            ))

        return lines_to_add

    async def _resolve_account(self, line, context: dict, company_id: uuid.UUID, module: str, subtype) -> uuid.UUID:
        source = line.account_source

        if source == 'SUBTYPE' and subtype:
            account_id = self._get_subtype_account(subtype, context)
            if account_id:
                return account_id

        if source == 'CONTEXT' and line.account_context_var:
            var_value = context.get(line.account_context_var)
            if var_value:
                if isinstance(var_value, uuid.UUID):
                    return var_value
                if isinstance(var_value, str):
                    try:
                        return uuid.UUID(var_value)
                    except ValueError:
                        account = await self.account_repo.get_by_code(company_id, var_value)
                        if account:
                            return account.id

        if source == 'PARAM' and line.account_param_concept:
            account_id = await self.config_repo.get_account_by_concept(
                company_id, module, line.account_param_concept
            )
            if account_id:
                return account_id

        if source == 'FIXED' and line.account_code:
            account = await self.account_repo.get_by_code(company_id, line.account_code)
            if account:
                return account.id

        raise AccountResolutionError(
            f"Cannot resolve account for line {line.line_order}: "
            f"source={source}, code={line.account_code}, "
            f"param={line.account_param_concept}, var={line.account_context_var}"
        )

    def _get_subtype_account(self, subtype, context: dict) -> Optional[uuid.UUID]:
        doc_type = context.get('document_type', '').upper()

        if doc_type in ('FAC', 'FACTURA', 'FAC_CONTADO', 'FAC_CREDITO'):
            return getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('NCR', 'NOTA_CREDITO'):
            return getattr(subtype, 'cuenta_descuentos_id', None) or getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('NDB', 'NOTA_DEBITO'):
            return getattr(subtype, 'cuenta_intereses_id', None) or getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('DEBITO', 'DEBIT'):
            # In banking: DEBITO (bank doc) = CREDIT (accounting), use contrapartida
            return getattr(subtype, 'cuenta_contrapartida_id', None) or getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('CREDITO', 'CREDIT'):
            # In banking: CREDITO (bank doc) = DEBIT (accounting), use principal
            return getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('CHEQUE',):
            return getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('MOV_BANCO',):
            return getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('OC', 'COMPRA'):
            return getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('SALIDA_INV',):
            return getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('PAGO',):
            return getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('RETENCION',):
            return getattr(subtype, 'cuenta_retencion_id', None)
        if doc_type in ('NOMINA', 'PAGO_NOMINA'):
            return getattr(subtype, 'cuenta_principal_id', None)
        if doc_type in ('DEPRECIACION',):
            return getattr(subtype, 'cuenta_principal_id', None)
        return getattr(subtype, 'cuenta_principal_id', None)

    async def _resolve_cost_center(self, line, context: dict, subtype) -> Optional[uuid.UUID]:
        source = line.cost_center_source
        if source == 'FIXED':
            return line.cost_center_id
        if source == 'CONTEXT' and line.cost_center_context_var:
            return context.get(line.cost_center_context_var)
        if source == 'SUBTYPE' and subtype:
            return getattr(subtype, 'cost_center_default_id', None)
        if source == 'FROM_TRANSACTION':
            return context.get('cost_center_id')
        return None

    def _validate_double_entry(self, lines: list[JournalEntryLineDTO]):
        total_debit = sum(l.amount for l in lines if l.nature == 'DEBIT')
        total_credit = sum(l.amount for l in lines if l.nature == 'CREDIT')
        if total_debit != total_credit:
            raise DoubleEntryError(
                f"Double entry does not balance: Debit={total_debit} vs Credit={total_credit}"
            )
        if total_debit == 0:
            raise DoubleEntryError("Journal entry cannot have zero amounts")
