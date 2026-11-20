from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as connection:
    print("PostGIS version:")
    print(connection.execute(
        text("SELECT PostGIS_Full_Version()")
    ).scalar())

    print("\nExisting grid records:")
    print(connection.execute(
        text("SELECT COUNT(*) FROM india_grid_catalogue")
    ).scalar())

    print("\nYearly observation records:")
    print(connection.execute(
        text("SELECT COUNT(*) FROM grid_yearly_observations")
    ).scalar())

engine.dispose()
