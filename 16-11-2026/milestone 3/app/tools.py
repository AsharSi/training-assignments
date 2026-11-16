"""LangChain tools: the ONLY source of trip and weather facts for the assistant."""
import json

from langchain_core.tools import tool

from . import db
from .weather import WeatherError, get_forecast


@tool
def get_trip_details(trip_id: str) -> str:
    """Look up a saved business trip by its trip ID (format TRP-XXXXXXXX).
    Returns destination, start_date, end_date, purpose and status."""
    trip = db.get_trip(trip_id)
    if not trip:
        return json.dumps({"error": f"No trip found with ID '{trip_id}'."})
    return json.dumps(trip)


@tool
def find_trip_by_destination(destination: str) -> str:
    """Find a saved business trip by destination city name (e.g. 'Jaipur').
    Use this when the user mentions a city but no trip ID."""
    trip = db.find_trip_by_destination(destination)
    if not trip:
        return json.dumps({"error": f"No saved trip found for destination '{destination}'."})
    return json.dumps(trip)


@tool
def get_weather_forecast(city: str, start_date: str, end_date: str) -> str:
    """Get the live daily weather forecast (temperature, precipitation, conditions) for a city
    between start_date and end_date (YYYY-MM-DD). Use the trip's own dates."""
    try:
        return json.dumps(get_forecast(city, start_date, end_date))
    except WeatherError as e:
        return json.dumps({"error": str(e), "weather_available": False})


TOOLS = [get_trip_details, find_trip_by_destination, get_weather_forecast]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
