"""Parser for spreadsheet formula expressions.

Builds an AST from a tokenised formula string.
Grammar:
  formula   := expr
  expr      := cmp_expr
  cmp_expr  := concat_expr ((EQUAL | NOT_EQUAL | GREATER | LESS | GREATER_EQ | LESS_EQ) concat_expr)*
  concat_expr := additive (AMP additive)*
  additive  := multiplicative ((PLUS | MINUS) multiplicative)*
  multiplicative := power ((STAR | SLASH | PERCENT) power)*
  power     := primary [CARET power]          # right-associative
  primary   := NUMBER | STRING | IDENTIFIER args? | LPAREN expr RPAREN
  args      := LPAREN (expr (COMMA expr)*)? RPAREN

Range references (A1:B3) are handled inside primary as a cell-ref:cell-ref sequence.
"""

from __future__ import annotations

import re

from univer.formula.ast import (
    ASTNode,
    FunctionNode,
    OperatorNode,
    ReferenceNode,
    ValueNode,
)
from univer.formula.errors import FormulaSyntaxError
from univer.formula.lexer import Lexer, Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # -- public --

    @classmethod
    def parse(cls, text: str) -> ASTNode | None:
        tokens: list[Token] = []
        try:
            tokens = list(Lexer(text))
        except Exception:
            # Lexer never raises; keep this branch for future extensions.
            return None
        # Filter out ERROR tokens emitted by the lexer for unsupported chars.
        error_tokens = [t for t in tokens if t.type == TokenType.ERROR]
        if error_tokens:
            err = error_tokens[0]
            raise FormulaSyntaxError(f"Unexpected character {err.value!r}", position=err.position)
        return cls(tokens).parse_expression()

    @classmethod
    def parse_formula(cls, text: str) -> ASTNode | None:
        """Entry point: strips leading '=' if present."""
        text = text.strip()
        if text.startswith("="):
            text = text[1:]
        return cls.parse(text)

    # -- reference helpers --

    @staticmethod
    def parse_ref(ref: str) -> tuple[int, int] | tuple[int, int, int, int] | None:
        """Parse a cell reference like A1 or a range like A1:B3."""
        ref = ref.strip().upper()
        parts = ref.split(":")
        if len(parts) == 1:
            return Parser._parse_cell(parts[0])
        if len(parts) == 2:
            a = Parser._parse_cell(parts[0])
            b = Parser._parse_cell(parts[1])
            if a is not None and b is not None:
                return (*a, *b)
        return None

    @staticmethod
    def _parse_cell(ref: str) -> tuple[int, int] | None:
        m = re.match(r"^([A-Z]+)(\d+)$", ref)
        if not m:
            return None
        col_str, row_str = m.group(1), m.group(2)
        col = 0
        for c in col_str:
            col = col * 26 + (ord(c) - ord("A") + 1)
        return (int(row_str) - 1, col - 1)

    # -- recursive-descent parsing --

    def _current(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return Token(TokenType.EOF, "", 0)

    def _consume(self, expected_type: TokenType | None = None) -> Token:
        tok = self._current()
        if expected_type and tok.type != expected_type:
            raise FormulaSyntaxError(
                f"Expected {expected_type.name}, got {tok.type.name} ({tok.value!r})",
                position=tok.position,
            )
        self._pos += 1
        return tok

    def parse_expression(self) -> ASTNode | None:
        return self._parse_cmp()

    # -- comparison level --

    def _parse_cmp(self) -> ASTNode | None:
        left = self._parse_concat()
        assert left is not None
        cmp_ops = {
            TokenType.EQUAL,
            TokenType.NOT_EQUAL,
            TokenType.GREATER,
            TokenType.LESS,
            TokenType.GREATER_EQ,
            TokenType.LESS_EQ,
        }
        while self._current().type in cmp_ops:
            op_tok = self._current()
            self._pos += 1
            right = self._parse_concat()
            assert right is not None
            left = OperatorNode(op_tok.value, left, right)
        return left

    # -- concatenation level (Excel '&' sits between additive and comparison) --

    def _parse_concat(self) -> ASTNode | None:
        left = self._parse_additive()
        assert left is not None
        while self._current().type == TokenType.AMP:
            op_tok = self._current()
            self._pos += 1
            right = self._parse_additive()
            assert right is not None
            left = OperatorNode(op_tok.value, left, right)
        return left

    # -- additive level --

    def _parse_additive(self) -> ASTNode | None:
        left = self._parse_multiplicative()
        assert left is not None
        while True:
            tok = self._current()
            if tok.type in (TokenType.PLUS, TokenType.MINUS):
                self._pos += 1
                right = self._parse_multiplicative()
                assert right is not None
                left = OperatorNode(tok.value, left, right)
            else:
                break
        return left

    # -- multiplicative level --

    def _parse_multiplicative(self) -> ASTNode | None:
        left = self._parse_power()
        assert left is not None
        while True:
            tok = self._current()
            if tok.type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
                self._pos += 1
                right = self._parse_power()
                assert right is not None
                left = OperatorNode(tok.value, left, right)
            else:
                break
        return left

    # -- power level --

    def _parse_power(self) -> ASTNode | None:
        base = self._parse_primary()
        assert base is not None
        tok = self._current()
        if tok.type == TokenType.CARET:
            self._pos += 1
            exp = self._parse_power()  # right-associative
            assert exp is not None
            return OperatorNode("**", base, exp)
        return base

    # -- primary level --

    def _parse_primary(self) -> ASTNode | None:
        tok = self._current()

        # unary minus
        if tok.type == TokenType.MINUS:
            self._pos += 1
            operand = self._parse_primary()
            assert operand is not None
            return OperatorNode("-", operand)

        if tok.type == TokenType.NUMBER:
            self._pos += 1
            try:
                return ValueNode(float(tok.value) if "." in tok.value else int(tok.value))
            except ValueError:
                return ValueNode(tok.value)

        if tok.type == TokenType.STRING:
            self._pos += 1
            return ValueNode(tok.value)

        if tok.type == TokenType.IDENTIFIER:
            name = tok.value.upper()
            self._pos += 1
            # check for range reference like A1:B3
            if self._is_cell_ref(name) and self._current().type == TokenType.COLON:
                self._pos += 1  # consume ':'
                next_tok = self._current()
                if next_tok.type == TokenType.IDENTIFIER and self._is_cell_ref(next_tok.value):
                    self._pos += 1
                    ref_str = f"{name}:{next_tok.value}"
                    return ReferenceNode(ref_str)
                raise FormulaSyntaxError(
                    f"Invalid range reference: expected cell ref after ':', got {next_tok.value!r}",
                    position=next_tok.position,
                )
            # check for function call
            nxt = self._current()
            if nxt.type == TokenType.LPAREN:
                return self._parse_function_call(name)
            # check for cell reference
            if self._is_cell_ref(name):
                return ReferenceNode(name)
            # Unrecognised identifier — not a cell ref, not a function, not a range.
            raise FormulaSyntaxError(
                f"Unrecognized identifier {name!r}",
                position=tok.position,
            )

        if tok.type == TokenType.LPAREN:
            self._pos += 1
            node = self.parse_expression()
            self._consume(TokenType.RPAREN)
            return node

        if tok.type == TokenType.EOF:
            return None

        # Unexpected token (operator, comma, etc. in primary position)
        raise FormulaSyntaxError(
            f"Unexpected token {tok.type.name} ({tok.value!r})",
            position=tok.position,
        )

    def _parse_function_call(self, name: str) -> FunctionNode:
        self._consume(TokenType.LPAREN)
        args: list[ASTNode] = []
        while self._current().type not in (TokenType.RPAREN, TokenType.EOF):
            arg = self.parse_expression()
            assert arg is not None
            args.append(arg)
            tok = self._current()
            if tok.type == TokenType.COMMA:
                self._pos += 1
            elif tok.type == TokenType.RPAREN:
                break
            else:
                break
        self._consume(TokenType.RPAREN)
        return FunctionNode(name, args)

    @staticmethod
    def _is_cell_ref(s: str) -> bool:
        return bool(re.match(r"^[A-Z]+\d+$", s.upper()))


def parse_formula(text: str) -> ASTNode | None:
    return Parser.parse_formula(text)


def parse_ref(ref: str) -> tuple[int, int] | tuple[int, int, int, int] | None:
    return Parser.parse_ref(ref)
