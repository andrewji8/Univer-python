"""Tests for the spreadsheet and document data models."""

from univer.models.document import Document, Section
from univer.models.sheet import Cell, Workbook, Worksheet


def test_worksheet_set_get_cell():
    ws = Worksheet(name="S1")
    ws.set_cell(0, 0, 42)
    assert ws.get_cell(0, 0) == 42
    assert ws.get_cell(5, 5) is None


def test_worksheet_cell_metadata():
    ws = Worksheet()
    ws.set_cell(0, 0, "=A1+B1", is_formula=True)
    cell = ws.cells[(0, 0)]
    assert isinstance(cell, Cell)
    assert cell.is_formula is True


def test_worksheet_get_range():
    ws = Worksheet()
    ws.set_cell(0, 0, 1)
    ws.set_cell(0, 1, 2)
    ws.set_cell(1, 0, 3)
    ws.set_cell(1, 1, 4)
    assert ws.get_range(0, 0, 1, 1) == [[1, 2], [3, 4]]


def test_workbook_add_and_active_sheet():
    wb = Workbook(name="Book")
    ws = wb.add_worksheet("Sheet1")
    assert wb.get_active_sheet() is ws
    assert wb.get_sheet(ws.id) is ws


def test_document_add_section():
    doc = Document(name="Doc")
    sec = doc.add_section("Hello", bold=True)
    assert isinstance(sec, Section)
    assert len(doc.sections) == 1


def test_document_to_dict():
    doc = Document(name="Doc")
    doc.add_section("Hi", italic=True, font_size=14)
    data = doc.to_dict()
    assert data["name"] == "Doc"
    assert data["sections"][0]["italic"] is True
    assert data["sections"][0]["fontSize"] == 14
