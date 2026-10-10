"""Lexer for spreadsheet formula expressions.

Handles tokenisation of formulas like:
  =SUM(A1:B3)+MAX(C1,C3)*2
  =A1+B1*C1
  ="hello"&"world"
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CARET = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    COLON = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER = auto()
    LESS = auto()
    GREATER_EQ = auto()
    LESS_EQ = auto()
    AMP = auto()  # &
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    position: int = 0

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r})"


class Lexer:
    def __init__(self, text: str) -> None:
        self._text = text
        self._pos = 0

    def __iter__(self) -> Iterator[Token]:
        while True:
            tok = self._next_token()
            if tok.type == TokenType.EOF:
                break
            yield tok

    def _skip_whitespace(self) -> None:
        while self._pos < len(self._text) and self._text[self._pos].isspace():
            self._pos += 1

    def _next_token(self) -> Token:
        self._skip_whitespace()
        if self._pos >= len(self._text):
            return Token(TokenType.EOF, "", self._pos)

        ch = self._text[self._pos]
        pos = self._pos

        # strings
        if ch in ('"', "'"):
            return self._read_string(ch)

        # numbers
        if ch.isdigit():
            return self._read_number()

        # identifiers / keywords
        if ch.isalpha() or ch == "_":
            return self._read_identifier()

        # two-char operators
        if ch == "=" and self._pos + 1 < len(self._text) and self._text[self._pos + 1] == "=":
            self._pos += 2
            return Token(TokenType.EQUAL, "==", pos)
        if ch == "!" and self._pos + 1 < len(self._text) and self._text[self._pos + 1] == "=":
            self._pos += 2
            return Token(TokenType.NOT_EQUAL, "!=", pos)
        if ch == ">" and self._pos + 1 < len(self._text) and self._text[self._pos + 1] == "=":
            self._pos += 2
            return Token(TokenType.GREATER_EQ, ">=", pos)
        if ch == "<" and self._pos + 1 < len(self._text) and self._text[self._pos + 1] == "=":
            self._pos += 2
            return Token(TokenType.LESS_EQ, "<=", pos)

        # single-char operators
        mapping = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "^": TokenType.CARET,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            "&": TokenType.AMP,
            ">": TokenType.GREATER,
            "<": TokenType.LESS,
        }
        if ch in mapping:
            self._pos += 1
            return Token(mapping[ch], ch, pos)

        # unknown character
        self._pos += 1
        return Token(TokenType.ERROR, ch, pos)

    def _read_string(self, quote: str) -> Token:
        start = self._pos
        self._pos += 1
        buf: list[str] = []
        while self._pos < len(self._text):
            ch = self._text[self._pos]
            if ch == "\\":
                self._pos += 1
                if self._pos < len(self._text):
                    buf.append(self._text[self._pos])
                    self._pos += 1
                continue
            if ch == quote:
                self._pos += 1
                return Token(TokenType.STRING, "".join(buf), start)
            buf.append(ch)
            self._pos += 1
        return Token(TokenType.ERROR, "".join(buf), start)

    def _read_number(self) -> Token:
        start = self._pos
        while self._pos < len(self._text) and (
            self._text[self._pos].isdigit() or self._text[self._pos] == "."
        ):
            self._pos += 1
        return Token(TokenType.NUMBER, self._text[start : self._pos], start)

    def _read_identifier(self) -> Token:
        start = self._pos
        while self._pos < len(self._text) and (
            self._text[self._pos].isalnum() or self._text[self._pos] in ("_", ".")
        ):
            self._pos += 1
        return Token(TokenType.IDENTIFIER, self._text[start : self._pos], start)
