CREATE TABLE IF NOT EXISTS trips (
    trip_id     TEXT PRIMARY KEY,               -- e.g. TRP-1A2B3C4D
    employee_id TEXT NOT NULL,
    destination TEXT NOT NULL,
    start_date  TEXT NOT NULL,                  -- ISO YYYY-MM-DD
    end_date    TEXT NOT NULL,
    purpose     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'PLANNED' CHECK (status IN ('PLANNED','CONFIRMED','CANCELLED','COMPLETED')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (end_date >= start_date)
);
CREATE INDEX IF NOT EXISTS idx_trips_employee ON trips(employee_id);
