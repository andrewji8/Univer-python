"""Tests for the formula lexer."""

from univer.formula.lexer import Lexer, TokenType


def test_basic_tokens():
    tokens = list(Lexer("=SUM(A1:B3)+MAX(C1,C3)"))
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert TokenType.IDENTIFIER in types
    assert TokenType.PLUS in types
    assert TokenType.COMMA in types


def test_numbers():
    tokens = list(Lexer("123 + 45.6"))
    nums = [t for t in tokens if t.type == TokenType.NUMBER]
    assert len(nums) == 2
    assert nums[0].value == "123"
    assert nums[1].value == "45.6"


def test_strings():
    tokens = list(Lexer('"hello world"'))
    strs = [t for t in tokens if t.type == TokenType.STRING]
    assert len(strs) == 1
    assert strs[0].value == "hello world"


def test_operators():
    tokens = list(Lexer("a + b - c * d / e"))
    ops = [
        t.value
        for t in tokens
        if t.type in (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH)
    ]
    assert ops == ["+", "-", "*", "/"]


def test_equal_signs():
    tokens = list(Lexer("a == b && c != d"))
    eqs = [t.value for t in tokens if t.type in (TokenType.EQUAL, TokenType.NOT_EQUAL)]
    assert "==" in eqs
    assert "!=" in eqs
