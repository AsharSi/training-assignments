"""Open-Meteo geocoding + forecast client. Never invents data: every failure is reported explicitly."""
from datetime import date, timedelta

import httpx

from .config import FORECAST_HORIZON_DAYS, FORECAST_URL, GEOCODING_URL

WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow", 77: "snow grains",
    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    85: "slight snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
}


class WeatherError(Exception):
    """Raised for missing locations, unsupported dates or API failures."""


def geocode(city: str) -> dict:
    try:
        r = httpx.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "en", "format": "json"},
                      timeout=10)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise WeatherError(f"Geocoding service unavailable: {e.__class__.__name__}") from e
    results = r.json().get("results") or []
    if not results:
        raise WeatherError(f"Destination '{city}' could not be found by the geocoding service.")
    g = results[0]
    return {"name": g["name"], "country": g.get("country"), "latitude": g["latitude"],
            "longitude": g["longitude"], "timezone": g.get("timezone", "auto")}


def get_forecast(city: str, start_date: str, end_date: str) -> dict:
    """Return a daily forecast for the overlap of [start_date, end_date] with the forecast horizon."""
    try:
        start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    except ValueError as e:
        raise WeatherError(f"Invalid date format: {e}") from e
    if end < start:
        raise WeatherError("End date is before start date.")

    today = date.today()
    horizon_end = today + timedelta(days=FORECAST_HORIZON_DAYS - 1)
    if end < today:
        raise WeatherError(f"Trip dates {start_date} to {end_date} are in the past; no forecast available.")
    if start > horizon_end:
        raise WeatherError(
            f"Trip dates {start_date} to {end_date} are beyond the forecast horizon "
            f"(forecast is only available up to {horizon_end.isoformat()}).")

    eff_start, eff_end = max(start, today), min(end, horizon_end)
    loc = geocode(city)
    params = {
        "latitude": loc["latitude"], "longitude": loc["longitude"], "timezone": "auto",
        "start_date": eff_start.isoformat(), "end_date": eff_end.isoformat(),
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                 "precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
    }
    try:
        r = httpx.get(FORECAST_URL, params=params, timeout=10)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise WeatherError(f"Forecast service unavailable: {e.__class__.__name__}") from e

    d = r.json().get("daily") or {}
    if not d.get("time"):
        raise WeatherError("Forecast service returned no daily data.")
    days = []
    for i, day in enumerate(d["time"]):
        days.append({
            "date": day,
            "conditions": WMO_CODES.get(d["weather_code"][i], f"code {d['weather_code'][i]}"),
            "temp_max_c": d["temperature_2m_max"][i],
            "temp_min_c": d["temperature_2m_min"][i],
            "precipitation_mm": d["precipitation_sum"][i],
            "precipitation_probability_pct": d["precipitation_probability_max"][i],
            "wind_max_kmh": d["wind_speed_10m_max"][i],
        })
    notes = []
    if eff_start > start:
        notes.append(f"Days before {eff_start} are in the past and not covered.")
    if eff_end < end:
        notes.append(f"Days after {eff_end} are beyond the forecast horizon and NOT covered.")
    return {"location": loc, "requested": {"start": start_date, "end": end_date},
            "covered": {"start": eff_start.isoformat(), "end": eff_end.isoformat()},
            "notes": notes, "daily": days, "source": "Open-Meteo"}
