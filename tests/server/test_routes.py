"""Tests for the FastAPI server routes (using httpx TestClient)."""

import pytest
from fastapi.testclient import TestClient

from univer.server.app import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_and_get_workbook(client):
    resp = client.post("/workbooks", json={"name": "TestBook"})
    assert resp.status_code == 200
    data = resp.json()
    wb_id = data["id"]

    resp = client.get(f"/workbooks/{wb_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "TestBook"


def test_create_worksheet(client):
    wb_resp = client.post("/workbooks", json={"name": "Book"})
    wb_id = wb_resp.json()["id"]

    ws_resp = client.post(f"/workbooks/{wb_id}/worksheets", json={"name": "S1"})
    assert ws_resp.status_code == 200
    assert ws_resp.json()["name"] == "S1"


def test_set_and_get_cell(client):
    wb_resp = client.post("/workbooks", json={})
    wb_id = wb_resp.json()["id"]
    ws_resp = client.post(f"/workbooks/{wb_id}/worksheets", json={})
    sheet_id = ws_resp.json()["id"]

    client.put(
        f"/workbooks/{wb_id}/sheets/{sheet_id}/cell/0/0", json={"row": 0, "col": 0, "value": 10}
    )
    cell_resp = client.get(f"/workbooks/{wb_id}/sheets/{sheet_id}/cell/0/0")
    assert cell_resp.json()["value"] == 10


def test_evaluate_formula(client):
    wb_resp = client.post("/workbooks", json={})
    wb_id = wb_resp.json()["id"]
    ws_resp = client.post(f"/workbooks/{wb_id}/worksheets", json={})
    sheet_id = ws_resp.json()["id"]

    client.put(
        f"/workbooks/{wb_id}/sheets/{sheet_id}/cell/0/0", json={"row": 0, "col": 0, "value": 5}
    )
    client.put(
        f"/workbooks/{wb_id}/sheets/{sheet_id}/cell/0/1", json={"row": 0, "col": 1, "value": 3}
    )

    eval_resp = client.post(
        f"/workbooks/{wb_id}/sheets/{sheet_id}/evaluate", json={"formula": "=A1+B1"}
    )
    assert eval_resp.status_code == 200
    assert eval_resp.json()["result"] == 8


def test_create_and_get_document(client):
    resp = client.post("/documents", json={"name": "MyDoc"})
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    get_resp = client.get(f"/documents/{doc_id}")
    assert resp.status_code == 200
    assert get_resp.json()["name"] == "MyDoc"


def test_add_section(client):
    doc_resp = client.post("/documents", json={"name": "Doc"})
    doc_id = doc_resp.json()["id"]

    sec_resp = client.post(f"/documents/{doc_id}/sections", params={"text": "Hello", "bold": True})
    assert sec_resp.status_code == 200
    assert sec_resp.json()["text"] == "Hello"
    assert sec_resp.json()["bold"] is True
