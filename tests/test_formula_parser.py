"""Tests for the formula parser."""

from univer.formula.ast import FunctionNode, OperatorNode, ReferenceNode, ValueNode
from univer.formula.parser import Parser, parse_formula


def test_value_node():
    ast = parse_formula("42")
    assert isinstance(ast, ValueNode)
    assert ast.value == 42


def test_string_value():
    ast = parse_formula('"hello"')
    assert isinstance(ast, ValueNode)
    assert ast.value == "hello"


def test_addition():
    ast = parse_formula("A1+B1")
    assert isinstance(ast, OperatorNode)
    assert ast.op == "+"
    assert isinstance(ast.left, ReferenceNode)
    assert ast.left.ref == "A1"
    assert isinstance(ast.right, ReferenceNode)
    assert ast.right.ref == "B1"


def test_multiplication_priority():
    ast = parse_formula("A1+B1*C1")
    assert isinstance(ast, OperatorNode)
    assert ast.op == "+"
    # B1*C1 should be the right child (multiplication has higher precedence)
    assert isinstance(ast.right, OperatorNode)
    assert ast.right.op == "*"


def test_power_right_associative():
    ast = parse_formula("2^3^2")
    assert isinstance(ast, OperatorNode)
    assert ast.op == "**"
    assert isinstance(ast.right, OperatorNode)
    assert ast.right.op == "**"


def test_function_call():
    ast = parse_formula("SUM(A1:B3)")
    assert isinstance(ast, FunctionNode)
    assert ast.name == "SUM"
    assert len(ast.args) == 1


def test_nested_functions():
    ast = parse_formula('IF(SUM(A1,A2)>10, "yes", "no")')
    assert isinstance(ast, FunctionNode)
    assert ast.name == "IF"
    assert len(ast.args) == 3


def test_leading_equals_stripped():
    ast1 = parse_formula("=A1+B1")
    ast2 = parse_formula("A1+B1")
    assert type(ast1) is type(ast2)


def test_parse_ref_cell():
    result = Parser.parse_ref("A1")
    assert result == (0, 0)

    result = Parser.parse_ref("Z99")
    assert result == (98, 25)


def test_parse_ref_range():
    result = Parser.parse_ref("A1:B3")
    assert result == (0, 0, 2, 1)
