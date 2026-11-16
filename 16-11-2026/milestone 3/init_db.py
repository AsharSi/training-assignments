"""Create the SQLite schema and insert sample trips (dates relative to today so they stay in the forecast window)."""
from datetime import date, timedelta

from app import db

SAMPLES = [
    ("EMP104", "Jaipur", 3, 5, "Client meeting"),
    ("EMP205", "Mumbai", 2, 4, "Quarterly business review"),
    ("EMP310", "London", 6, 9, "Partner workshop"),
    ("EMP411", "Bengaluru", 40, 42, "Conference (beyond forecast horizon - for failure demo)"),
]

if __name__ == "__main__":
    db.init_db()
    today = date.today()
    for emp, city, s, e, purpose in SAMPLES:
        t = db.create_trip(emp, city, (today + timedelta(days=s)).isoformat(),
                           (today + timedelta(days=e)).isoformat(), purpose)
        print(t)
