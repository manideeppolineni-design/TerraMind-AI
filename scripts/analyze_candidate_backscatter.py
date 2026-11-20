import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd
from rasterio.mask import mask
from pathlib import Path

# Existing files - read only
geojson_path = (
    "data/processed/satellite/chennai/"
    "potential_inundation_regions.geojson"
)

before_path = (
    "data/raw/satellite/chennai/"
    "chennai_before_VV_VH.tif"
)

after_path = (
    "data/raw/satellite/chennai/"
    "chennai_after_aligned.tif"
)

output_path = (
    "data/processed/satellite/chennai/"
    "candidate_backscatter_analysis.csv"
)

gdf = gpd.read_file(geojson_path)
records = []

with rasterio.open(before_path) as before_src, \
     rasterio.open(after_path) as after_src:

    print("===== SENTINEL-1 BAND INSPECTION =====")
    print("Before bands:", before_src.count)
    print("After bands:", after_src.count)
    print("Before descriptions:", before_src.descriptions)
    print("After descriptions:", after_src.descriptions)

    if before_src.count < 2 or after_src.count < 2:
        raise ValueError("Expected VV and VH bands in both rasters.")

    if before_src.crs != after_src.crs:
        raise ValueError("Before and after CRS do not match.")

    if before_src.transform != after_src.transform:
        raise ValueError("Before and after grids do not match.")

    candidates = gdf.to_crs(before_src.crs)

    for _, feature in candidates.iterrows():

        geom = [feature.geometry]

        before, _ = mask(
            before_src,
            geom,
            crop=True,
            filled=False
        )

        after, _ = mask(
            after_src,
            geom,
            crop=True,
            filled=False
        )

        # Assumes band 1 = VV and band 2 = VH.
        # Confirm the band order from the printed metadata.
        vv_before = before[0]
        vh_before = before[1]

        vv_after = after[0]
        vh_after = after[1]

        valid = (
            ~np.ma.getmaskarray(vv_before)
            & ~np.ma.getmaskarray(vh_before)
            & ~np.ma.getmaskarray(vv_after)
            & ~np.ma.getmaskarray(vh_after)
        )

        valid &= (
            np.isfinite(vv_before.filled(np.nan))
            & np.isfinite(vh_before.filled(np.nan))
            & np.isfinite(vv_after.filled(np.nan))
            & np.isfinite(vh_after.filled(np.nan))
        )

        if not np.any(valid):
            print("No valid pixels:", feature["region_id"])
            continue

        vb = vv_before.data[valid]
        hb = vh_before.data[valid]
        va = vv_after.data[valid]
        ha = vh_after.data[valid]

        vv_change = va - vb
        vh_change = ha - hb

        records.append({
            "region_id": feature["region_id"],
            "area_hectares": feature["area_hectares"],
            "valid_pixels": int(valid.sum()),
            "vv_before_mean_db": float(np.mean(vb)),
            "vv_after_mean_db": float(np.mean(va)),
            "vv_change_db": float(np.mean(vv_change)),
            "vh_before_mean_db": float(np.mean(hb)),
            "vh_after_mean_db": float(np.mean(ha)),
            "vh_change_db": float(np.mean(vh_change)),
            "vv_decrease_pixels": int(np.sum(vv_change <= -3)),
            "vh_decrease_pixels": int(np.sum(vh_change <= -2))
        })

df = pd.DataFrame(records)

if df.empty:
    raise SystemExit("No candidate backscatter records were produced.")

df.to_csv(output_path, index=False)

print("\n===== BACKSCATTER ANALYSIS SUMMARY =====")
print("Regions analyzed:", len(df))
print("Mean VV change:", round(df["vv_change_db"].mean(), 3), "dB")
print("Mean VH change:", round(df["vh_change_db"].mean(), 3), "dB")

print("\nRegions with VV decrease >= 3 dB:")
print(int((df["vv_change_db"] <= -3).sum()))

print("Regions with VH decrease >= 2 dB:")
print(int((df["vh_change_db"] <= -2).sum()))

print("\nFirst 15 regions:")
print(df.head(15).to_string(index=False))

print("\nSaved:", output_path)
print("\nBACKSCATTER ANALYSIS COMPLETED")
