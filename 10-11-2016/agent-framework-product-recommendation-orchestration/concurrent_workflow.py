"""
concurrent_workflow.py - Product recommendation workflow using ConcurrentBuilder.

(Named concurrent_workflow.py, NOT concurrent.py: a file called concurrent.py
shadows Python's built-in `concurrent` package, which breaks `import asyncio`
for every script in this folder.)

                         +--> Top-Rated Agent    --+
    Customer Request ----+--> Best-Value Agent   --+--> Aggregator --> Final Recommendation
       (fan-out)         +--> Stock Check Agent  --+     (fan-in)

Unlike sequential.py, the three analyst agents do not depend on each other:
ConcurrentBuilder sends the same customer request to all of them at the same
time, each one uses the tools independently, and a custom aggregator collects
the three reports and asks a Recommendation agent to make the final decision.

Run:
    python concurrent_workflow.py
    python concurrent_workflow.py "Find 3 smartphones within ₹1,00,000 total."
    python concurrent_workflow.py --all        # run all 8 assignment test requests
"""

import asyncio
import json
import os
import sys
import time

try:                       # newer openai SDKs are built on httpx2, older ones on httpx
    import httpx2 as httpx
except ImportError:
    import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

from agent_framework import Agent
from agent_framework.orchestrations import ConcurrentBuilder

# Reuse the tool wrappers and OpenRouter client from the sequential version.
from sequential import calculate_order_total_tool, search_products_tool

load_dotenv()


class _ThrottledTransport(httpx.AsyncHTTPTransport):
    """Lets at most `limit` HTTP requests to the model be in flight at once.

    The agents still run concurrently in the workflow; only their calls to the
    model API queue up when more than `limit` happen at the same moment.
    """

    def __init__(self, limit, **kwargs):
        super().__init__(**kwargs)
        self._semaphore = asyncio.Semaphore(limit)

    async def handle_async_request(self, request):
        async with self._semaphore:
            response = await super().handle_async_request(request)
            await response.aread()   # hold the slot until the whole (streamed) body has arrived
            return response


def create_client():
    """OpenRouter client tuned for concurrent agents.

    Free OpenRouter models reject bursts of simultaneous requests with HTTP 429
    ("temporarily rate-limited upstream"). Two safeguards:
      - OPENROUTER_MAX_PARALLEL (default 2): max simultaneous model requests.
      - OPENROUTER_MAX_RETRIES (default 8): the OpenAI SDK retries 429s with
        exponential backoff.
    With a paid model you can raise OPENROUTER_MAX_PARALLEL to 3 or more.
    """
    from agent_framework.openai import OpenAIChatCompletionClient

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to the .env file.")
    transport = _ThrottledTransport(int(os.getenv("OPENROUTER_MAX_PARALLEL", "2")))
    return OpenAIChatCompletionClient(
        model=os.getenv("OPENROUTER_MODEL", "liquid/lfm-3-1.7b:free"),
        async_client=AsyncOpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            max_retries=int(os.getenv("OPENROUTER_MAX_RETRIES", "8")),
            http_client=httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(120.0)),
        ),
    )


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------
_COMMON = """Read the customer's request and identify the product name or category, the quantity
(default 1 if not stated) and the budget in INR ("none" if not stated). Indian formats such as
"1,20,000" or "1.2 lakh" mean 120000.

Call search_products with the product name or category (retry once with a simpler term, e.g. the
singular form, if nothing is found). Then call calculate_order_total for EVERY matching product
with the customer's quantity; the tool checks stock and rejects invalid quantities.
Use only figures returned by the tools. Never invent products, prices or stock."""

TOP_RATED_INSTRUCTIONS = f"""You are the Top-Rated Agent, one of three analysts working in parallel.

{_COMMON}

Your focus: QUALITY. Find the highest-rated product that is in stock for the requested quantity
and whose total is within budget. If ratings tie, prefer the lower total.

Reply in exactly this format:
REQUIREMENTS: product=<term>, quantity=<n>, budget_inr=<number or none>
CANDIDATES:
- <id> | <name> | rating <rating> | total ₹<total or n/a> | <AFFORDABLE / OVER BUDGET / INSUFFICIENT STOCK / OUT OF STOCK>
TOP-RATED PICK: <name> (<id>), rating <rating>, total ₹<total>   (or "TOP-RATED PICK: none - <reason>")"""

BEST_VALUE_INSTRUCTIONS = f"""You are the Best-Value Agent, one of three analysts working in parallel.

{_COMMON}

Your focus: PRICE. Find the cheapest product that is in stock for the requested quantity and
within budget, and report how much budget it leaves unused.

Reply in exactly this format:
REQUIREMENTS: product=<term>, quantity=<n>, budget_inr=<number or none>
TOTALS (cheapest first):
- <id> | <name> | total ₹<total or n/a> | <AFFORDABLE / OVER BUDGET / INSUFFICIENT STOCK / OUT OF STOCK>
BEST-VALUE PICK: <name> (<id>), total ₹<total>, saves ₹<budget - total>   (or "BEST-VALUE PICK: none - <reason>")"""

STOCK_CHECK_INSTRUCTIONS = f"""You are the Stock Check Agent, one of three analysts working in parallel.

{_COMMON}

Your focus: AVAILABILITY. Report the stock of every matching product and whether it can cover the
requested quantity. Do not judge price or rating.

Reply in exactly this format:
REQUIREMENTS: product=<term>, quantity=<n>
STOCK:
- <id> | <name> | stock <stock> | <CAN FULFIL / INSUFFICIENT STOCK / OUT OF STOCK>
FULFILLABLE IDS: <comma-separated ids, or none>"""

RECOMMENDATION_INSTRUCTIONS = """You are the Recommendation Agent. Three analysts (Top-Rated, Best-Value
and Stock Check) examined the same customer request in parallel; their reports are given to you.

Choose ONE product using these rules:
1. Only consider products that are in stock for the requested quantity AND within budget.
   If the analysts disagree on a figure, trust the Stock Check report for stock and the
   tool-calculated totals for price.
2. Among those, pick the highest rating. If ratings are equal, pick the lower total cost.

Reply in exactly this format:

FINAL RECOMMENDATION: <name> (<id>)
Quantity: <n> | Total: ₹<total> | Rating: <rating>
Why: <one or two sentences; mention the cheaper Best-Value alternative if it differs>

If nothing qualifies, reply:

FINAL RECOMMENDATION: None
Why: <short reason, e.g. no matching products / insufficient stock / over budget, plus the
cheapest available option and its total if there is one>"""


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------
ANALYSTS = {
    "TopRatedAgent": "TOP-RATED AGENT",
    "BestValueAgent": "BEST-VALUE AGENT",
    "StockCheckAgent": "STOCK CHECK AGENT",
}


def build_workflow(client=None, *, recommendation_client=None):
    """Create three parallel analyst agents plus an aggregator, wired with ConcurrentBuilder."""
    client = client or create_client()
    tools = [search_products_tool, calculate_order_total_tool]

    top_rated = Agent(client, TOP_RATED_INSTRUCTIONS, name="TopRatedAgent", tools=tools)
    best_value = Agent(client, BEST_VALUE_INSTRUCTIONS, name="BestValueAgent", tools=tools)
    stock_check = Agent(client, STOCK_CHECK_INSTRUCTIONS, name="StockCheckAgent", tools=tools)
    recommender = Agent(recommendation_client or client, RECOMMENDATION_INSTRUCTIONS,
                        name="RecommendationAgent")

    async def aggregate_recommendation(results):
        """Fan-in: runs once, after ALL analysts finish. Receives list[AgentExecutorResponse]."""
        request = next((m.text for r in results for m in r.full_conversation if m.role == "user"), "")
        reports = "\n\n".join(
            f"### {ANALYSTS.get(r.executor_id, r.executor_id)} report\n{r.agent_response.text.strip()}"
            for r in results
        )
        response = await recommender.run(
            f"CUSTOMER REQUEST: {request}\n\n{reports}\n\nGive the final recommendation."
        )
        return {
            "reports": {r.executor_id: r.agent_response.text.strip() for r in results},
            "recommendation": response.text.strip(),
        }

    return (
        ConcurrentBuilder(
            participants=[top_rated, best_value, stock_check],
            intermediate_output_from="all_other",   # stream each analyst's output as it works
        )
        .with_aggregator(aggregate_recommendation)
        .build()
    )


# ---------------------------------------------------------------------------
# Execution and display
# ---------------------------------------------------------------------------
def _print_header(title):
    print("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)


async def run_workflow(customer_request, workflow=None, show=True):
    """Run the concurrent workflow once and return each analyst's report and the final pick."""
    workflow = workflow or build_workflow()

    texts, tool_logs, finished_at = {}, {}, {}
    final = None
    start = time.perf_counter()

    if show:
        _print_header("CUSTOMER REQUEST")
        print(customer_request)
        print(f"\nRunning {len(ANALYSTS)} analyst agents concurrently...")

    async for event in workflow.run(customer_request, stream=True):
        if event.type == "intermediate" and event.executor_id in ANALYSTS:
            # Updates from the three agents arrive interleaved, so buffer them per agent.
            agent_id = event.executor_id
            for content in getattr(event.data, "contents", None) or []:
                if content.type == "function_call":
                    args = content.arguments if isinstance(content.arguments, str) else json.dumps(content.arguments or "")
                    logs = tool_logs.setdefault(agent_id, [])
                    if content.name:
                        logs.append([content.name, args])
                    elif logs and isinstance(logs[-1], list):
                        logs[-1][1] += args
                elif content.type == "function_result":
                    tool_logs.setdefault(agent_id, []).append(f"<- {content.result}")
                elif content.type == "text" and content.text:
                    texts[agent_id] = texts.get(agent_id, "") + content.text

        elif event.type == "executor_completed" and event.executor_id in ANALYSTS:
            agent_id = event.executor_id
            finished_at[agent_id] = time.perf_counter() - start
            if show:
                _print_header(f"{ANALYSTS[agent_id]}  (finished at {finished_at[agent_id]:.1f}s)")
                for entry in tool_logs.get(agent_id, []):
                    line = f"-> {entry[0]}({entry[1]})" if isinstance(entry, list) else entry
                    print(f"  [tool] {line if len(line) <= 200 else line[:197] + '...'}")
                if tool_logs.get(agent_id):
                    print()
                print(texts.get(agent_id, "(no reply)").strip())

        elif event.type == "output":
            final = event.data

        elif event.type in ("failed", "error"):
            details = getattr(event, "details", None)
            reason = getattr(details, "message", None) or details or event.data
            raise RuntimeError(f"Workflow failed: {reason}")

    final = final or {"reports": {}, "recommendation": ""}
    if show:
        _print_header(f"FINAL RECOMMENDATION  (total {time.perf_counter() - start:.1f}s)")
        print(final["recommendation"] or "(no recommendation produced)")

    return {
        "reports": {k: final["reports"].get(k) or texts.get(k, "").strip() for k in ANALYSTS},
        "recommendation": final["recommendation"],
        "finished_at": finished_at,
        "tool_calls": {k: [f"-> {e[0]}({e[1]})" if isinstance(e, list) else e for e in v]
                       for k, v in tool_logs.items()},
    }


TEST_REQUESTS = [
    "Recommend 2 laptops within ₹1,20,000 total.",
    "Find 3 smartphones within ₹1,00,000 total.",
    "Recommend 2 monitors within ₹50,000 total.",
    "Find 5 headphones under ₹20,000 total.",
    "Recommend 2 tablets under ₹60,000 total.",
    "Find 10 printers within ₹1,00,000 total.",
    "Find 100 laptops and verify stock availability.",
    "Recommend a smartwatch within ₹30,000 total.",   # category not in the dataset
]


async def main():
    # Windows consoles default to cp1252, which cannot print "₹".
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if args == ["--all"]:
        workflow_client = create_client()
        for i, request in enumerate(TEST_REQUESTS, 1):
            print(f"\n\n{'#' * 70}\n# TEST {i}\n{'#' * 70}")
            # A workflow instance runs one request at a time, so build a fresh one per test.
            await run_workflow(request, build_workflow(workflow_client))
    else:
        await run_workflow(" ".join(args) or "Recommend 2 laptops within ₹1,20,000 total.")


if __name__ == "__main__":
    asyncio.run(main())
