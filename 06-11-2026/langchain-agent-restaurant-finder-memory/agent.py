import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from guardrails import check_question, redact_pii
from tools import search_restaurants, calculate_dining_cost, get_restaurants

load_dotenv()

# Windows consoles default to cp1252, which can't print the ₹ symbol.
sys.stdout.reconfigure(encoding="utf-8")

SYSTEM_PROMPT = """You are a restaurant reservation assistant. You help users find restaurants and estimate dining costs.

Rules:
- Always use the tools to get restaurant information. Never invent restaurant names, prices, IDs, locations or seat availability.
- To find restaurants, call search_restaurants with a cuisine (e.g. "Indian") or a restaurant name.
- To estimate a cost, call calculate_dining_cost with the restaurant's ID. If the user names a restaurant but you don't know its ID, first call search_restaurants with that name.
- Use the conversation history. Remember the previously selected restaurant, the number of guests and earlier cost calculations. If the user says "make that 6 people", reuse the previous restaurant with the new number of guests.
- If the user asks for a cost without naming a restaurant and none was selected earlier, ask which restaurant they mean.
- If it's unclear which restaurant the user means, ask them to choose instead of guessing.
- Whenever the user asks for a cost, you MUST call calculate_dining_cost, even if the guest count looks invalid or exceeds the seats. Never reject a guest count yourself; the tool enforces the 1-20 limit and checks seats. Example: "cost for 50 guests" after discussing Spice Garden -> call calculate_dining_cost(restaurant_id="R101", guests=50), then report the tool's message.
- If the tool says the guest count is invalid or exceeds the available seats, tell the user.
- You only estimate costs. Do not make bookings or take payments.
- Keep answers short and clear. Show prices in ₹.
- If the user asks about anything unrelated to restaurants, politely tell them you can only help with restaurants."""


api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("OPENROUTER_API_KEY is missing. Add it to the .env file.")

if api_key.startswith("sk-or-"):
    # OpenRouter exposes an OpenAI-compatible API, so ChatOpenAI works with its base URL.
    llm = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
    )
else:
    # A regular OpenAI key: call GPT-4o-mini directly.
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0)

agent = create_agent(
    model=llm,
    tools=[search_restaurants, calculate_dining_cost],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)

RESTAURANT_NAMES = [r["name"] for r in get_restaurants()]


if __name__ == "__main__":
    thread_number = 1
    previous_count = 0

    print("Restaurant AI Agent")
    print("Type /new for a new conversation")
    print("Type exit to quit")

    while True:
        question = input("\nYou: ").strip()

        if question.lower() in ("exit", "quit"):
            break

        if question.lower() == "/new":
            thread_number += 1
            previous_count = 0
            print("New conversation started. Previous details have been cleared.")
            continue

        # Input guardrails: empty/long input, PII, domain restriction
        rejection = check_question(question, RESTAURANT_NAMES)
        if rejection:
            print("[GUARDRAIL]:", rejection)
            continue

        config = {"configurable": {"thread_id": f"restaurant-{thread_number}"}}

        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config=config,
            )

            messages = result["messages"]
            new_messages = messages[previous_count:]
            previous_count = len(messages)

            for message in new_messages:
                if isinstance(message, AIMessage):
                    for call in message.tool_calls:
                        print("[TOOL]:", call["name"])
                        print("Arguments:", call["args"])

                if isinstance(message, ToolMessage):
                    print("[TOOL RESULT]:", message.content)

            # Output guardrail: redact emails / phone numbers
            print("\nAgent:", redact_pii(messages[-1].content))

        except Exception as error:
            print("Error:", error)
