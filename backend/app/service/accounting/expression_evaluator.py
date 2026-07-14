"""
Safe expression evaluator for accounting template expressions.

Supports:
  {{variable}}                     -> value from context
  {{subtotal - descuento}}         -> arithmetic (+, -, *, /)
  {{total * 0.15}}                 -> multiplication with constant
  {{sum(array, 'field')}}          -> sum of field across array
  {{if(cond, then_val, else_val)}} -> conditional

No eval() used. Uses shunting-yard with Decimal precision.
"""
from decimal import Decimal, InvalidOperation
from typing import Any
import re


class ExpressionError(Exception):
    pass


class ExpressionEvaluator:
    VARIABLE_RE = re.compile(r'\{\{(.+?)\}\}')
    SIMPLE_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_]\w*$')
    FUNC_CALL_RE = re.compile(r'^(sum|if)\(')

    OPERATORS = {
        '+': (1, lambda a, b: a + b),
        '-': (1, lambda a, b: a - b),
        '*': (2, lambda a, b: a * b),
        '/': (2, lambda a, b: a / b),
    }

    COMPARISON_OPS = {
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '>': lambda a, b: a > b,
        '<': lambda a, b: a < b,
        '>=': lambda a, b: a >= b,
        '<=': lambda a, b: a <= b,
    }

    def evaluate(self, expression: str, context: dict) -> Decimal:
        if not expression or not expression.strip():
            return Decimal('0')
        result = self._evaluate_expression(expression, context)
        if isinstance(result, bool):
            return Decimal('1') if result else Decimal('0')
        return self._to_decimal(result)

    def evaluate_condition(self, expression: str, context: dict) -> bool:
        if not expression or not expression.strip():
            return True
        result = self._evaluate_expression(expression, context)
        if isinstance(result, bool):
            return result
        if isinstance(result, Decimal):
            return result != Decimal('0')
        return bool(result)

    def evaluate_description(self, expression: str, context: dict) -> str:
        if not expression:
            return ""
        def replace_var(match):
            inner = match.group(1).strip()
            if self.FUNC_CALL_RE.match(inner):
                return match.group(0)
            val = self._resolve_name(inner, context)
            if isinstance(val, Decimal):
                return str(round(val, 2))
            return str(val) if val is not None else match.group(0)
        return self.VARIABLE_RE.sub(replace_var, expression)

    def _evaluate_expression(self, expression: str, context: dict) -> Any:
        def replace_var(match):
            inner = match.group(1).strip()
            if self.FUNC_CALL_RE.match(inner):
                if inner.startswith('sum('):
                    args = inner[4:-1]
                    return f"__SUM__{args}__"
                if inner.startswith('if('):
                    args = inner[3:-1]
                    return f"__IF__{args}__"
            tokens = self._tokenize_expression(inner)
            evaluated_tokens = []
            for tok in tokens:
                if self.SIMPLE_IDENTIFIER_RE.match(tok) and tok not in self.OPERATORS and tok not in ('(', ')', ',') and tok not in self.COMPARISON_OPS:
                    val = self._resolve_name(tok, context)
                    if val is None:
                        evaluated_tokens.append('0')
                    elif isinstance(val, Decimal):
                        evaluated_tokens.append(str(val))
                    elif isinstance(val, str):
                        evaluated_tokens.append(f"'{val}'")
                    else:
                        evaluated_tokens.append(str(val))
                else:
                    evaluated_tokens.append(tok)
            return ' '.join(evaluated_tokens)

        resolved = self.VARIABLE_RE.sub(replace_var, expression)

        if '__SUM__' in resolved:
            return self._eval_sum(resolved, context)
        if '__IF__' in resolved:
            return self._eval_if(resolved, context)

        return self._evaluate_tokens(resolved)

    def _resolve_name(self, name: str, context: dict) -> Any:
        parts = name.split('.')
        val = context
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                try:
                    val = getattr(val, part, None)
                except Exception:
                    return None
            if val is None:
                return None
        return val

    def _tokenize_expression(self, expr: str) -> list[str]:
        tokens = []
        i = 0
        while i < len(expr):
            c = expr[i]
            if c.isspace():
                i += 1
                continue
            if c.isdigit() or (c == '.' and i + 1 < len(expr) and expr[i + 1].isdigit()):
                j = i
                while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                    j += 1
                tokens.append(expr[i:j])
                i = j
                continue
            if c.isalpha() or c == '_':
                j = i
                while j < len(expr) and (expr[j].isalnum() or expr[j] == '_'):
                    j += 1
                tokens.append(expr[i:j])
                i = j
                continue
            if c in ("'", '"'):
                quote = c
                j = i + 1
                while j < len(expr) and expr[j] != quote:
                    j += 1
                if j < len(expr):
                    tokens.append(expr[i + 1:j])
                    i = j + 1
                    continue
                i += 1
                continue
            if expr[i:i+2] in ('==', '!=', '>=', '<='):
                tokens.append(expr[i:i+2])
                i += 2
                continue
            if c in '()+-*/,><':
                tokens.append(c)
                i += 1
                continue
            i += 1
        return tokens

    def _tokenize_full(self, expr: str) -> list[str]:
        tokens = []
        i = 0
        while i < len(expr):
            c = expr[i]
            if c.isspace():
                i += 1
                continue
            if c.isdigit() or (c == '.' and i + 1 < len(expr) and expr[i + 1].isdigit()):
                j = i
                while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                    j += 1
                tokens.append(expr[i:j])
                i = j
                continue
            if c.isalpha() or c == '_':
                j = i
                while j < len(expr) and (expr[j].isalnum() or expr[j] == '_'):
                    j += 1
                token = expr[i:j]
                if token.startswith('__SUM__') or token.startswith('__IF__'):
                    depth = 0
                    while j < len(expr):
                        if expr[j] == '(':
                            depth += 1
                        elif expr[j] == ')':
                            depth -= 1
                            if depth < 0:
                                j += 1
                                break
                        j += 1
                    tokens.append(expr[i:j])
                    i = j
                    continue
                tokens.append(token)
                i = j
                continue
            if c in ("'", '"'):
                quote = c
                j = i + 1
                while j < len(expr) and expr[j] != quote:
                    j += 1
                if j < len(expr):
                    tokens.append(expr[i:j + 1])
                    i = j + 1
                    continue
                i += 1
                continue
            if expr[i:i+2] in ('==', '!=', '>=', '<='):
                tokens.append(expr[i:i+2])
                i += 2
                continue
            if c in '()+-*/,><':
                tokens.append(c)
                i += 1
                continue
            i += 1
        return tokens

    def _evaluate_tokens(self, expr: str) -> Any:
        tokens = self._tokenize_full(expr)
        if not tokens:
            return Decimal('0')
        if len(tokens) == 1:
            return self._parse_literal(tokens[0])
        return self._shunting_yard(tokens)

    def _parse_literal(self, token: str) -> Any:
        if token.startswith("'") and token.endswith("'"):
            return token[1:-1]
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]
        try:
            return Decimal(token)
        except (InvalidOperation, ValueError):
            return token

    def _shunting_yard(self, tokens: list[str]) -> Any:
        output = []
        ops = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.startswith('__SUM__') or token.startswith('__IF__'):
                output.append(token)
            elif self._is_number(token):
                output.append(Decimal(token))
            elif token == '(':
                ops.append(token)
            elif token == ')':
                while ops and ops[-1] != '(':
                    self._apply_op(ops.pop(), output)
                ops.pop()
            elif token == ',':
                while ops and ops[-1] != '(':
                    self._apply_op(ops.pop(), output)
            elif token in self.OPERATORS:
                while (ops and ops[-1] in self.OPERATORS
                       and self.OPERATORS[ops[-1]][0] >= self.OPERATORS[token][0]):
                    self._apply_op(ops.pop(), output)
                ops.append(token)
            elif token in self.COMPARISON_OPS:
                while (ops and ops[-1] in self.OPERATORS
                       and self.OPERATORS[ops[-1]][0] >= 1):
                    self._apply_op(ops.pop(), output)
                ops.append(token)
            else:
                val = self._parse_literal(token)
                output.append(val)
            i += 1
        while ops:
            self._apply_op(ops.pop(), output)
        return output[0] if output else Decimal('0')

    def _apply_op(self, op: str, output: list):
        right = output.pop()
        left = output.pop()
        if isinstance(left, str) and (left.startswith('__SUM__') or left.startswith('__IF__')):
            output.append(left)
            output.append(right)
            return
        if op in self.OPERATORS:
            left_d = self._to_decimal(left)
            right_d = self._to_decimal(right)
            output.append(self.OPERATORS[op][1](left_d, right_d))
        elif op in self.COMPARISON_OPS:
            output.append(self.COMPARISON_OPS[op](left, right))

    def _is_number(self, token: str) -> bool:
        try:
            Decimal(token)
            return True
        except (InvalidOperation, ValueError):
            return False

    def _to_decimal(self, val: Any) -> Decimal:
        if isinstance(val, Decimal):
            return val
        if isinstance(val, bool):
            return Decimal('1') if val else Decimal('0')
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        if isinstance(val, str):
            try:
                return Decimal(val)
            except (InvalidOperation, ValueError):
                return Decimal('0')
        return Decimal('0')

    def _eval_sum(self, expr: str, context: dict) -> Decimal:
        m = re.search(r'__SUM__(.+?)__', expr)
        if not m:
            return Decimal('0')
        args = m.group(1)
        parts = [p.strip() for p in args.split(',', 1)]
        if len(parts) != 2:
            return Decimal('0')
        array_name = parts[0].strip()
        field_name = parts[1].strip().strip("'\"")
        array = context.get(array_name, [])
        total = Decimal('0')
        for item in array:
            if isinstance(item, dict):
                val = item.get(field_name, 0)
            else:
                val = 0
            total += Decimal(str(val))
        return total

    def _eval_if(self, expr: str, context: dict) -> Decimal:
        m = re.search(r'__IF__(.+?)__', expr)
        if not m:
            return Decimal('0')
        args = m.group(1)
        parts = self._split_args(args)
        if len(parts) != 3:
            return Decimal('0')
        cond_val = self._evaluate_tokens(parts[0])
        if isinstance(cond_val, bool):
            condition = cond_val
        elif isinstance(cond_val, Decimal):
            condition = cond_val != Decimal('0')
        else:
            condition = bool(cond_val)
        if condition:
            return self._to_decimal(self._evaluate_tokens(parts[1]))
        return self._to_decimal(self._evaluate_tokens(parts[2]))

    def _split_args(self, args: str) -> list[str]:
        depth = 0
        current = []
        parts = []
        for c in args:
            if c == '(':
                depth += 1
                current.append(c)
            elif c == ')':
                depth -= 1
                current.append(c)
            elif c == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(c)
        parts.append(''.join(current))
        return parts
