"""AI Library Assistant using OpenRouter (free models) + OpenAI-style function calling.

Try:
- Find books related to Python programming.
- Is Python Crash Course available?
- Reserve Python Crash Course for Ahmed.
- Show me books related to artificial intelligence.
- Reserve a book that has no available copies.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from tools import reserve_book, search_books

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
if not API_KEY or API_KEY.startswith("replace_with"):
    raise SystemExit("Missing OPENROUTER_API_KEY. Copy .env.example to .env and add your key "
                     "(free key at https://openrouter.ai/keys).")

# Comma-separated list: the first model is tried first, the rest are fallbacks
# (free models are often rate-limited, so fallbacks keep the demo working).
MODELS = [m.strip() for m in os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b:free,google/gemma-4-31b-it:free,nvidia/nemotron-3.5-super-vl:free",
).split(",") if m.strip()]

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_books",
            "description": (
                "Search the library catalogue by title, author, category or keyword. "
                "Returns matching books with their ID and available copies. Use it for "
                "any question about finding books or checking availability. Pass an "
                "empty string to list every book."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Book title or keyword, e.g. 'Python' or 'artificial intelligence'.",
                    }
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_book",
            "description": (
                "Reserve one copy of a book for a customer, using the numeric book ID "
                "from search_books. The application asks the user for final approval "
                "before saving. Only call when the user asks to reserve a book."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {"type": "integer", "description": "Numeric book ID, e.g. 101."},
                    "customer_name": {"type": "string", "description": "Name of the customer."},
                },
                "required": ["book_id", "customer_name"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a friendly AI Library Assistant.
You have two tools: search_books and reserve_book.

RULES:
1. To find books or check availability, call search_books. Only mention books it returns.
2. To reserve a book, you need its numeric ID. If you only know the title, call
   search_books first, then call reserve_book with the matching ID.
3. If the user asks to reserve a book but gives no customer name, ask for it.
4. If the user asks to reserve "a book with no available copies", search the
   catalogue (empty keyword), pick a book with 0 copies and attempt reserve_book
   so the user sees the outcome.
5. Never claim a reservation exists unless reserve_book returned reserved=true.
   If it returned reserved=false, explain the reason.
6. Keep answers short and clear. Show book ID, title, author and copies available.
"""


def execute_tool(name: str, args: dict) -> dict:
    """Run only the approved local Python functions."""
    if name == "search_books":
        return search_books(keyword=str(args.get("keyword", "")))
    if name == "reserve_book":
        return reserve_book(book_id=int(args["book_id"]),
                            customer_name=str(args["customer_name"]))
    return {"error": f"Unknown tool: {name}"}


def chat(messages: list[dict]):
    """Call OpenRouter, falling back to the next free model on errors."""
    last_error = None
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0,
            )
            if not response.choices:
                raise RuntimeError(f"{model} returned no choices")
            return response.choices[0].message
        except Exception as exc:  # rate limit, model unavailable, etc.
            print(f"[model {model} failed: {str(exc)[:150]}]")
            last_error = exc
    raise RuntimeError(f"All models failed. Last error: {last_error}")


def answer_one_turn(history: list[dict]) -> str:
    """Let the model pick tools, run them, return results, repeat until it answers."""
    for _ in range(6):  # safety limit on tool-call rounds
        message = chat(history)

        if not message.tool_calls:
            history.append({"role": "assistant", "content": message.content or ""})
            return message.content or "No answer generated."

        history.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ],
        })
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            print(f"\n[AGENT SELECTED TOOL] {name}  args={tool_call.function.arguments}")
            try:
                args = json.loads(tool_call.function.arguments or "{}")
                result = execute_tool(name, args)
            except (ValueError, TypeError, KeyError) as exc:
                result = {"error": str(exc)}
            print("[TOOL RESULT]", json.dumps(result, ensure_ascii=False)[:800])
            history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })
    return "Stopped after too many tool calls. Please try a simpler request."


def main() -> None:
    print("AI Library Assistant (OpenRouter)")
    print("Models:", ", ".join(MODELS))
    print("Tools : search_books, reserve_book")
    print("Type 'exit' to quit.\n")
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        previous_length = len(history)
        history.append({"role": "user", "content": question})
        try:
            print("\nAssistant:", answer_one_turn(history), "\n")
        except Exception as exc:
            del history[previous_length:]  # drop the failed partial exchange
            print("Request failed:", exc, "\n")


if __name__ == "__main__":
    main()
