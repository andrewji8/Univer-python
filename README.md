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

## Installation

**Requirements:** Python **3.11+** (uses `X | Y` unions and modern typing).

### Option A — Poetry (recommended)

```bash
poetry install                              # creates .venv and installs univer-python + deps
poetry run uvicorn univer.server.app:app --reload
```

`poetry install` installs the package itself (editable), so `poetry run python -c "import univer"`
works out of the box.

### Option B — pip + venv

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -e .
uvicorn univer.server.app:app --reload
```

### Run without installing (dev shortcut)

If you only want to run the code without installing the package:

```bash
set PYTHONPATH=src          # Windows (PowerShell:  $env:PYTHONPATH="src")
export PYTHONPATH=src       # Unix
python -m uvicorn univer.server.app:app --reload
```

The test suite does **not** need this — `pyproject.toml` already sets
`pythonpath = ["src"]`, so `pytest` finds the package automatically.

### Run tests

```bash
poetry run pytest -q        # or: pytest -q
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

State (workbooks, documents, presentations) is persisted as a single JSON file. It is
loaded on server startup and saved after every write operation, so data survives a
restart. A corrupted state file raises a clear `PersistenceError` on startup rather than
being silently ignored.

> ⚠️ The store path is **derived from the installed package location**, not the current
> working directory. In a dev/editable checkout it resolves to
> **`src/.univer_data/store.json`**; in a non-editable `pip install` it lands under
> `site-packages/.univer_data/`. To control it explicitly, construct
> `JsonFilePersistence(data_dir="/your/path")`. See [Pitfalls](#pitfalls-避坑指南).

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

---

## Notes & Caveats

- **Early-stage (v0.1.0).** APIs and on-disk format may change between minor versions.
- **Single-process by design.** The FastAPI app keeps all state in one module-level
  `FUniver` instance (`univer/server/app.py`). Persistence is a **single JSON file** with
  no locking, so do **not** run multiple workers or multiple processes pointing at the same
  store — they will overwrite each other.
- **Formula engine is a limited subset**, not full Excel. Known semantics:
  - Empty cells are treated as `0` in arithmetic (Excel-like), not errors.
  - Type mismatches (e.g. text in arithmetic) and divide-by-zero return `None`
    (analogous to `#VALUE!` / `#DIV/0!`) instead of raising.
  - Syntax errors (unknown identifier, malformed expression) raise `FormulaSyntaxError`.
- **Slides is skeletal.** The Presentation/Slide/Shape model is a data container only —
  there is no real layout engine or rendering.
- **No `poetry.lock` is committed** (it is `.gitignore`d, per library convention). CI runs
  `poetry lock` before installing, so a fresh resolve happens there. A local/offline
  environment with no PyPI access must already have dependencies available.
- **CI check strictness:** `ruff check` and `ruff format --check` are **blocking**;
  `black --check` and `mypy` are currently `continue-on-error` (informational).

---

## Pitfalls (避坑指南)

| Symptom | Cause & Fix |
|---------|-------------|
| `ModuleNotFoundError: No module named 'univer'` | Package not installed and `src` not on the path. Run `poetry install` / `pip install -e .`, or set `PYTHONPATH=src`. (Tests don't need this.) |
| `poetry install` hangs / "All attempts to connect to pypi.org failed" | No network. Poetry must resolve deps from PyPI. Use an environment that already has the deps, or restore a network connection. |
| `pyproject.toml changed significantly since poetry.lock was last generated` | Stale lock. Run `poetry lock`. CI does this automatically before `poetry install`. |
| Data "disappears" after restart / not found | Check the **actual** store path — it's `src/.univer_data/store.json` in a dev checkout, **not** the project root. Set `data_dir` explicitly to pin it. |
| Two server instances clobber each other's data | Single-file JSON store with no locking. Run only one process/worker against a given store. |
| `PersistenceError: Corrupted state file ...` | `store.json` has invalid JSON (e.g. hand-edited or truncated). Restore a backup or delete the file to start fresh. |
| Formula unexpectedly returns `None` | By design: text in arithmetic, divide-by-zero, or unsupported operations yield `None`. Verify cell types before assuming a bug. |
| `ImportError` on `from univer import ...` but tests pass | You're importing outside the installed/path context. Tests inject `src` via pytest config; your script needs the package installed or `PYTHONPATH=src`. |
| Windows: `LF will be replaced by CRLF` warning | Line-ending normalization. The repo ships `.gitattributes` enforcing LF; set `git config core.autocrlf true` locally to silence it. |
| `black` not installed but CI expects it | Local dev sandbox may lack `black`. `ruff format` (line-length 100) is the authoritative, blocking formatter; `black` runs only where it's installed. |

