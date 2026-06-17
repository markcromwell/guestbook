"""Architecture contract tests — ARCHITECTURE.md must exist and stay canonical."""
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ARCHITECTURE = _REPO_ROOT / "ARCHITECTURE.md"

REQUIRED_SECTION_HEADINGS = [
    "file structure",
    "naming conventions",
    "module responsibilities",
    "key design decisions",
    "how to run tests",
]

REQUIRED_PATH_TOKENS = [
    "src/guestbook",
    "app.py",
    "storage.py",
    "templates",
]

REQUIRED_COMMAND_LINES = [
    "PYTHONPATH=src uvicorn guestbook.app:app --reload",
    "python -m pytest scripts/test_unit.py -x -q",
]

REQUIRED_DESIGN_DECISIONS = [
    "file-backed json",
    "validation",
    "newest",
    "sort",
]


@pytest.fixture(scope="module")
def architecture_text() -> str:
    assert _ARCHITECTURE.is_file(), "ARCHITECTURE.md must exist in the repository root"
    return _ARCHITECTURE.read_text(encoding="utf-8")


def test_architecture_file_exists():
    assert _ARCHITECTURE.is_file()


@pytest.mark.parametrize("heading", REQUIRED_SECTION_HEADINGS)
def test_required_section_headings(architecture_text: str, heading: str):
    assert heading in architecture_text.lower(), (
        f"ARCHITECTURE.md must contain section heading: {heading!r}"
    )


@pytest.mark.parametrize("token", REQUIRED_PATH_TOKENS)
def test_required_path_tokens(architecture_text: str, token: str):
    assert token in architecture_text, (
        f"ARCHITECTURE.md must document required path token: {token!r}"
    )


@pytest.mark.parametrize("command", REQUIRED_COMMAND_LINES)
def test_required_run_and_test_commands(architecture_text: str, command: str):
    assert command in architecture_text, (
        f"ARCHITECTURE.md must document required command: {command!r}"
    )


def test_design_decisions_cover_guestbook_contract(architecture_text: str):
    lowered = architecture_text.lower()
    for phrase in REQUIRED_DESIGN_DECISIONS:
        assert phrase in lowered, (
            f"Key design decisions must mention {phrase!r} "
            "(file-backed JSON, in-handler validation, newest-first sort-on-read)"
        )