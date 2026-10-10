"""Formula parsing and lexing errors."""

from __future__ import annotations


class FormulaSyntaxError(Exception):
    """Raised when a formula string cannot be parsed.

    Attributes:
        position: Character offset into the original formula text where the error occurred.
        message:  Human-readable description of the problem.
    """

    def __init__(self, message: str, position: int = 0) -> None:
        self.position = position
        self.message = message
        super().__init__(f"[pos {position}] {message}")
