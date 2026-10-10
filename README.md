# Univer Python

Headless Office engine for AI agents — Spreadsheets, Docs, and Slides in Python.

This is the server-side half of [Univer](https://github.com/dream-num/univer). The frontend (React + Canvas) remains in TypeScript; this package implements the formula engine, data models, and Facade API in Python for use as a headless processing backend.

## Architecture

```
Browser (React + Canvas)          Python Backend (FastAPI)
┌──────────────────────┐         ┌──────────────────────┐
│  sheets-ui / docs-ui │  HTTP   │  FastAPI server      │
│  Facade API (JS)     │◄──────►│  Formula engine      │
│  Canvas renderer     │         │  Data models         │
└──────────────────────┘         │  Commands/Mutations  │
                                 └──────────────────────┘
```

## Quick Start

```bash
poetry install
poetry run uvicorn univer.server.app:app --reload
```

Server runs at `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

## Capabilities

| Area | Highlights |
|------|------------|
| **Spreadsheets** | Workbook / Worksheet / Cell models, sparse storage, range reads |
| **Docs** | Document / Section model with rich-text flags (bold, italic, font size) |
| **Slides** | Presentation / Slide / Shape model — add slides and positioned shapes |
| **Formula engine** | Lexer → recursive-descent parser → AST evaluator, ~30 built-in functions (`SUM`, `IF`, `VLOOKUP`, text & date helpers, …). Syntax errors raise `FormulaSyntaxError`; runtime errors (type mismatch, divide-by-zero) yield `None` like Excel error values. |

## REST endpoints

```
POST   /workbooks                                    create a workbook
GET    /workbooks/{workbook_id}                       fetch a workbook
POST   /workbooks/{workbook_id}/worksheets            add a worksheet
GET    /workbooks/{workbook_id}/sheets/{sheet_id}/cell/{row}/{col}
PUT    /workbooks/{workbook_id}/sheets/{sheet_id}/cell/{row}/{col}
GET    /workbooks/{workbook_id}/sheets/{sheet_id}/range
POST   /workbooks/{workbook_id}/sheets/{sheet_id}/evaluate   evaluate a formula
POST   /documents / GET /documents/{doc_id} / POST /documents/{doc_id}/sections
POST   /presentations                                create a presentation
GET    /presentations/{presentation_id}
POST   /presentations/{presentation_id}/slides       add a slide
POST   /presentations/{presentation_id}/slides/{slide_id}/shapes   add a shape
GET    /health                                       health check
```

## Persistence

State (workbooks, documents, presentations) is persisted as a single JSON file at
`.univer_data/store.json`. It is loaded on server startup and saved after every
write operation, so data survives a restart. A corrupted state file raises a clear
`PersistenceError` on startup rather than being silently ignored.

## Development

```bash
poetry install
poetry run pytest -q        # run the test suite
poetry run ruff check .     # lint
poetry run ruff format --check .
poetry run black --check .
poetry run mypy src         # type check
```

CI (`.github/workflows/ci.yml`) runs all of the above on every push and pull request.
