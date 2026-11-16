# AI-Powered Travel & Weather Advisory Assistant

FastAPI + LangChain + Ollama (`llama3.2:3b`) + SQLite + Redis + Open-Meteo.

## Architecture

```
Employee ──► FastAPI ──► Stage 1: ChatOllama.bind_tools(...)  ──► tools ──► SQLite (trips)
                         (model picks tools; guard verifies          └────► Open-Meteo geocoding + forecast
                          facts came from tools, not guesses)
                     ──► Stage 2: prompt | ChatOllama | parser  ──► advisory (destination, weather, 3-4 tips)
                     ◄─► Redis: per-session history + active trip (TTL, isolated per session_id)
```

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI endpoints + Pydantic validation |
| `app/db.py`, `schema.sql`, `init_db.py` | SQLite schema, persistence, sample records |
| `app/weather.py` | Open-Meteo client; reports missing city / out-of-horizon dates / API failures |
| `app/tools.py` | LangChain tools: `get_trip_details`, `find_trip_by_destination`, `get_weather_forecast` |
| `app/assistant.py` | Two-stage LangChain pipeline (tool orchestration → advisory chain) |
| `app/memory.py` | Redis session memory (`travel:session:<id>:history` / `:context`) |
| `demo.py` | Runs all required scenarios, writes `evidence/demo_output.md` |

## Install

```bash
pip install -r requirements.txt
cp .env.example .env          # fill values (see defaults in app/config.py)
```

## Start services

```bash
ollama pull llama3.2:3b       # any tool-capable Ollama model works, e.g. qwen2.5:3b
ollama serve                  # if not already running
docker run -d --name redis -p 6379:6379 redis:7-alpine   # or: docker start <existing-redis>
python init_db.py             # create schema + sample trips (dates relative to today)
```

## Run FastAPI

```bash
uvicorn app.main:app --port 8000
```
Swagger UI: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | SQLite / Redis / Ollama status |
| POST | `/trips` | Create trip (validated, saved to SQLite) |
| GET | `/trips/{trip_id}` | Retrieve a saved trip |
| GET | `/trips?employee_id=EMP104` | List trips |
| POST | `/assistant/ask` | Ask the assistant (`session_id`, `question`, optional `trip_id`) |
| GET / DELETE | `/assistant/sessions/{session_id}` | Inspect / clear Redis session memory |

## Sample requests

```bash
curl -X POST localhost:8000/trips -H "Content-Type: application/json" \
  -d '{"employee_id":"EMP104","destination":"Jaipur","start_date":"2026-11-18","end_date":"2026-11-20","purpose":"Client meeting"}'

curl -X POST localhost:8000/assistant/ask -H "Content-Type: application/json" \
  -d '{"session_id":"sess-emp104","question":"What weather should I expect for my Jaipur trip?","trip_id":"TRP-XXXXXXXX"}'

curl -X POST localhost:8000/assistant/ask -H "Content-Type: application/json" \
  -d '{"session_id":"sess-emp104","question":"Should I pack an umbrella and light jacket?"}'
```
Use dates within the next 16 days (Open-Meteo forecast horizon).

## Test scenarios / evidence

Run `python demo.py` with the server up. It records every request and response in `evidence/demo_output.md`:

| Scenario | Result |
|---|---|
| New employee trip | `201`, saved in SQLite |
| Existing trip lookup | `200` from SQLite |
| Weather inquiry | Tools called (`tool_calls` shows `by: model` / `by: guard`), live forecast advice |
| Follow-up | Same session answers "umbrella?" without the destination (Redis context) |
| Session isolation | New session gets "no trip/destination identified" |
| Failures | `422` invalid dates / employee id, `404` unknown trip, out-of-horizon dates and unknown city reported, with no invented weather |

## Design notes
- **No fabricated weather:** the advisory prompt only receives tool output. Any tool error (city not found, dates beyond the 16-day horizon, HTTP failure) reaches the model as an explicit `error`, and the response also includes `weather_available` / `weather_error` fields.
- **Tool orchestration with a guard:** a 3B model sometimes skips a tool or passes the wrong arguments. After the model's tool loop, a guard checks that the trip came from SQLite and that the weather was fetched for the trip's real destination and dates. If not, the guard calls the tool itself. `tool_calls` in the response shows who made each call.
- **Memory:** Redis keeps the last `SESSION_MAX_MESSAGES` messages and the active trip per `session_id`, with a TTL. Each session uses its own keys, so sessions are isolated.

Weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0, non-commercial free tier).
