import ee
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. INITIALIZE GOOGLE EARTH ENGINE
# --------------------------------------------------

GEE_PROJECT = "terramind-ai-511418"

try:
    ee.Initialize(project=GEE_PROJECT)
    print("Google Earth Engine initialized.")
except Exception as error:
    print("Earth Engine initialization failed:", error)
    raise SystemExit(1)

# --------------------------------------------------
# 2. CHENNAI STUDY AREA
# --------------------------------------------------

CENTER_LON = 80.27847
CENTER_LAT = 13.08784
BUFFER_METERS = 5000

study_area = (
    ee.Geometry.Point([CENTER_LON, CENTER_LAT])
    .buffer(BUFFER_METERS)
)

START_DATE = "2026-10-16"
END_DATE = "2026-10-29"  # Exclusive: includes October 28

# --------------------------------------------------
# 3. OUTPUT DIRECTORY
# --------------------------------------------------

output_dir = Path("data/processed/rainfall/chennai")
output_dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 4. CHIRPS DAILY RAINFALL
# Band: precipitation (mm/day)
# --------------------------------------------------

print("\nChecking CHIRPS daily rainfall...")

chirps = (
    ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    .filterDate(START_DATE, END_DATE)
    .filterBounds(study_area)
)

chirps_count = chirps.size().getInfo()
print("CHIRPS images found:", chirps_count)

# --------------------------------------------------
# 5. ERA5-LAND DAILY RAINFALL
# Band: total_precipitation_sum (metres/day)
# --------------------------------------------------

print("\nChecking ERA5-Land daily rainfall...")

era5 = (
    ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    .filterDate(START_DATE, END_DATE)
    .filterBounds(study_area)
)

era5_count = era5.size().getInfo()
print("ERA5-Land images found:", era5_count)

# --------------------------------------------------
# 6. EXTRACT DAILY RAINFALL
# --------------------------------------------------

records = []

def extract_collection(collection, band, dataset_name, scale, factor):
    images = collection.sort("system:time_start").toList(collection.size())

    count = collection.size().getInfo()

    for index in range(count):
        image = ee.Image(images.get(index))

        date = ee.Date(
            image.get("system:time_start")
        ).format("YYYY-MM-dd")

        rainfall = image.select(band).multiply(factor)

        stats = rainfall.reduceRegion(
            reducer=ee.Reducer.mean()
                .combine(
                    reducer2=ee.Reducer.max(),
                    sharedInputs=True
                ),
            geometry=study_area,
            scale=scale,
            maxPixels=10000000,
            bestEffort=True
        )

        result = ee.Dictionary({
            "date": date,
            "stats": stats
        }).getInfo()

        values = result["stats"]

        records.append({
            "date": result["date"],
            "dataset": dataset_name,
            "mean_rainfall_mm": values.get(
                band + "_mean"
            ),
            "max_rainfall_mm": values.get(
                band + "_max"
            )
        })

        print(
            dataset_name,
            result["date"],
            "Mean:",
            values.get(band + "_mean"),
            "mm"
        )

# CHIRPS resolution approximately 5.5 km
if chirps_count:
    extract_collection(
        chirps,
        "precipitation",
        "CHIRPS",
        5566,
        1
    )
else:
    print("No CHIRPS data available for this period.")

# ERA5-Land resolution approximately 11 km
if era5_count:
    extract_collection(
        era5,
        "total_precipitation_sum",
        "ERA5_LAND",
        11132,
        1000
    )
else:
    print("No ERA5-Land data available for this period.")

# --------------------------------------------------
# 7. SAVE RESULTS
# --------------------------------------------------

if not records:
    print("\nNo rainfall records were retrieved.")
    raise SystemExit(0)

df = pd.DataFrame(records)
df["date"] = pd.to_datetime(df["date"])

csv_path = output_dir / "chennai_daily_rainfall_2026.csv"

df.to_csv(csv_path, index=False)

print("\n===== RAINFALL VALIDATION SUMMARY =====")

for dataset_name, group in df.groupby("dataset"):
    print("\nDataset:", dataset_name)
    print("Available days:", len(group))
    print(
        "Mean daily rainfall:",
        round(group["mean_rainfall_mm"].mean(), 2),
        "mm"
    )
    print(
        "Accumulated area-mean rainfall:",
        round(group["mean_rainfall_mm"].sum(), 2),
        "mm"
    )
    print(
        "Highest daily area-mean rainfall:",
        round(group["mean_rainfall_mm"].max(), 2),
        "mm"
    )

print("\nDaily records:")
print(df.to_string(index=False))

print("\nSaved rainfall data to:", csv_path)
print("\nRAINFALL EXTRACTION COMPLETED")
