import ee

ee.Initialize(project="terramind-ai-511418")

LAT = 13.08784
LON = 80.27847

area = ee.Geometry.Point([LON, LAT]).buffer(5000)

collection = (
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
)

dates = [
    ("BEFORE", "2026-10-16", "2026-10-17"),
    ("AFTER", "2026-10-28", "2026-10-29")
]

for label, start, end in dates:
    image = ee.Image(
        collection.filterDate(start, end).first()
    )

    print("\n==========", label, "==========")
    print("Bands:", image.bandNames().getInfo())

    angle = image.select("angle")

    stats = angle.reduceRegion(
        reducer=ee.Reducer.minMax().combine(
            reducer2=ee.Reducer.mean(),
            sharedInputs=True
        ),
        geometry=area,
        scale=100,
        maxPixels=1000000
    ).getInfo()

    print("Incidence angle statistics:", stats)

print("\nINCIDENCE ANGLE CHECK COMPLETED")
