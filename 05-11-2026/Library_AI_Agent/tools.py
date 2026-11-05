"""Local Python tools used by the Library AI Agent (plain JSON files, no database)."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
BOOKS_PATH = ROOT / "books.json"
RESERVATIONS_PATH = ROOT / "reservations.json"

STOP_WORDS = {
    "the", "a", "an", "is", "are", "of", "to", "and", "or", "for", "with",
    "on", "in", "about", "book", "books", "related", "find", "show", "me",
    "any", "some", "available", "do", "you", "have",
}


def _load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: list) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOP_WORDS


def search_books(keyword: str) -> dict:
    """Find books whose title, author or category match the keyword(s).

    Books are ranked by how many keyword terms they match (title matches count
    double). An empty keyword returns the whole catalogue.
    """
    books = _load(BOOKS_PATH)
    terms = _words(keyword)
    phrase = keyword.strip().lower()
    ranked = []

    for book in books:
        title, author, category = (book["title"].lower(), book["author"].lower(),
                                   book["category"].lower())
        if not terms:
            score = 1
        else:
            score = (2 * len(terms & _words(title))
                     + len(terms & _words(author))
                     + len(terms & _words(category)))
            if phrase and phrase in f"{title} {author} {category}":
                score += 3  # exact phrase bonus
        if score > 0:
            ranked.append((score, book))

    ranked.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    results = [
        {**book, "is_available": book["available_copies"] > 0}
        for _, book in ranked
    ]
    return {
        "keyword": keyword,
        "match_count": len(results),
        "results": results,
        "message": "Matching books listed." if results
        else "No matching books found. Do not invent books.",
    }


def reserve_book(
    book_id: int,
    customer_name: str,
    confirm: Callable[[str], str] = input,
) -> dict:
    """Reserve one copy of a book after explicit confirmation from the user."""
    customer_name = customer_name.strip()
    if not customer_name:
        return {"reserved": False, "reason": "Customer name is missing."}

    books = _load(BOOKS_PATH)
    book = next((b for b in books if b["id"] == int(book_id)), None)
    if book is None:
        return {"reserved": False, "reason": f"No book found with ID {book_id}."}
    if book["available_copies"] <= 0:
        return {
            "reserved": False,
            "reason": f"'{book['title']}' has no available copies.",
            "book": book,
        }

    print("\n--- RESERVATION APPROVAL REQUIRED ---")
    print(f"Book     : {book['title']} (ID {book['id']}) by {book['author']}")
    print(f"Customer : {customer_name}")
    print(f"Copies   : {book['available_copies']} available")
    answer = confirm("Confirm this reservation? (y/n): ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Reservation was NOT created.")
        return {"reserved": False, "reason": "User declined the reservation."}

    reservations = _load(RESERVATIONS_PATH)
    next_id = max([int(r["reservation_id"].split("-")[-1]) for r in reservations]
                  or [0]) + 1
    reservation = {
        "reservation_id": f"RES-{next_id:04d}",
        "book_id": book["id"],
        "title": book["title"],
        "customer_name": customer_name,
        "reserved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    reservations.append(reservation)
    book["available_copies"] -= 1

    _save(RESERVATIONS_PATH, reservations)
    _save(BOOKS_PATH, books)
    return {
        "reserved": True,
        "reservation": reservation,
        "remaining_copies": book["available_copies"],
    }
