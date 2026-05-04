from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

from src.config import DESTINATIONS_CSV, WEATHER_DAILY_CSV
from src.utils import read_destinations, write_csv


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather_for_destination(row: pd.Series) -> list[dict[str, Any]]:
    params = {
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": 7,
        "timezone": "auto",
    }
    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily", {})

    records = []
    for i, forecast_date in enumerate(daily.get("time", [])):
        records.append(
            {
                "destination_id": row["destination_id"],
                "destination_name": row["destination_name"],
                "forecast_date": forecast_date,
                "temperature_max_c": daily.get("temperature_2m_max", [None])[i],
                "temperature_min_c": daily.get("temperature_2m_min", [None])[i],
                "precipitation_mm": daily.get("precipitation_sum", [None])[i],
                "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
    return records


def extract_weather() -> pd.DataFrame:
    destinations = read_destinations(DESTINATIONS_CSV)
    all_records: list[dict[str, Any]] = []

    for _, row in destinations.iterrows():
        print(f"Fetching Open-Meteo forecast for {row['destination_name']}...")
        try:
            all_records.extend(fetch_weather_for_destination(row))
        except Exception as exc:
            print(f"WARNING: Weather fetch failed for {row['destination_name']}: {exc}")
            # Keep the pipeline runnable even if one API request fails.
            all_records.append(
                {
                    "destination_id": row["destination_id"],
                    "destination_name": row["destination_name"],
                    "forecast_date": None,
                    "temperature_max_c": None,
                    "temperature_min_c": None,
                    "precipitation_mm": None,
                    "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
                }
            )

    df = pd.DataFrame(all_records)
    write_csv(df, WEATHER_DAILY_CSV)
    print(f"Wrote {len(df)} weather rows to {WEATHER_DAILY_CSV}")
    return df


if __name__ == "__main__":
    extract_weather()
