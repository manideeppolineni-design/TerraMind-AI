import ee
import argparse
from datetime import datetime, timezone

parser = argparse.ArgumentParser()
parser.add_argument("--name", default="Chennai")
parser.add_argument("--latitude", type=float, default=13.08784)
parser.add_argument("--longitude", type=float, default=80.27847)
parser.add_argument("--radius-km", type=float, default=10)
args = parser.parse_args()

ee.Initialize(project="terramind-ai-511418")

point = ee.Geometry.Point([args.longitude, args.latitude])
area = point.buffer(args.radius_km * 1000)

start_date = "2024-01-01"
end_date = "2026-11-09"

collection = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(area)
    .filterDate(start_date, end_date)
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .filter(ee.Filter.listContains(
        "transmitterReceiverPolarisation", "VV"
    ))
    .filter(ee.Filter.listContains(
        "transmitterReceiverPolarisation", "VH"
    ))
    .select(["VV", "VH"])
    .sort("system:time_start", False)
)

count = collection.size().getInfo()

print("\n===== TERRAMIND SENTINEL-1 RETRIEVAL =====")
print("Location:", args.name)
print("Latitude:", args.latitude)
print("Longitude:", args.longitude)
print("Search radius:", args.radius_km, "km")
print("Date range:", start_date, "to", end_date)
print("Matching Sentinel-1 scenes:", count)

if count:
    dates = collection.aggregate_array("system:time_start").getInfo()
    for timestamp in dates[:20]:
        date = datetime.fromtimestamp(
            timestamp / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d")
        print("Acquisition:", date)

    first = ee.Image(collection.first())
    print("\nLatest scene metadata:")
    print("Image ID:", first.get("system:index").getInfo())
    print("Acquisition date:", datetime.fromtimestamp(
        first.get("system:time_start").getInfo() / 1000,
        tz=timezone.utc
    ).isoformat())
    print("Polarizations: VV, VH")
    print("Bands:", first.bandNames().getInfo())
    print("Footprint:", first.geometry().bounds().getInfo())
else:
    print("No matching scenes found for this location and date range.")

print("\nRetrieval test completed.")
