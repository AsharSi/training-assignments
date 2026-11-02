# ai-feedback

React UI for the RAG feedback log (`../Simple_Python_RAG_PyCharm/rag_feedback.csv`).
It does the same thing as `10_log_ai_feedback.py`, but in the browser, and lets you
compare many models and questions at once.

## Run

1. Backend (from `Simple_Python_RAG_PyCharm/`):

   ```
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   .venv\Scripts\python.exe -m uvicorn feedback_api:app --reload --port 8000
   ```

2. Frontend (from `ai-feedback/`):

   ```
   npm install
   npm run dev
   ```

   Open http://localhost:5173. Vite forwards `/api/*` to port 8000.

## Tabs

- **Ask & Rate**: pick models × questions (× repeats), run them in sequence, and rate each answer Correct / Incorrect / Skip.
  Every call goes into the CSV right away as "Not rated", and your rating updates that row.
- **Logs**: all CSV rows, newest first, with filters and search. Click a row to read the answer or change its rating.
- **Analysis**: accuracy, p50/p95 latency, the "not found" rate and average retrieval distance per model,
  plus a question × model accuracy heatmap.
- **Library**: models and questions saved in localStorage. You can import them from the log and export/import them as JSON.

Rows from the CLI script and from the UI go into the same CSV, so both show up here.
Open `/#analysis`, `/#logs` or `/#library` to jump straight to a tab.
