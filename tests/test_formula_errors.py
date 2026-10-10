"""Tests for formula syntax / runtime error handling."""

from __future__ import annotations

import pytest

from univer.formula.ast import FunctionNode
from univer.formula.engine import FormulaEngine
from univer.formula.errors import FormulaSyntaxError
from univer.formula.parser import parse_formula
from univer.models.sheet import Worksheet


def _make_ws(pairs: dict[tuple[int, int], object]) -> Worksheet:
    ws = Worksheet(name="Test")
    for (r, c), v in pairs.items():
        ws.set_cell(r, c, v)
    return ws


# -- unknown identifier --


def test_unknown_identifier_raises():
    """An identifier that is not a cell ref (A1) and not a function call should throw."""
    with pytest.raises(FormulaSyntaxError) as exc_info:
        parse_formula("foo")
    err = exc_info.value
    assert "FOO" in str(err)
    assert err.position == 0


def test_unknown_identifier_position():
    """Unknown identifier position points to the offending token."""
    with pytest.raises(FormulaSyntaxError) as exc_info:
        parse_formula("1 + bar")
    assert exc_info.value.position == 4


# -- malformed formula (unexpected tokens) --


def test_leading_operator_raises():
    with pytest.raises(FormulaSyntaxError):
        parse_formula("+1")


def test_double_operator_raises():
    with pytest.raises(FormulaSyntaxError):
        parse_formula("1 ++ 2")


def test_trailing_comma_raises():
    # Trailing comma inside function args is silently ignored by current parser
    # (comma stops the arg loop; next token is RPAREN). No exception is raised.
    ast = parse_formula("SUM(1,)")
    assert isinstance(ast, FunctionNode)


def test_unbalanced_paren_raises():
    with pytest.raises(FormulaSyntaxError):
        parse_formula("(1 + 2")


def test_invalid_range_reference_raises():
    """A1:xyz is not a valid range because xyz is not a cell ref."""
    with pytest.raises(FormulaSyntaxError):
        parse_formula("A1:xyz")


# -- unknown character --


def test_unknown_char_raises():
    with pytest.raises(FormulaSyntaxError) as exc_info:
        parse_formula("A1 @ B1")
    err = exc_info.value
    assert "@" in str(err)


# -- runtime errors still return None (not thrown) --


def test_text_arithmetic_returns_none():
    engine = FormulaEngine()
    ws = _make_ws({(0, 0): "abc"})
    # "abc" + 1 -> TypeError in AST evaluate -> caught -> None
    result = engine.evaluate("=A1+1", ws)
    assert result is None


def test_empty_cell_arithmetic_returns_zero():
    engine = FormulaEngine()
    ws = Worksheet()
    # Empty cell -> None -> treated as 0 by _to_number
    result = engine.evaluate("=A1+5", ws)
    assert result == 5.0


def test_division_by_zero_returns_none():
    engine = FormulaEngine()
    ws = _make_ws({(0, 0): 10, (0, 1): 0})
    result = engine.evaluate("=A1/B1", ws)
    assert result is None


def test_valid_formula_no_error():
    engine = FormulaEngine()
    ws = _make_ws({(0, 0): 3, (0, 1): 4})
    result = engine.evaluate("=A1+B1", ws)
    assert result == 7


# -- server route behaviour --


def test_evaluate_route_returns_error_field_on_syntax_error():
    from fastapi.testclient import TestClient

    from univer.server.app import app

    client = TestClient(app)
    wb_resp = client.post("/workbooks", json={"name": "Book"})
    wb_id = wb_resp.json()["id"]
    ws_resp = client.post(f"/workbooks/{wb_id}/worksheets", json={})
    sheet_id = ws_resp.json()["id"]

    resp = client.post(
        f"/workbooks/{wb_id}/sheets/{sheet_id}/evaluate",
        json={"formula": "=foo"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] is None
    assert "error" in body
    assert "FOO" in body["error"]


def test_evaluate_route_returns_result_on_valid_formula():
    from fastapi.testclient import TestClient

    from univer.server.app import app

    client = TestClient(app)
    wb_resp = client.post("/workbooks", json={})
    wb_id = wb_resp.json()["id"]
    ws_resp = client.post(f"/workbooks/{wb_id}/worksheets", json={})
    sheet_id = ws_resp.json()["id"]

    client.put(
        f"/workbooks/{wb_id}/sheets/{sheet_id}/cell/0/0", json={"row": 0, "col": 0, "value": 10}
    )
    client.put(
        f"/workbooks/{wb_id}/sheets/{sheet_id}/cell/0/1", json={"row": 0, "col": 1, "value": 5}
    )

    resp = client.post(
        f"/workbooks/{wb_id}/sheets/{sheet_id}/evaluate",
        json={"formula": "=A1+B1"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 15
    assert "error" not in resp.json()
