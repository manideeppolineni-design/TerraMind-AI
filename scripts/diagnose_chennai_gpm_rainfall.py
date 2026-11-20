import ee

ee.Initialize(project="terramind-ai-511418")

center = ee.Geometry.Point([80.27847, 13.08784])

# Larger context area: 25 km radius
area = center.buffer(25000)

gpm = ee.ImageCollection(
    "NASA/GPM_L3/IMERG_V07"
)

print("===== GPM SPATIAL QUALITY CHECK =====")

for date in [
    "2026-10-17",
    "2026-10-20",
    "2026-10-21",
    "2026-10-25"
]:
    next_date = ee.Date(date).advance(1, "day")

    daily = gpm.filterDate(date, next_date)

    # Accumulate half-hourly rainfall amounts
    rainfall = (
        daily.select("precipitation")
        .map(lambda img: img.multiply(0.5))
        .sum()
    )

    stats = rainfall.reduceRegion(
        reducer=(
            ee.Reducer.count()
            .combine(ee.Reducer.mean(), sharedInputs=True)
            .combine(ee.Reducer.min(), sharedInputs=True)
            .combine(ee.Reducer.max(), sharedInputs=True)
        ),
        geometry=area,
        scale=11132,
        maxPixels=1000000
    )

    print("\nDate:", date)
    print("Half-hourly images:", daily.size().getInfo())
    print("25 km radius rainfall statistics:")
    print(stats.getInfo())

print("\nSPATIAL QUALITY CHECK COMPLETED")
