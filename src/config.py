from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SEED_DIR = DATA_DIR / "seeds"
DUCKDB_PATH = DATA_DIR / "travel.duckdb"

DESTINATIONS_CSV = SEED_DIR / "destinations.csv"
WEATHER_DAILY_CSV = RAW_DIR / "weather_daily.csv"
POI_COUNTS_CSV = RAW_DIR / "poi_counts.csv"
AIRPORT_ACCESS_CSV = RAW_DIR / "airport_access.csv"
DASHBOARD_EXPORT_CSV = DATA_DIR / "destination_scores.csv"

ORIGIN = {
    "name": "Istanbul",
    "latitude": 41.0082,
    "longitude": 28.9784,
}
