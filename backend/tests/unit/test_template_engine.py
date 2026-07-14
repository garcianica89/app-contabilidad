import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.service.accounting.template_engine import (
    TemplateEngine,
    JournalEntryLineDTO,
    TemplateMatchError,
    DoubleEntryError,
    AccountResolutionError,
)
from app.domain.accounting.models import (
    JournalType,
    JournalTemplate,
    JournalTemplateLine,
    ModuleAccountingConfig,
    Account,
)


@pytest.fixture
def company_id():
    return uuid.uuid4()


@pytest.fixture
def account_id_1():
    return uuid.uuid4()


@pytest.fixture
def account_id_2():
    return uuid.uuid4()


@pytest.fixture
def account_id_3():
    return uuid.uuid4()


@pytest.fixture
def account_id_4():
    return uuid.uuid4()


@pytest.fixture
def journal_type_id():
    return uuid.uuid4()


@pytest.fixture
def template_id():
    return uuid.uuid4()


@pytest.fixture
def mock_account_repo(company_id, account_id_1, account_id_2, account_id_3, account_id_4):
    repo = AsyncMock()
    account1 = MagicMock(spec=Account, id=account_id_1, code="1-1-1-1-01", name="Caja")
    account2 = MagicMock(spec=Account, id=account_id_2, code="4-1-1-1-01", name="Ventas")
    account3 = MagicMock(spec=Account, id=account_id_3, code="2-1-2-1-00-00-00-0000", name="IVA por Pagar")
    account4 = MagicMock(spec=Account, id=account_id_4, code="5-1-1-1-01-00-00-0000", name="Costo de Ventas")
    repo.get_by_code.side_effect = lambda cid, code: {
        "1-1-1-1-01": account1,
        "4-1-1-1-01": account2,
        "2-1-2-1-00-00-00-0000": account3,
        "5-1-1-1-01-00-00-0000": account4,
    }.get(code, None)
    return repo


@pytest.fixture
def mock_journal_type_repo(company_id, journal_type_id, template_id):
    repo = AsyncMock()

    jt = MagicMock(
        spec=JournalType,
        id=journal_type_id,
        company_id=company_id,
        code="VENTA_CONT",
        nature="AUTOMATIC",
    )
    repo.get_by_code.return_value = jt

    tmpl = MagicMock(
        spec=JournalTemplate,
        id=template_id,
        journal_type_id=journal_type_id,
        company_id=company_id,
        name="Venta Contado Default",
        priority=0,
        condition_expr="{{tipo_pago}} == 'CONTADO'",
        is_active=True,
    )
    repo.get_active_templates.return_value = [tmpl]

    line1 = MagicMock(
        spec=JournalTemplateLine,
        id=uuid.uuid4(),
        template_id=template_id,
        line_order=1,
        nature="DEBIT",
        account_source="FIXED",
        account_code="1-1-1-1-01",
        account_param_concept=None,
        account_context_var=None,
        amount_expression="{{total}}",
        description_expression="Venta contado {{number}}",
        cost_center_source="SUBTYPE",
        cost_center_id=None,
        cost_center_context_var=None,
        condition_expr=None,
        is_mandatory=True,
        invert_in_banking=False,
    )
    line2 = MagicMock(
        spec=JournalTemplateLine,
        id=uuid.uuid4(),
        template_id=template_id,
        line_order=2,
        nature="CREDIT",
        account_source="FIXED",
        account_code="4-1-1-1-01",
        account_param_concept=None,
        account_context_var=None,
        amount_expression="{{subtotal - descuento}}",
        description_expression="Venta {{number}}",
        cost_center_source="SUBTYPE",
        cost_center_id=None,
        cost_center_context_var=None,
        condition_expr="{{subtotal - descuento}} > 0",
        is_mandatory=True,
        invert_in_banking=False,
    )
    line3 = MagicMock(
        spec=JournalTemplateLine,
        id=uuid.uuid4(),
        template_id=template_id,
        line_order=3,
        nature="CREDIT",
        account_source="FIXED",
        account_code="2-1-2-1-00-00-00-0000",
        account_param_concept=None,
        account_context_var=None,
        amount_expression="{{iva}}",
        description_expression="IVA {{number}}",
        cost_center_source="SUBTYPE",
        cost_center_id=None,
        cost_center_context_var=None,
        condition_expr="{{iva}} > 0",
        is_mandatory=False,
        invert_in_banking=False,
    )
    repo.get_template_lines.return_value = [line1, line2, line3]

    return repo


@pytest.fixture
def mock_config_repo(company_id):
    return AsyncMock()


@pytest.fixture
def engine(mock_account_repo, mock_journal_type_repo, mock_config_repo):
    return TemplateEngine(
        account_repo=mock_account_repo,
        journal_type_repo=mock_journal_type_repo,
        config_repo=mock_config_repo,
    )


class TestTemplateEngine:

    @pytest.mark.asyncio
    async def test_generate_success(self, engine, company_id):
        context = {
            "total": 1092.50,
            "subtotal": 1000.00,
            "descuento": 50.00,
            "iva": 142.50,
            "number": "F001-000123",
            "tipo_pago": "CONTADO",
        }
        lines = await engine.generate(
            journal_type_code="VENTA_CONT",
            context=context,
            company_id=company_id,
            module="sales",
        )
        assert len(lines) == 3
        assert lines[0].nature == "DEBIT"
        assert lines[0].amount == Decimal("1092.50")
        assert lines[0].description == "Venta contado F001-000123"
        assert lines[1].nature == "CREDIT"
        assert lines[1].amount == Decimal("950.00")
        assert lines[1].description == "Venta F001-000123"
        assert lines[2].nature == "CREDIT"
        assert lines[2].amount == Decimal("142.50")
        assert lines[2].description == "IVA F001-000123"

    @pytest.mark.asyncio
    async def test_double_entry_validation(self, engine, company_id):
        context = {
            "total": 1000.00,
            "subtotal": 1000.00,
            "descuento": 0,
            "iva": 0,
            "number": "F001-000124",
            "tipo_pago": "CONTADO",
        }
        lines = await engine.generate(
            journal_type_code="VENTA_CONT",
            context=context,
            company_id=company_id,
            module="sales",
        )
        total_debit = sum(l.amount for l in lines if l.nature == "DEBIT")
        total_credit = sum(l.amount for l in lines if l.nature == "CREDIT")
        assert total_debit == total_credit
        assert total_debit == Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_journal_type_not_found(self, engine, company_id):
        engine.journal_type_repo.get_by_code.return_value = None
        with pytest.raises(TemplateMatchError, match="not found"):
            await engine.generate(
                journal_type_code="INEXISTENTE",
                context={},
                company_id=company_id,
                module="sales",
            )

    @pytest.mark.asyncio
    async def test_no_active_templates(self, engine, company_id):
        engine.journal_type_repo.get_active_templates.return_value = []
        with pytest.raises(TemplateMatchError, match="No active templates"):
            await engine.generate(
                journal_type_code="VENTA_CONT",
                context={},
                company_id=company_id,
                module="sales",
            )

    @pytest.mark.asyncio
    async def test_condition_not_met_skips_template(self, engine, company_id):
        context = {
            "total": 1000.00,
            "subtotal": 1000.00,
            "descuento": 0,
            "iva": 0,
            "number": "F001-000125",
            "tipo_pago": "CREDITO",
        }
        with pytest.raises(TemplateMatchError):
            await engine.generate(
                journal_type_code="VENTA_CONT",
                context=context,
                company_id=company_id,
                module="sales",
            )

    @pytest.mark.asyncio
    async def test_account_not_resolved(self, engine, company_id):
        engine.journal_type_repo.get_template_lines.return_value = [
            MagicMock(
                spec=JournalTemplateLine,
                id=uuid.uuid4(),
                template_id=uuid.uuid4(),
                line_order=1,
                nature="DEBIT",
                account_source="FIXED",
                account_code="NONEXISTENT",
                account_param_concept=None,
                account_context_var=None,
                amount_expression="100",
                description_expression="Test",
                cost_center_source="SUBTYPE",
                cost_center_id=None,
                cost_center_context_var=None,
                condition_expr=None,
                is_mandatory=True,
            ),
            MagicMock(
                spec=JournalTemplateLine,
                id=uuid.uuid4(),
                template_id=uuid.uuid4(),
                line_order=2,
                nature="CREDIT",
                account_source="FIXED",
                account_code="4-1-1-1-01",
                account_param_concept=None,
                account_context_var=None,
                amount_expression="100",
                description_expression="Test",
                cost_center_source="SUBTYPE",
                cost_center_id=None,
                cost_center_context_var=None,
                condition_expr=None,
                is_mandatory=True,
            ),
        ]
        engine.account_repo.get_by_code.side_effect = lambda cid, code: None
        with pytest.raises(TemplateMatchError, match="Cannot resolve account"):
            await engine.generate(
                journal_type_code="VENTA_CONT",
                context={"tipo_pago": "CONTADO"},
                company_id=company_id,
                module="sales",
            )
