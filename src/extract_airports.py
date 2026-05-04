from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO

import pandas as pd
import requests

from src.config import AIRPORT_ACCESS_CSV, DESTINATIONS_CSV, ORIGIN
from src.utils import haversine_km, read_destinations, write_csv


OURAIRPORTS_CSV_URL = "https://ourairports.com/airports.csv"

FALLBACK_AIRPORTS = [
    {"ident": "LTFM", "type": "large_airport", "name": "Istanbul Airport", "latitude_deg": 41.2613, "longitude_deg": 28.7419, "iso_country": "TR", "municipality": "Istanbul", "iata_code": "IST", "scheduled_service": "yes"},
    {"ident": "LTAI", "type": "large_airport", "name": "Antalya Airport", "latitude_deg": 36.8987, "longitude_deg": 30.8005, "iso_country": "TR", "municipality": "Antalya", "iata_code": "AYT", "scheduled_service": "yes"},
    {"ident": "UGTB", "type": "large_airport", "name": "Tbilisi International Airport", "latitude_deg": 41.6692, "longitude_deg": 44.9547, "iso_country": "GE", "municipality": "Tbilisi", "iata_code": "TBS", "scheduled_service": "yes"},
    {"ident": "UGSB", "type": "medium_airport", "name": "Batumi International Airport", "latitude_deg": 41.6103, "longitude_deg": 41.5997, "iso_country": "GE", "municipality": "Batumi", "iata_code": "BUS", "scheduled_service": "yes"},
    {"ident": "LTAU", "type": "medium_airport", "name": "Kayseri Erkilet Airport", "latitude_deg": 38.7704, "longitude_deg": 35.4954, "iso_country": "TR", "municipality": "Kayseri", "iata_code": "ASR", "scheduled_service": "yes"},
    {"ident": "LGAV", "type": "large_airport", "name": "Athens International Airport", "latitude_deg": 37.9364, "longitude_deg": 23.9445, "iso_country": "GR", "municipality": "Athens", "iata_code": "ATH", "scheduled_service": "yes"},
    {"ident": "LIRF", "type": "large_airport", "name": "Rome–Fiumicino International Airport", "latitude_deg": 41.8003, "longitude_deg": 12.2389, "iso_country": "IT", "municipality": "Rome", "iata_code": "FCO", "scheduled_service": "yes"},
    {"ident": "LEBL", "type": "large_airport", "name": "Barcelona-El Prat Airport", "latitude_deg": 41.2971, "longitude_deg": 2.07846, "iso_country": "ES", "municipality": "Barcelona", "iata_code": "BCN", "scheduled_service": "yes"},
    {"ident": "LPPT", "type": "large_airport", "name": "Lisbon Humberto Delgado Airport", "latitude_deg": 38.7813, "longitude_deg": -9.13592, "iso_country": "PT", "municipality": "Lisbon", "iata_code": "LIS", "scheduled_service": "yes"},
    {"ident": "GCTS", "type": "large_airport", "name": "Tenerife Sur Airport", "latitude_deg": 28.0445, "longitude_deg": -16.5725, "iso_country": "ES", "municipality": "Tenerife", "iata_code": "TFS", "scheduled_service": "yes"},
    {"ident": "OMDB", "type": "large_airport", "name": "Dubai International Airport", "latitude_deg": 25.2528, "longitude_deg": 55.3644, "iso_country": "AE", "municipality": "Dubai", "iata_code": "DXB", "scheduled_service": "yes"},
]


def fetch_airports() -> pd.DataFrame:
    print("Fetching OurAirports CSV...")
    try:
        response = requests.get(OURAIRPORTS_CSV_URL, timeout=60)
        response.raise_for_status()
        airports = pd.read_csv(StringIO(response.text))
    except Exception as exc:
        print(f"WARNING: OurAirports download failed, using fallback airport list: {exc}")
        airports = pd.DataFrame(FALLBACK_AIRPORTS)

    airports = airports[
        airports["type"].isin(["large_airport", "medium_airport"])
        & airports["iata_code"].notna()
    ].copy()
    return airports


def nearest_airport(airports: pd.DataFrame, lat: float, lon: float) -> pd.Series:
    distances = airports.apply(
        lambda r: haversine_km(lat, lon, r["latitude_deg"], r["longitude_deg"]),
        axis=1,
    )
    nearest = airports.loc[distances.idxmin()].copy()
    nearest["distance_to_point_km"] = distances.min()
    return nearest

def extract_airport_access() -> pd.DataFrame:
    destinations = read_destinations(DESTINATIONS_CSV)
    airports = fetch_airports()
    origin_airport = nearest_airport(airports, ORIGIN["latitude"], ORIGIN["longitude"])

    records = []
    for _, row in destinations.iterrows():
        dest_airport = nearest_airport(airports, row["latitude"], row["longitude"])
        route_distance_km = haversine_km(
            origin_airport["latitude_deg"],
            origin_airport["longitude_deg"],
            dest_airport["latitude_deg"],
            dest_airport["longitude_deg"],
        )
        records.append(
            {
                "destination_id": row["destination_id"],
                "destination_name": row["destination_name"],
                "origin_city": ORIGIN["name"],
                "origin_airport_iata": origin_airport["iata_code"],
                "origin_airport_name": origin_airport["name"],
                "nearest_airport_iata": dest_airport["iata_code"],
                "nearest_airport_name": dest_airport["name"],
                "airport_to_destination_km": round(float(dest_airport["distance_to_point_km"]), 1),
                "origin_to_destination_airport_km": round(float(route_distance_km), 1),
                "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )

    df = pd.DataFrame(records)
    write_csv(df, AIRPORT_ACCESS_CSV)
    print(f"Wrote {len(df)} airport access rows to {AIRPORT_ACCESS_CSV}")
    return df


if __name__ == "__main__":
    extract_airport_access()
