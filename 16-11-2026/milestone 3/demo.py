"""Runs the required test scenarios against the running API and writes evidence/demo_output.md."""
import json
from datetime import date, timedelta
from pathlib import Path

import httpx

BASE = "http://localhost:8000"
c = httpx.Client(base_url=BASE, timeout=300)
out: list[str] = ["# Demo evidence\n", f"Run date: {date.today()}\n"]


def log(title: str, method: str, path: str, body=None, resp: httpx.Response | None = None):
    out.append(f"\n## {title}\n\n`{method} {path}`\n")
    if body is not None:
        out.append("Request:\n```json\n" + json.dumps(body, indent=2) + "\n```\n")
    out.append(f"Response ({resp.status_code}):\n```json\n" + json.dumps(resp.json(), indent=2, ensure_ascii=False)
               + "\n```\n")
    print(f"\n=== {title} [{resp.status_code}] ===")
    data = resp.json()
    print(data.get("answer", json.dumps(data, indent=1)[:800]) if isinstance(data, dict) else data)


def call(title, method, path, body=None):
    r = c.request(method, path, json=body)
    log(title, method, path, body, r)
    return r


today = date.today()
call("0. Health check", "GET", "/health")

# 1. New employee trip
trip_body = {"employee_id": "EMP104", "destination": "Jaipur",
             "start_date": (today + timedelta(days=2)).isoformat(),
             "end_date": (today + timedelta(days=4)).isoformat(), "purpose": "Client meeting"}
trip = call("1. New employee trip (saved to SQLite)", "POST", "/trips", trip_body).json()
tid = trip["trip_id"]

# 2. Existing trip lookup
call("2. Existing trip lookup (from SQLite)", "GET", f"/trips/{tid}")

# 3. Weather inquiry
c.delete("/assistant/sessions/sess-emp104")
c.delete("/assistant/sessions/sess-emp310")
call("3. Weather inquiry (LangChain tools + live Open-Meteo forecast)", "POST", "/assistant/ask",
     {"session_id": "sess-emp104", "question": "What weather should I expect for my Jaipur trip?", "trip_id": tid})

# 4. Follow-up using Redis memory (no destination, no trip_id)
call("4. Follow-up question (Redis session memory)", "POST", "/assistant/ask",
     {"session_id": "sess-emp104", "question": "Should I pack an umbrella and light jacket?"})
call("4b. Another follow-up", "POST", "/assistant/ask",
     {"session_id": "sess-emp104", "question": "Will I need an umbrella there?"})
call("4c. Session memory stored in Redis", "GET", "/assistant/sessions/sess-emp104")

# 5. Session isolation: a different session has no knowledge of Jaipur
call("5. Session isolation (new session, same follow-up)", "POST", "/assistant/ask",
     {"session_id": "sess-other", "question": "Will I need an umbrella there?"})
c.delete("/assistant/sessions/sess-other")

# 6. Failure / invalid input
call("6a. Invalid dates (end before start) -> 422", "POST", "/trips",
     {**trip_body, "start_date": (today + timedelta(days=5)).isoformat(),
      "end_date": (today + timedelta(days=1)).isoformat()})
call("6b. Invalid employee id -> 422", "POST", "/trips", {**trip_body, "employee_id": "104"})
call("6c. Unknown trip ID -> 404", "GET", "/trips/TRP-DOESNOTEXIST")
far = c.post("/trips", json={"employee_id": "EMP411", "destination": "Bengaluru",
                             "start_date": (today + timedelta(days=40)).isoformat(),
                             "end_date": (today + timedelta(days=42)).isoformat(),
                             "purpose": "Conference"}).json()
call("6d. Date beyond forecast horizon -> no fabricated weather", "POST", "/assistant/ask",
     {"session_id": "sess-emp411", "question": "What's the weather going to be like on my trip?",
      "trip_id": far["trip_id"]})
bad = c.post("/trips", json={"employee_id": "EMP999", "destination": "Xyzzyqwerty",
                             "start_date": (today + timedelta(days=2)).isoformat(),
                             "end_date": (today + timedelta(days=3)).isoformat(),
                             "purpose": "Unknown site visit"}).json()
call("6e. Unknown destination -> geocoding failure reported", "POST", "/assistant/ask",
     {"session_id": "sess-emp999", "question": "What weather should I expect?", "trip_id": bad["trip_id"]})
for s in ("sess-emp411", "sess-emp999"):
    c.delete(f"/assistant/sessions/{s}")

Path(__file__).parent.joinpath("evidence", "demo_output.md").write_text("".join(out), encoding="utf-8")
print("\nEvidence written to evidence/demo_output.md")
