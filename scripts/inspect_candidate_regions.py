import json
from pathlib import Path

import rasterio
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape

input_path = Path(
    "data/processed/satellite/chennai/potential_inundation_candidates.tif"
)

output_dir = Path("data/processed/satellite/chennai")
geojson_path = output_dir / "potential_inundation_regions.geojson"

regions = []

with rasterio.open(input_path) as src:
    raster = src.read(1)
    mask = raster == 1

    print("\n===== CANDIDATE REGION INSPECTION =====")
    print("Raster dimensions:", src.width, "x", src.height)
    print("CRS:", src.crs)
    print("Candidate pixels:", int(mask.sum()))

    for geometry, value in shapes(
        raster,
        mask=mask,
        transform=src.transform,
        connectivity=8
    ):
        if value != 1:
            continue

        polygon = shape(geometry)
        area_m2 = polygon.area
        centroid = polygon.centroid

        geographic_geometry = transform_geom(
            src.crs,
            "EPSG:4326",
            geometry
        )

        geographic_centroid = transform_geom(
            src.crs,
            "EPSG:4326",
            {
                "type": "Point",
                "coordinates": [centroid.x, centroid.y]
            }
        )

        regions.append({
            "geometry": geographic_geometry,
            "properties": {
                "region_id": len(regions) + 1,
                "area_m2": round(area_m2, 2),
                "area_hectares": round(area_m2 / 10000, 4),
                "centroid_longitude": geographic_centroid["coordinates"][0],
                "centroid_latitude": geographic_centroid["coordinates"][1],
                "classification": "potential_inundation_unvalidated"
            }
        })

regions.sort(
    key=lambda item: item["properties"]["area_m2"],
    reverse=True
)

for index, region in enumerate(regions, start=1):
    region["properties"]["region_id"] = index

geojson = {
    "type": "FeatureCollection",
    "name": "Chennai Potential Inundation Candidates",
    "features": [
        {
            "type": "Feature",
            "geometry": region["geometry"],
            "properties": region["properties"]
        }
        for region in regions
    ]
}

geojson_path.write_text(
    json.dumps(geojson, indent=2),
    encoding="utf-8"
)

total_area = sum(
    region["properties"]["area_m2"]
    for region in regions
)

print("\n===== REGION SUMMARY =====")
print("Connected regions:", len(regions))
print("Total candidate area (ha):", round(total_area / 10000, 4))

print("\n===== TOP 10 LARGEST REGIONS =====")

for region in regions[:10]:
    p = region["properties"]
    print(
        f'Region {p["region_id"]}: '
        f'{p["area_hectares"]} ha | '
        f'Lat: {p["centroid_latitude"]:.6f} | '
        f'Lon: {p["centroid_longitude"]:.6f}'
    )

print("\nGeoJSON saved:", geojson_path)
print("Classification: POTENTIAL INUNDATION — UNVALIDATED")
print("\nInspection completed.")
