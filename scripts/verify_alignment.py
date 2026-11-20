import rasterio

before_path = "data/raw/satellite/chennai/chennai_before_VV_VH.tif"
aligned_path = "data/raw/satellite/chennai/chennai_after_aligned.tif"

with rasterio.open(before_path) as before, rasterio.open(aligned_path) as after:

    print("===== CORRECTED ALIGNMENT VERIFICATION =====")
    print("Dimensions match:", (before.width, before.height) == (after.width, after.height))
    print("CRS matches:", before.crs == after.crs)
    print("Transform matches:", before.transform == after.transform)
    print("Bounds match:", before.bounds == after.bounds)
    print("Pixel size matches:", before.res == after.res)
