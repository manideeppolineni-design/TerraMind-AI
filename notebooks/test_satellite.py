
import ee

ee.Initialize(project="terramind-ai-511418")

area = ee.Geometry.Rectangle([79.8, 12.8, 80.4, 13.3])

images = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(area)
    .filterDate("2023-12-01", "2024-01-01")
    .filter(ee.Filter.eq("instrumentMode", "IW"))
)

print("Sentinel-1 images found:", images.size().getInfo())

if images.size().getInfo() > 0:
    image = ee.Image(images.first())
    print("Available bands:", image.bandNames().getInfo())
    print("Satellite data test successful!")
else:
    print("No images found for this period and area.")
