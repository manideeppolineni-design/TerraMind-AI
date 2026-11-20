
import csv
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent

SATELLITE_DIR = (
    ROOT_DIR
    / "data"
    / "processed"
    / "satellite"
    / "chennai"
)


def read_csv(filename):
    path = SATELLITE_DIR / filename

    if not path.is_file():
        raise FileNotFoundError(
            f"Satellite evidence file not found: {path}"
        )

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_chennai_satellite_evidence():

    backscatter = read_csv(
        "candidate_backscatter_analysis.csv"
    )

    comparison = read_csv(
        "candidate_vs_local_control_analysis.csv"
    )

    water_history = read_csv(
        "candidate_water_history_analysis.csv"
    )

    def get_metric(group, metric):
        for row in comparison:
            if row["group"] == group and row["metric"] == metric:
                return {
                    "mean": float(row["mean"]),
                    "median": float(row["median"]),
                    "pixel_count": int(row["pixel_count"])
                }
        return None

    total_area = sum(
        float(row["area_hectares"])
        for row in backscatter
    )

    return {
        "location": "Chennai",
        "state": "Tamil Nadu",
        "classification": "potential_inundation_unvalidated",
        "candidate_region_count": len(backscatter),
        "candidate_area_hectares": round(total_area, 3),
        "candidate_pixel_count": sum(
            int(row["valid_pixels"])
            for row in backscatter
        ),
        "backscatter": {
            "candidate_vv_change": get_metric(
                "candidate", "VV_change_dB"
            ),
            "candidate_vh_change": get_metric(
                "candidate", "VH_change_dB"
            ),
            "control_vv_change": get_metric(
                "local_control_100_500m_approx", "VV_change_dB"
            ),
            "control_vh_change": get_metric(
                "local_control_100_500m_approx", "VH_change_dB"
            ),
            "candidate_after_vv": get_metric(
                "candidate", "After_VV_dB"
            )
        },
        "water_history": {
            "region_count": len(water_history),
            "mean_occurrence_percent": round(
                sum(
                    float(row["mean_water_occurrence"])
                    for row in water_history
                ) / len(water_history),
                2
            ),
            "zero_occurrence_regions": sum(
                float(row["zero_occurrence_percent"]) == 100.0
                for row in water_history
            )
        },
        "limitations": [
            "Satellite detections are experimental and unvalidated.",
            "Backscatter changes alone cannot confirm flooding.",
            "JRC occurrence represents historical water frequency, not current flood truth.",
            "Local control area is an approximate 100-500 metre comparison."
        ]
    }
