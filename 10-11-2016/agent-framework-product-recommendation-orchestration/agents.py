# import asyncio, os
# from agent_framework.openai import OpenAIChatCompletionClient
# from dotenv import load_dotenv

# load_dotenv()  # reads .env into os.environ

# client = OpenAIChatCompletionClient(
#     api_key=os.getenv("OPENROUTER_API_KEY"),
#     base_url="https://openrouter.ai/api/v1",
#     model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
# )
"""
agents.py - Inventory, Pricing and Recommendation agents.

Flow:  CustomerRequest -> InventoryAgent -> PricingAgent -> RecommendationAgent

Each agent's run() returns a plain dict, which is passed to the next agent.
"""

from dataclasses import dataclass
from tools import search_products, calculate_order_total


@dataclass
class CustomerRequest:
    query: str          # product name or category, e.g. "laptop"
    quantity: int = 1   # units the customer wants
    budget_inr: float = None  # max total spend; None means no budget limit


# ---------------------------------------------------------------------------
# Agent 1 - Inventory Agent
# ---------------------------------------------------------------------------
class InventoryAgent:
    name = "Inventory Agent"

    def run(self, request: CustomerRequest) -> dict:
        query = (request.query or "").strip()
        result = search_products(query)

        # Understand simple plurals: "laptops" -> "laptop"
        if not result["success"] and query.lower().endswith("s") and len(query) > 1:
            singular = search_products(query[:-1])
            if singular["success"]:
                result = singular

        products = []
        for p in result["results"]:
            products.append({
                **p,
                "in_stock": p["stock"] > 0,
                "enough_stock": p["stock"] >= request.quantity if isinstance(request.quantity, int) else False,
            })

        return {
            "agent": self.name,
            "success": result["success"],
            "message": result["message"],
            "query": query,
            "products": products,
        }


# ---------------------------------------------------------------------------
# Agent 2 - Pricing Agent
# ---------------------------------------------------------------------------
class PricingAgent:
    name = "Pricing Agent"

    def run(self, request: CustomerRequest, inventory: dict) -> dict:
        if not inventory["success"]:
            return {"agent": self.name, "success": False,
                    "message": "No products to price: " + inventory["message"],
                    "priced": []}

        budget = request.budget_inr
        if budget is not None and (isinstance(budget, bool) or not isinstance(budget, (int, float)) or budget <= 0):
            return {"agent": self.name, "success": False,
                    "message": "Invalid budget: must be a positive number.", "priced": []}

        priced = []
        for p in inventory["products"]:
            order = calculate_order_total(p["id"], request.quantity)

            # Invalid quantity applies to every product, so stop early.
            if not order["success"] and "Invalid quantity" in order["message"]:
                return {"agent": self.name, "success": False,
                        "message": order["message"], "priced": []}

            entry = {
                "id": p["id"],
                "name": p["name"],
                "rating": p["rating"],
                "stock": p["stock"],
                "unit_price_inr": p["price_inr"],
                "quantity": request.quantity,
                "available": order["success"],
                "total_inr": order.get("total_inr"),
                "within_budget": False,
                "note": order["message"],
            }
            if order["success"]:
                entry["within_budget"] = budget is None or order["total_inr"] <= budget
                if not entry["within_budget"]:
                    entry["note"] = f"Total ₹{order['total_inr']:,} exceeds budget ₹{budget:,.0f}."
            priced.append(entry)

        affordable = [e for e in priced if e["available"] and e["within_budget"]]
        return {
            "agent": self.name,
            "success": True,
            "message": f"Priced {len(priced)} product(s); {len(affordable)} available within budget.",
            "budget_inr": budget,
            "priced": priced,
            "affordable_ids": [e["id"] for e in affordable],
        }


# ---------------------------------------------------------------------------
# Agent 3 - Recommendation Agent
# ---------------------------------------------------------------------------
class RecommendationAgent:
    name = "Recommendation Agent"

    def run(self, request: CustomerRequest, inventory: dict, pricing: dict) -> dict:
        if not pricing["success"]:
            return {"agent": self.name, "recommendation": None,
                    "explanation": pricing["message"]}

        # Only available AND affordable products are eligible.
        candidates = [e for e in pricing["priced"] if e["available"] and e["within_budget"]]

        if not candidates:
            return {"agent": self.name, "recommendation": None,
                    "explanation": self._explain_no_match(request, pricing["priced"])}

        # Highest rating first; on equal rating, lower total cost wins.
        candidates.sort(key=lambda e: (-e["rating"], e["total_inr"]))
        best = candidates[0]

        reason = (f"{best['name']} ({best['id']}) has the highest rating ({best['rating']}) "
                  f"among {len(candidates)} option(s) that are in stock")
        reason += " and within budget." if request.budget_inr is not None else "."
        ties = [c for c in candidates[1:] if c["rating"] == best["rating"]]
        if ties:
            reason += (f" It ties on rating with {', '.join(t['name'] for t in ties)}, "
                       f"but costs less.")
        reason += (f" {best['quantity']} unit(s) at ₹{best['unit_price_inr']:,} "
                   f"= ₹{best['total_inr']:,}.")

        return {
            "agent": self.name,
            "recommendation": {
                "id": best["id"],
                "name": best["name"],
                "rating": best["rating"],
                "quantity": best["quantity"],
                "total_inr": best["total_inr"],
            },
            "explanation": reason,
        }

    @staticmethod
    def _explain_no_match(request, priced):
        if not priced:
            return "No matching products were found."
        if not any(e["available"] for e in priced):
            return (f"None of the matching products have {request.quantity} unit(s) in stock.")
        cheapest = min((e for e in priced if e["available"]), key=lambda e: e["total_inr"])
        return (f"No available product fits the budget of ₹{request.budget_inr:,.0f}. "
                f"The cheapest available option is {cheapest['name']} at ₹{cheapest['total_inr']:,}.")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def run_pipeline(query, quantity=1, budget_inr=None, verbose=False):
    request = CustomerRequest(query=query, quantity=quantity, budget_inr=budget_inr)

    inventory = InventoryAgent().run(request)
    pricing = PricingAgent().run(request, inventory)
    recommendation = RecommendationAgent().run(request, inventory, pricing)

    if verbose:
        print(f"\nRequest: {quantity} x '{query}', budget: "
              f"{'none' if budget_inr is None else f'₹{budget_inr:,.0f}'}")
        print(f"  [Inventory]      {inventory['message']}")
        for p in inventory["products"]:
            print(f"                   {p['id']} {p['name']}: ₹{p['price_inr']:,}, "
                  f"stock {p['stock']}, rating {p['rating']}")
        print(f"  [Pricing]        {pricing['message']}")
        for e in pricing["priced"]:
            print(f"                   {e['id']}: {e['note']}")
        rec = recommendation["recommendation"]
        print(f"  [Recommendation] {rec['name'] if rec else 'None'}")
        print(f"                   {recommendation['explanation']}")

    return {"inventory": inventory, "pricing": pricing, "recommendation": recommendation}


if __name__ == "__main__":
    run_pipeline("laptop", quantity=2, budget_inr=120000, verbose=True)
    run_pipeline("smartphones", quantity=1, budget_inr=50000, verbose=True)
    run_pipeline("audio", quantity=3, budget_inr=5000, verbose=True)
    run_pipeline("tablet", quantity=1, budget_inr=30000, verbose=True)