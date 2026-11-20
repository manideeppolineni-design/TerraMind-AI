from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import json
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

path = Path(
    "data/raw/geography/tamil_nadu/extracted/vb_soi_tn.GeoJSON"
)

with path.open("r", encoding="utf-8") as f:
    data = json.load(f)

print("===== POSTGIS CRS VERIFICATION =====")

with engine.connect() as connection:
    srid_exists = connection.execute(text("""
        SELECT COUNT(*)
        FROM spatial_ref_sys
        WHERE srid = 7755
    """)).scalar()

    print("EPSG:7755 registered:", srid_exists > 0)

    for index in [0, 1, 2, 73, 2912]:
        feature = data["features"][index]
        x, y = feature["geometry"]["coordinates"][0][0][0][:2]

        result = connection.execute(text("""
            SELECT
                ST_X(transformed) AS longitude,
                ST_Y(transformed) AS latitude
            FROM (
                SELECT ST_Transform(
                    ST_SetSRID(
                        ST_MakePoint(:x, :y),
                        7755
                    ),
                    4326
                ) AS transformed
            ) AS converted
        """), {"x": x, "y": y}).one()

        print(
            f"\n{feature['properties']['village']}: "
            f"longitude={result.longitude:.6f}, "
            f"latitude={result.latitude:.6f}"
        )

engine.dispose()
