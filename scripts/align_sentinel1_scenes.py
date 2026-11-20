from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

before_path = Path("data/raw/satellite/chennai/chennai_before_VV_VH.tif")
after_path = Path("data/raw/satellite/chennai/chennai_after_VV_VH.tif")
aligned_path = Path("data/raw/satellite/chennai/chennai_after_aligned.tif")

NODATA = -9999.0

with rasterio.open(before_path) as before, rasterio.open(after_path) as after:

    print("===== ALIGNMENT =====")
    print("Reference grid:", before.width, "x", before.height)
    print("Source grid:", after.width, "x", after.height)

    profile = before.profile.copy()
    profile.update(
        driver="GTiff",
        dtype="float32",
        count=2,
        nodata=NODATA,
        compress="deflate"
    )

    aligned = np.full(
        (2, before.height, before.width),
        NODATA,
        dtype=np.float32
    )

    for band in (1, 2):
        reproject(
            source=rasterio.band(after, band),
            destination=aligned[band - 1],
            src_transform=after.transform,
            src_crs=after.crs,
            src_nodata=after.nodata,
            dst_transform=before.transform,
            dst_crs=before.crs,
            dst_nodata=NODATA,
            resampling=Resampling.bilinear
        )

    with rasterio.open(aligned_path, "w", **profile) as output:
        output.write(aligned)

    print("Aligned image saved:", aligned_path)

    print("\n===== PIXEL-LEVEL CHANGE INSPECTION =====")

    for band, name in ((1, "VV"), (2, "VH")):
        earlier = before.read(band).astype(np.float32)
        later = aligned[band - 1]

        valid = (
            np.isfinite(earlier)
            & np.isfinite(later)
            & (earlier != before.nodata)
            & (later != NODATA)
        )

        old_values = earlier[valid]
        new_values = later[valid]
        difference = new_values - old_values

        if difference.size == 0:
            print(name, ": No overlapping valid pixels")
            continue

        print(f"\n{name} CHANGE (after - before)")
        print("Comparable pixels:", difference.size)
        print("Mean change (dB):", round(float(np.mean(difference)), 3))
        print("Median change (dB):", round(float(np.median(difference)), 3))
        print("5th percentile:", round(float(np.percentile(difference, 5)), 3))
        print("95th percentile:", round(float(np.percentile(difference, 95)), 3))
        print("Pixels with absolute change > 3 dB:",
              int(np.sum(np.abs(difference) > 3)))
        print("Pixels with absolute change > 5 dB:",
              int(np.sum(np.abs(difference) > 5)))

        print("Note: These are change measurements, not flood detections.")

    print("\n===== FINAL ALIGNMENT CHECK =====")
    print("Dimensions match:", aligned.shape[1:] == (before.height, before.width))
    print("CRS matches:", before.crs == after.crs)
    print("Transform matches:", before.transform == after.transform)

print("\nAlignment and inspection completed.")
