
import ee
import csv
from pathlib import Path

print("Connecting to Earth Engine...", flush=True)
ee.Initialize(project="terramind-ai-511418")
print("Connected successfully!\n", flush=True)

india = (
    ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    .filter(ee.Filter.eq("country_na", "India"))
    .geometry()
)

output_file = (
    Path(__file__).resolve().parent
    / "india_satellite_catalogue.csv"
)

results = []

for year in range(2014, 2027):
    start_date = f"{year}-01-01"

    if year == 2026:
        end_date = "2026-10-14"
    else:
        end_date = f"{year + 1}-01-01"

    print(f"Checking {year}...", flush=True)

    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(india)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(
            ee.Filter.listContains(
                "transmitterReceiverPolarisation", "VV"
            )
        )
    )

    count = collection.size().getInfo()
    results.append([year, count])

    print(f"  {year}: {count} matching images", flush=True)

with output_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Year", "Matching Sentinel-1 Images"])
    writer.writerows(results)

print("\nCatalogue completed!", flush=True)
print("Saved to:", output_file, flush=True)
