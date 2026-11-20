import json
from pathlib import Path
from collections import Counter

path = Path(
    "data/raw/geography/tamil_nadu/extracted/vb_soi_tn.GeoJSON"
)

with path.open("r", encoding="utf-8") as f:
    data = json.load(f)

print("===== GEOJSON METADATA =====")
print("Top-level keys:", list(data.keys()))
print("CRS metadata:", json.dumps(data.get("crs"), indent=2))

print("\n===== COORDINATE SAMPLES =====")

for index in [0, 1, 2, 73, 2912]:
    feature = data["features"][index]
    print("\nFeature:", index)
    print("Village:", feature["properties"].get("village"))
    print("Village code:", feature["properties"].get("vlcode"))

    coordinates = feature["geometry"]["coordinates"]
    print("First coordinate:", coordinates[0][0][0][:2])

print("\n===== SOFTWARE VERSIONS =====")

import pyproj
import shapely

print("PyProj:", pyproj.__version__)
print("Shapely:", shapely.__version__)
