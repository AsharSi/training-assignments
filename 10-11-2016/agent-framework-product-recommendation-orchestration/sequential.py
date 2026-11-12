"""
sequential.py - Product recommendation workflow using Microsoft Agent Framework.

    Customer Request -> Inventory Agent -> Pricing Agent -> Recommendation Agent -> Final Recommendation

The three agents are orchestrated by SequentialBuilder. The workflow runs once,
asynchronously, and passes the full conversation (customer request, each agent's
reply and every tool call/result) from one agent to the next.

Setup:
    pip install agent-framework --pre

    # .env (OpenRouter)
    OPENROUTER_API_KEY=...
    OPENROUTER_MODEL="liquid/lfm-3-1.7b:free"

Run:
    python sequential.py
    python sequential.py "I need 3 audio products, budget 30000 rupees"
"""

import asyncio
import json
import os
import sys
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field

from agent_framework import Agent, tool
from agent_framework.orchestrations import SequentialBuilder

from tools import search_products, calculate_order_total

load_dotenv()  # reads OPENROUTER_API_KEY / OPENROUTER_MODEL from .env


# ---------------------------------------------------------------------------
# Tools (wrappers expose only the arguments the LLM should fill in)
# ---------------------------------------------------------------------------
@tool(name="search_products",
      description="Search the product catalogue by product name or category. "
                  "Returns matching products with id, name, category, price_inr, stock and rating.")
def search_products_tool(
    query: Annotated[str, Field(description="Product name or category, e.g. 'laptop' or 'NovaBook'.")],
) -> str:
    return json.dumps(search_products(query), ensure_ascii=False)


@tool(name="calculate_order_total",
      description="Calculate the total cost for a product ID and quantity. "
                  "Checks that enough stock is available and rejects invalid quantities.")
def calculate_order_total_tool(
    product_id: Annotated[str, Field(description="Product ID, e.g. 'P101'.")],
    quantity: Annotated[int, Field(description="Number of units the customer wants.")],
) -> str:
    return json.dumps(calculate_order_total(product_id, quantity), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------
INVENTORY_INSTRUCTIONS = """You are the Inventory Agent, the first step in a product recommendation workflow.

1. Read the customer's request and identify the product name or category, the quantity
   (default 1 if not stated) and the budget in INR (note "none" if not stated).
   Indian formats such as "1,20,000" or "1.2 lakh" mean 120000.
2. Call search_products with the product name or category. If it finds nothing, retry once
   with a simpler term (e.g. singular form, or just the category).
3. Report your findings for the next agent in exactly this format:

CUSTOMER REQUIREMENTS: product=<term>, quantity=<n>, budget_inr=<number or none>
MATCHING PRODUCTS:
- <id> | <name> | <category> | price ₹<price_inr> | stock <stock> | rating <rating> | <IN STOCK or OUT OF STOCK>

If no products match, write "MATCHING PRODUCTS: none" and say so.
Only report data returned by the tool. Do not calculate totals or recommend anything."""

PRICING_INSTRUCTIONS = """You are the Pricing Agent, the second step in a product recommendation workflow.

The Inventory Agent has listed the customer's requirements and the matching products above.

1. For EVERY product the Inventory Agent listed, call calculate_order_total with its id and the
   customer's quantity. Do not skip any, even out-of-stock ones; the tool validates stock.
2. If the tool reports an invalid quantity, report that and stop.
3. Compare each successful total with the budget (no budget means every total is within budget).
4. Report in exactly this format:

PRICING RESULTS (quantity <n>, budget ₹<budget or none>):
- <id> | <name> | rating <rating> | total ₹<total_inr or n/a> | <AFFORDABLE / OVER BUDGET / INSUFFICIENT STOCK / OUT OF STOCK>
AFFORDABLE PRODUCTS: <comma-separated ids, or none>

Use only the figures returned by the tool. Do not recommend a product."""

RECOMMENDATION_INSTRUCTIONS = """You are the Recommendation Agent, the final step in a product recommendation workflow.

Review the Inventory Agent's and Pricing Agent's results above and choose ONE product using these rules:
1. Only consider products the Pricing Agent marked AFFORDABLE. Never recommend a product that is
   out of stock, has insufficient stock, or is over budget.
2. Among those, pick the highest rating.
3. If ratings are equal, pick the one with the lower total cost.

Reply in exactly this format:

FINAL RECOMMENDATION: <name> (<id>)
Quantity: <n> | Total: ₹<total> | Rating: <rating>
Why: <one or two sentences explaining the choice, mentioning any higher-rated products that were excluded and why>

If no product is affordable and available, reply:

FINAL RECOMMENDATION: None
Why: <short reason, and the cheapest available option with its total if there is one>"""


# ---------------------------------------------------------------------------
# Client and workflow
# ---------------------------------------------------------------------------
def create_client():
    """OpenRouter (OpenAI-compatible Chat Completions API), configured from .env."""
    from agent_framework.openai import OpenAIChatCompletionClient

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to the .env file.")
    return OpenAIChatCompletionClient(
        model=os.getenv("OPENROUTER_MODEL", "liquid/lfm-3-1.7b:free"),
        api_key=api_key,
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )


def build_workflow(client=None, *, inventory_client=None, pricing_client=None, recommendation_client=None):
    """Create the three agents and wire them together with SequentialBuilder."""
    client = client or (None if inventory_client else create_client())

    inventory_agent = Agent(
        inventory_client or client,
        INVENTORY_INSTRUCTIONS,
        name="InventoryAgent",
        tools=[search_products_tool],
    )
    pricing_agent = Agent(
        pricing_client or client,
        PRICING_INSTRUCTIONS,
        name="PricingAgent",
        tools=[calculate_order_total_tool],
    )
    recommendation_agent = Agent(
        recommendation_client or client,
        RECOMMENDATION_INSTRUCTIONS,
        name="RecommendationAgent",
    )

    workflow = SequentialBuilder(
        participants=[inventory_agent, pricing_agent, recommendation_agent],
        output_from=[recommendation_agent],                          # final workflow output
        intermediate_output_from=[inventory_agent, pricing_agent],   # streamed as intermediate results
        ensure_trailing_user_turn=True,
    ).build()
    return workflow


# ---------------------------------------------------------------------------
# Execution and display
# ---------------------------------------------------------------------------
STEP_TITLES = {
    "InventoryAgent": "STEP 1 - INVENTORY AGENT",
    "PricingAgent": "STEP 2 - PRICING AGENT",
    "RecommendationAgent": "STEP 3 - RECOMMENDATION AGENT",
}


def _print_header(title):
    print("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)


async def run_workflow(customer_request, workflow=None, show=True):
    """Run the workflow once (asynchronously) and return each agent's final text."""
    workflow = workflow or build_workflow()

    texts = {}       # executor id -> accumulated reply text
    tool_logs = {}   # executor id -> list of tool call lines

    if show:
        _print_header("CUSTOMER REQUEST")
        print(customer_request)

    async for event in workflow.run(customer_request, stream=True):
        if event.type in ("intermediate", "output"):
            agent_id = event.executor_id
            for content in getattr(event.data, "contents", None) or []:
                if content.type == "function_call":
                    args = content.arguments if isinstance(content.arguments, str) else json.dumps(content.arguments or "")
                    logs = tool_logs.setdefault(agent_id, [])
                    if content.name:   # start of a new call
                        logs.append([content.name, args])
                    elif logs and isinstance(logs[-1], list):   # streamed argument chunk
                        logs[-1][1] += args
                elif content.type == "function_result":
                    tool_logs.setdefault(agent_id, []).append(f"<- {content.result}")
                elif content.type == "text" and content.text:
                    texts[agent_id] = texts.get(agent_id, "") + content.text

        elif event.type == "executor_completed" and event.executor_id in STEP_TITLES and show:
            agent_id = event.executor_id
            _print_header(STEP_TITLES[agent_id])
            for entry in tool_logs.get(agent_id, []):
                line = f"-> {entry[0]}({entry[1]})" if isinstance(entry, list) else entry
                print(f"  [tool] {line if len(line) <= 200 else line[:197] + '...'}")
            if tool_logs.get(agent_id):
                print()
            print(texts.get(agent_id, "(no reply)").strip())

        elif event.type in ("failed", "error"):
            details = getattr(event, "details", None)
            reason = getattr(details, "message", None) or details or event.data
            raise RuntimeError(f"Workflow failed: {reason}")

    final = texts.get("RecommendationAgent", "").strip()
    if show:
        _print_header("FINAL RECOMMENDATION")
        print(final or "(no recommendation produced)")

    return {
        "inventory": texts.get("InventoryAgent", "").strip(),
        "pricing": texts.get("PricingAgent", "").strip(),
        "recommendation": final,
        "tool_calls": {k: [f"-> {e[0]}({e[1]})" if isinstance(e, list) else e for e in v]
                       for k, v in tool_logs.items()},
    }


async def main():
    request = " ".join(sys.argv[1:]) or "I need 2 laptops. My total budget is ₹1,20,000."
    await run_workflow(request)


if __name__ == "__main__":
    asyncio.run(main())