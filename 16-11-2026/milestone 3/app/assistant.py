"""Two-stage LangChain pipeline.

Stage 1 (gather facts): the Ollama model, with tools bound, decides which tools to call
          (trip lookup / weather). A deterministic guard then makes sure the facts the answer
          depends on were really fetched by tools — the model is never trusted to recall them.
Stage 2 (advise):       prompt | model | parser composes the advisory strictly from the tool outputs.

Redis supplies the recent conversation and the session's active trip, so follow-ups
("Will I need an umbrella there?") resolve without repeating the destination.
"""
import json
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from . import db, memory
from .config import OLLAMA_BASE_URL, OLLAMA_MODEL
from .tools import TOOLS, TOOLS_BY_NAME

log = logging.getLogger("assistant")

llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
llm_with_tools = llm.bind_tools(TOOLS)

STAGE1_SYSTEM = """You are a data-gathering step for a business travel assistant.
Your ONLY job is to call tools to fetch facts needed to answer the employee. Do not answer the question.
- If a trip ID is known, call get_trip_details with it.
- If only a city is mentioned, call find_trip_by_destination.
- Then call get_weather_forecast with the trip's destination, start_date and end_date.
Session context (from memory): {context}"""

ADVISORY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a concise corporate travel & weather advisor.\n"
     "STRICT RULES:\n"
     "1. Use ONLY the facts in TOOL_RESULTS. Never invent temperatures, rain or conditions.\n"
     "2. If TOOL_RESULTS contains a weather error or weather_available=false, clearly say the forecast "
     "is unavailable and why; give only generic, non-weather travel tips.\n"
     "3. If no trip was found, say so and ask for the trip ID or destination.\n"
     "4. If 'notes' say some days are not covered, mention it.\n"
     "5. Umbrella is needed only if any day has precipitation_mm > 0 or precipitation_probability_pct >= 40. "
     "A light jacket is useful if any temp_min_c < 18.\n"
     "6. Always use this format (even for follow-up questions):\n"
     "Destination: <city, country> (<dates>)\n"
     "Weather: <1-2 sentence summary with min/max °C and precipitation>\n"
     "Advice: <one sentence that directly answers what the employee asked>\n"
     "Suggestions:\n- <3 to 4 short packing/travel tips grounded in the weather>\n\n"
     "TOOL_RESULTS:\n{facts}"),
    ("placeholder", "{history}"),
    ("human", "{question}"),
])
advisory_chain = ADVISORY_PROMPT | llm | StrOutputParser()


def _run_tool(name: str, args: dict, trace: list) -> dict:
    result = TOOLS_BY_NAME[name].invoke(args)
    parsed = json.loads(result)
    trace.append({"tool": name, "args": args, "ok": "error" not in parsed})
    return parsed


def _stage1_gather(question: str, ctx: dict, history: list[dict]) -> tuple[dict, list]:
    """Let the model orchestrate tools, then enforce the required facts deterministically."""
    trace: list = []
    trip: dict | None = None
    weather: dict | None = None

    msgs = [SystemMessage(STAGE1_SYSTEM.format(context=json.dumps(ctx) if ctx else "none"))]
    msgs += [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history[-4:]]
    msgs.append(HumanMessage(question))

    try:
        for _ in range(3):  # bounded tool loop
            ai = llm_with_tools.invoke(msgs)
            msgs.append(ai)
            if not ai.tool_calls:
                break
            for call in ai.tool_calls:
                if call["name"] not in TOOLS_BY_NAME:
                    continue
                res = _run_tool(call["name"], call["args"], trace)
                trace[-1]["by"] = "model"
                if (call["name"] in ("get_trip_details", "find_trip_by_destination")
                        and "error" not in res and trip is None):  # first resolved trip wins
                    trip = res
                elif call["name"] == "get_weather_forecast":
                    weather = res
                msgs.append(ToolMessage(json.dumps(res), tool_call_id=call["id"]))
    except Exception as e:  # model/tool-calling failure must not break the request
        log.warning("Stage-1 tool calling failed: %s", e)

    # --- Guard: guarantee facts come from tools, never from model guesses ---
    if trip is None and ctx.get("trip_id"):
        res = _run_tool("get_trip_details", {"trip_id": ctx["trip_id"]}, trace)
        trace[-1]["by"] = "guard"
        trip = None if "error" in res else res
    if trip is None:  # user named a city that matches a saved trip
        for t in db.list_trips():
            if re.search(rf"\b{re.escape(t['destination'])}\b", question, re.I):
                res = _run_tool("find_trip_by_destination", {"destination": t["destination"]}, trace)
                trace[-1]["by"] = "guard"
                trip = None if "error" in res else res
                break

    # Weather must match the trip's real destination and dates (model args may be wrong/hallucinated).
    if trip:
        ok = (weather and "error" not in weather
              and weather["location"]["name"].lower() == trip["destination"].lower()
              and weather["requested"] == {"start": trip["start_date"], "end": trip["end_date"]})
        wanted = {"city": trip["destination"].lower(), "start_date": trip["start_date"], "end_date": trip["end_date"]}
        last_w = next((t for t in reversed(trace) if t["tool"] == "get_weather_forecast"), None)
        same_failed = bool(weather and "error" in weather and last_w
                           and {**last_w["args"], "city": str(last_w["args"].get("city", "")).lower()} == wanted)
        if not ok and not same_failed:
            weather = _run_tool("get_weather_forecast", {"city": trip["destination"],
                                "start_date": trip["start_date"], "end_date": trip["end_date"]}, trace)
            trace[-1]["by"] = "guard"
    elif weather is not None:
        # No saved trip: only keep weather the model fetched for a city the user actually named.
        city = next((t["args"].get("city", "") for t in reversed(trace) if t["tool"] == "get_weather_forecast"), "")
        if not city or city.lower() not in question.lower():
            weather = None

    facts = {"trip": trip or {"error": "No saved trip identified for this question."},
             "weather": weather or {"error": "Weather not retrieved because no trip/destination was identified.",
                                    "weather_available": False}}
    return facts, trace


def ask(session_id: str, question: str, trip_id: str | None = None) -> dict:
    if trip_id:
        trip = db.get_trip(trip_id)
        if trip:
            memory.set_context(session_id, trip_id=trip["trip_id"], destination=trip["destination"],
                               start_date=trip["start_date"], end_date=trip["end_date"])
    ctx = memory.get_context(session_id)
    history = memory.get_history(session_id)

    facts, trace = _stage1_gather(question, ctx, history)

    hist_msgs = [("human" if m["role"] == "user" else "ai", m["content"]) for m in history]
    answer = advisory_chain.invoke({"facts": json.dumps(facts, indent=1), "history": hist_msgs,
                                    "question": question}).strip()

    trip = facts["trip"]
    if "error" not in trip:
        memory.set_context(session_id, trip_id=trip["trip_id"], destination=trip["destination"],
                           start_date=trip["start_date"], end_date=trip["end_date"])
    memory.add_message(session_id, "user", question)
    memory.add_message(session_id, "assistant", answer)

    w = facts["weather"]
    return {
        "session_id": session_id,
        "answer": answer,
        "trip_id": trip.get("trip_id"),
        "destination": trip.get("destination"),
        "weather_available": "error" not in w,
        "weather_error": w.get("error"),
        "tool_calls": trace,
        "session_context": memory.get_context(session_id),
    }
