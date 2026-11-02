# ai-feedback — Frontend

React + TypeScript (Vite) UI for evaluating the RAG pipeline in [`../Simple_Python_RAG_PyCharm`](../Simple_Python_RAG_PyCharm/README.md).

It does what `10_log_ai_feedback.py` does, but in the browser: ask questions against many models at once, rate each answer, browse the log, and compare accuracy and latency per model. All data lives in the backend's `rag_feedback.csv`.

## Prerequisites

- **Node.js 20+** and npm
- The backend set up and running (see below)

## Run

1. **Backend** (from `Simple_Python_RAG_PyCharm/`; first time: install requirements, set `.env`, and run `05_store_in_chroma.py`):

   ```powershell
   .venv\Scripts\python.exe -m uvicorn feedback_api:app --reload --port 8000
   ```

2. **Frontend** (from `ai-feedback/`):

   ```powershell
   npm install
   npm run dev
   ```

   Open http://localhost:5173. The Vite dev server proxies `/api/*` to `http://127.0.0.1:8000` (see `vite.config.ts`).

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the dev server with hot reload |
| `npm run build` | Type-check (`tsc -b`) and build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Lint with oxlint |

> The `/api` proxy only exists in `dev` and `preview`. If you host `dist/` elsewhere, serve it behind the same origin as the backend or add a proxy, and add that origin to the CORS list in `feedback_api.py`.

## Tabs

- **Ask & Rate** — pick models × questions (× repeats) and run them in sequence. Each call is written to the CSV immediately as `Not rated`; rating it Correct / Incorrect / Skip updates that row. Run results can be exported to CSV.
- **Logs** — every CSV row, newest first, with filters and search. Click a row to read the answer or change its rating. The filtered log can be exported to CSV.
- **Analysis** — per model: accuracy, p50/p95 latency, "not found" rate, error rate and average retrieval distance, plus a question × model accuracy heatmap.
- **Library** — saved models (OpenRouter slugs, e.g. `openai/gpt-4o-mini`) and questions. Import them from the log, or export/import as JSON.

Open `/#logs`, `/#analysis` or `/#library` to jump straight to a tab.

Rows logged by the CLI script and by the UI go into the same CSV, so both appear here.

## Project structure

```
ai-feedback/
├── index.html
├── vite.config.ts           # React plugin + /api proxy to port 8000
├── public/                  # favicon, icons
└── src/
    ├── main.tsx             # Entry point
    ├── App.tsx              # Tabs, health check, log loading
    ├── api.ts               # fetch wrapper for the backend endpoints
    ├── types.ts             # LogRow, AskResult, Health, SavedModel, ...
    ├── stats.ts             # Accuracy / percentile helpers for Analysis
    ├── csv.ts               # CSV export (Excel-friendly, UTF-8 BOM)
    ├── storage.ts           # useLocalStorage hook ("aiFeedback.*" keys)
    ├── index.css
    └── components/
        ├── RunPanel.tsx         # Ask & Rate
        ├── ResultsTable.tsx     # Results of a run
        ├── FeedbackButtons.tsx  # Correct / Incorrect / Skip
        ├── LogsPanel.tsx        # Logs
        ├── AnalysisPanel.tsx    # Analysis
        └── LibraryPanel.tsx     # Library
```

## Backend API used

| Method | Path | Used for |
|---|---|---|
| `GET` | `/api/health` | Default model and whether an API key is set |
| `POST` | `/api/ask` | Run one question against one model (`{ question, model, top_k }`) |
| `GET` | `/api/logs` | Load all log rows |
| `PATCH` | `/api/logs/{index}` | Save a rating (`{ feedback }`) |

Full details are in the backend README.

## Data storage

- **Answers and ratings**: `rag_feedback.csv` on the backend.
- **Saved models, questions and the last open tab**: browser `localStorage` (keys prefixed `aiFeedback.`). Use Library → export to back them up or move them to another browser.

## Troubleshooting

- **"Backend not reachable. Is feedback_api.py running on port 8000?"** — start uvicorn as shown above.
- **"Add OPENAI_API_KEY to the .env file."** — create `Simple_Python_RAG_PyCharm/.env` from `.env.example` and restart the backend.
- **"No indexed collection"** — run `05_store_in_chroma.py` in the backend folder.
- **502 errors for one model** — the model slug is wrong or rate-limited; check it on openrouter.ai.
