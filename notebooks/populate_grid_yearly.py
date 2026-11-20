
import ee
import csv
from pathlib import Path

ee.Initialize(project="terramind-ai-511418")

csv_path = (
    Path(__file__).resolve().parent
    / "india_grid_catalogue.csv"
)

output_path = (
    Path(__file__).resolve().parent
    / "grid_yearly_observations.csv"
)

with csv_path.open("r", newline="", encoding="utf-8") as file:
    grid_rows = list(csv.DictReader(file))

print("Grid cells loaded:", len(grid_rows), flush=True)

with output_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["grid_id", "year", "image_count"])

    for grid_row in grid_rows:
        south = float(grid_row["south"])
        west = float(grid_row["west"])

        cell = ee.Geometry.Rectangle(
            [west, south, west + 2, south + 2],
            proj="EPSG:4326",
            geodesic=False
        )

        collection = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(cell)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(
                ee.Filter.listContains(
                    "transmitterReceiverPolarisation", "VV"
                )
            )
        )

        for year in range(2014, 2027):
            start = f"{year}-01-01"
            end = (
                "2026-10-14"
                if year == 2026
                else f"{year + 1}-01-01"
            )

            count = (
                collection
                .filterDate(start, end)
                .size()
                .getInfo()
            )

            writer.writerow([
                grid_row["grid_id"],
                year,
                count
            ])

        print(
            f"Completed grid: {grid_row['grid_id']}",
            flush=True
        )

print("Yearly catalogue saved to:", output_path)
