
import csv
from pathlib import Path
from datetime import datetime

from sqlalchemy import text
from backend.main import engine


ROOT_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = ROOT_DIR / "data" / "raw" / "India_Flood_Inventory_v3.csv"


def parse_date(value):
    if not value:
        return None

    value = value.strip()

    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None
    return None


def parse_number(value):
    if not value:
        return None

    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        return None


def main():
    if not CSV_FILE.exists():
        print("CSV file not found:", CSV_FILE)
        return

    inserted = 0
    skipped = 0

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        with engine.begin() as connection:

            for row in reader:

                event_id = (row.get("UEI") or "").strip()

                location = (
                    row.get("Location")
                    or row.get("Districts")
                    or row.get("State")
                    or ""
                ).strip()

                state = (row.get("State") or "").strip()

                event_date = parse_date(
                    row.get("Start Date")
                )

                latitude = parse_number(
                    row.get("Latitude")
                )

                longitude = parse_number(
                    row.get("Longitude")
                )

                severity = (
                    row.get("Severity") or ""
                ).strip()

                source = (
                    row.get("Event Source") or ""
                ).strip()

                description = (
                    row.get("Main Cause") or ""
                ).strip()

                if not event_id or not location or not event_date:
                    skipped += 1
                    continue

                if (
                    latitude is not None
                    and not -90 <= latitude <= 90
                ):
                    latitude = None

                if (
                    longitude is not None
                    and not -180 <= longitude <= 180
                ):
                    longitude = None

                rainfall_mm = None

                existing = connection.execute(
                    text("""
                        SELECT id
                        FROM historical_flood_events
                        WHERE event_name = :event_name
                          AND event_date = :event_date
                    """),
                    {
                        "event_name": event_id,
                        "event_date": event_date,
                    },
                ).first()

                if existing:
                    skipped += 1
                    continue

                connection.execute(
                    text("""
                        INSERT INTO historical_flood_events (
                            event_name,
                            location,
                            state,
                            event_date,
                            rainfall_mm,
                            flood_severity,
                            source,
                            latitude,
                            longitude
                        )
                        VALUES (
                            :event_name,
                            :location,
                            :state,
                            :event_date,
                            :rainfall_mm,
                            :flood_severity,
                            :source,
                            :latitude,
                            :longitude
                        )
                    """),
                    {
                        "event_name": event_id,
                        "location": location,
                        "state": state or None,
                        "event_date": event_date,
                        "rainfall_mm": rainfall_mm,
                        "flood_severity": severity or description or None,
                        "source": source or "India Flood Inventory",
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                )

                inserted += 1

    print("Historical flood import completed")
    print("Inserted records:", inserted)
    print("Skipped records:", skipped)


if __name__ == "__main__":
    main()
