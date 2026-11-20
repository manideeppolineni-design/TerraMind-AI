import json
from pathlib import Path
from collections import Counter
from shapely.geometry import shape
from shapely.validation import explain_validity

path = Path(
    "data/raw/geography/tamil_nadu/extracted/vb_soi_tn.GeoJSON"
)

with path.open("r", encoding="utf-8") as file:
    data = json.load(file)

features = data["features"]

geometry_types = Counter()
invalid_geometries = []
missing_names = 0
missing_codes = 0
districts = Counter()
classifications = Counter()
coordinate_ranges = []

def clean_properties(properties):
    return {
        str(key).strip(): value
        for key, value in properties.items()
    }

for index, feature in enumerate(features):
    properties = clean_properties(feature.get("properties", {}))

    name = properties.get("village")
    code = properties.get("vlcode")
    district = properties.get("district")
    classification = properties.get("total_urban_rural")

    if not name or not str(name).strip():
        missing_names += 1

    if not code or not str(code).strip():
        missing_codes += 1

    if district:
        districts[str(district).strip()] += 1

    if classification:
        classifications[str(classification).strip()] += 1

    geometry_data = feature.get("geometry")

    if not geometry_data:
        invalid_geometries.append((index, "Missing geometry"))
        continue

    geometry = shape(geometry_data)
    geometry_types[geometry.geom_type] += 1

    if geometry.is_empty or not geometry.is_valid:
        invalid_geometries.append(
            (index, explain_validity(geometry))
        )

    if not geometry.is_empty:
        min_x, min_y, max_x, max_y = geometry.bounds
        coordinate_ranges.append(
            (min_x, min_y, max_x, max_y)
        )

print("\n===== VALIDATION SUMMARY =====")
print("Total features:", len(features))
print("Geometry types:", dict(geometry_types))
print("Missing village names:", missing_names)
print("Missing village codes:", missing_codes)
print("Invalid geometries:", len(invalid_geometries))
print("Unique districts:", len(districts))

print("\n===== URBAN / RURAL CLASSIFICATION =====")
print(dict(classifications))

print("\n===== TOP 15 DISTRICTS =====")
for district, count in districts.most_common(15):
    print(district, ":", count)

if coordinate_ranges:
    print("\n===== COORDINATE EXTENT =====")
    print(
        "Min longitude:",
        min(item[0] for item in coordinate_ranges)
    )
    print(
        "Min latitude:",
        min(item[1] for item in coordinate_ranges)
    )
    print(
        "Max longitude:",
        max(item[2] for item in coordinate_ranges)
    )
    print(
        "Max latitude:",
        max(item[3] for item in coordinate_ranges)
    )

print("\n===== INVALID GEOMETRY SAMPLES =====")
for item in invalid_geometries[:10]:
    print(item)

print("\n===== DUPLICATE VILLAGE CODES =====")
codes = [
    clean_properties(feature.get("properties", {})).get("vlcode")
    for feature in features
]

valid_codes = [
    str(code).strip()
    for code in codes
    if code and str(code).strip()
]

duplicates = [
    code for code, count in Counter(valid_codes).items()
    if count > 1
]

print("Duplicate codes:", len(duplicates))
print("Samples:", duplicates[:10])
