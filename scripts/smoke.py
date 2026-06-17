#!/usr/bin/env python3
"""Smoke test for the guestbook server using stdlib only."""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOST = "127.0.0.1"
PORT = 8765
BASE_URL = f"http://{HOST}:{PORT}"
HEALTH_URL = f"{BASE_URL}/health"
FORM_URL = BASE_URL
SAMPLE_NAME = "Smoke Test"
SAMPLE_MESSAGE = "Hello from scripts/smoke.py"
OLDER_NAME = "Earlier Visitor"
OLDER_MESSAGE = "Earlier smoke entry"


def wait_for_health(timeout_seconds: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    return False


def post_entry(name: str, message: str) -> int:
    body = urllib.parse.urlencode({"name": name, "message": message}).encode("utf-8")
    request = urllib.request.Request(
        FORM_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=5.0) as response:
        return response.status


def fetch_home_page() -> str:
    with urllib.request.urlopen(FORM_URL, timeout=5.0) as response:
        return response.read().decode("utf-8")


def main() -> int:
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "guestbook.app:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print(f"Guestbook URL: {FORM_URL}")
    print("Waiting for server health check...")

    try:
        if not wait_for_health():
            print("ERROR: Server did not become healthy in time.", file=sys.stderr)
            return 1

        print(f"GET {HEALTH_URL} -> OK")

        for entry_name, entry_message in (
            (OLDER_NAME, OLDER_MESSAGE),
            (SAMPLE_NAME, SAMPLE_MESSAGE),
        ):
            status = post_entry(entry_name, entry_message)
            if status not in {200, 303}:
                print(f"ERROR: POST / returned unexpected status {status}.", file=sys.stderr)
                return 1

        html = fetch_home_page()
        print(f"GET {FORM_URL} -> {len(html)} bytes")

        if SAMPLE_MESSAGE not in html:
            print("ERROR: Sample message not found in rendered page.", file=sys.stderr)
            return 1
        if SAMPLE_NAME not in html:
            print("ERROR: Sample name not found in rendered page.", file=sys.stderr)
            return 1

        sample_pos = html.index(SAMPLE_MESSAGE)
        older_pos = html.index(OLDER_MESSAGE)
        if sample_pos > older_pos:
            print(
                "ERROR: Sample entry does not appear at the top of the list.",
                file=sys.stderr,
            )
            return 1

        print("Smoke check passed: sample entry is visible at the top of the list.")
        print(f"Open {FORM_URL} in a browser to interact with the guestbook.")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())