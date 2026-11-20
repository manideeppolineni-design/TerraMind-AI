import ee
import requests
from pathlib import Path

ee.Initialize(project="terramind-ai-511418")

LATITUDE = 13.08784
LONGITUDE = 80.27847
RADIUS_KM = 5

OUTPUT = Path("data/raw/satellite/chennai")
OUTPUT.mkdir(parents=True, exist_ok=True)

area = ee.Geometry.Point(
    [LONGITUDE, LATITUDE]
).buffer(RADIUS_KM * 1000)

base = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(area)
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .filter(ee.Filter.listContains(
        "transmitterReceiverPolarisation", "VV"
    ))
    .filter(ee.Filter.listContains(
        "transmitterReceiverPolarisation", "VH"
    ))
    .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))
    .filter(ee.Filter.eq("relativeOrbitNumber_start", 92))
    .filter(ee.Filter.eq("platform_number", "D"))
    .select(["VV", "VH"])
)

dates = [
    ("before", "2026-10-16", "2026-10-17"),
    ("after", "2026-10-28", "2026-10-29")
]

for label, start, end in dates:
    matches = base.filterDate(start, end).sort("system:time_start")

    count = matches.size().getInfo()

    if count == 0:
        raise RuntimeError(
            f"No matching Sentinel-1 scene for {label}: {start}"
        )

    image = ee.Image(matches.first())
    image_id = image.get("system:index").getInfo()
    acquisition = image.date().format(
        "YYYY-MM-dd HH:mm:ss"
    ).getInfo()

    print(f"\n{label.upper()} SCENE")
    print("Image ID:", image_id)
    print("Acquisition:", acquisition)
    print("Bands:", image.bandNames().getInfo())

    clipped = image.clip(area)

    url = clipped.getDownloadURL({
        "name": f"chennai_{label}_VV_VH",
        "scale": 10,
        "region": area,
        "format": "GEO_TIFF"
    })

    response = requests.get(url, timeout=180)
    response.raise_for_status()

    output_file = OUTPUT / f"chennai_{label}_VV_VH.tif"
    output_file.write_bytes(response.content)

    print("Saved:", output_file)
    print("File size:", round(len(response.content) / (1024 * 1024), 2), "MB")

print("\nBoth satellite downloads completed.")
