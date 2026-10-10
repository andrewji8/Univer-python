"""Document data model — mirrors the Univer docs package core."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Section:
    """A document section (paragraph-like unit)."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    text: str = ""
    bold: bool = False
    italic: bool = False
    font_size: int = 11

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "bold": self.bold,
            "italic": self.italic,
            "fontSize": self.font_size,
        }


@dataclass
class Document:
    """An in-memory document composed of sections."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = "Untitled Doc"
    sections: list[Section] = field(default_factory=list)

    def add_section(
        self, text: str, *, bold: bool = False, italic: bool = False, font_size: int = 11
    ) -> Section:
        section = Section(text=text, bold=bold, italic=italic, font_size=font_size)
        self.sections.append(section)
        return section

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "sections": [s.to_dict() for s in self.sections],
        }

    # -- serialization --

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        doc = cls(id=data.get("id", ""), name=data.get("name", "Untitled Doc"))
        for sec_data in data.get("sections", []):
            doc.sections.append(
                Section(
                    id=sec_data.get("id", ""),
                    text=sec_data.get("text", ""),
                    bold=sec_data.get("bold", False),
                    italic=sec_data.get("italic", False),
                    font_size=sec_data.get("fontSize", sec_data.get("font_size", 11)),
                )
            )
        return doc
