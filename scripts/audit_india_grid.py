import csv
from collections import Counter

path = "notebooks/india_grid_catalogue.csv"

with open(path, "r", encoding="utf-8-sig", newline="") as file:
    rows = list(csv.DictReader(file))

if not rows:
    raise RuntimeError("The India grid catalogue is empty.")

south = [float(row["south"]) for row in rows]
west = [float(row["west"]) for row in rows]
counts = [int(row["image_count_2023"]) for row in rows]
grid_ids = [row["grid_id"] for row in rows]

print("\n===== INDIA GRID CATALOGUE AUDIT =====")
print("Total records:", len(rows))
print("Unique grid IDs:", len(set(grid_ids)))
print("Duplicate grid IDs:", len(grid_ids) - len(set(grid_ids)))

print("\n===== GEOGRAPHIC EXTENT =====")
print("Southern latitude:", min(south))
print("Northern latitude:", max(south))
print("Western longitude:", min(west))
print("Eastern longitude:", max(west))

print("\n===== GRID SPACING =====")
latitudes = sorted(set(south))
longitudes = sorted(set(west))

lat_intervals = sorted(set(
    round(latitudes[i + 1] - latitudes[i], 6)
    for i in range(len(latitudes) - 1)
))
lon_intervals = sorted(set(
    round(longitudes[i + 1] - longitudes[i], 6)
    for i in range(len(longitudes) - 1)
))

print("Latitude intervals:", lat_intervals)
print("Longitude intervals:", lon_intervals)

print("\n===== IMAGE COUNT DISTRIBUTION =====")
print("Minimum:", min(counts))
print("Maximum:", max(counts))
print("Average:", round(sum(counts) / len(counts), 2))
print("Median:", sorted(counts)[len(counts) // 2])

print("\n===== LOWEST IMAGE COUNTS =====")
for row in sorted(rows, key=lambda r: int(r["image_count_2023"]))[:10]:
    print(row)

print("\n===== HIGHEST IMAGE COUNTS =====")
for row in sorted(rows, key=lambda r: int(r["image_count_2023"]), reverse=True)[:10]:
    print(row)

print("\n===== AUDIT COMPLETE =====")
