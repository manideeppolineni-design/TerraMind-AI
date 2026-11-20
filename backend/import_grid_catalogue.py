
import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is missing from the .env file.")

csv_path = (
    Path(__file__).resolve().parent.parent
    / "notebooks"
    / "india_grid_catalogue.csv"
)

with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        with csv_path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                cursor.execute(
                    """
                    INSERT INTO india_grid_catalogue
                    (grid_id, south, west, image_count_2023)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (grid_id) DO UPDATE SET
                        south = EXCLUDED.south,
                        west = EXCLUDED.west,
                        image_count_2023 = EXCLUDED.image_count_2023
                    """,
                    (
                        row["grid_id"],
                        float(row["south"]),
                        float(row["west"]),
                        int(row["image_count_2023"]),
                    ),
                )

        cursor.execute("SELECT COUNT(*) FROM india_grid_catalogue")
        count = cursor.fetchone()[0]

print(f"Import successful. Grid cells in database: {count}")
