import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
SESSION_MAX_MESSAGES = int(os.getenv("SESSION_MAX_MESSAGES", "10"))
DB_PATH = str(BASE_DIR / os.getenv("DB_PATH", "trips.db"))
GEOCODING_URL = os.getenv("GEOCODING_URL", "https://geocoding-api.open-meteo.com/v1/search")
FORECAST_URL = os.getenv("FORECAST_URL", "https://api.open-meteo.com/v1/forecast")
FORECAST_HORIZON_DAYS = 16  # Open-Meteo free forecast horizon
