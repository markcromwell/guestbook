# GUESTBOOK Architecture

Canonical architecture contract for the guestbook application. All specs and
implementation work must follow the paths, naming rules, and design decisions
documented here.

## File structure

All application code lives under the `src/guestbook` package:

```
.
├── ARCHITECTURE.md
├── data/
│   └── guestbook.json          # persisted entries (created at runtime)
├── src/
│   └── guestbook/
│       ├── __init__.py
│       ├── app.py                # HTTP handler layer
│       ├── storage.py            # JSON persistence layer
│       └── templates/
│           └── index.html        # template layer (form + entry list)
├── scripts/
│   ├── test_unit.py              # smoke tests
│   └── tests/
│       └── test_architecture_contract.py
├── main.py                       # thin entrypoint (imports guestbook.app)
└── requirements.txt
```

- **Package root:** `src/guestbook`
- **HTTP handler:** `src/guestbook/app.py`
- **Persistence:** `src/guestbook/storage.py`
- **Templates:** `src/guestbook/templates/`
- **JSON data file:** `data/guestbook.json`

## Naming conventions

| Kind | Convention | Example |
|------|------------|---------|
| Files | `snake_case.py` | `storage.py`, `app.py` |
| Modules | `snake_case` package and module names under `src/guestbook` | `guestbook.storage` |
| Classes | `PascalCase` | `GuestbookStorage`, `Entry` |
| Functions | `snake_case` | `load_entries`, `save_entry` |
| Template files | `snake_case.html` in `templates/` | `index.html` |
| Route handlers | `snake_case` functions in `app.py` | `show_form`, `submit_entry` |

Do not place guestbook logic outside `src/guestbook` except for the thin
`main.py` entrypoint and test scripts under `scripts/`.

## Module responsibilities

### `src/guestbook/app.py` — HTTP handler layer

- Defines the FastAPI application and route handlers.
- Renders templates for the form page and entry list.
- Validates incoming requests (required fields, length limits, sanitization)
  inside the handler before calling persistence.
- Returns appropriate HTTP status codes for validation failures.
- Delegates all read/write of guestbook data to `storage.py`.

### `src/guestbook/storage.py` — JSON persistence layer

- Reads and writes the guestbook entry list to `data/guestbook.json`.
- Ensures the `data/` directory exists before writing.
- Serializes and deserializes entries as JSON.
- Sorts entries newest-first on every read (by timestamp or monotonic id).
- Contains no HTTP or template logic.

### `src/guestbook/templates/` — template layer

- Holds HTML templates rendered by the handler layer.
- Contains presentation markup only; no business logic or direct file I/O.

## Key design decisions

1. **Minimal Python web stack.** FastAPI + Uvicorn in a single process serves
   both the form page and persistence. No external database or message broker.

2. **File-backed JSON persistence.** Entries are stored in `data/guestbook.json`
   so data survives process restarts without external services. One JSON file,
   one writer process.

3. **Layer separation.** HTTP handling (`app.py`), persistence (`storage.py`),
   and presentation (`templates/`) are separate modules with clear boundaries.
   The handler calls storage; storage never imports templates or FastAPI.

4. **Validation in the request handler.** All input validation runs inside
   `app.py` route handlers before entries are passed to `storage.py`. Storage
   assumes already-validated data.

5. **Newest entries first.** The guestbook displays the most recent entries at
   the top. Ordering is applied on read in `storage.py` by sorting entries
   (descending by timestamp or id), not by prepending on write.

## How to run tests

Install dependencies once:

```bash
pip install -r requirements.txt
```

Run the development server:

```bash
PYTHONPATH=src uvicorn guestbook.app:app --reload
```

Run the smoke test suite:

```bash
python -m pytest scripts/test_unit.py -x -q
```

Run architecture contract tests:

```bash
python -m pytest scripts/tests/test_architecture_contract.py -x -q
```