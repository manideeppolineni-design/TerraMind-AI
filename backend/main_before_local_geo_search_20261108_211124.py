
from datetime import datetime
from pathlib import Path
import os

import httpx

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

from backend.flood_analysis import analyze_flood_risk
from backend.ai_agent import analyze_with_agent


# ==================================================
# APPLICATION
# ==================================================

app = FastAPI(
    title="TerraMind AI",
    description="Agentic Satellite Intelligence and Flood Impact Analysis",
    version="1.0.0"
)



# Allow the frontend dashboard to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
# FLOOD ALERT DATABASE INITIALIZATION
# ==================================================

def initialize_flood_alerts_table():

    create_table_query = text("""
        CREATE TABLE IF NOT EXISTS flood_alerts (
            id BIGSERIAL PRIMARY KEY,
            location_name VARCHAR(200) NOT NULL,
            district VARCHAR(200),
            state VARCHAR(200),
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            risk_level VARCHAR(30) NOT NULL,
            current_rainfall_mm DOUBLE PRECISION,
            forecast_rainfall_mm DOUBLE PRECISION,
            total_rainfall_mm DOUBLE PRECISION,
            historical_flood_count INTEGER DEFAULT 0,
            explanation TEXT,
            analysis_time TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    with engine.begin() as connection:
        connection.execute(create_table_query)

        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flood_alerts_location
            ON flood_alerts (latitude, longitude);
        """))

        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flood_alerts_created_at
            ON flood_alerts (created_at DESC);
        """))


initialize_flood_alerts_table()



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
# PLACE NAME SEARCH API
# ==================================================

@app.get("/api/v1/location/search")
async def search_location(
    q: str = Query(..., min_length=2, max_length=150),
    limit: int = Query(8, ge=1, le=10)
):
    """Search Indian places using Open-Meteo with Photon fallback."""

    query = q.strip()

    if len(query) < 2:
        raise HTTPException(
            status_code=400,
            detail="Enter at least two characters to search."
        )

    results = []
    seen = set()
    errors = []

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        headers={"User-Agent": "TerraMindAI/1.0"}
    ) as client:

        # PROVIDER 1: OPEN-METEO
        try:
            response = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": query,
                    "count": limit,
                    "countryCode": "IN",
                    "language": "en",
                    "format": "json"
                }
            )
            response.raise_for_status()
            data = response.json()

            for place in data.get("results", []):
                if place.get("country_code", "").upper() != "IN":
                    continue

                latitude = place.get("latitude")
                longitude = place.get("longitude")

                if latitude is None or longitude is None:
                    continue

                key = (round(latitude, 4), round(longitude, 4))

                if key in seen:
                    continue

                seen.add(key)

                results.append({
                    "name": place.get("name"),
                    "state": place.get("admin1"),
                    "district": place.get("admin2"),
                    "subdistrict": place.get("admin3"),
                    "country": place.get("country", "India"),
                    "type": place.get("feature_code"),
                    "latitude": latitude,
                    "longitude": longitude,
                    "population": place.get("population"),
                    "timezone": place.get("timezone"),
                    "source": "Open-Meteo Geocoding"
                })

        except (httpx.HTTPError, ValueError) as error:
            errors.append(f"Open-Meteo: {str(error)}")

        # PROVIDER 2: PHOTON FALLBACK
        if len(results) < limit:
            try:
                response = await client.get(
                    "https://photon.komoot.io/api/",
                    params={
                        "q": query,
                        "limit": limit * 2,
                        "lang": "en"
                    }
                )
                response.raise_for_status()
                data = response.json()

                for feature in data.get("features", []):
                    properties = feature.get("properties", {})
                    coordinates = feature.get("geometry", {}).get("coordinates", [])

                    if len(coordinates) < 2:
                        continue

                    country = (
                        properties.get("country")
                        or properties.get("countrycode")
                        or ""
                    )

                    if country.upper() not in ("IN", "INDIA"):
                        continue

                    longitude, latitude = coordinates[0], coordinates[1]
                    key = (round(latitude, 4), round(longitude, 4))

                    if key in seen:
                        continue

                    seen.add(key)

                    results.append({
                        "name": (
                            properties.get("name")
                            or properties.get("locality")
                            or properties.get("district")
                            or properties.get("city")
                        ),
                        "state": properties.get("state"),
                        "district": (
                            properties.get("district")
                            or properties.get("county")
                        ),
                        "subdistrict": properties.get("suburb"),
                        "country": "India",
                        "type": properties.get("type"),
                        "latitude": latitude,
                        "longitude": longitude,
                        "population": None,
                        "timezone": None,
                        "source": "Photon OpenStreetMap"
                    })

                    if len(results) >= limit:
                        break

            except (httpx.HTTPError, ValueError) as error:
                errors.append(f"Photon: {str(error)}")

    return {
        "query": query,
        "count": len(results),
        "results": results,
        "providers": ["Open-Meteo", "Photon"],
        "message": (
            "Some smaller or remote places may not be indexed "
            "by the available geocoding providers."
        ),
        "provider_errors": errors if not results else []
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
        "saved_alert_id": saved_alert_id,
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
    longitude: float = Query(..., ge=-180, le=180),
    location_name: str = Query("Unknown location", max_length=200),
    district: str = Query(None, max_length=200),
    state: str = Query(None, max_length=200)
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
    # 7. SAVE FLOOD ALERT TO POSTGRESQL
    # ----------------------------------------------

    saved_alert_id = None

    with engine.begin() as connection:

        saved_alert_id = connection.execute(
            text("""
                INSERT INTO flood_alerts (
                    location_name,
                    district,
                    state,
                    latitude,
                    longitude,
                    risk_level,
                    current_rainfall_mm,
                    forecast_rainfall_mm,
                    total_rainfall_mm,
                    historical_flood_count,
                    explanation,
                    analysis_time
                )
                VALUES (
                    :location_name,
                    :district,
                    :state,
                    :latitude,
                    :longitude,
                    :risk_level,
                    :current_rainfall,
                    :forecast_rainfall,
                    :total_rainfall,
                    :historical_count,
                    :explanation,
                    :analysis_time
                )
                RETURNING id
            """),
            {
                "location_name": location_name,
                "district": district,
                "state": state,
                "latitude": latitude,
                "longitude": longitude,
                "risk_level": risk_result.get(
                    "risk_level", "INSUFFICIENT_DATA"
                ),
                "current_rainfall": risk_result.get(
                    "current_rainfall_mm", current_rainfall
                ),
                "forecast_rainfall": risk_result.get(
                    "forecast_rainfall_mm", forecast_rainfall
                ),
                "total_rainfall": risk_result.get(
                    "total_rainfall_mm"
                ),
                "historical_count": historical_flood_count,
                "explanation": risk_result.get("explanation"),
                "analysis_time": datetime.now()
            }
        ).scalar_one()

    # ----------------------------------------------
    # 8. FINAL RESPONSE
    # ----------------------------------------------


    return {
        "saved_alert_id": saved_alert_id,
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


# ==================================================
# SAVED FLOOD ALERTS API
# ==================================================

@app.get("/api/v1/flood/alerts")
def get_saved_flood_alerts(
    limit: int = Query(100, ge=1, le=500)
):

    try:
        with engine.connect() as connection:

            rows = connection.execute(
                text("""
                    SELECT
                        id,
                        location_name,
                        district,
                        state,
                        latitude,
                        longitude,
                        risk_level,
                        current_rainfall_mm,
                        forecast_rainfall_mm,
                        total_rainfall_mm,
                        historical_flood_count,
                        explanation,
                        analysis_time,
                        created_at
                    FROM flood_alerts
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            ).mappings().all()

        return {
            "total": len(rows),
            "alerts": [dict(row) for row in rows]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve flood alerts: {str(error)}"
        )



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





