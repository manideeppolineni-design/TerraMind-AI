import json
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = __import__("os").getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing")

SOURCE = ROOT_DIR / (
    "data/raw/geography/tamil_nadu/extracted/vb_soi_tn.GeoJSON"
)

TABLE = "india_admin_locations"
BATCH_SIZE = 250

engine = create_engine(DATABASE_URL)

def clean_properties(properties):
    return {
        str(key).strip(): value
        for key, value in properties.items()
    }

def clean_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None

def clean_number(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

create_table = text("""
CREATE TABLE IF NOT EXISTS india_admin_locations (
    id BIGSERIAL PRIMARY KEY,
    source_feature_index INTEGER NOT NULL UNIQUE,
    village_code VARCHAR(30),
    village_name TEXT NOT NULL,
    gram_panchayat TEXT,
    block_name TEXT,
    subdistrict TEXT,
    district TEXT,
    state_code VARCHAR(10),
    state_name TEXT,
    urban_rural VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',
    population DOUBLE PRECISION,
    households DOUBLE PRECISION,
    source_crs INTEGER NOT NULL DEFAULT 7755,
    source_name TEXT NOT NULL DEFAULT 'Survey of India',
    source_properties JSONB NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

create_indexes = [
    """
    CREATE INDEX IF NOT EXISTS
    idx_india_admin_locations_geom
    ON india_admin_locations USING GIST (geom);
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_india_admin_locations_name
    ON india_admin_locations (lower(village_name));
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_india_admin_locations_district
    ON india_admin_locations (lower(district));
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_india_admin_locations_state
    ON india_admin_locations (state_code);
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_india_admin_locations_village_code
    ON india_admin_locations (village_code);
    """
]

insert_sql = text("""
INSERT INTO india_admin_locations (
    source_feature_index,
    village_code,
    village_name,
    gram_panchayat,
    block_name,
    subdistrict,
    district,
    state_code,
    state_name,
    urban_rural,
    population,
    households,
    source_crs,
    source_properties,
    geom
)
VALUES (
    :source_feature_index,
    :village_code,
    :village_name,
    :gram_panchayat,
    :block_name,
    :subdistrict,
    :district,
    :state_code,
    :state_name,
    :urban_rural,
    :population,
    :households,
    7755,
    CAST(:source_properties AS JSONB),
    ST_Multi(
        ST_CollectionExtract(
            ST_MakeValid(
                ST_Transform(
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry_json),
                        7755
                    ),
                    4326
                )
            ),
            3
        )
    )
)
ON CONFLICT (source_feature_index)
DO UPDATE SET
    village_code = EXCLUDED.village_code,
    village_name = EXCLUDED.village_name,
    gram_panchayat = EXCLUDED.gram_panchayat,
    block_name = EXCLUDED.block_name,
    subdistrict = EXCLUDED.subdistrict,
    district = EXCLUDED.district,
    state_code = EXCLUDED.state_code,
    state_name = EXCLUDED.state_name,
    urban_rural = EXCLUDED.urban_rural,
    population = EXCLUDED.population,
    households = EXCLUDED.households,
    source_crs = EXCLUDED.source_crs,
    source_properties = EXCLUDED.source_properties,
    geom = EXCLUDED.geom,
    updated_at = CURRENT_TIMESTAMP;
""")

def main():
    print("Reading Tamil Nadu GeoJSON...")

    with SOURCE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    features = data.get("features", [])
    print("Source features:", len(features))

    imported = 0
    skipped = 0

    with engine.begin() as connection:
        connection.execute(create_table)

        for index, statement in enumerate(create_indexes):
            connection.execute(text(statement))

        batch = []

        for feature_index, feature in enumerate(features):
            properties = clean_properties(
                feature.get("properties", {})
            )

            geometry = feature.get("geometry")

            village_name = clean_text(
                properties.get("village")
            )

            if not geometry or not village_name:
                skipped += 1
                continue

            classification = (
                clean_text(properties.get("total_urban_rural"))
                or "UNKNOWN"
            ).upper()

            if classification not in ("RURAL", "URBAN"):
                classification = "UNKNOWN"

            row = {
                "source_feature_index": feature_index,
                "village_code": clean_text(
                    properties.get("vlcode")
                ),
                "village_name": village_name,
                "gram_panchayat": clean_text(
                    properties.get("gram_panchayat_name")
                ),
                "block_name": clean_text(
                    properties.get("block")
                ),
                "subdistrict": clean_text(
                    properties.get("subdistric")
                ),
                "district": clean_text(
                    properties.get("district")
                ),
                "state_code": clean_text(
                    properties.get("stcode")
                ),
                "state_name": clean_text(
                    properties.get("state_name")
                ) or "Tamil Nadu",
                "urban_rural": classification,
                "population": clean_number(
                    properties.get("total_population_village")
                ),
                "households": clean_number(
                    properties.get("total_households")
                ),
                "source_properties": json.dumps(
                    properties,
                    ensure_ascii=False
                ),
                "geometry_json": json.dumps(
                    geometry,
                    ensure_ascii=False
                )
            }

            batch.append(row)

            if len(batch) >= BATCH_SIZE:
                connection.execute(insert_sql, batch)
                imported += len(batch)
                print(f"Processed: {imported}/{len(features)}")

                batch.clear()

        if batch:
            connection.execute(insert_sql, batch)
            imported += len(batch)

    print("\n===== IMPORT SUMMARY =====")
    print("Source features:", len(features))
    print("Processed:", imported)
    print("Skipped:", skipped)

    with engine.connect() as connection:
        total = connection.execute(text("""
            SELECT COUNT(*)
            FROM india_admin_locations
        """)).scalar()

        invalid = connection.execute(text("""
            SELECT COUNT(*)
            FROM india_admin_locations
            WHERE geom IS NULL
               OR ST_IsEmpty(geom)
               OR NOT ST_IsValid(geom)
        """)).scalar()

        wrong_srid = connection.execute(text("""
            SELECT COUNT(*)
            FROM india_admin_locations
            WHERE ST_SRID(geom) <> 4326
        """)).scalar()

        print("Total table records:", total)
        print("Invalid stored geometries:", invalid)
        print("Wrong SRID records:", wrong_srid)

    print("\nImport completed.")

if __name__ == "__main__":
    main()
