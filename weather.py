from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server for weather tools
mcp = FastMCP("weather")

# Constants for the National Weather Service API
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

def _doc_url(endpoint: str) -> str:
    """Return the full documentation URL for a given NWS endpoint (for future reference)."""
    return f"{NWS_API_BASE}/{endpoint}"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """
    Make an asynchronous HTTP GET request to the NWS API with proper headers and error handling.

    Args:
        url: The full URL to request from the NWS API.
    Returns:
        The parsed JSON response as a dictionary, or None if the request fails.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            # Log error in production code
            return None

def format_alert(feature: dict) -> str:
    """
    Format a single weather alert feature from the NWS API into a readable string.

    Args:
        feature: A dictionary representing a single alert feature from the API.
    Returns:
        A formatted string describing the alert.
    """
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    Retrieve active weather alerts for a given US state using the NWS API.

    Args:
        state: Two-letter US state code (e.g. 'CA', 'NY').
    Returns:
        A formatted string of active alerts, or a message if none are found or on error.
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    Retrieve the weather forecast for a specific latitude and longitude using the NWS API.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
    Returns:
        A formatted string with the next 5 forecast periods, or an error message.
    """
    # First, get the forecast grid endpoint for the given coordinates
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the forecast periods into a readable string (limit to next 5 periods)
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    # Entry point: run the FastMCP server using stdio transport
    mcp.run(transport='stdio')