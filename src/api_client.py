from typing import Any

import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"


class WeatherAPIError(Exception):
    """Raised when an Open-Meteo API request fails."""


def request_json(url: str, params: dict[str, Any], timeout: int = 60,) -> dict:
    """Send a GET request and return a validated JSON object.
    Returns:
        The decoded JSON response as a dictionary.

    Raises:
        WeatherAPIError: If the request fails, the response is invalid, or the
            API returns an inline error object."""
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise WeatherAPIError(
            f"API request failed for {url}: {error}"
        ) from error

    try:
        payload = response.json()
    except ValueError as error:
        raise WeatherAPIError(
            f"The API returned invalid JSON for {url}."
        ) from error

    if not isinstance(payload, dict):
        raise WeatherAPIError(
            f"Unexpected API response from {url}."
        )

    if payload.get("error"):
        raise WeatherAPIError(
            payload.get("reason", "The API returned an error.")
        )

    return payload

def geocode_city(city_name: str) -> dict:
    """Resolve a city name using Open-Meteo's Geocoding API.
    Args:
        city_name: City name to search for.

    Returns:
        A normalized dictionary describing the top geocoding match.

    Raises:
        WeatherAPIError: If the city name is empty, no results are found, or
            the top result does not contain valid coordinates."""
    payload = request_json(
        GEOCODING_URL,
        params={
            "name": city_name,
            "count": 10,
            "language": "en",
            "format": "json",
            "countryCode": "MX",
        },
    )

    results = payload.get("results", [])

    if not results:
        raise WeatherAPIError(
            f"No location was found for {city_name}, Mexico."
        )

    result = results[0]

    return {
        "city": city_name,
        "resolved_name": result.get("name"),
        "admin1": result.get("admin1"),
        "country": result.get("country"),
        "country_code": result.get("country_code"),
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "timezone": result.get("timezone"),
    }

def get_historical_weather(latitude: float,longitude: float,timezone: str,start_date: str = "2023-01-01",end_date: str = "2025-12-31",) -> dict:
    """
    Extract daily historical weather data from Open-Meteo's Archive API.
    Returns:
        The full raw JSON payload returned by Open-Meteo.
    """
    DAILY_VARIABLES = [
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "precipitation_sum",
        "rain_sum",
        "precipitation_hours",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "shortwave_radiation_sum",
    ]
    return request_json(
        HISTORICAL_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ",".join(DAILY_VARIABLES),
            "timezone": timezone,
        },
    )