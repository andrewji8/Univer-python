"""Spreadsheet data model — mirrors the Univer sheets package core."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Union

# A cell can hold a number, string, boolean, or be empty (None).
CellValue = Union[int, float, str, bool, None]


@dataclass
class Cell:
    """A single cell value. Can be a primitive or a formula string."""

    value: CellValue = None
    is_formula: bool = False


@dataclass
class Worksheet:
    """In-memory worksheet with sparse cell storage."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = "Sheet1"
    _cells: dict[tuple[int, int], Cell] = field(default_factory=dict)

    def set_cell(self, row: int, col: int, value: Any, *, is_formula: bool = False) -> None:
        self._cells[(row, col)] = Cell(value=value, is_formula=is_formula)

    def get_cell(self, row: int, col: int) -> Any:
        cell = self._cells.get((row, col))
        return cell.value if cell is not None else None

    def get_range(self, row1: int, col1: int, row2: int, col2: int) -> list[list[Any]]:
        r_min, r_max = min(row1, row2), max(row1, row2)
        c_min, c_max = min(col1, col2), max(col1, col2)
        result: list[list[Any]] = []
        for r in range(r_min, r_max + 1):
            row_vals = []
            for c in range(c_min, c_max + 1):
                row_vals.append(self.get_cell(r, c))
            result.append(row_vals)
        return result

    @property
    def cells(self) -> dict[tuple[int, int], Cell]:
        return self._cells

    # -- serialization --

    def to_dict(self) -> dict[str, Any]:
        cells: dict[str, Any] = {}
        for (r, c), cell in self._cells.items():
            cells[f"{r},{c}"] = {"value": cell.value, "is_formula": cell.is_formula}
        return {
            "id": self.id,
            "name": self.name,
            "cells": cells,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Worksheet:
        ws = cls(id=data.get("id", ""), name=data.get("name", "Sheet1"))
        for key, cell_data in data.get("cells", {}).items():
            parts = key.split(",")
            r, c = int(parts[0]), int(parts[1])
            ws._cells[(r, c)] = Cell(
                value=cell_data.get("value"), is_formula=cell_data.get("is_formula", False)
            )
        return ws


@dataclass
class Workbook:
    """Top-level workbook containing multiple worksheets."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = "Untitled"
    worksheets: dict[str, Worksheet] = field(default_factory=dict)
    active_sheet_id: str | None = None

    def add_worksheet(self, name: str = "Sheet1") -> Worksheet:
        ws = Worksheet(name=name)
        self.worksheets[ws.id] = ws
        if self.active_sheet_id is None:
            self.active_sheet_id = ws.id
        return ws

    def get_active_sheet(self) -> Worksheet | None:
        if self.active_sheet_id is None:
            return None
        return self.worksheets.get(self.active_sheet_id)

    def get_sheet(self, sheet_id: str) -> Worksheet | None:
        return self.worksheets.get(sheet_id)

    # -- serialization --

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "active_sheet_id": self.active_sheet_id,
            "worksheets": {sid: ws.to_dict() for sid, ws in self.worksheets.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workbook:
        wb = cls(
            id=data.get("id", ""),
            name=data.get("name", "Untitled"),
            active_sheet_id=data.get("active_sheet_id"),
        )
        for sid, ws_data in data.get("worksheets", {}).items():
            wb.worksheets[sid] = Worksheet.from_dict(ws_data)
        return wb
