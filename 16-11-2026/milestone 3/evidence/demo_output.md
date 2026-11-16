# Demo evidence
Run date: 2026-11-16

## 0. Health check

`GET /health`
Response (200):
```json
{
  "sqlite": true,
  "redis": true,
  "ollama": true,
  "model": "llama3.2:3b"
}
```

## 1. New employee trip (saved to SQLite)

`POST /trips`
Request:
```json
{
  "employee_id": "EMP104",
  "destination": "Jaipur",
  "start_date": "2026-11-18",
  "end_date": "2026-11-20",
  "purpose": "Client meeting"
}
```
Response (201):
```json
{
  "trip_id": "TRP-0FC5AE9B",
  "employee_id": "EMP104",
  "destination": "Jaipur",
  "start_date": "2026-11-18",
  "end_date": "2026-11-20",
  "purpose": "Client meeting",
  "status": "PLANNED",
  "created_at": "2026-11-16 09:57:30"
}
```

## 2. Existing trip lookup (from SQLite)

`GET /trips/TRP-0FC5AE9B`
Response (200):
```json
{
  "trip_id": "TRP-0FC5AE9B",
  "employee_id": "EMP104",
  "destination": "Jaipur",
  "start_date": "2026-11-18",
  "end_date": "2026-11-20",
  "purpose": "Client meeting",
  "status": "PLANNED",
  "created_at": "2026-11-16 09:57:30"
}
```

## 3. Weather inquiry (LangChain tools + live Open-Meteo forecast)

`POST /assistant/ask`
Request:
```json
{
  "session_id": "sess-emp104",
  "question": "What weather should I expect for my Jaipur trip?",
  "trip_id": "TRP-0FC5AE9B"
}
```
Response (200):
```json
{
  "session_id": "sess-emp104",
  "answer": "Destination: Jaipur, India (2026-11-18 to 2026-11-20)\nWeather: Clear skies expected throughout the trip, with temperatures ranging from 15.4°C to 26.5°C. No precipitation is forecasted.\nAdvice: No specific weather concerns are expected for your trip.\nSuggestions:\n- Pack light and breathable clothing suitable for warm weather.\n- Don't forget to bring sunscreen with a high SPF to protect yourself from the sun.\n- Stay hydrated by drinking plenty of water throughout the day.\n- Consider packing a light jacket or sweater for cooler evenings.",
  "trip_id": "TRP-0BCA0551",
  "destination": "Jaipur",
  "weather_available": true,
  "weather_error": null,
  "tool_calls": [
    {
      "tool": "find_trip_by_destination",
      "args": {
        "destination": "Jaipur"
      },
      "ok": true,
      "by": "model"
    },
    {
      "tool": "get_weather_forecast",
      "args": {
        "city": "Jaipur",
        "start_date": "2026-11-18",
        "end_date": "2026-11-20"
      },
      "ok": true,
      "by": "guard"
    }
  ],
  "session_context": {
    "trip_id": "TRP-0BCA0551",
    "destination": "Jaipur",
    "start_date": "2026-11-18",
    "end_date": "2026-11-20"
  }
}
```

## 4. Follow-up question (Redis session memory)

`POST /assistant/ask`
Request:
```json
{
  "session_id": "sess-emp104",
  "question": "Should I pack an umbrella and light jacket?"
}
```
Response (200):
```json
{
  "session_id": "sess-emp104",
  "answer": "No, an umbrella is not needed as there is no precipitation forecasted. However, a light jacket or sweater is suggested for cooler evenings, as the temperature drops to around 14.0°C on the last day of your trip.",
  "trip_id": "TRP-0BCA0551",
  "destination": "Jaipur",
  "weather_available": true,
  "weather_error": null,
  "tool_calls": [
    {
      "tool": "find_trip_by_destination",
      "args": {
        "destination": "Jaipur"
      },
      "ok": true,
      "by": "model"
    },
    {
      "tool": "get_weather_forecast",
      "args": {
        "city": "Jaipur",
        "start_date": "2026-11-18",
        "end_date": "2026-11-20"
      },
      "ok": true,
      "by": "guard"
    }
  ],
  "session_context": {
    "trip_id": "TRP-0BCA0551",
    "destination": "Jaipur",
    "start_date": "2026-11-18",
    "end_date": "2026-11-20"
  }
}
```

## 4b. Another follow-up

`POST /assistant/ask`
Request:
```json
{
  "session_id": "sess-emp104",
  "question": "Will I need an umbrella there?"
}
```
Response (200):
```json
{
  "session_id": "sess-emp104",
  "answer": "No, an umbrella is not needed as there is no precipitation forecasted.",
  "trip_id": "TRP-0BCA0551",
  "destination": "Jaipur",
  "weather_available": true,
  "weather_error": null,
  "tool_calls": [
    {
      "tool": "find_trip_by_destination",
      "args": {
        "destination": "Jaipur"
      },
      "ok": true,
      "by": "model"
    },
    {
      "tool": "get_trip_details",
      "args": {
        "trip_id": "TRP-0BCA0551"
      },
      "ok": true,
      "by": "model"
    },
    {
      "tool": "get_weather_forecast",
      "args": {
        "city": "Jaipur",
        "start_date": "2026-11-18",
        "end_date": "2026-11-20"
      },
      "ok": true,
      "by": "guard"
    }
  ],
  "session_context": {
    "trip_id": "TRP-0BCA0551",
    "destination": "Jaipur",
    "start_date": "2026-11-18",
    "end_date": "2026-11-20"
  }
}
```

## 4c. Session memory stored in Redis

`GET /assistant/sessions/sess-emp104`
Response (200):
```json
{
  "context": {
    "trip_id": "TRP-0BCA0551",
    "destination": "Jaipur",
    "start_date": "2026-11-18",
    "end_date": "2026-11-20"
  },
  "history": [
    {
      "role": "user",
      "content": "What weather should I expect for my Jaipur trip?"
    },
    {
      "role": "assistant",
      "content": "Destination: Jaipur, India (2026-11-18 to 2026-11-20)\nWeather: Clear skies expected throughout the trip, with temperatures ranging from 15.4°C to 26.5°C. No precipitation is forecasted.\nAdvice: No specific weather concerns are expected for your trip.\nSuggestions:\n- Pack light and breathable clothing suitable for warm weather.\n- Don't forget to bring sunscreen with a high SPF to protect yourself from the sun.\n- Stay hydrated by drinking plenty of water throughout the day.\n- Consider packing a light jacket or sweater for cooler evenings."
    },
    {
      "role": "user",
      "content": "Should I pack an umbrella and light jacket?"
    },
    {
      "role": "assistant",
      "content": "No, an umbrella is not needed as there is no precipitation forecasted. However, a light jacket or sweater is suggested for cooler evenings, as the temperature drops to around 14.0°C on the last day of your trip."
    },
    {
      "role": "user",
      "content": "Will I need an umbrella there?"
    },
    {
      "role": "assistant",
      "content": "No, an umbrella is not needed as there is no precipitation forecasted."
    }
  ]
}
```

## 5. Session isolation (new session, same follow-up)

`POST /assistant/ask`
Request:
```json
{
  "session_id": "sess-other",
  "question": "Will I need an umbrella there?"
}
```
Response (200):
```json
{
  "session_id": "sess-other",
  "answer": "Destination: Not specified (<dates>)\nWeather: Weather not retrieved because no trip/destination was identified.\nAdvice: Please provide the destination and dates to get the weather information.\nSuggestions: \n- Check with your travel provider for assistance.\n- Verify your destination and dates before proceeding.\n- Ensure you have a reliable source for weather updates.",
  "trip_id": null,
  "destination": null,
  "weather_available": false,
  "weather_error": "Weather not retrieved because no trip/destination was identified.",
  "tool_calls": [
    {
      "tool": "get_weather_forecast",
      "args": {
        "city": "destination",
        "start_date": "start_date",
        "end_date": "end_date"
      },
      "ok": false,
      "by": "model"
    }
  ],
  "session_context": {}
}
```

## 6a. Invalid dates (end before start) -> 422

`POST /trips`
Request:
```json
{
  "employee_id": "EMP104",
  "destination": "Jaipur",
  "start_date": "2026-11-21",
  "end_date": "2026-11-17",
  "purpose": "Client meeting"
}
```
Response (422):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": [
        "body"
      ],
      "msg": "Value error, end_date must be on or after start_date",
      "input": {
        "employee_id": "EMP104",
        "destination": "Jaipur",
        "start_date": "2026-11-21",
        "end_date": "2026-11-17",
        "purpose": "Client meeting"
      },
      "ctx": {
        "error": {}
      }
    }
  ]
}
```

## 6b. Invalid employee id -> 422

`POST /trips`
Request:
```json
{
  "employee_id": "104",
  "destination": "Jaipur",
  "start_date": "2026-11-18",
  "end_date": "2026-11-20",
  "purpose": "Client meeting"
}
```
Response (422):
```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": [
        "body",
        "employee_id"
      ],
      "msg": "String should match pattern '^EMP\\d{3,6}$'",
      "input": "104",
      "ctx": {
        "pattern": "^EMP\\d{3,6}$"
      }
    }
  ]
}
```

## 6c. Unknown trip ID -> 404

`GET /trips/TRP-DOESNOTEXIST`
Response (404):
```json
{
  "detail": "Trip 'TRP-DOESNOTEXIST' not found"
}
```

## 6d. Date beyond forecast horizon -> no fabricated weather

`POST /assistant/ask`
Request:
```json
{
  "session_id": "sess-emp411",
  "question": "What's the weather going to be like on my trip?",
  "trip_id": "TRP-1AF44E4B"
}
```
Response (200):
```json
{
  "session_id": "sess-emp411",
  "answer": "Destination: Bengaluru, India (2026-12-26 to 2026-12-28)\nWeather: Forecast unavailable due to trip dates being beyond the forecast horizon.\nAdvice: Please check the forecast for the specific dates of your trip or contact the travel agency for assistance.\nSuggestions:\n- Verify the dates of your trip to ensure they are within the forecast horizon.\n- Contact the travel agency for assistance with finding alternative dates or making changes to your trip.\n- Check the weather forecast for the specific dates of your trip to plan accordingly.\n- Pack accordingly for the expected weather conditions.",
  "trip_id": "TRP-1AF44E4B",
  "destination": "Bengaluru",
  "weather_available": false,
  "weather_error": "Trip dates 2026-12-26 to 2026-12-28 are beyond the forecast horizon (forecast is only available up to 2026-12-01).",
  "tool_calls": [
    {
      "tool": "get_trip_details",
      "args": {
        "trip_id": "TRP-1AF44E4B"
      },
      "ok": true,
      "by": "model"
    },
    {
      "tool": "find_trip_by_destination",
      "args": {
        "destination": "Bengaluru"
      },
      "ok": true,
      "by": "model"
    },
    {
      "tool": "get_weather_forecast",
      "args": {
        "city": "Bengaluru",
        "start_date": "2026-12-26",
        "end_date": "2026-12-28"
      },
      "ok": false,
      "by": "guard"
    }
  ],
  "session_context": {
    "trip_id": "TRP-1AF44E4B",
    "destination": "Bengaluru",
    "start_date": "2026-12-26",
    "end_date": "2026-12-28"
  }
}
```

## 6e. Unknown destination -> geocoding failure reported

`POST /assistant/ask`
Request:
```json
{
  "session_id": "sess-emp999",
  "question": "What weather should I expect?",
  "trip_id": "TRP-62370288"
}
```
Response (200):
```json
{
  "session_id": "sess-emp999",
  "answer": "Forecast is unavailable. The destination 'Xyzzyqwerty' could not be found by the geocoding service.",
  "trip_id": "TRP-62370288",
  "destination": "Xyzzyqwerty",
  "weather_available": false,
  "weather_error": "Destination 'Xyzzyqwerty' could not be found by the geocoding service.",
  "tool_calls": [
    {
      "tool": "get_weather_forecast",
      "args": {
        "start_date": "2026-11-18",
        "end_date": "2026-11-19",
        "city": "Xyzzyqwerty"
      },
      "ok": false,
      "by": "model"
    },
    {
      "tool": "get_trip_details",
      "args": {
        "trip_id": "TRP-62370288"
      },
      "ok": true,
      "by": "guard"
    }
  ],
  "session_context": {
    "trip_id": "TRP-62370288",
    "destination": "Xyzzyqwerty",
    "start_date": "2026-11-18",
    "end_date": "2026-11-19"
  }
}
```
