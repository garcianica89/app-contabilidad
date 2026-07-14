from decimal import Decimal
import pytest
from app.service.accounting.expression_evaluator import ExpressionEvaluator


@pytest.fixture
def evaluator():
    return ExpressionEvaluator()


@pytest.fixture
def context():
    return {
        "subtotal": Decimal("1000.00"),
        "descuento": Decimal("50.00"),
        "iva": Decimal("142.50"),
        "total": Decimal("1092.50"),
        "tipo_pago": "CONTADO",
        "number": "F001-000123",
        "costos": [
            {"cuenta_param": "COSTO_VENTAS", "monto": 300.00},
            {"cuenta_param": "INVENTARIO_MERCANCIAS", "monto": 300.00},
        ],
    }


class TestExpressionEvaluator:

    def test_simple_variable(self, evaluator, context):
        result = evaluator.evaluate("{{total}}", context)
        assert result == Decimal("1092.50")

    def test_subtraction(self, evaluator, context):
        result = evaluator.evaluate("{{subtotal - descuento}}", context)
        assert result == Decimal("950.00")

    def test_multiplication(self, evaluator, context):
        result = evaluator.evaluate("{{total * 0.15}}", context)
        assert result == Decimal("163.875")

    def test_division(self, evaluator, context):
        result = evaluator.evaluate("{{total / 1.15}}", context)
        assert round(result, 2) == Decimal("950.00")

    def test_addition(self, evaluator, context):
        result = evaluator.evaluate("{{subtotal + iva}}", context)
        assert result == Decimal("1142.50")

    def test_zero_expression(self, evaluator, context):
        result = evaluator.evaluate("{{total - total}}", context)
        assert result == Decimal("0")

    def test_sum_function(self, evaluator, context):
        result = evaluator.evaluate("{{sum(costos, 'monto')}}", context)
        assert result == Decimal("600.00")

    def test_condition_true(self, evaluator, context):
        assert evaluator.evaluate_condition("{{iva}} > 0", context) is True

    def test_condition_false(self, evaluator, context):
        assert evaluator.evaluate_condition("{{iva}} == 0", context) is False

    def test_condition_equals_string(self, evaluator, context):
        assert evaluator.evaluate_condition("{{tipo_pago}} == 'CONTADO'", context) is True

    def test_condition_not_equals_string(self, evaluator, context):
        assert evaluator.evaluate_condition("{{tipo_pago}} == 'CREDITO'", context) is False

    def test_condition_greater_than(self, evaluator, context):
        assert evaluator.evaluate_condition("{{total}} >= 1000", context) is True
        assert evaluator.evaluate_condition("{{total}} < 1000", context) is False

    def test_empty_expression(self, evaluator, context):
        assert evaluator.evaluate("", context) == Decimal("0")
        assert evaluator.evaluate("  ", context) == Decimal("0")

    def test_expression_without_variables(self, evaluator, context):
        result = evaluator.evaluate("100 + 50", context)
        assert result == Decimal("150")

    def test_description_evaluation(self, evaluator, context):
        desc = evaluator.evaluate_description("Venta {{number}}", context)
        assert desc == "Venta F001-000123"

    def test_description_with_numbers(self, evaluator, context):
        desc = evaluator.evaluate_description("Total: {{total}}", context)
        assert desc == "Total: 1092.50"

    def test_blank_description(self, evaluator, context):
        assert evaluator.evaluate_description("", context) == ""
        assert evaluator.evaluate_description(None, context) == ""

    def test_complex_arithmetic(self, evaluator, context):
        result = evaluator.evaluate("{{subtotal - descuento + iva}}", context)
        assert result == Decimal("1092.50")

    def test_variable_not_found_returns_zero(self, evaluator, context):
        result = evaluator.evaluate("{{inexistente}}", context)
        assert result == Decimal("0")

    def test_condition_empty(self, evaluator, context):
        assert evaluator.evaluate_condition("", context) is True
        assert evaluator.evaluate_condition(None, context) is True
