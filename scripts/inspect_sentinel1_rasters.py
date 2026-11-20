from pathlib import Path
import numpy as np
import rasterio

files = {
    "BEFORE": Path("data/raw/satellite/chennai/chennai_before_VV_VH.tif"),
    "AFTER": Path("data/raw/satellite/chennai/chennai_after_VV_VH.tif"),
}

datasets = {}

for label, path in files.items():
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    ds = rasterio.open(path)
    datasets[label] = ds

    print(f"\n===== {label} IMAGE =====")
    print("File:", path)
    print("Dimensions:", ds.width, "x", ds.height)
    print("Bands:", ds.count)
    print("Band descriptions:", ds.descriptions)
    print("CRS:", ds.crs)
    print("Pixel size:", ds.res)
    print("Bounds:", ds.bounds)
    print("NoData:", ds.nodata)

    for band_number, band_name in enumerate(["VV", "VH"], start=1):
        values = ds.read(band_number, masked=True)
        valid = values.compressed()

        if valid.size == 0:
            print(band_name, ": No valid pixels")
            continue

        print(f"\n{band_name} backscatter statistics:")
        print("Valid pixels:", valid.size)
        print("Minimum:", round(float(np.min(valid)), 3))
        print("Maximum:", round(float(np.max(valid)), 3))
        print("Mean:", round(float(np.mean(valid)), 3))
        print("Median:", round(float(np.median(valid)), 3))
        print("5th percentile:", round(float(np.percentile(valid, 5)), 3))
        print("95th percentile:", round(float(np.percentile(valid, 95)), 3))

before = datasets["BEFORE"]
after = datasets["AFTER"]

print("\n===== SPATIAL ALIGNMENT CHECK =====")
print("Same dimensions:", (before.width, before.height) == (after.width, after.height))
print("Same CRS:", before.crs == after.crs)
print("Same transform:", before.transform == after.transform)
print("Same bounds:", before.bounds == after.bounds)

for ds in datasets.values():
    ds.close()

print("\nInspection completed.")
