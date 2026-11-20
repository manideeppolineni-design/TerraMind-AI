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

OUTPUT = PROCESSED / "candidate_vs_local_control_analysis.csv"

print("\n===== LOCAL CONTROL ANALYSIS =====")

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
            raise RuntimeError(f"{name} raster is not aligned.")

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
        & (jrc < 90)
    )

    candidate &= valid

    # Calculate distance in 10-metre pixel units without SciPy.
    # This uses repeated neighbourhood expansion.
    nearby = candidate.copy()
    distance = np.zeros(candidate.shape, dtype=np.uint8)

    for step in range(1, 51):
        expanded = nearby.copy()
        expanded[1:, :] |= nearby[:-1, :]
        expanded[:-1, :] |= nearby[1:, :]
        expanded[:, 1:] |= nearby[:, :-1]
        expanded[:, :-1] |= nearby[:, 1:]
        expanded[1:, 1:] |= nearby[:-1, :-1]
        expanded[1:, :-1] |= nearby[:-1, 1:]
        expanded[:-1, 1:] |= nearby[1:, :-1]
        expanded[:-1, :-1] |= nearby[1:, 1:]

        new_pixels = expanded & (~nearby)
        distance[new_pixels] = step
        nearby = expanded

    # Approximate 100–500 m local controls using 10 m pixels.
    local_control = (
        valid
        & (~candidate)
        & (distance >= 10)
        & (distance <= 50)
    )

    vv_change = after_vv - before_vv
    vh_change = after_vh - before_vh

    groups = {
        "candidate": candidate,
        "local_control_100_500m_approx": local_control
    }

    rows = []

    for group_name, mask in groups.items():
        count = int(mask.sum())
        print(f"\n{group_name}: {count} pixels")

        if count == 0:
            print("No pixels available.")
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
                "q75": float(np.percentile(selected, 75))
            })

    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT, index=False)

    print("\n===== COMPARISON RESULTS =====")
    print(result.to_string(index=False))
    print("\nSaved:", OUTPUT)

print("\nLOCAL CONTROL ANALYSIS COMPLETED")
