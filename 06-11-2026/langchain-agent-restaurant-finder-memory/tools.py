from langchain.tools import tool
from pathlib import Path
import json

from guardrails import validate_guests

FILE = Path(__file__).parent / "restaurants.json"


def get_restaurants():
    return json.loads(FILE.read_text(encoding="utf-8"))


def format_restaurant(r) -> str:
    return (
        f"id: {r['id']}, {r['name']} ({r['cuisine']}, {r['location']}), "
        f"₹{r['price_per_person']} per person, {r['available_seats']} seats available"
    )


@tool
def search_restaurants(query: str) -> str:
    """Search restaurants by cuisine type or restaurant name keyword.

    Args:
        query: A cuisine (e.g. "Indian", "Italian") or part of a restaurant
            name (e.g. "Spice Garden"). Matches name, cuisine or location.

    Returns each match's id, name, cuisine, location, price per person and available seats.
    """
    q = query.strip().lower()
    if not q:
        return "Please provide a cuisine type or restaurant name to search for."

    matches = [
        format_restaurant(r)
        for r in get_restaurants()
        if q in r["name"].lower() or q in r["cuisine"].lower() or q in r["location"].lower()
    ]

    if not matches:
        return f"No restaurants found matching '{query}'."

    return "\n".join(matches)


@tool
def calculate_dining_cost(restaurant_id: str, guests: int) -> str:
    """Calculate the estimated total dining cost for a group at a restaurant.

    Use this after finding a restaurant with search_restaurants, when the user
    asks how much a meal will cost for their group.

    Args:
        restaurant_id: The restaurant's ID, as returned by search_restaurants (e.g. "R101").
        guests: Number of people dining, between 1 and 20.

    Returns the per-person price, number of guests, and estimated total cost.
    """
    error = validate_guests(guests)
    if error:
        return error

    for r in get_restaurants():
        if r["id"].lower() == restaurant_id.strip().lower():
            total = r["price_per_person"] * guests
            result = (
                f"{r['name']} ({r['id']}): ₹{r['price_per_person']} per person × "
                f"{guests} guests = ₹{total} estimated total."
            )
            if guests > r["available_seats"]:
                result += f" Note: only {r['available_seats']} seats are currently available."
            return result

    return f"No restaurant found with ID {restaurant_id}."
