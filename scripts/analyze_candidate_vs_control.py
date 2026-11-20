from pathlib import Path
import numpy as np
import pandas as pd
import rasterio

BASE = Path("data/raw/satellite/chennai")
PROCESSED = Path("data/processed/satellite/chennai")

BEFORE = BASE / "chennai_before_VV_VH.tif"
AFTER = BASE / "chennai_after_aligned.tif"
CANDIDATE = PROCESSED / "potential_inundation_candidates.tif"
JRC = PROCESSED / "frequent_water_reference_nodata_fixed.tif"

OUTPUT = PROCESSED / "candidate_vs_control_analysis.csv"

print("\n===== CANDIDATE VS CONTROL ANALYSIS =====")

with rasterio.open(BEFORE) as b, \
     rasterio.open(AFTER) as a, \
     rasterio.open(CANDIDATE) as c, \
     rasterio.open(JRC) as j:

    for name, src in [
        ("AFTER", a),
        ("CANDIDATE", c),
        ("JRC", j)
    ]:
        if (
            src.transform != b.transform
            or src.crs != b.crs
            or src.shape != b.shape
        ):
            raise RuntimeError(f"{name} raster is not aligned with BEFORE.")

    before_vv = b.read(1).astype(np.float32)
    before_vh = b.read(2).astype(np.float32)

    after_vv = a.read(1).astype(np.float32)
    after_vh = a.read(2).astype(np.float32)

    candidate = c.read(1) == 1
    jrc = j.read(1).astype(np.float32)

    valid = (
        np.isfinite(before_vv)
        & np.isfinite(before_vh)
        & np.isfinite(after_vv)
        & np.isfinite(after_vh)
        & (before_vv != b.nodata)
        & (before_vh != b.nodata)
        & (after_vv != a.nodata)
        & (after_vh != a.nodata)
        & np.isfinite(jrc)
        & (jrc >= 0)
        & (jrc <= 100)
    )

    candidate &= valid
    control = valid & (~candidate) & (jrc < 90)

    vv_change = after_vv - before_vv
    vh_change = after_vh - before_vh

    groups = {
        "candidate": candidate,
        "control": control
    }

    rows = []

    for group_name, mask in groups.items():
        count = int(np.count_nonzero(mask))

        if count == 0:
            continue

        for metric_name, values in [
            ("VV_change_dB", vv_change),
            ("VH_change_dB", vh_change),
            ("After_VV_dB", after_vv),
            ("JRC_occurrence_percent", jrc)
        ]:
            selected = values[mask]

            rows.append({
                "group": group_name,
                "metric": metric_name,
                "pixel_count": count,
                "mean": float(np.mean(selected)),
                "median": float(np.median(selected)),
                "q25": float(np.percentile(selected, 25)),
                "q75": float(np.percentile(selected, 75)),
                "minimum": float(np.min(selected)),
                "maximum": float(np.max(selected))
            })

    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT, index=False)

    print("Valid candidate pixels:", int(candidate.sum()))
    print("Valid control pixels:", int(control.sum()))
    print("\nComparison results:")
    print(result.to_string(index=False))
    print("\nSaved:", OUTPUT)

print("\nANALYSIS COMPLETED")
