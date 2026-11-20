from pathlib import Path
import ee
import numpy as np
import rasterio
import requests

from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.features import sieve

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT = "terramind-ai-511418"

BEFORE_PATH = Path(
    "data/raw/satellite/chennai/chennai_before_VV_VH.tif"
)
AFTER_PATH = Path(
    "data/raw/satellite/chennai/chennai_after_aligned.tif"
)

OUTPUT_DIR = Path("data/processed/satellite/chennai")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WATER_REFERENCE_PATH = OUTPUT_DIR / "frequent_water_reference.tif"
CANDIDATE_PATH = OUTPUT_DIR / "potential_inundation_candidates.tif"

# Initial screening thresholds, not universal flood thresholds.
FREQUENT_WATER_OCCURRENCE = 90
AFTER_VV_MAX_DB = -15.0
VV_DECREASE_MIN_DB = 3.0
VH_DECREASE_MIN_DB = 2.0
MIN_CONNECTED_PIXELS = 9

# --------------------------------------------------
# 1. INITIALIZE EARTH ENGINE
# --------------------------------------------------

print("\n===== STEP 1: EARTH ENGINE =====")
ee.Initialize(project=PROJECT)
print("Earth Engine initialized.")

# --------------------------------------------------
# 2. READ REFERENCE GRID
# --------------------------------------------------

print("\n===== STEP 2: READING SATELLITE DATA =====")

with rasterio.open(BEFORE_PATH) as before, \
     rasterio.open(AFTER_PATH) as after:

    if before.transform != after.transform:
        raise RuntimeError("Before and after images are not aligned.")

    if before.crs != after.crs:
        raise RuntimeError("Before and after CRS do not match.")

    if (before.width, before.height) != (after.width, after.height):
        raise RuntimeError("Before and after dimensions do not match.")

    reference_profile = before.profile.copy()
    reference_transform = before.transform
    reference_crs = before.crs
    width = before.width
    height = before.height
    bounds = before.bounds

    before_vv = before.read(1).astype(np.float32)
    before_vh = before.read(2).astype(np.float32)

    after_vv = after.read(1).astype(np.float32)
    after_vh = after.read(2).astype(np.float32)

    before_nodata = before.nodata
    after_nodata = after.nodata

print("Reference dimensions:", width, "x", height)
print("Reference CRS:", reference_crs)

# --------------------------------------------------
# 3. DOWNLOAD JRC WATER OCCURRENCE
# --------------------------------------------------

print("\n===== STEP 3: JRC WATER REFERENCE =====")

west, south, east, north = transform_bounds(
    reference_crs,
    "EPSG:4326",
    bounds.left,
    bounds.bottom,
    bounds.right,
    bounds.top
)

region = ee.Geometry.Rectangle(
    [west, south, east, north],
    proj="EPSG:4326",
    geodesic=False
)

water_image = (
    ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
    .select("occurrence")
    .unmask(0)
    .clip(region)
)

download_url = water_image.getDownloadURL({
    "name": "chennai_jrc_water_occurrence",
    "scale": 10,
    "crs": reference_crs.to_string(),
    "region": region,
    "format": "GEO_TIFF"
})

response = requests.get(download_url, timeout=180)
response.raise_for_status()

temporary_water_path = OUTPUT_DIR / "jrc_water_occurrence_download.tif"
temporary_water_path.write_bytes(response.content)

print("JRC water occurrence downloaded.")
print("Temporary file:", temporary_water_path)

# --------------------------------------------------
# 4. ALIGN WATER REFERENCE TO SENTINEL GRID
# --------------------------------------------------

print("\n===== STEP 4: ALIGNING WATER REFERENCE =====")

with rasterio.open(temporary_water_path) as water_source:

    source_water = water_source.read(1).astype(np.float32)

    aligned_water = np.zeros(
        (height, width),
        dtype=np.float32
    )

    reproject(
        source=source_water,
        destination=aligned_water,
        src_transform=water_source.transform,
        src_crs=water_source.crs,
        src_nodata=water_source.nodata,
        dst_transform=reference_transform,
        dst_crs=reference_crs,
        dst_nodata=0,
        resampling=Resampling.nearest
    )

water_profile = reference_profile.copy()
water_profile.update(
    driver="GTiff",
    count=1,
    dtype="float32",
    nodata=0,
    compress="deflate"
)

with rasterio.open(WATER_REFERENCE_PATH, "w", **water_profile) as output:
    output.write(aligned_water, 1)

frequent_water = aligned_water >= FREQUENT_WATER_OCCURRENCE

print("Frequent-water threshold:", FREQUENT_WATER_OCCURRENCE, "%")
print("Frequent-water pixels:", int(np.count_nonzero(frequent_water)))
print("Saved:", WATER_REFERENCE_PATH)

# --------------------------------------------------
# 5. CALCULATE SENTINEL-1 CHANGE
# --------------------------------------------------

print("\n===== STEP 5: SAR CHANGE ANALYSIS =====")

valid = (
    np.isfinite(before_vv)
    & np.isfinite(before_vh)
    & np.isfinite(after_vv)
    & np.isfinite(after_vh)
)

if before_nodata is not None:
    valid &= (before_vv != before_nodata) & (before_vh != before_nodata)

if after_nodata is not None:
    valid &= (after_vv != after_nodata) & (after_vh != after_nodata)

vv_change = after_vv - before_vv
vh_change = after_vh - before_vh

# Negative change means radar backscatter decreased.
vv_decrease = vv_change <= -VV_DECREASE_MIN_DB
vh_decrease = vh_change <= -VH_DECREASE_MIN_DB

# Initial open-water-like screening.
candidate = (
    valid
    & (~frequent_water)
    & (after_vv <= AFTER_VV_MAX_DB)
    & vv_decrease
    & vh_decrease
)

print("Valid comparison pixels:", int(np.count_nonzero(valid)))
print("VV decrease threshold:", VV_DECREASE_MIN_DB, "dB")
print("VH decrease threshold:", VH_DECREASE_MIN_DB, "dB")
print("After VV threshold:", AFTER_VV_MAX_DB, "dB")
print("Raw candidate pixels:", int(np.count_nonzero(candidate)))

# --------------------------------------------------
# 6. REMOVE SMALL ISOLATED PATCHES
# --------------------------------------------------

print("\n===== STEP 6: SPATIAL FILTERING =====")

candidate_uint8 = candidate.astype(np.uint8)

filtered = sieve(
    candidate_uint8,
    size=MIN_CONNECTED_PIXELS,
    connectivity=8
).astype(bool)

# Keep only candidate pixels that survived filtering.
filtered &= candidate

candidate_pixels = int(np.count_nonzero(filtered))

pixel_area_m2 = abs(
    reference_transform.a * reference_transform.e
    - reference_transform.b * reference_transform.d
)

candidate_area_m2 = candidate_pixels * pixel_area_m2
candidate_area_hectares = candidate_area_m2 / 10000

print("Minimum connected patch:", MIN_CONNECTED_PIXELS, "pixels")
print("Filtered candidate pixels:", candidate_pixels)
print("Pixel area:", round(pixel_area_m2, 2), "square metres")
print("Potential candidate area:", round(candidate_area_hectares, 3), "hectares")

# --------------------------------------------------
# 7. SAVE CANDIDATE RASTER
# --------------------------------------------------

print("\n===== STEP 7: SAVING OUTPUT =====")

candidate_profile = reference_profile.copy()
candidate_profile.update(
    driver="GTiff",
    count=1,
    dtype="uint8",
    nodata=255,
    compress="deflate"
)

output_array = np.where(filtered, 1, 0).astype(np.uint8)

with rasterio.open(CANDIDATE_PATH, "w", **candidate_profile) as output:
    output.write(output_array, 1)

print("Saved candidate raster:", CANDIDATE_PATH)

print("\n===== FINAL SUMMARY =====")
print("Location: Chennai")
print("Before scene: 2026-10-16")
print("After scene: 2026-10-28")
print("Frequent-water reference:", WATER_REFERENCE_PATH)
print("Potential inundation candidates:", CANDIDATE_PATH)
print("Candidate area (hectares):", round(candidate_area_hectares, 3))
print("Classification: POTENTIAL INUNDATION — UNVALIDATED")
print("\nProcessing completed.")
