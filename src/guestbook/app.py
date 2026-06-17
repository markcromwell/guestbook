"""HTTP handler layer for the guestbook application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from guestbook.storage import GuestbookStorage

MAX_NAME_LENGTH = 50
MAX_MESSAGE_LENGTH = 500

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

app = FastAPI(title="GUESTBOOK", version="0.1.0")
storage = GuestbookStorage()


def _render_index(
    request: Request,
    *,
    error: str | None = None,
    name: str = "",
    message: str = "",
    status_code: int = 200,
) -> HTMLResponse:
    entries = storage.load_entries()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "entries": entries,
            "error": error,
            "name": name,
            "message": message,
        },
        status_code=status_code,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "guestbook"}


@app.get("/", response_class=HTMLResponse)
def show_form(request: Request) -> HTMLResponse:
    return _render_index(request)


@app.post("/", response_model=None)
def submit_entry(
    request: Request,
    name: str = Form(""),
    message: str = Form(""),
):
    name = name.strip()
    message = message.strip()

    if not name:
        return _render_index(
            request,
            error="Name is required.",
            name=name,
            message=message,
            status_code=400,
        )
    if not message:
        return _render_index(
            request,
            error="Message is required.",
            name=name,
            message=message,
            status_code=400,
        )
    if len(name) > MAX_NAME_LENGTH:
        return _render_index(
            request,
            error=f"Name must be at most {MAX_NAME_LENGTH} characters.",
            name=name,
            message=message,
            status_code=400,
        )
    if len(message) > MAX_MESSAGE_LENGTH:
        return _render_index(
            request,
            error=f"Message must be at most {MAX_MESSAGE_LENGTH} characters.",
            name=name,
            message=message,
            status_code=400,
        )

    storage.save_entry(name, message)
    return RedirectResponse(url="/", status_code=303)