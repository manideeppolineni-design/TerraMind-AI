import geopandas as gpd
import rasterio
import pandas as pd
import numpy as np
from rasterio.mask import mask
from pathlib import Path

# Existing candidate polygons
geojson_path = (
    "data/processed/satellite/chennai/"
    "potential_inundation_regions.geojson"
)

# Corrected JRC raster
jrc_path = (
    "data/processed/satellite/chennai/"
    "frequent_water_reference_nodata_fixed.tif"
)

output_path = (
    "data/processed/satellite/chennai/"
    "candidate_water_history_analysis.csv"
)

gdf = gpd.read_file(geojson_path)

if gdf.crs is None:
    raise ValueError("Candidate GeoJSON has no CRS.")

records = []

with rasterio.open(jrc_path) as src:

    candidates = gdf.to_crs(src.crs)

    print("===== CANDIDATE WATER HISTORY ANALYSIS =====")
    print("Candidate polygons:", len(candidates))
    print("JRC raster CRS:", src.crs)

    for _, feature in candidates.iterrows():

        geometry = feature.geometry

        data, transform = mask(
            src,
            [geometry],
            crop=True,
            filled=False
        )

        values = data[0].compressed()
        values = values[
            np.isfinite(values)
        ]

        if len(values) == 0:
            mean_occurrence = np.nan
            max_occurrence = np.nan
            frequent_water_percent = np.nan
            zero_occurrence_percent = np.nan
        else:
            mean_occurrence = float(np.mean(values))
            max_occurrence = float(np.max(values))

            frequent_water_percent = float(
                np.mean(values >= 90) * 100
            )

            zero_occurrence_percent = float(
                np.mean(values == 0) * 100
            )

        records.append({
            "region_id": feature["region_id"],
            "area_hectares": feature["area_hectares"],
            "centroid_longitude": feature["centroid_longitude"],
            "centroid_latitude": feature["centroid_latitude"],
            "valid_jrc_pixels": len(values),
            "mean_water_occurrence": mean_occurrence,
            "max_water_occurrence": max_occurrence,
            "frequent_water_percent": frequent_water_percent,
            "zero_occurrence_percent": zero_occurrence_percent
        })

df = pd.DataFrame(records)

df.to_csv(output_path, index=False)

print("\n===== SUMMARY =====")
print("Regions analyzed:", len(df))
print(
    "Regions with frequent historical water:",
    int((df["frequent_water_percent"] > 0).sum())
)
print(
    "Regions with zero historical water occurrence:",
    int((df["zero_occurrence_percent"] == 100).sum())
)

print("\nFirst 10 regions:")
print(df.head(10).to_string(index=False))

print("\nSaved:", output_path)
print("\nWATER HISTORY ANALYSIS COMPLETED")
