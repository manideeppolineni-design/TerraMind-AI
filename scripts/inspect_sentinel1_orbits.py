import ee
from datetime import datetime, timezone

ee.Initialize(project="terramind-ai-511418")

latitude = 13.08784
longitude = 80.27847
radius_km = 10

area = ee.Geometry.Point([longitude, latitude]).buffer(radius_km * 1000)

collection = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(area)
    .filterDate("2024-01-01", "2026-11-09")
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
    .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
    .select(["VV", "VH"])
    .sort("system:time_start", False)
)

properties = [
    "system:index",
    "system:time_start",
    "orbitProperties_pass",
    "relativeOrbitNumber_start",
    "platform_number",
    "sliceNumber",
    "totalSlices"
]

metadata = collection.limit(30).map(
    lambda image: ee.Feature(None, image.toDictionary(properties))
).getInfo()

scenes = []

print("\n===== SENTINEL-1 ORBIT INSPECTION =====")

for feature in metadata["features"]:
    p = feature["properties"]
    date = datetime.fromtimestamp(
        p["system:time_start"] / 1000,
        tz=timezone.utc
    ).strftime("%Y-%m-%d")

    scene = {
        "id": p.get("system:index"),
        "date": date,
        "pass": p.get("orbitProperties_pass"),
        "orbit": p.get("relativeOrbitNumber_start"),
        "platform": p.get("platform_number"),
        "slice": p.get("sliceNumber"),
        "total_slices": p.get("totalSlices")
    }
    scenes.append(scene)

    print(
        f'{date} | {scene["pass"]} | '
        f'Orbit: {scene["orbit"]} | '
        f'Platform: {scene["platform"]} | '
        f'ID: {scene["id"]}'
    )

pair = None

for i, later in enumerate(scenes):
    for earlier in scenes[i + 1:]:
        if (
            later["pass"] == earlier["pass"]
            and later["orbit"] == earlier["orbit"]
            and later["platform"] == earlier["platform"]
        ):
            pair = (earlier, later)
            break
    if pair:
        break

print("\n===== MATCHING COMPARISON PAIR =====")

if pair:
    before, after = pair
    print("Earlier scene:", before["date"])
    print("Earlier image ID:", before["id"])
    print("Later scene:", after["date"])
    print("Later image ID:", after["id"])
    print("Orbit direction:", after["pass"])
    print("Relative orbit:", after["orbit"])
    print("Satellite:", after["platform"])
    print("\nMatching pair found. Ready for the next processing step.")
else:
    print("No matching pair found in the latest 30 scenes.")
    print("A wider date search may be required.")

print("\nInspection completed.")
