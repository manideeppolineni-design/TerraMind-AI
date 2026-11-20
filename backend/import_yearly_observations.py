
import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is missing from .env")

csv_path = (
    Path(__file__).resolve().parent.parent
    / "notebooks"
    / "grid_yearly_observations.csv"
)

if not csv_path.exists():
    raise FileNotFoundError(f"CSV file not found: {csv_path}")

with csv_path.open("r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    rows = [
        (
            row["grid_id"],
            int(row["year"]),
            int(row["image_count"])
        )
        for row in reader
    ]

if not rows:
    raise ValueError("The CSV file contains no data.")

print("Rows loaded from CSV:", len(rows))

with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO grid_yearly_observations
                (grid_id, year, image_count)
            VALUES (%s, %s, %s)
            ON CONFLICT (grid_id, year)
            DO UPDATE SET
                image_count = EXCLUDED.image_count
            """,
            rows
        )

        cursor.execute("""
            SELECT COUNT(*)
            FROM grid_yearly_observations
        """)

        total_rows = cursor.fetchone()[0]

        cursor.execute("""
            SELECT MIN(year), MAX(year)
            FROM grid_yearly_observations
        """)

        first_year, last_year = cursor.fetchone()

print("Import successful!")
print("Total yearly records in database:", total_rows)
print("Years covered:", first_year, "to", last_year)
