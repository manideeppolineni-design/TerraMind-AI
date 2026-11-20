import ee
from datetime import datetime, timezone

ee.Initialize(project="terramind-ai-511418")

area = ee.Geometry.Point([80.27847, 13.08784]).buffer(5000)

collection = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(area)
    .filterDate("2026-06-30", "2026-10-17")
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))
    .filter(ee.Filter.eq("relativeOrbitNumber_start", 92))
    .filter(ee.Filter.eq("platform_number", "D"))
    .filter(ee.Filter.listContains(
        "transmitterReceiverPolarisation", "VV"
    ))
    .filter(ee.Filter.listContains(
        "transmitterReceiverPolarisation", "VH"
    ))
    .select(["VV", "VH"])
    .sort("system:time_start")
)

count = collection.size().getInfo()

print("\n===== MULTI-DATE BASELINE SCENES =====")
print("Location: Chennai")
print("Orbit: Descending 92")
print("Satellite: Sentinel-1D")
print("Baseline period: 2026-06-30 to 2026-10-16")
print("Matching scenes:", count)

images = collection.toList(count)

for i in range(count):
    image = ee.Image(images.get(i))

    date = image.date().format("YYYY-MM-dd").getInfo()
    image_id = image.get("system:index").getInfo()

    print(f"{i + 1}. {date} | {image_id}")

print("\nBaseline inspection completed.")
