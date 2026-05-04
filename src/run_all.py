from __future__ import annotations

import duckdb

from src.config import DUCKDB_PATH
from src.extract_airports import extract_airport_access
from src.extract_osm import extract_osm_poi_counts
from src.extract_weather import extract_weather
from src.export_dashboard import export_destination_scores
from src.load_duckdb import load_raw_to_duckdb


SQL_FILES = [
    "assets/04_stg_destination_activity.sql",
    "assets/05_mart_destination_scores.sql",
]


def _extract_sql_body(text: str) -> str:
    marker = "@bruin */"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text


def run_sql_assets() -> None:
    with duckdb.connect(str(DUCKDB_PATH)) as con:
        for sql_file in SQL_FILES:
            print(f"Running SQL asset fallback: {sql_file}")
            sql = _extract_sql_body(open(sql_file, encoding="utf-8").read())
            # The fallback path manually materializes the Bruin SQL assets.
            if "04_stg_destination_activity" in sql_file:
                con.execute("DROP TABLE IF EXISTS stg_destination_activity")
                con.execute(f"CREATE TABLE stg_destination_activity AS {sql}")
            elif "05_mart_destination_scores" in sql_file:
                con.execute("DROP TABLE IF EXISTS mart_destination_scores")
                con.execute(f"CREATE TABLE mart_destination_scores AS {sql}")


def main() -> None:
    extract_weather()
    extract_airport_access()
    extract_osm_poi_counts()
    load_raw_to_duckdb()
    run_sql_assets()
    export_destination_scores()


if __name__ == "__main__":
    main()
