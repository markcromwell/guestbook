"""JSON persistence layer for guestbook entries."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class GuestbookStorage:
    """File-backed storage for guestbook entries."""

    def __init__(self, data_file: Path | str | None = None) -> None:
        if data_file is None:
            self._data_file = Path("data/guestbook.json")
        else:
            self._data_file = Path(data_file)
        self._data_dir = self._data_file.parent
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def load_entries(self) -> list[dict[str, Any]]:
        """Return entries from disk, sorted newest-first by id."""
        raw_entries = self._read_raw_entries()
        return sorted(raw_entries, key=lambda entry: entry["id"], reverse=True)

    def save_entry(self, name: str, message: str) -> dict[str, Any]:
        """Append an entry and atomically persist to disk."""
        entries = self._read_raw_entries()
        next_id = max((entry["id"] for entry in entries), default=0) + 1
        entry = {
            "id": next_id,
            "name": name,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        entries.append(entry)
        self._write_entries(entries)
        return entry

    def _read_raw_entries(self) -> list[dict[str, Any]]:
        if not self._data_file.is_file():
            return []

        text = self._data_file.read_text(encoding="utf-8").strip()
        if not text:
            return []

        data = json.loads(text)
        if not isinstance(data, list):
            return []
        return data

    def _write_entries(self, entries: list[dict[str, Any]]) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(entries, indent=2)
        fd, temp_path = tempfile.mkstemp(dir=self._data_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self._data_file)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise