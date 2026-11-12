"""Offline tests for the tools (no API key needed). Run: python test_tools.py"""

import json
import shutil
import tempfile
from pathlib import Path

import tools


def run() -> None:
    tmp = Path(tempfile.mkdtemp())
    shutil.copy(tools.BOOKS_PATH, tmp / "books.json")
    (tmp / "reservations.json").write_text("[]", encoding="utf-8")
    tools.BOOKS_PATH = tmp / "books.json"
    tools.RESERVATIONS_PATH = tmp / "reservations.json"

    # Scenario 1 / 2 / 4: searching
    python = tools.search_books("Python programming")
    assert python["results"][0]["id"] in {101, 102}, python
    crash = tools.search_books("Python Crash Course")
    assert crash["results"][0]["id"] == 101 and crash["results"][0]["is_available"]
    ai = tools.search_books("artificial intelligence")
    assert {103, 104, 106} <= {b["id"] for b in ai["results"]}, ai
    assert tools.search_books("cooking recipes")["match_count"] == 0

    # Declined reservation -> nothing saved
    r = tools.reserve_book(101, "Ahmed", confirm=lambda _: "n")
    assert r["reserved"] is False
    assert json.loads(tools.RESERVATIONS_PATH.read_text()) == []

    # Scenario 3: approved reservation -> saved, copies reduced
    r = tools.reserve_book(101, "Ahmed", confirm=lambda _: "y")
    assert r["reserved"] and r["remaining_copies"] == 2, r
    assert len(json.loads(tools.RESERVATIONS_PATH.read_text())) == 1

    # Scenario 5: no copies -> refused without asking
    def never(_):
        raise AssertionError("should not ask for confirmation")
    r = tools.reserve_book(104, "Sara", confirm=never)
    assert r["reserved"] is False and "no available copies" in r["reason"]

    # Unknown book
    assert tools.reserve_book(999, "Sara", confirm=never)["reserved"] is False

    shutil.rmtree(tmp)
    print("All tool tests passed.")


if __name__ == "__main__":
    run()
