"""SQLite persistence for trips."""
import sqlite3
import uuid
from contextlib import contextmanager

from .config import BASE_DIR, DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    schema = (BASE_DIR / "schema.sql").read_text()
    with get_conn() as conn:
        conn.executescript(schema)


def create_trip(employee_id: str, destination: str, start_date: str, end_date: str,
                purpose: str, status: str = "PLANNED") -> dict:
    trip_id = f"TRP-{uuid.uuid4().hex[:8].upper()}"
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO trips (trip_id, employee_id, destination, start_date, end_date, purpose, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trip_id, employee_id, destination, start_date, end_date, purpose, status),
        )
    return get_trip(trip_id)


def get_trip(trip_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM trips WHERE trip_id = ?", (trip_id.strip().upper(),)).fetchone()
    return dict(row) if row else None


def list_trips(employee_id: str | None = None) -> list[dict]:
    with get_conn() as conn:
        if employee_id:
            rows = conn.execute("SELECT * FROM trips WHERE employee_id = ? ORDER BY start_date",
                                (employee_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM trips ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def find_trip_by_destination(destination: str, employee_id: str | None = None) -> dict | None:
    q = "SELECT * FROM trips WHERE lower(destination) = lower(?)"
    args: list = [destination.strip()]
    if employee_id:
        q += " AND employee_id = ?"
        args.append(employee_id)
    q += " AND status != 'CANCELLED' ORDER BY start_date LIMIT 1"
    with get_conn() as conn:
        row = conn.execute(q, args).fetchone()
    return dict(row) if row else None
