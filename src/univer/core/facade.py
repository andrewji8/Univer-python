"""Facade API — the public high-level interface, mirrored from FUniver in TypeScript."""

from __future__ import annotations

from typing import Any

from univer.core.di import DIContainer
from univer.core.plugin import PluginContext, PluginRegistry
from univer.formula.engine import FormulaEngine
from univer.models.document import Document
from univer.models.sheet import Workbook, Worksheet
from univer.models.slides import Presentation, Slide


class FUniver:
    """Unified Facade API for managing workbooks, documents, and formula evaluation."""

    def __init__(self, container: DIContainer) -> None:
        self._container = container
        self._workbooks: dict[str, Workbook] = {}
        self._documents: dict[str, Document] = {}
        self._presentations: dict[str, Presentation] = {}
        self._registry = PluginRegistry()

    # -- Plugin lifecycle --

    def register_plugin(self, plugin: Any) -> None:
        self._registry.register(plugin)

    def initialize(self) -> None:
        ctx = PluginContext(self._container)
        self._registry.install_all(ctx)

    # -- Workbook --

    def create_workbook(self, name: str = "Untitled") -> str:
        wb = Workbook(name=name)
        self._workbooks[wb.id] = wb
        return wb.id

    def get_workbook(self, workbook_id: str) -> Workbook | None:
        return self._workbooks.get(workbook_id)

    def add_worksheet(self, workbook_id: str, name: str = "Sheet1") -> str:
        wb = self._workbooks.get(workbook_id)
        if wb is None:
            raise KeyError(f"Workbook {workbook_id!r} not found")
        ws = wb.add_worksheet(name)
        return ws.id

    def get_worksheet(self, workbook_id: str, worksheet_id: str) -> Worksheet | None:
        wb = self._workbooks.get(workbook_id)
        if wb is None:
            return None
        return wb.worksheets.get(worksheet_id)

    def set_cell(self, workbook_id: str, worksheet_id: str, row: int, col: int, value: Any) -> None:
        ws = self.get_worksheet(workbook_id, worksheet_id)
        if ws is None:
            raise KeyError(f"Worksheet {worksheet_id!r} not found in {workbook_id!r}")
        ws.set_cell(row, col, value)

    def get_cell(self, workbook_id: str, worksheet_id: str, row: int, col: int) -> Any:
        ws = self.get_worksheet(workbook_id, worksheet_id)
        if ws is None:
            return None
        return ws.get_cell(row, col)

    # -- Document --

    def create_document(self, name: str = "Untitled Doc") -> str:
        doc = Document(name=name)
        self._documents[doc.id] = doc
        return doc.id

    def get_document(self, doc_id: str) -> Document | None:
        return self._documents.get(doc_id)

    # -- Formula --

    def evaluate_formula(self, workbook_id: str, worksheet_id: str, formula: str) -> Any:
        engine = self._container.get(FormulaEngine)
        ws = self.get_worksheet(workbook_id, worksheet_id)
        if ws is None:
            raise KeyError(f"Worksheet {worksheet_id!r} not found")
        return engine.evaluate(formula, ws)

    def evaluate_range(self, workbook_id: str, worksheet_id: str, range_str: str) -> Any:
        engine = self._container.get(FormulaEngine)
        ws = self.get_worksheet(workbook_id, worksheet_id)
        if ws is None:
            raise KeyError(f"Worksheet {worksheet_id!r} not found")
        return engine.evaluate_range(range_str, ws)

    @property
    def workbooks(self) -> dict[str, Workbook]:
        return dict(self._workbooks)

    @property
    def documents(self) -> dict[str, Document]:
        return dict(self._documents)

    # -- Presentation --

    def create_presentation(self, name: str = "Untitled Presentation") -> str:
        pres = Presentation(name=name)
        self._presentations[pres.id] = pres
        return pres.id

    def get_presentation(self, presentation_id: str) -> Presentation | None:
        return self._presentations.get(presentation_id)

    def add_slide(self, presentation_id: str, title: str = "") -> str:
        pres = self._presentations.get(presentation_id)
        if pres is None:
            raise KeyError(f"Presentation {presentation_id!r} not found")
        slide = pres.add_slide(title)
        return slide.id

    def get_slide(self, presentation_id: str, slide_id: str) -> Slide | None:
        pres = self._presentations.get(presentation_id)
        if pres is None:
            return None
        return pres.get_slide(slide_id)

    def add_shape(
        self,
        presentation_id: str,
        slide_id: str,
        shape_type: str = "text",
        text: str = "",
        *,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
    ) -> str:
        slide = self.get_slide(presentation_id, slide_id)
        if slide is None:
            raise KeyError(f"Slide {slide_id!r} not found in {presentation_id!r}")
        shape = slide.add_shape(shape_type, text, x=x, y=y, width=width, height=height)
        return shape.id

    @property
    def presentations(self) -> dict[str, Presentation]:
        return dict(self._presentations)

    # -- persistence --

    def to_state(self) -> dict[str, Any]:
        return {
            "workbooks": {wid: wb.to_dict() for wid, wb in self._workbooks.items()},
            "documents": {did: doc.to_dict() for did, doc in self._documents.items()},
            "presentations": {pid: pres.to_dict() for pid, pres in self._presentations.items()},
        }

    def from_state(self, state: dict[str, Any]) -> None:
        self._workbooks.clear()
        self._documents.clear()
        self._presentations.clear()
        for wb_data in state.get("workbooks", {}).values():
            wb = Workbook.from_dict(wb_data)
            self._workbooks[wb.id] = wb
        for doc_data in state.get("documents", {}).values():
            doc = Document.from_dict(doc_data)
            self._documents[doc.id] = doc
        for pres_data in state.get("presentations", {}).values():
            pres = Presentation.from_dict(pres_data)
            self._presentations[pres.id] = pres


def new_api(container: DIContainer) -> FUniver:
    """Factory that mirrors the TypeScript FUniver.newAPI(univer) pattern."""
    return FUniver(container)
