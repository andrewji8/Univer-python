"""Tests for the formula engine and built-in functions."""

from univer.formula.engine import FormulaEngine
from univer.formula.functions import registry
from univer.models.sheet import Worksheet


def _make_ws(pairs: dict[tuple[int, int], any]) -> Worksheet:
    ws = Worksheet(name="Test")
    for (r, c), v in pairs.items():
        ws.set_cell(r, c, v)
    return ws


def test_sum_function():
    assert registry["SUM"](1, 2, 3) == 6
    assert registry["SUM"]([1, 2], [3, 4]) == 10.0
    assert registry["SUM"]() == 0.0


def test_average_function():
    assert registry["AVERAGE"](10, 20, 30) == 20.0
    assert registry["AVG"](4, 6) == 5.0


def test_max_min():
    assert registry["MAX"](1, 5, 3) == 5
    assert registry["MIN"](1, 5, 3) == 1


def test_count():
    assert registry["COUNT"](1, None, "a", "") == 3
    assert registry["COUNTA"](1, None, "a", "") == 2


def test_if():
    assert registry["IF"](True, "yes", "no") == "yes"
    assert registry["IF"](False, "yes", "no") == "no"
    assert registry["IF"](None, "yes", "no") == "no"


def test_arithmetic():
    engine = FormulaEngine()
    ws = _make_ws({(0, 0): 10, (0, 1): 5})
    assert engine.evaluate("=A1+B1", ws) == 15
    assert engine.evaluate("=A1*B1", ws) == 50
    assert engine.evaluate("=A1/B1", ws) == 2.0
    assert engine.evaluate("=A1-B1", ws) == 5


def test_text_functions():
    assert registry["LEN"]("hello") == 5
    assert registry["UPPER"]("hello") == "HELLO"
    assert registry["LOWER"]("HELLO") == "hello"
    assert registry["CONCAT"]("a", "b", "c") == "abc"


def test_date_functions():
    assert registry["YEAR"]("2024-03-15") == 2024
    assert registry["MONTH"]("2024-03-15") == 3
    assert registry["DAY"]("2024-03-15") == 15


def test_evaluate_with_refs():
    engine = FormulaEngine()
    ws = _make_ws({(0, 0): 100, (0, 1): 200, (1, 0): 50})
    assert engine.evaluate("=A1+B1", ws) == 300
    assert engine.evaluate("=A1*2", ws) == 200


def test_evaluate_range():
    engine = FormulaEngine()
    ws = _make_ws({(0, 0): 1, (0, 1): 2, (1, 0): 3, (1, 1): 4})
    result = engine.evaluate_range("A1:B2", ws)
    assert result == [[1, 2], [3, 4]]


def test_empty_cells_arithmetic():
    # Empty cells behave like 0 (Excel semantics) instead of raising.
    engine = FormulaEngine()
    ws = Worksheet()
    assert engine.evaluate("=A1+A2", ws) == 0.0
    assert engine.evaluate("=A1-1", ws) == -1.0
    assert engine.evaluate("=5+A1", ws) == 5.0


def test_empty_cells_comparison():
    engine = FormulaEngine()
    ws = Worksheet()
    # empty cell compared to a number is treated as 0
    assert engine.evaluate("=A1>1", ws) is False
    assert engine.evaluate("=A1==0", ws) is True


def test_text_arithmetic_returns_none():
    # Adding text to a number is a #VALUE!-style error -> None (no crash).
    engine = FormulaEngine()
    ws = _make_ws({(0, 0): "abc"})
    assert engine.evaluate("=A1+1", ws) is None


def test_concat_with_empty_cell():
    engine = FormulaEngine()
    ws = _make_ws({(0, 0): "hello"})
    assert engine.evaluate('=A1&" world"', ws) == "hello world"
