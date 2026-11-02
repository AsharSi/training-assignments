# Simple Python RAG — Backend

A small, **fully Python-driven** RAG (Retrieval-Augmented Generation) project built around a fictional employee guide (`BrightPath_Employee_Guide.txt`).

- **Lessons 1–10** are plain Python scripts you run one at a time in PyCharm. No LangChain, Docker, or external vector database.
- **`feedback_api.py`** is an optional FastAPI server that exposes the same RAG + feedback logging over HTTP for the [`ai-feedback`](../ai-feedback/README.md) React frontend.

## Folder layout

```
Simple_Python_RAG_PyCharm/
├── Documents/
│   └── BrightPath_Employee_Guide.txt    # Source document
├── chroma_db/                           # Local persistent vector DB (created by step 5, git-ignored)
├── rag_core.py                          # Shared read / chunk / embed / search functions
├── 01_read_document.py ... 10_log_ai_feedback.py   # Lesson scripts
├── feedback_api.py                      # FastAPI backend for the ai-feedback UI
├── benchmark_results.csv                # Output of step 8
├── experiment_results.csv               # Output of step 9
├── rag_feedback.csv                     # Feedback log (step 10 + feedback_api.py)
├── Arch Diagram.png, Cosine Similarity.png
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

Requires **Python 3.10+**.

```powershell
cd Simple_Python_RAG_PyCharm
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # then edit .env
```

`.env` settings (only needed for steps 7, 10 and `feedback_api.py`):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | API key. Calls go to **OpenRouter** (`https://openrouter.ai/api/v1`), so use an OpenRouter key. |
| `OPENAI_MODEL` | Optional default model as an OpenRouter slug, e.g. `openai/gpt-4o-mini`. Defaults to `nvidia/nemotron-3-ultra-550b-a55b:free`. |

In PyCharm, set the project interpreter to `.venv\Scripts\python.exe`.

## Lessons

Run the scripts in order (right-click → Run, or `.venv\Scripts\python.exe 01_read_document.py`).

| Script | What to observe | What is happening |
|---|---|---|
| `01_read_document.py` | Text loaded from `Documents/` | Python opens a local `.txt` document |
| `02_tokenization.py` | Tokens, token IDs, token count | Text is split into tokens for inspection |
| `03_embeddings.py` | Vector length, sample values, similarity scores | A **local** embedding model turns strings into vectors |
| `04_chunking.py` | Overlapping chunks | Document split into **180-token chunks** with 35-token overlap |
| `05_store_in_chroma.py` | Record count and DB path | Each chunk is embedded and stored (ID, vector, text) in local ChromaDB |
| `06_search_chroma.py` | Top 3 chunks and distances | Question is embedded and nearest vectors retrieved. **No AI call** |
| `07_ask_ai.py` | Retrieved IDs and grounded answer | Retrieved chunks + question sent to the model; answer cites chunk IDs |
| `08_benchmark_retrieval.py` | PASS/FAIL per test question, overall score | Checks the expected evidence appears in the top 3 chunks → `benchmark_results.csv` |
| `09_compare_chunk_size.py` | Chunk count, score, query time per config | Builds a second 100/35 index and compares it with the 180/35 baseline → `experiment_results.csv` |
| `10_log_ai_feedback.py` | Answer, timing, y/n/skip prompt | Runs RAG, then logs the answer, chunks, distance, latency and your rating → `rag_feedback.csv` |

Steps 1–6, 8 and 9 run fully locally and are free. Steps 7 and 10 need an API key.

### What runs where?

- Source document, `tiktoken` tokenization, embeddings, ChromaDB and vector search all run **locally**.
- Embeddings use Chroma's `all-MiniLM-L6-v2` model (384 dimensions). It is downloaded and cached on first use.
- Only the **retrieved chunks and the question** are sent to the AI, never the whole document.
- `tiktoken`'s `cl100k_base` is used for chunking/visualisation; MiniLM has its own internal tokenizer, so token counts differ.

## Feedback API (`feedback_api.py`)

Backend for the `ai-feedback` React app. It uses the same retrieval and prompt as step 10 and writes to the same `rag_feedback.csv`, so rows from the CLI and the UI show up together.

**Prerequisite:** run `05_store_in_chroma.py` once so `chroma_db/` exists.

```powershell
.venv\Scripts\python.exe -m uvicorn feedback_api:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs. CORS allows `http://localhost:5173` (the Vite dev server).

### Endpoints

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/health` | – | `{ ok, default_model, has_api_key, log_path }` |
| `POST` | `/api/ask` | `{ question, model?, top_k? (1–10, default 3) }` | Retrieves chunks, calls the model, logs the row as `Not rated`, returns the row + `retrieval_seconds` + `matches` |
| `GET` | `/api/logs` | – | All CSV rows with their `index` |
| `PATCH` | `/api/logs/{index}` | `{ feedback: "Correct" \| "Incorrect" \| "Not rated" }` | Updates the rating of one row |

Errors: `500` if the index is missing or no API key is set, `502` for model/network failures (rate limit, unknown model, …). Failed calls are still logged with the `error` column filled in, so the Analysis tab can report error rates.

### `rag_feedback.csv` columns

`timestamp, model, question, answer, retrieved_chunk_ids, best_distance, total_seconds, feedback, error`

`error` is added by the API. Older logs written only by step 10 are upgraded automatically on the first API write. Writes are guarded by a lock and the file is replaced atomically on updates.

## Try these questions

1. How many days of annual leave do full-time employees receive?
2. Which days are designated office days for eligible hybrid employees?
3. How quickly should a lost company laptop be reported?
4. What is the reimbursement submission deadline?
5. When must new employees complete security training?
6. What are the initial IT response targets for Priority 1 and Priority 2 incidents?
7. What are the maternity leave benefits? (Not in the document — the model should **not** invent an answer.)

## Re-index or replace the document

Edit `Documents/BrightPath_Employee_Guide.txt` and re-run `05_store_in_chroma.py`. It replaces the previous collection so old chunks don't linger. The document must stay a plain `.txt` file (PDF/DOCX would need extra parsing libraries).

## Troubleshooting

- `ModuleNotFoundError`: PyCharm isn't using the `.venv` interpreter where you installed `requirements.txt`.
- First embedding run is slow: the MiniLM model is downloading. Later runs are fast.
- `No indexed collection` / `collection is empty`: run `05_store_in_chroma.py` first.
- Missing API key: copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
- `429` / insufficient credits: the account needs credits, or pick a `:free` model. Steps 1–6, 8 and 9 still work offline.
- Unknown model: model names must be OpenRouter slugs (`provider/model`), e.g. `openai/gpt-4o-mini`.

## RAG pipeline

```
Documents/BrightPath_Employee_Guide.txt
                 |
              Read text
                 |
           Token inspection
                 |
          Split into chunks
                 |
        Local embedding model
                 |
       ChromaDB / chroma_db/
                 |
      User question -> embed question
                 |
       Similarity search (top 3)
                 |
       Retrieved original chunks
                 |
         AI + context + question
                 |
        Grounded answer + sources
                 |
      Log + rate (rag_feedback.csv)
```
