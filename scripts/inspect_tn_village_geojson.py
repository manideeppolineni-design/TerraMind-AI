import json
from pathlib import Path
from collections import Counter

path = Path(
    "data/raw/geography/tamil_nadu/extracted/vb_soi_tn.GeoJSON"
)

print("Reading GeoJSON...")

with path.open("r", encoding="utf-8") as file:
    data = json.load(file)

features = data.get("features", [])

print("\n===== DATASET SUMMARY =====")
print("Feature count:", len(features))
print("Geometry types:", Counter(
    feature.get("geometry", {}).get("type")
    for feature in features
))

print("\n===== PROPERTY FIELD NAMES =====")

field_counts = Counter()

for feature in features:
    field_counts.update(feature.get("properties", {}).keys())

for field, count in field_counts.items():
    print(f"{field}: {count}")

print("\n===== FIRST THREE FEATURES =====")

for feature in features[:3]:
    print("\nProperties:")
    print(json.dumps(feature.get("properties", {}), indent=2, ensure_ascii=False))

    geometry = feature.get("geometry") or {}
    print("Geometry type:", geometry.get("type"))
