"""FastAPI entry point: Travel & Weather Advisory Assistant."""
import logging
import sqlite3
from datetime import date

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from . import assistant, db, memory
from .config import OLLAMA_BASE_URL, OLLAMA_MODEL

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="AI Travel & Weather Advisory Assistant", version="1.0.0",
              description="LangChain + Ollama + SQLite + Redis + Open-Meteo. Weather data by Open-Meteo.com")


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


class TripCreate(BaseModel):
    employee_id: str = Field(..., pattern=r"^EMP\d{3,6}$", examples=["EMP104"])
    destination: str = Field(..., min_length=2, max_length=80, examples=["Jaipur"])
    start_date: date
    end_date: date
    purpose: str = Field(..., min_length=3, max_length=200, examples=["Client meeting"])

    @field_validator("destination", "purpose")
    @classmethod
    def strip(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.start_date < date.today():
            raise ValueError("start_date must not be in the past")
        return self


class AskRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64, examples=["sess-emp104"])
    question: str = Field(..., min_length=2, max_length=500,
                          examples=["What weather should I expect for my Jaipur trip?"])
    trip_id: str | None = Field(None, description="Optional; otherwise resolved from question or session memory")


@app.get("/health", tags=["system"])
def health():
    try:
        ollama_ok = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3).status_code == 200
    except httpx.HTTPError:
        ollama_ok = False
    return {"sqlite": True, "redis": memory.ping(), "ollama": ollama_ok, "model": OLLAMA_MODEL}


@app.post("/trips", status_code=201, tags=["trips"])
def create_trip(trip: TripCreate):
    try:
        return db.create_trip(trip.employee_id, trip.destination, trip.start_date.isoformat(),
                              trip.end_date.isoformat(), trip.purpose)
    except sqlite3.Error as e:
        raise HTTPException(500, f"Database error: {e}")


@app.get("/trips/{trip_id}", tags=["trips"])
def get_trip(trip_id: str):
    trip = db.get_trip(trip_id)
    if not trip:
        raise HTTPException(404, f"Trip '{trip_id}' not found")
    return trip


@app.get("/trips", tags=["trips"])
def list_trips(employee_id: str | None = None):
    return db.list_trips(employee_id)


@app.post("/assistant/ask", tags=["assistant"])
def ask(req: AskRequest):
    if not memory.ping():
        raise HTTPException(503, "Redis session memory is unavailable")
    if req.trip_id and not db.get_trip(req.trip_id):
        raise HTTPException(404, f"Trip '{req.trip_id}' not found")
    try:
        return assistant.ask(req.session_id, req.question, req.trip_id)
    except httpx.ConnectError:
        raise HTTPException(503, "Ollama model server is unavailable")


@app.get("/assistant/sessions/{session_id}", tags=["assistant"])
def get_session(session_id: str):
    return {"context": memory.get_context(session_id), "history": memory.get_history(session_id)}


@app.delete("/assistant/sessions/{session_id}", status_code=204, tags=["assistant"])
def clear_session(session_id: str):
    memory.clear(session_id)
