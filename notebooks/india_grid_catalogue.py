
import ee
import csv
from pathlib import Path

print("Connecting to Earth Engine...", flush=True)
ee.Initialize(project="terramind-ai-511418")

print("Creating India's geographic grid...", flush=True)

india = (
    ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    .filter(ee.Filter.eq("country_na", "India"))
    .geometry()
)

# Create 2-degree grid cells over India's approximate bounds.
cells = []

cell_size = 2.0
lat = 6.0

while lat < 38.0:
    lon = 67.0

    while lon < 99.0:
        cell = ee.Geometry.Rectangle(
            [lon, lat, lon + cell_size, lat + cell_size],
            proj="EPSG:4326",
            geodesic=False
        )

        cells.append(
            ee.Feature(cell, {
                "grid_id": f"GRID_{lat}_{lon}",
                "south": lat,
                "west": lon
            })
        )

        lon += cell_size

    lat += cell_size

grid = (
    ee.FeatureCollection(cells)
    .filterBounds(india)
)

print("Grid cells intersecting India:", grid.size().getInfo())
print("Counting 2023 observations by grid...", flush=True)

images = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterDate("2023-01-01", "2024-01-01")
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .filter(
        ee.Filter.listContains(
            "transmitterReceiverPolarisation", "VV"
        )
    )
)

def count_images(feature):
    count = images.filterBounds(feature.geometry()).size()

    return feature.set("image_count_2023", count)

results = grid.map(count_images)

data = results.getInfo()["features"]

output_file = (
    Path(__file__).resolve().parent
    / "india_grid_catalogue.csv"
)

with output_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "grid_id",
        "south",
        "west",
        "image_count_2023"
    ])

    for item in data:
        properties = item["properties"]

        writer.writerow([
            properties["grid_id"],
            properties["south"],
            properties["west"],
            properties["image_count_2023"]
        ])

print("\nGrid catalogue completed!")
print("Grid cells recorded:", len(data))
print("Saved to:", output_file)
