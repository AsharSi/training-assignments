# Library AI Agent

An AI library assistant. The model picks one of two Python tools, `search_books` or `reserve_book`. It runs on **free OpenRouter models** through the OpenAI SDK's function calling.

## Setup
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Put your free key from https://openrouter.ai/keys in `.env` as `OPENROUTER_API_KEY`.
`OPENROUTER_MODEL` takes a comma-separated list of free models. If one is rate-limited, the agent moves on to the next.

## Run
```
python agent.py        # interactive agent
python test_tools.py   # offline tool tests (no API key needed)
```

## Test scenarios
1. Find books related to Python programming. → `search_books`
2. Is Python Crash Course available? → `search_books`
3. Reserve Python Crash Course for Ahmed. → `search_books` → `reserve_book` (asks y/n before saving)
4. Show me books related to artificial intelligence. → `search_books`
5. Reserve a book that has no available copies. → `reserve_book` refuses (books 104 and 106 have 0 copies)

The agent prints `[AGENT SELECTED TOOL]` in the terminal each time it picks a tool. A reservation is written to `reservations.json`, and `available_copies` goes down, only after you answer `y`.

## Web UI
The React UI in `../library-agent-ui` talks to `server.py`, a FastAPI wrapper around the same agent loop. In the UI, the y/n reservation prompt shows up as **Confirm / Decline** buttons.
```
# terminal 1 (backend)
cd Library_AI_Agent
.venv\Scripts\activate
uvicorn server:app --reload --port 8000

# terminal 2 (frontend)
cd library-agent-ui
npm run dev            # open http://localhost:5173
```
