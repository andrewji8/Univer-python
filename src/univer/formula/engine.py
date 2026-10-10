"""Formula engine — coordinates parsing, evaluation, and dependency tracking."""

from __future__ import annotations

from typing import Any

from univer.formula.parser import Parser


class FormulaEngine:
    """Evaluates spreadsheet formulas against a Worksheet model."""

    def evaluate(self, formula: str, worksheet: Any) -> Any:
        """Parse and evaluate a formula string (with or without leading =)."""
        ast = Parser.parse_formula(formula)
        if ast is None:
            return None
        return ast.evaluate(worksheet)

    def evaluate_range(self, range_str: str, worksheet: Any) -> list[list[Any]]:
        """Return the values in a range like 'A1:B3' as a 2-D list."""
        parsed = Parser.parse_ref(range_str)
        if parsed is None:
            return []
        if len(parsed) == 4:
            r1, c1, r2, c2 = parsed
            return list[list[Any]](worksheet.get_range(r1, c1, r2, c2))
        return []

    def resolve_reference(self, ref: str, worksheet: Any) -> Any:
        """Resolve a single cell or range reference to its value(s)."""
        parsed = Parser.parse_ref(ref)
        if parsed is None:
            return None
        if len(parsed) == 4:
            r1, c1, r2, c2 = parsed
            return worksheet.get_range(r1, c1, r2, c2)
        row, col = parsed
        return worksheet.get_cell(row, col)
