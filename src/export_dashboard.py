from __future__ import annotations

import duckdb

from src.config import DASHBOARD_EXPORT_CSV, DUCKDB_PATH


def export_destination_scores() -> None:
    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(f"DuckDB database not found: {DUCKDB_PATH}")

    DASHBOARD_EXPORT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as con:
        con.execute(
            f"""
            COPY (
                SELECT *
                FROM mart_destination_scores
                ORDER BY final_score DESC
            )
            TO '{DASHBOARD_EXPORT_CSV.as_posix()}'
            WITH (HEADER, DELIMITER ',')
            """
        )
    print(f"Exported dashboard table to {DASHBOARD_EXPORT_CSV}")


if __name__ == "__main__":
    export_destination_scores()
