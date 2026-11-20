from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is missing from .env")

engine = create_engine(database_url)

with engine.connect() as connection:
    print("\n===== DATABASE CONNECTION =====")
    print(connection.execute(text("SELECT current_database()")).scalar())

    print("\n===== EXISTING PUBLIC TABLES =====")
    tables = connection.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)).scalars().all()

    for table in tables:
        print("-", table)

    print("\n===== GEOGRAPHIC AND SATELLITE TABLES =====")
    for table in tables:
        if any(word in table.lower() for word in [
            "india", "grid", "location", "village",
            "district", "state", "flood", "historical"
        ]):
            print(f"\n--- {table} ---")
            columns = connection.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table
                ORDER BY ordinal_position
            """), {"table": table}).all()

            for column in columns:
                print(f"{column[0]}: {column[1]}")

engine.dispose()
