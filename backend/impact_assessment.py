def safe_float(value):
    """Convert a value to float or return None if unavailable."""
    try:
        if value is None:
            return None

        result = float(value)

        if result != result or result in (float("inf"), float("-inf")):
            return None

        return result

    except (TypeError, ValueError):
        return None


def summarize_values(values):
    """Summarize numerical values such as hourly rainfall."""
    numbers = [
        number
        for value in values
        if (number := safe_float(value)) is not None
    ]

    if not numbers:
        return {
            "available": False,
            "count": 0,
            "sum": None,
            "mean": None,
            "maximum": None
        }

    return {
        "available": True,
        "count": len(numbers),
        "sum": round(sum(numbers), 2),
        "mean": round(sum(numbers) / len(numbers), 2),
        "maximum": round(max(numbers), 2)
    }


def summarize_probabilities(values):
    """Summarize probabilities without adding percentage values."""
    numbers = [
        number
        for value in values
        if (number := safe_float(value)) is not None
    ]

    if not numbers:
        return {
            "available": False,
            "count": 0,
            "mean": None,
            "maximum": None
        }

    return {
        "available": True,
        "count": len(numbers),
        "mean": round(sum(numbers) / len(numbers), 2),
        "maximum": round(max(numbers), 2)
    }


def build_flood_impact_assessment(evidence: dict) -> dict:
    """
    Build an evidence-based flood impact assessment.

    This is not a validated flood prediction model.
    """

    weather = evidence.get("weather") or {}
    historical = evidence.get("historical_data") or {}
    satellite = evidence.get("satellite_evidence")

    current_weather = weather.get("current_weather") or {}
    forecast = weather.get("hourly_forecast") or {}

    location = evidence.get("location") or {}

    # 1. Rainfall assessment

    current_rainfall = safe_float(
        current_weather.get("precipitation")
    )

    hourly_rainfall_values = (forecast.get("precipitation") or [])[:24]
    hourly_probability_values = (forecast.get("precipitation_probability") or [])[:24]

    forecast_rainfall = summarize_values(hourly_rainfall_values)
    forecast_probability = summarize_probabilities(hourly_probability_values)

    rainfall_assessment = {
        "current_precipitation_mm": current_rainfall,
        "next_24_hours_forecast": forecast_rainfall,
        "forecast_hours_available": forecast_rainfall["count"],
        "next_24_hours_probability_percent": forecast_probability,
        "data_source": weather.get("source", "Not specified")
    }

    # 2. Historical flood assessment

    flood_events = historical.get(
        "historical_flood_events", []
    ) or []

    historical_assessment = {
        "event_count": len(flood_events),
        "search_radius_km": historical.get("search_radius_km"),
        "data_status": historical.get(
            "historical_data_status", "Unavailable"
        ),
        "events": flood_events
    }

    # 3. Satellite assessment

    if satellite:

        backscatter = satellite.get("backscatter") or {}
        water_history = satellite.get("water_history") or {}

        satellite_assessment = {
            "available": True,
            "classification": satellite.get("classification"),
            "candidate_region_count": satellite.get(
                "candidate_region_count"
            ),
            "candidate_area_hectares": satellite.get(
                "candidate_area_hectares"
            ),
            "candidate_pixel_count": satellite.get(
                "candidate_pixel_count"
            ),
            "backscatter_comparison": backscatter,
            "historical_water_occurrence": water_history,
            "limitations": satellite.get("limitations", [])
        }

    else:

        satellite_assessment = {
            "available": False,
            "message": (
                "Location-specific satellite inundation "
                "evidence is unavailable."
            )
        }

    # 4. Geographic summary

    geographic_summary = {
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "historical_search_radius_km": historical.get(
            "search_radius_km"
        ),
        "candidate_geometry_available": False,
        "note": (
            "Aggregate satellite statistics are available, "
            "but individual candidate geometries are not "
            "included in this assessment."
        )
    }

    # 5. Limitations

    limitations = [
        "This assessment is an evidence summary, not a validated flood prediction.",
        "Satellite inundation candidates are not confirmed flood locations.",
        "Historical flood records may be incomplete.",
        "Rainfall forecasts are estimates and may change.",
        "Geographic impact boundaries require individual validated spatial features."
    ]

    if not forecast_rainfall["available"]:
        limitations.append(
            "Next 24-hour rainfall forecast data is unavailable."
        )

    if not satellite:
        limitations.append(
            "Satellite inundation evidence is unavailable for this location."
        )

    # 6. Final assessment

    return {
        "assessment_type": "Evidence-based flood impact assessment",
        "status": "completed",
        "location": location,
        "rainfall_assessment": rainfall_assessment,
        "historical_impact": historical_assessment,
        "satellite_impact": satellite_assessment,
        "geographic_summary": geographic_summary,
        "limitations": limitations,
        "official_warning": False
    }
