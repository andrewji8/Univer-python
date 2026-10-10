"""Slide/Presentation data model — mirrors the Univer slides package core."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Shape:
    """A shape element on a slide (text box, image placeholder, etc.)."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    type: str = "text"
    text: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class Slide:
    """A single slide in a presentation."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    shapes: list[Shape] = field(default_factory=list)

    def add_shape(
        self,
        shape_type: str = "text",
        text: str = "",
        *,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
    ) -> Shape:
        shape = Shape(
            type=shape_type,
            text=text,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        self.shapes.append(shape)
        return shape

    def get_shape(self, shape_id: str) -> Shape | None:
        for s in self.shapes:
            if s.id == shape_id:
                return s
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "shapes": [s.to_dict() for s in self.shapes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Slide:
        slide = cls(id=data.get("id", ""), title=data.get("title", ""))
        for sh_data in data.get("shapes", []):
            slide.shapes.append(
                Shape(
                    id=sh_data.get("id", ""),
                    type=sh_data.get("type", "text"),
                    text=sh_data.get("text", ""),
                    x=sh_data.get("x", 0),
                    y=sh_data.get("y", 0),
                    width=sh_data.get("width", 0),
                    height=sh_data.get("height", 0),
                )
            )
        return slide


@dataclass
class Presentation:
    """A presentation composed of multiple slides."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = "Untitled Presentation"
    slides: list[Slide] = field(default_factory=list)

    def add_slide(self, title: str = "") -> Slide:
        slide = Slide(title=title)
        self.slides.append(slide)
        return slide

    def get_slide(self, slide_id: str) -> Slide | None:
        for s in self.slides:
            if s.id == slide_id:
                return s
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slides": [s.to_dict() for s in self.slides],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Presentation:
        pres = cls(id=data.get("id", ""), name=data.get("name", "Untitled Presentation"))
        for sl_data in data.get("slides", []):
            pres.slides.append(Slide.from_dict(sl_data))
        return pres
