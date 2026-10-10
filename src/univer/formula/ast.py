"""Formula AST nodes — mirrors the TypeScript AST node hierarchy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class ASTNode(ABC):
    @abstractmethod
    def evaluate(self, ws: Any, context: dict[str, Any] | None = None) -> Any: ...


@dataclass
class ValueNode(ASTNode):
    value: Any

    def evaluate(self, ws: Any, context: dict[str, Any] | None = None) -> Any:
        return self.value


@dataclass
class ReferenceNode(ASTNode):
    """A cell or range reference, e.g. A1, $A$1, A1:B3."""

    ref: str

    def evaluate(self, ws: Any, context: dict[str, Any] | None = None) -> Any:
        from univer.formula.parser import parse_ref

        parsed = parse_ref(self.ref)
        if parsed is None:
            return None
        if len(parsed) == 4:
            start_row, start_col, end_row, end_col = parsed
            return ws.get_range(start_row, start_col, end_row, end_col)
        row, col = parsed
        return ws.get_cell(row, col)


@dataclass
class OperatorNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode | None = None

    # Arithmetic operators: empty cells (None) are treated as 0.
    _ARITH: ClassVar[set[str]] = {"+", "-", "*", "/", "**", "%"}

    _BINOPS: ClassVar[dict[str, Any]] = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a / b if b != 0 else None,
        "**": lambda a, b: a**b,
        "%": lambda a, b: a % b,
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "&": lambda a, b: str(a) + str(b),
    }

    @staticmethod
    def _to_number(v: Any) -> float:
        """Coerce a value to a number (Excel semantics): None -> 0.0."""
        if v is None:
            return 0.0
        if isinstance(v, bool):
            return float(v)
        if isinstance(v, int | float):
            return v
        return float(v)  # may raise ValueError for non-numeric text

    @staticmethod
    def _to_text(v: Any) -> str:
        """Coerce a value to text for concatenation: None -> ''."""
        return "" if v is None else str(v)

    @staticmethod
    def _coerce_cmp(a: Any, b: Any) -> tuple[Any, Any]:
        """For comparisons, treat an empty cell as 0 when the other side is
        numeric, or as '' when the other side is text."""
        if a is None and b is None:
            return 0, 0
        if a is None:
            return (0.0, "")[isinstance(b, str)], b
        if b is None:
            return a, (0.0, "")[isinstance(a, str)]
        return a, b

    def evaluate(self, ws: Any, context: dict[str, Any] | None = None) -> Any:
        if self.right is not None:
            fn = self._BINOPS.get(self.op)
            if fn is None:
                return None
            left_val = self.left.evaluate(ws, context)
            right_val = self.right.evaluate(ws, context)
            try:
                if self.op in self._ARITH:
                    return fn(self._to_number(left_val), self._to_number(right_val))
                if self.op == "&":
                    return fn(self._to_text(left_val), self._to_text(right_val))
                # comparison operators
                lv, rv = self._coerce_cmp(left_val, right_val)
                return fn(lv, rv)
            except (TypeError, ValueError, ZeroDivisionError):
                return None
        # unary minus
        if self.op == "-":
            val = self.left.evaluate(ws, context)
            if val is None:
                return 0.0
            try:
                return -self._to_number(val)
            except (TypeError, ValueError):
                return None
        return None


@dataclass
class FunctionNode(ASTNode):
    name: str
    args: list[ASTNode] = field(default_factory=list)

    def evaluate(self, ws: Any, context: dict[str, Any] | None = None) -> Any:
        from univer.formula.functions import registry

        fn = registry.get(self.name.upper())
        if fn is None:
            return None
        args = [a.evaluate(ws, context) for a in self.args]
        return fn(*args)


@dataclass
class UnionNode(ASTNode):
    """Represents a union of references, e.g. A1:B3,C5:D7 used in SUM(A1:B3,C5:D7)."""

    nodes: list[ASTNode] = field(default_factory=list)

    def evaluate(self, ws: Any, context: dict[str, Any] | None = None) -> list[Any]:
        results = []
        for node in self.nodes:
            val = node.evaluate(ws, context)
            if isinstance(val, list):
                results.extend(val)
            elif val is not None:
                results.append(val)
        return results


@dataclass
class PrefixNode(ASTNode):
    """Unary prefix operator node (placeholder for future extension)."""

    operand: ASTNode

    def evaluate(self, ws: Any, context: dict[str, Any] | None = None) -> Any:
        return self.operand.evaluate(ws, context)
