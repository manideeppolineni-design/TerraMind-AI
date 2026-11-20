import ee
import pandas as pd
from pathlib import Path

# 1. Initialize Earth Engine
ee.Initialize(project="terramind-ai-511418")

# 2. Chennai study area
study_area = (
    ee.Geometry.Point([80.27847, 13.08784])
    .buffer(5000)
)

START_DATE = "2026-10-16"
END_DATE = "2026-10-29"

# 3. Load GPM IMERG V07
gpm = (
    ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
    .filterDate(START_DATE, END_DATE)
    .filterBounds(study_area)
)

print("GPM images:", gpm.size().getInfo())

# 4. Output directory
output_dir = Path("data/processed/rainfall/chennai")
output_dir.mkdir(parents=True, exist_ok=True)

records = []

# 5. Extract daily accumulated rainfall
for day in pd.date_range(
    START_DATE,
    "2026-10-28",
    freq="D"
):
    date_string = day.strftime("%Y-%m-%d")

    next_day = (
        day + pd.Timedelta(days=1)
    ).strftime("%Y-%m-%d")

    daily_images = gpm.filterDate(
        date_string,
        next_day
    )

    image_count = daily_images.size().getInfo()

    if image_count == 0:
        print(date_string, "No GPM images")
        continue

    # Band is precipitation rate in mm/hour.
    # Multiply by 0.5 hour for each 30-minute image.
    daily_rainfall = (
        daily_images
        .select("precipitation")
        .map(lambda image: image.multiply(0.5))
        .sum()
    )

    stats = daily_rainfall.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            reducer2=ee.Reducer.max(),
            sharedInputs=True
        ),
        geometry=study_area,
        scale=11132,
        maxPixels=1000000
    ).getInfo()

    mean_value = stats.get("precipitation_mean")
    max_value = stats.get("precipitation_max")

    records.append({
        "date": date_string,
        "dataset": "GPM_IMERG_V07",
        "images": image_count,
        "mean_rainfall_mm": mean_value,
        "max_rainfall_mm": max_value
    })

    print(
        date_string,
        "| Images:", image_count,
        "| Mean:", mean_value,
        "mm | Max:", max_value,
        "mm"
    )

# 6. Save CSV
if not records:
    print("No daily GPM rainfall records retrieved.")
    raise SystemExit(0)

df = pd.DataFrame(records)

output_file = (
    output_dir / "chennai_gpm_daily_rainfall_2026.csv"
)

df.to_csv(output_file, index=False)

# 7. Summary
print("\n===== GPM RAINFALL SUMMARY =====")

print("Available days:", len(df))
print(
    "Accumulated area-mean rainfall:",
    round(df["mean_rainfall_mm"].sum(), 2),
    "mm"
)
print(
    "Average daily rainfall:",
    round(df["mean_rainfall_mm"].mean(), 2),
    "mm"
)
print(
    "Highest daily area-mean rainfall:",
    round(df["mean_rainfall_mm"].max(), 2),
    "mm"
)

print("\nSaved:", output_file)
print("\nGPM DAILY EXTRACTION COMPLETED")
