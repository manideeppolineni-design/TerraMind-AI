
from datetime import datetime
from pathlib import Path
import os

import httpx

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, text

from backend.flood_analysis import analyze_flood_risk
from backend.ai_agent import analyze_with_agent


# ==================================================
# APPLICATION
# ==================================================

@app.get("/api/v1/location/search")
async def search_location(
    q: str = Query(..., min_length=2, max_length=150),
    limit: int = Query(8, ge=1, le=10)
):
    url = "https://photon.komoot.io/api/"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                params={
                    "q": q.strip(),
                    "limit": limit,
                    "lang": "en",
                    "lat": 20.5937,
                    "lon": 78.9629
                }
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="Location search is temporarily unavailable."
        )

    results = []

    for feature in data.get("features", []):
        properties = feature.get("properties", {})
        coordinates = feature.get("geometry", {}).get("coordinates", [])

        if len(coordinates) < 2:
            continue

        country = properties.get("country", "")

        if country and country.lower() not in ("india", "भारत"):
            continue

        name = (
            properties.get("name")
            or properties.get("city")
            or properties.get("district")
            or properties.get("county")
        )

        if not name:
            continue

        results.append({
            "name": name,
            "state": properties.get("state"),
            "district": properties.get("district"),
            "country": country or "India",
            "type": properties.get("type"),
            "latitude": coordinates[1],
            "longitude": coordinates[0]
        })

    return {
        "query": q.strip(),
        "count": len(results),
        "results": results
    }

# ==================================================
# DATABASE CONFIGURATION
# ==================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

engine = create_engine(DATABASE_URL)


# ==================================================
# HOME
# ==================================================

@app.get("/")
def home():
    return {
        "project": "TerraMind AI",
        "message": "Flood analysis system is running"
    }


# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ==================================================
# PROJECT INFORMATION
# ==================================================

@app.get("/api/v1/project")
def project_info():
    return {
        "name": "TerraMind AI",
        "features": [
            "Satellite data analysis",
            "Flood detection",
            "Geospatial impact analysis",
            "Disaster report retrieval",
            "Agentic AI",
            "Live weather monitoring",
            "Historical flood analysis"
        ]
    }


# ==================================================
# WEATHER API
# ==================================================

@app.get("/api/v1/weather")
async def get_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "weather_code"
        ],

        "hourly": [
            "precipitation",
            "rain",
            "precipitation_probability"
        ],

        "forecast_days": 2,
        "timezone": "auto"
    }

    try:

        async with httpx.AsyncClient(timeout=20) as client:

            response = await client.get(
                url,
                params=params
            )

            response.raise_for_status()

            weather_data = response.json()

        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "current_weather": weather_data.get("current"),

            "hourly_forecast": weather_data.get("hourly"),

            "source": "Open-Meteo"
        }

    except httpx.HTTPError:

        raise HTTPException(
            status_code=503,
            detail="Weather data is temporarily unavailable"
        )


# ==================================================
# LOCATION HISTORY API
# ==================================================

@app.get("/api/v1/location/history")
def get_location_history(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):

    # Satellite grid search area
    south = latitude - 1
    north = latitude + 1

    west = longitude - 1
    east = longitude + 1

    with engine.connect() as connection:

        # ------------------------------------------
        # SATELLITE HISTORY
        # ------------------------------------------

        satellite_query = text("""
            SELECT
                g.grid_id,
                g.south,
                g.west,
                y.year,
                y.image_count

            FROM india_grid_catalogue g

            JOIN grid_yearly_observations y
                ON g.grid_id = y.grid_id

            WHERE g.south BETWEEN :south AND :north
              AND g.west BETWEEN :west AND :east

            ORDER BY y.year
        """)

        satellite_result = connection.execute(
            satellite_query,
            {
                "south": south,
                "north": north,
                "west": west,
                "east": east
            }
        )

        satellite_records = [
            dict(row._mapping)
            for row in satellite_result
        ]

        # ------------------------------------------
        # HISTORICAL FLOOD EVENTS
        # ------------------------------------------

        flood_query = text("""
            SELECT
                event_name,
                location,
                state,
                event_date,
                rainfall_mm,
                flood_severity,
                source,
                latitude,
                longitude,

                (
                    6371 * acos(
                        LEAST(
                            1.0,
                            GREATEST(
                                -1.0,

                                cos(radians(:latitude))
                                * cos(radians(latitude))
                                * cos(
                                    radians(longitude)
                                    - radians(:longitude)
                                )

                                + sin(radians(:latitude))
                                * sin(radians(latitude))
                            )
                        )
                    )
                ) AS distance_km

            FROM historical_flood_events

            WHERE latitude IS NOT NULL
              AND longitude IS NOT NULL

            ORDER BY distance_km ASC
        """)

        flood_result = connection.execute(
            flood_query,
            {
                "latitude": latitude,
                "longitude": longitude
            }
        )

        # Keep only events within 50 km
        flood_records = []

        for row in flood_result:

            record = dict(row._mapping)

            distance = record.get("distance_km")

            if distance is not None and distance <= 50:

                flood_records.append(record)

    return {
        "selected_location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "satellite_history": satellite_records,

        "historical_flood_events": flood_records,

        "historical_flood_count": len(flood_records),

        "search_radius_km": 50,

        "historical_data_status": (
            "Available"
            if flood_records
            else "No nearby historical flood records found"
        )
    }


# ==================================================
# COMPLETE LOCATION API
# ==================================================

@app.get("/api/v1/location/complete")
async def get_complete_location_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):

    # Get weather
    weather = await get_weather(
        latitude=latitude,
        longitude=longitude
    )

    # Get location history
    history = get_location_history(
        latitude=latitude,
        longitude=longitude
    )

    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "current_weather": weather,

        "historical_information": history
    }


# ==================================================
# MANUAL FLOOD ANALYSIS API
# ==================================================

@app.get("/api/v1/flood/analyze")
def flood_analysis_api(
    rainfall_mm: float = Query(..., ge=0),
    forecast_rainfall_mm: float = Query(..., ge=0),
    historical_flood_count: int = Query(0, ge=0)
):

    try:

        result = analyze_flood_risk(
            rainfall_mm=rainfall_mm,
            forecast_rainfall_mm=forecast_rainfall_mm,
            historical_flood_count=historical_flood_count
        )

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ==================================================
# AUTOMATIC LOCATION FLOOD ANALYSIS
# ==================================================

@app.get("/api/v1/flood/analyze/location")
async def analyze_selected_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):

    # ----------------------------------------------
    # 1. GET WEATHER
    # ----------------------------------------------

    weather = await get_weather(
        latitude=latitude,
        longitude=longitude
    )

    current_weather = weather.get("current_weather") or {}

    hourly = weather.get("hourly_forecast") or {}

    # ----------------------------------------------
    # 2. CURRENT RAINFALL
    # ----------------------------------------------

    current_rainfall = current_weather.get("rain")

    if current_rainfall is None:

        current_rainfall = current_weather.get(
            "precipitation"
        )

    # ----------------------------------------------
    # 3. HOURLY FORECAST
    # ----------------------------------------------

    hourly_times = hourly.get("time", [])

    hourly_rainfall = hourly.get("precipitation", [])

    forecast_rainfall = None

    current_time = current_weather.get("time")

    # ----------------------------------------------
    # 4. CALCULATE NEXT 24 HOURS
    # ----------------------------------------------

    if (
        current_time
        and hourly_times
        and hourly_rainfall
    ):

        # Current hour in local forecast timezone
        current_hour = current_time[:13] + ":00"

        start_index = next(
            (
                index
                for index, forecast_time
                in enumerate(hourly_times)
                if forecast_time >= current_hour
            ),
            None
        )

        if start_index is not None:

            next_24_hours = hourly_rainfall[
                start_index:start_index + 24
            ]

            if len(next_24_hours) == 24:

                forecast_rainfall = sum(
                    float(value or 0)
                    for value in next_24_hours
                )

    # ----------------------------------------------
    # 5. GET LOCATION HISTORY
    # ----------------------------------------------

    history = get_location_history(
        latitude=latitude,
        longitude=longitude
    )

    historical_flood_count = history.get(
        "historical_flood_count",
        0
    )

    historical_events = history.get(
        "historical_flood_events",
        []
    )

    # ----------------------------------------------
    # 6. FLOOD ANALYSIS
    # ----------------------------------------------

    if (
        current_rainfall is not None
        and forecast_rainfall is not None
    ):

        risk_result = analyze_flood_risk(
            rainfall_mm=current_rainfall,
            forecast_rainfall_mm=forecast_rainfall,
            historical_flood_count=historical_flood_count
        )

    else:

        risk_result = {
            "risk_level": "INSUFFICIENT_DATA",

            "explanation": (
                "Current or forecast rainfall data "
                "is unavailable."
            ),

            "official_warning": False
        }

    # ----------------------------------------------
    # 7. FINAL RESPONSE
    # ----------------------------------------------

    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "current_weather": current_weather,

        "forecast_rainfall_next_24_hours_mm": (
            forecast_rainfall
        ),

        "flood_analysis": risk_result,

        "historical_flood_count": (
            historical_flood_count
        ),

        "historical_flood_events": (
            historical_events
        ),

        "historical_data_status": (
            history.get("historical_data_status")
        ),

        "satellite_history": (
            history.get("satellite_history")
        ),

        "source": "Open-Meteo",

        "analysis_time": datetime.now().isoformat()
    }


@app.post("/api/v1/agent/analyze")
async def agent_flood_analysis(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    try:
        weather = await get_weather(
            latitude=latitude,
            longitude=longitude
        )

        history = get_location_history(
            latitude=latitude,
            longitude=longitude
        )

        evidence = {
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "weather": weather,
            "historical_data": history
        }

        result = await analyze_with_agent(evidence)

        return {
            "location": evidence["location"],
            "evidence": evidence,
            "ai_analysis": result
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

