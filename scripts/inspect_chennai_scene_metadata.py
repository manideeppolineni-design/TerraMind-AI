import ee

ee.Initialize(project="terramind-ai-511418")

LATITUDE = 13.08784
LONGITUDE = 80.27847
RADIUS_KM = 5

area = ee.Geometry.Point(
    [LONGITUDE, LATITUDE]
).buffer(RADIUS_KM * 1000)

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

properties = [
    "system:index",
    "system:time_start",
    "platform_number",
    "instrumentMode",
    "instrumentSwath",
    "orbitProperties_pass",
    "relativeOrbitNumber_start",
    "relativeOrbitNumber_stop",
    "orbitNumber_start",
    "orbitNumber_stop",
    "sliceNumber",
    "totalSlices",
    "missionDataTakeID",
    "productTimelinessCategory",
    "resolution_meters",
    "transmitterReceiverPolarisation",
    "incidenceAngle"
]

dates = [
    ("BEFORE", "2026-10-16", "2026-10-17"),
    ("AFTER", "2026-10-28", "2026-10-29")
]

for label, start, end in dates:
    print("\n" + "=" * 60)
    print(label, "DATE:", start)
    print("=" * 60)

    matches = collection.filterDate(start, end).sort("system:time_start")

    count = matches.size().getInfo()
    print("Matching scenes:", count)

    images = matches.toList(count)

    for index in range(count):
        image = ee.Image(images.get(index))

        print(f"\n--- SCENE {index + 1} ---")

        info = image.toDictionary(properties).getInfo()

        for key in properties:
            print(f"{key}: {info.get(key, 'NOT AVAILABLE')}")

        print("Acquisition UTC:",
              image.date().format("YYYY-MM-dd HH:mm:ss").getInfo())

        print("Footprint bounds:",
              image.geometry().bounds().coordinates().getInfo())

print("\nSCENE METADATA INSPECTION COMPLETED")
