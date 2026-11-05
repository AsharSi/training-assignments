"""HTTP API for the Library AI Agent, used by the React UI in ../library-agent-ui.

Run:  uvicorn server:app --reload --port 8000

The agent loop is the same as agent.py (same model, tools and system prompt).
The only difference is the reservation approval: instead of a terminal y/n
prompt, the server pauses the loop and returns `needs_approval`; the UI then
calls /api/approve and the loop continues.
"""

import json
import uuid
from dataclasses import dataclass, field

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import MODELS, SYSTEM_PROMPT, chat, execute_tool
from tools import BOOKS_PATH, RESERVATIONS_PATH, _load, reserve_book

MAX_ROUNDS = 6


class NeedsApproval(Exception):
    """Raised from reserve_book's confirm hook to pause the agent loop."""


def _ask_ui(_prompt: str) -> str:
    raise NeedsApproval


@dataclass
class Session:
    history: list = field(default_factory=lambda: [{"role": "system", "content": SYSTEM_PROMPT}])
    queue: list = field(default_factory=list)       # tool calls not yet executed
    pending: dict | None = None                     # reservation awaiting approval
    decision: bool | None = None                    # user's answer to `pending`


SESSIONS: dict[str, Session] = {}

app = FastAPI(title="Library AI Agent API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


def _get_session(session_id: str) -> Session:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(404, "Unknown session. Start a new chat.")
    return session


def _run_queue(session: Session, steps: list) -> dict | None:
    """Execute queued tool calls. Returns an approval request if one is needed."""
    while session.queue:
        call = session.queue[0]
        name = call["function"]["name"]
        args: dict = {}
        try:
            args = json.loads(call["function"]["arguments"] or "{}")
            if name == "reserve_book":
                book_id, customer = int(args["book_id"]), str(args["customer_name"])
                if session.decision is None:
                    try:
                        result = reserve_book(book_id, customer, confirm=_ask_ui)
                    except NeedsApproval:
                        book = next((b for b in _load(BOOKS_PATH) if b["id"] == book_id), None)
                        session.pending = {"book": book, "customer_name": customer.strip()}
                        return session.pending
                else:
                    answer = "y" if session.decision else "n"
                    result = reserve_book(book_id, customer, confirm=lambda _p: answer)
                    session.pending = session.decision = None
            else:
                result = execute_tool(name, args)
        except (ValueError, TypeError, KeyError) as exc:
            result = {"error": str(exc)}

        steps.append({"tool": name, "args": args, "result": result})
        session.history.append({"role": "tool", "tool_call_id": call["id"],
                                "content": json.dumps(result, ensure_ascii=False)})
        session.queue.pop(0)
    return None


def _abort(session: Session) -> None:
    """Answer any unexecuted tool calls so the history stays valid, then clear state."""
    for call in session.queue:
        session.history.append({"role": "tool", "tool_call_id": call["id"],
                                "content": json.dumps({"error": "Cancelled after a failure."})})
    session.queue, session.pending, session.decision = [], None, None


def _run_agent(session: Session) -> dict:
    """Continue the agent loop until it answers or needs approval."""
    steps: list = []
    for _ in range(MAX_ROUNDS):
        approval = _run_queue(session, steps)
        if approval:
            return {"status": "needs_approval", "approval": approval, "steps": steps}

        message = chat(session.history)
        if not message.tool_calls:
            reply = message.content or "No answer generated."
            session.history.append({"role": "assistant", "content": reply})
            return {"status": "done", "reply": reply, "steps": steps}

        calls = [{"id": tc.id, "type": "function",
                  "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                 for tc in message.tool_calls]
        session.history.append({"role": "assistant", "content": message.content or "",
                                "tool_calls": calls})
        session.queue = calls

    session.queue = []
    return {"status": "done", "steps": steps,
            "reply": "Stopped after too many tool calls. Please try a simpler request."}


class ChatIn(BaseModel):
    session_id: str | None = None
    message: str


class ApproveIn(BaseModel):
    session_id: str
    approved: bool


@app.get("/api/health")
def health():
    return {"ok": True, "models": MODELS}


@app.post("/api/chat")
def post_chat(body: ChatIn):
    text = body.message.strip()
    if not text:
        raise HTTPException(400, "Message is empty.")
    session_id = body.session_id or uuid.uuid4().hex
    session = SESSIONS.setdefault(session_id, Session())
    if session.pending:
        raise HTTPException(409, "Approve or decline the pending reservation first.")

    checkpoint = len(session.history)
    session.history.append({"role": "user", "content": text})
    try:
        result = _run_agent(session)
    except Exception as exc:
        del session.history[checkpoint:]  # drop the failed partial exchange
        session.queue, session.pending, session.decision = [], None, None
        raise HTTPException(502, f"Agent request failed: {exc}") from exc
    return {"session_id": session_id, **result}


@app.post("/api/approve")
def post_approve(body: ApproveIn):
    session = _get_session(body.session_id)
    if not session.pending:
        raise HTTPException(409, "No reservation is waiting for approval.")
    session.decision = body.approved
    try:
        result = _run_agent(session)
    except Exception as exc:
        _abort(session)
        raise HTTPException(502, f"Agent request failed: {exc}") from exc
    return {"session_id": body.session_id, **result}


@app.post("/api/reset")
def post_reset(body: dict):
    SESSIONS.pop(str(body.get("session_id")), None)
    return {"ok": True}


@app.get("/api/books")
def get_books():
    return _load(BOOKS_PATH)


@app.get("/api/reservations")
def get_reservations():
    return _load(RESERVATIONS_PATH)
