from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

queries = {
    "TOTAL RECORDS": """
        SELECT COUNT(*) FROM india_admin_locations
    """,

    "RURAL / URBAN COUNTS": """
        SELECT urban_rural, COUNT(*)
        FROM india_admin_locations
        GROUP BY urban_rural
        ORDER BY urban_rural
    """,

    "DISTRICT COUNT": """
        SELECT COUNT(DISTINCT district)
        FROM india_admin_locations
    """,

    "DISTRICT RECORD COUNTS": """
        SELECT district, COUNT(*)
        FROM india_admin_locations
        GROUP BY district
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """,

    "DUPLICATE VILLAGE CODES": """
        SELECT village_code, COUNT(*) AS records,
               STRING_AGG(village_name, ', ') AS names
        FROM india_admin_locations
        WHERE village_code IS NOT NULL
        GROUP BY village_code
        HAVING COUNT(*) > 1
        ORDER BY records DESC, village_code
    """,

    "GEOGRAPHIC EXTENT": """
        SELECT
            ROUND(ST_XMin(ST_Extent(geom))::numeric, 5) AS min_lon,
            ROUND(ST_YMin(ST_Extent(geom))::numeric, 5) AS min_lat,
            ROUND(ST_XMax(ST_Extent(geom))::numeric, 5) AS max_lon,
            ROUND(ST_YMax(ST_Extent(geom))::numeric, 5) AS max_lat
        FROM india_admin_locations
    """,

    "EMPTY OR INVALID GEOMETRIES": """
        SELECT COUNT(*)
        FROM india_admin_locations
        WHERE geom IS NULL
           OR ST_IsEmpty(geom)
           OR NOT ST_IsValid(geom)
    """,

    "DUPLICATE SOURCE INDICES": """
        SELECT COUNT(*) - COUNT(DISTINCT source_feature_index)
        FROM india_admin_locations
    """
}

with engine.connect() as connection:
    for label, sql in queries.items():
        print(f"\n===== {label} =====")

        result = connection.execute(text(sql))

        for row in result:
            print(*row)

    print("\n===== VILLAGE SEARCH TEST =====")

    rows = connection.execute(text("""
        SELECT village_name, district, subdistrict,
               urban_rural, village_code,
               ROUND(ST_Y(ST_PointOnSurface(geom))::numeric, 6)
                   AS latitude,
               ROUND(ST_X(ST_PointOnSurface(geom))::numeric, 6)
                   AS longitude
        FROM india_admin_locations
        WHERE lower(village_name) LIKE '%athipattu%'
        ORDER BY village_name
        LIMIT 10
    """))

    for row in rows:
        print(*row)

engine.dispose()
