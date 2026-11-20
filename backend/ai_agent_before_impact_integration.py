
import json
from langchain_ollama import ChatOllama


def create_flood_agent():
    return ChatOllama(
        model="llama3.2:3b",
        temperature=0,
        base_url="http://localhost:11434",
    )


async def analyze_with_agent(evidence: dict) -> dict:
    model = create_flood_agent()

    # Extract the evidence structure returned by the backend.
    weather_data = evidence.get("weather", {})
    historical_data = evidence.get("historical_data", {})

    current_weather = weather_data.get("current_weather", {})
    forecast = weather_data.get("hourly_forecast", {})

    satellite_history = historical_data.get("satellite_history", [])
    satellite_evidence = evidence.get("satellite_evidence")

    flood_events = historical_data.get("historical_flood_events", [])

    # Summarize the forecast without sending unnecessary data to the model.
    rainfall = forecast.get("precipitation", [])
    rain_probability = forecast.get("precipitation_probability", [])

    forecast_summary = {
        "next_24_hours_precipitation_mm": rainfall[:24],
        "next_24_hours_precipitation_probability_percent": rain_probability[:24],
    }

    evidence_summary = {
        "location": evidence.get("location", {}),
        "current_weather": current_weather,
        "forecast": forecast_summary,
        "flood_analysis": evidence.get("flood_analysis"),
        "historical_flood_events": flood_events,
        "historical_flood_count": historical_data.get(
            "historical_flood_count", len(flood_events)
        ),
        "historical_data_status": historical_data.get(
            "historical_data_status"
        ),
        "satellite_history": satellite_history,
        "satellite_detection_evidence": satellite_evidence,
    }

    prompt = f"""
You are TerraMind AI, a satellite intelligence and flood-impact
analysis assistant.

Analyze the evidence below and provide a clear, human-readable report.

Return these sections:
1. Summary
2. Current weather
3. Rainfall outlook
4. Historical flood evidence
5. Satellite data observations
6. Limitations and recommended next steps

Rules:
- Use only facts supported by the evidence.
- Satellite image counts do not prove flooding.
- No historical records found does not prove that flooding never occurred.
- Do not invent flood detections, risk scores, or official warnings.
- If evidence is missing, state that clearly.
- Explain that this is not an official flood warning or validated prediction.
- Do not return tool calls, JSON, or internal reasoning. Return the report only.
- Analyze Sentinel-1 VV and VH backscatter changes using the supplied measurements.
- Compare candidate pixels with local control pixels when available.
- Report the candidate area and region count accurately.
- Distinguish historical water occurrence from current flooding.
- Never describe potential inundation candidates as confirmed floods.
- If satellite detection evidence is unavailable, explicitly state that.

Evidence:
{json.dumps(evidence_summary, ensure_ascii=False, default=str)}
"""

    try:
        response = await model.ainvoke(prompt)
        explanation = response.content

        if not isinstance(explanation, str):
            explanation = str(explanation)

        explanation = explanation.strip()

        if not explanation:
            raise ValueError("The local model returned an empty response.")

        return {
            "ai_explanation": explanation,
            "model": "llama3.2:3b",
            "provider": "ollama",
            "status": "success",
        }

    except Exception as exc:
        return {
            "ai_explanation": (
                "The local AI analysis failed. Please check that Ollama "
                "is running and the llama3.2:3b model is available."
            ),
            "error": str(exc),
            "model": "llama3.2:3b",
            "provider": "ollama",
            "status": "error",
        }
