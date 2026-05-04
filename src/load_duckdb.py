from __future__ import annotations

import duckdb
import pandas as pd

from src.config import (
    AIRPORT_ACCESS_CSV,
    DESTINATIONS_CSV,
    DUCKDB_PATH,
    POI_COUNTS_CSV,
    WEATHER_DAILY_CSV,
)


def _load_csv(con: duckdb.DuckDBPyConnection, table_name: str, path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required input file does not exist: {path}")

    df = pd.read_csv(path)
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.register("_tmp_df", df)
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM _tmp_df")
    con.unregister("_tmp_df")
    print(f"Loaded {len(df)} rows into {table_name}")


def load_raw_to_duckdb() -> None:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DUCKDB_PATH)) as con:
        _load_csv(con, "raw_destinations", DESTINATIONS_CSV)
        _load_csv(con, "raw_weather_daily", WEATHER_DAILY_CSV)
        _load_csv(con, "raw_poi_counts", POI_COUNTS_CSV)
        _load_csv(con, "raw_airport_access", AIRPORT_ACCESS_CSV)

        for table_name in [
            "raw_destinations",
            "raw_weather_daily",
            "raw_poi_counts",
            "raw_airport_access",
        ]:
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            if count == 0:
                raise ValueError(f"{table_name} is empty")


if __name__ == "__main__":
    load_raw_to_duckdb()
