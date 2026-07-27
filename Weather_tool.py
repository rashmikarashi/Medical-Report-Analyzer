"""
Weather tool — external API integration (Day 5).

Uses Open-Meteo (https://open-meteo.com), a free weather API that needs
NO API key/signup, so the agent stays instantly runnable for anyone who
clones the repo. Two calls are made:
  1. Geocoding API: place name -> lat/lon
  2. Forecast API: lat/lon -> current conditions (temp, pressure, humidity)

Why weather, tied to the Day 4 medical agent: barometric pressure drops and
temperature swings are commonly self-reported triggers for migraines, joint
pain, and respiratory symptoms. This tool lets the agent add that contextual
signal to its summary — never as a diagnosis, only as an observation the
patient/clinician may find useful.
"""

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10


def get_weather(location: str) -> dict:
    """Look up current weather conditions for a place name. Returns a dict
    with temperature_c, humidity_pct, pressure_hpa, wind_kph, conditions,
    or an 'error' key if the lookup failed."""
    try:
        geo = requests.get(
            GEOCODE_URL, params={"name": location, "count": 1}, timeout=TIMEOUT
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return {"error": f"Could not find location '{location}'."}
        lat, lon = results[0]["latitude"], results[0]["longitude"]
        resolved_name = f"{results[0]['name']}, {results[0].get('country', '')}"

        fc = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,weather_code",
            },
            timeout=TIMEOUT,
        )
        fc.raise_for_status()
        current = fc.json().get("current", {})

        return {
            "location": resolved_name,
            "temperature_c": current.get("temperature_2m"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "pressure_hpa": current.get("surface_pressure"),
            "wind_kph": current.get("wind_speed_10m"),
            "conditions_code": current.get("weather_code"),
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Weather API request failed: {e}"}
