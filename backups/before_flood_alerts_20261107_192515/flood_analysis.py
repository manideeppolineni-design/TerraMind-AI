
from datetime import datetime


def analyze_flood_risk(
    rainfall_mm=None,
    forecast_rainfall_mm=None,
    historical_flood_count=0
):
    """
    Analyze preliminary flood risk using rainfall,
    forecast rainfall, and historical flood events.

    This is a prototype rule-based assessment.
    It is not an official flood warning or validated
    flood prediction model.
    """

    # Validate rainfall values
    if rainfall_mm is not None and rainfall_mm < 0:
        raise ValueError("Rainfall cannot be negative")

    if forecast_rainfall_mm is not None and forecast_rainfall_mm < 0:
        raise ValueError("Forecast rainfall cannot be negative")

    if historical_flood_count < 0:
        raise ValueError("Historical flood count cannot be negative")

    # Handle missing weather data
    if rainfall_mm is None:
        current_rainfall = None
    else:
        current_rainfall = float(rainfall_mm)

    if forecast_rainfall_mm is None:
        forecast_rainfall = None
    else:
        forecast_rainfall = float(forecast_rainfall_mm)

    historical_count = int(historical_flood_count)

    # Calculate rainfall only when both values are available
    if (
        current_rainfall is not None
        and forecast_rainfall is not None
    ):
        total_rainfall = (
            current_rainfall + forecast_rainfall
        )
    else:
        total_rainfall = None

    # Preliminary risk classification
    if total_rainfall is None:

        risk_level = "INSUFFICIENT_DATA"

        explanation = (
            "Current or forecast rainfall data is missing. "
            "Flood risk cannot be assessed reliably."
        )

    elif total_rainfall >= 100 and historical_count > 0:

        risk_level = "HIGH"

        explanation = (
            "High rainfall and documented historical "
            "flood events were found."
        )

    elif total_rainfall >= 50:

        risk_level = "MODERATE"

        explanation = (
            "Rainfall is elevated. Continue monitoring "
            "weather conditions and official warnings."
        )

    elif total_rainfall >= 20:

        risk_level = "LOW"

        explanation = (
            "Rainfall is present, but this preliminary "
            "assessment does not identify a high rainfall threshold."
        )

    else:

        risk_level = "LOW"

        explanation = (
            "Available rainfall values are below the "
            "prototype thresholds."
        )

    # Return analysis result
    return {
        "analysis_time": datetime.utcnow().isoformat(),
        "current_rainfall_mm": current_rainfall,
        "forecast_rainfall_mm": forecast_rainfall,
        "total_rainfall_mm": total_rainfall,
        "historical_flood_count": historical_count,
        "risk_level": risk_level,
        "explanation": explanation,
        "model_type": "Preliminary rule-based assessment",
        "official_warning": False,
        "warning_message": (
            "This result is not an official weather warning. "
            "Check official government alerts."
        )
    }
