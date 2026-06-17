"""Unit tests for GUESTBOOK."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

import guestbook.app as guestbook_app_module
from guestbook.storage import GuestbookStorage
from main import app


@pytest.fixture
def guestbook_storage(tmp_path: Path) -> GuestbookStorage:
    return GuestbookStorage(data_file=tmp_path / "guestbook.json")


@pytest.fixture
def client(guestbook_storage: GuestbookStorage, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(guestbook_app_module, "storage", guestbook_storage)
    return TestClient(guestbook_app_module.app)


def test_health():
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_storage_load_entries_empty_when_no_file(guestbook_storage: GuestbookStorage):
    assert guestbook_storage.load_entries() == []


def test_storage_save_and_reload_round_trip(guestbook_storage: GuestbookStorage):
    saved = guestbook_storage.save_entry("Ada", "Hello, guestbook!")
    reloaded = GuestbookStorage(data_file=guestbook_storage._data_file)

    entries = reloaded.load_entries()
    assert len(entries) == 1
    assert entries[0]["id"] == saved["id"]
    assert entries[0]["name"] == "Ada"
    assert entries[0]["message"] == "Hello, guestbook!"
    assert entries[0]["created_at"] == saved["created_at"]


def test_storage_load_entries_newest_first(guestbook_storage: GuestbookStorage):
    first = guestbook_storage.save_entry("First", "One")
    second = guestbook_storage.save_entry("Second", "Two")
    third = guestbook_storage.save_entry("Third", "Three")

    entries = guestbook_storage.load_entries()
    assert [entry["id"] for entry in entries] == [
        third["id"],
        second["id"],
        first["id"],
    ]


def test_storage_saved_entry_has_required_fields(guestbook_storage: GuestbookStorage):
    entry = guestbook_storage.save_entry("Grace", "Testing fields")

    assert set(entry.keys()) == {"id", "name", "message", "created_at"}
    assert isinstance(entry["id"], int)
    assert entry["name"] == "Grace"
    assert entry["message"] == "Testing fields"
    assert isinstance(entry["created_at"], str)
    assert "T" in entry["created_at"]


def test_show_form_renders_empty_list(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Guestbook" in resp.text
    assert 'name="name"' in resp.text
    assert 'name="message"' in resp.text


def test_submit_entry_redirects_and_shows_at_top(client: TestClient):
    resp = client.post(
        "/",
        data={"name": "Test User", "message": "Integration test entry"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"

    client.post(
        "/",
        data={"name": "Older User", "message": "Older entry message"},
        follow_redirects=True,
    )
    client.post(
        "/",
        data={"name": "Newest User", "message": "Newest entry message"},
        follow_redirects=True,
    )

    page = client.get("/")
    assert page.status_code == 200
    text = page.text
    newest_pos = text.index("Newest entry message")
    older_pos = text.index("Older entry message")
    first_pos = text.index("Integration test entry")
    assert newest_pos < older_pos
    assert newest_pos < first_pos


def test_submit_entry_rejects_name_over_50_chars(
    client: TestClient, guestbook_storage: GuestbookStorage
):
    long_name = "x" * 51
    resp = client.post("/", data={"name": long_name, "message": "Valid message"})
    assert resp.status_code == 400
    assert "50 characters" in resp.text
    assert guestbook_storage.load_entries() == []


def test_submit_entry_rejects_message_over_500_chars(
    client: TestClient, guestbook_storage: GuestbookStorage
):
    long_message = "y" * 501
    resp = client.post("/", data={"name": "Valid Name", "message": long_message})
    assert resp.status_code == 400
    assert "500 characters" in resp.text
    assert guestbook_storage.load_entries() == []