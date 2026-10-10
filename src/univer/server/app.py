"""FastAPI application — HTTP server exposing the Univer Python facade."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from univer.core.di import DIContainer
from univer.core.facade import FUniver, new_api
from univer.core.persistence import JsonFilePersistence, PersistenceError
from univer.formula.engine import FormulaEngine
from univer.formula.errors import FormulaSyntaxError

# -- request models --


class CreateWorkbookRequest(BaseModel):
    name: str = "Untitled"


class CreateWorksheetRequest(BaseModel):
    name: str = "Sheet1"


class SetCellRequest(BaseModel):
    row: int
    col: int
    value: object


class EvaluateRequest(BaseModel):
    formula: str


class DocumentRequest(BaseModel):
    name: str = "Untitled Doc"


class AddSlideRequest(BaseModel):
    title: str = ""


class AddShapeRequest(BaseModel):
    shape_type: str = "text"
    text: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


# Rebuild models to resolve any forward references
CreateWorkbookRequest.model_rebuild()
CreateWorksheetRequest.model_rebuild()
SetCellRequest.model_rebuild()
EvaluateRequest.model_rebuild()
DocumentRequest.model_rebuild()
AddSlideRequest.model_rebuild()
AddShapeRequest.model_rebuild()


# -- app factory --

_container = DIContainer()
_container.register(FormulaEngine, singleton=True)
_facade = new_api(_container)


def get_facade() -> FUniver:
    return _facade


_persistence = JsonFilePersistence()


def _load_state() -> None:
    try:
        state = _persistence.load()
        if state is not None:
            _facade.from_state(state)
    except PersistenceError as exc:
        raise RuntimeError(f"Failed to load persistent state: {exc}") from exc


def _save_state() -> None:
    try:
        _persistence.save(_facade.to_state())
    except PersistenceError as exc:
        raise RuntimeError(f"Failed to persist state: {exc}") from exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_state()
    _facade.initialize()
    yield
    try:
        _save_state()
    except RuntimeError as exc:
        print(f"[univer] warn: could not persist state on shutdown: {exc}", flush=True)


app = FastAPI(
    title="Univer Python — Headless Office Engine",
    description="Server-side Office SDK for AI agents (sheets, docs, formula engine)",
    version="0.1.0",
    lifespan=lifespan,
)


# -- workbook routes --


@app.post("/workbooks", response_model=dict)
async def create_workbook(req: CreateWorkbookRequest):
    wb_id = _facade.create_workbook(req.name)
    _save_state()
    return {"id": wb_id, "name": req.name}


@app.get("/workbooks/{workbook_id}")
async def get_workbook(workbook_id: str):
    wb = _facade.get_workbook(workbook_id)
    if wb is None:
        raise HTTPException(status_code=404, detail="Workbook not found")
    return {
        "id": wb.id,
        "name": wb.name,
        "worksheets": {sid: {"id": s.id, "name": s.name} for sid, s in wb.worksheets.items()},
    }


@app.post("/workbooks/{workbook_id}/worksheets", response_model=dict)
async def create_worksheet(workbook_id: str, req: CreateWorksheetRequest):
    ws_id = _facade.add_worksheet(workbook_id, req.name)
    _save_state()
    return {"id": ws_id, "name": req.name, "workbook_id": workbook_id}


@app.get("/workbooks/{workbook_id}/sheets/{sheet_id}/cell/{row}/{col}")
async def get_cell(workbook_id: str, sheet_id: str, row: int, col: int):
    val = _facade.get_cell(workbook_id, sheet_id, row, col)
    return {"value": val, "row": row, "col": col}


@app.put("/workbooks/{workbook_id}/sheets/{sheet_id}/cell/{row}/{col}")
async def set_cell(workbook_id: str, sheet_id: str, row: int, col: int, req: SetCellRequest):
    _facade.set_cell(workbook_id, sheet_id, row, col, req.value)
    _save_state()
    return {"ok": True}


@app.post("/workbooks/{workbook_id}/sheets/{sheet_id}/evaluate", response_model=dict)
async def evaluate_formula(workbook_id: str, sheet_id: str, req: EvaluateRequest):
    try:
        result = _facade.evaluate_formula(workbook_id, sheet_id, req.formula)
    except FormulaSyntaxError as exc:
        return {"formula": req.formula, "result": None, "error": str(exc)}
    return {"formula": req.formula, "result": result}


@app.get("/workbooks/{workbook_id}/sheets/{sheet_id}/range")
async def get_range(
    workbook_id: str, sheet_id: str, row1: int = 0, col1: int = 0, row2: int = 0, col2: int = 0
):
    ws = _facade.get_worksheet(workbook_id, sheet_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Worksheet not found")
    data = ws.get_range(row1, col1, row2, col2)
    return {"range": data}


# -- document routes --


@app.post("/documents", response_model=dict)
async def create_document(req: DocumentRequest):
    doc_id = _facade.create_document(req.name)
    _save_state()
    return {"id": doc_id, "name": req.name}


@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    doc = _facade.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.to_dict()


@app.post("/documents/{doc_id}/sections")
async def add_section(
    doc_id: str, text: str, bold: bool = False, italic: bool = False, font_size: int = 11
):
    doc = _facade.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    section = doc.add_section(text, bold=bold, italic=italic, font_size=font_size)
    _save_state()
    return section.to_dict()


# -- presentation routes --


class PresentationRequest(BaseModel):
    name: str = "Untitled Presentation"


PresentationRequest.model_rebuild()


@app.post("/presentations", response_model=dict)
async def create_presentation(req: PresentationRequest):
    pres_id = _facade.create_presentation(req.name)
    _save_state()
    return {"id": pres_id, "name": req.name}


@app.get("/presentations/{presentation_id}")
async def get_presentation(presentation_id: str):
    pres = _facade.get_presentation(presentation_id)
    if pres is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return pres.to_dict()


@app.post("/presentations/{presentation_id}/slides", response_model=dict)
async def add_slide(presentation_id: str, req: AddSlideRequest):
    slide_id = _facade.add_slide(presentation_id, req.title)
    _save_state()
    return {"id": slide_id, "presentation_id": presentation_id, "title": req.title}


@app.post("/presentations/{presentation_id}/slides/{slide_id}/shapes", response_model=dict)
async def add_shape(presentation_id: str, slide_id: str, req: AddShapeRequest):
    shape_id = _facade.add_shape(
        presentation_id,
        slide_id,
        shape_type=req.shape_type,
        text=req.text,
        x=req.x,
        y=req.y,
        width=req.width,
        height=req.height,
    )
    _save_state()
    return {"id": shape_id, "slide_id": slide_id, "presentation_id": presentation_id}


# -- root --


@app.get("/")
async def root():
    return {
        "service": "univer-python",
        "version": "0.1.0",
        "description": "Headless Office engine for AI agents — Spreadsheets, Docs, Slides",
        "endpoints": {
            "health": "/health",
            "api_docs": "/docs",
            "workbooks": "/workbooks",
            "documents": "/documents",
            "presentations": "/presentations",
        },
        "note": "Use /docs for full interactive API reference",
    }


# -- health --


@app.get("/health")
async def health():
    return {"status": "ok", "service": "univer-python"}
