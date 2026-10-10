"""Tests for the JSON-file persistence layer."""

from __future__ import annotations

import json

import pytest

from univer.core.di import DIContainer
from univer.core.facade import new_api
from univer.core.persistence import JsonFilePersistence, PersistenceError
from univer.formula.engine import FormulaEngine


def _make_facade(tmp_path):
    container = DIContainer()
    container.register(FormulaEngine)
    facade = new_api(container)
    persistence = JsonFilePersistence(data_dir=str(tmp_path))
    return facade, persistence


def test_save_and_load_roundtrip(tmp_path):
    facade, persistence = _make_facade(tmp_path)

    # mutate state
    wb_id = facade.create_workbook("Book")
    ws_id = facade.add_worksheet(wb_id, "Sheet1")
    facade.set_cell(wb_id, ws_id, 0, 0, 42)

    doc_id = facade.create_document("Doc")
    doc = facade.get_document(doc_id)
    doc.add_section("Hi", bold=True)

    pres_id = facade.create_presentation("Deck")
    slide_id = facade.add_slide(pres_id, "Slide1")
    facade.add_shape(pres_id, slide_id, "text", "Hello", x=10, y=20, width=100, height=50)

    # save
    persistence.save(facade.to_state())

    # create a fresh facade and load
    facade2, _ = _make_facade(tmp_path)
    state = persistence.load()
    assert state is not None
    facade2.from_state(state)

    assert facade2.get_workbook(wb_id).name == "Book"
    assert facade2.get_cell(wb_id, ws_id, 0, 0) == 42
    assert facade2.get_document(doc_id).name == "Doc"
    assert facade2.get_presentation(pres_id).name == "Deck"
    assert facade2.get_slide(pres_id, slide_id).title == "Slide1"


def test_load_returns_none_when_file_missing(tmp_path):
    persistence = JsonFilePersistence(data_dir=str(tmp_path))
    assert persistence.load() is None


def test_load_returns_none_on_empty_file(tmp_path):
    path = tmp_path / "store.json"
    path.write_text("")
    persistence = JsonFilePersistence(data_dir=str(tmp_path))
    with pytest.raises(PersistenceError):
        persistence.load()


def test_load_rejects_invalid_json(tmp_path):
    path = tmp_path / "store.json"
    path.write_text("{ not valid json !!")
    persistence = JsonFilePersistence(data_dir=str(tmp_path))
    with pytest.raises(PersistenceError):
        persistence.load()


def test_load_returns_list_instead_of_dict(tmp_path):
    """Non-dict JSON (e.g. a list) is treated as empty — load returns None, not an error."""
    path = tmp_path / "store.json"
    path.write_text("[1, 2, 3]")
    persistence = JsonFilePersistence(data_dir=str(tmp_path))
    result = persistence.load()
    assert result is None


def test_save_writes_valid_json(tmp_path):
    facade, persistence = _make_facade(tmp_path)
    facade.create_workbook("Book")
    persistence.save(facade.to_state())

    path = tmp_path / "store.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "workbooks" in data


def test_facade_from_state_clears_existing_data(tmp_path):
    facade, persistence = _make_facade(tmp_path)
    facade.create_workbook("OldBook")
    persistence.save(facade.to_state())

    facade2, _ = _make_facade(tmp_path)
    facade2.create_workbook("NewBook")
    persistence.save(facade2.to_state())

    facade3, _ = _make_facade(tmp_path)
    state = persistence.load()
    assert state is not None
    facade3.from_state(state)
    # should only have NewBook
    assert "NewBook" in {wb.name for wb in facade3.workbooks.values()}
    assert "OldBook" not in {wb.name for wb in facade3.workbooks.values()}


def test_persistence_error_is_runtime_error_subclass():
    assert issubclass(PersistenceError, RuntimeError)
