from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any

import pandas as pd
import requests

from src.config import DESTINATIONS_CSV, POI_COUNTS_CSV
from src.utils import read_destinations, write_csv


OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

SEARCH_RADIUS_METERS = 25000

CATEGORY_FILTERS = {
    "accommodation": [
        '["tourism"~"^(hotel|hostel|guest_house|apartment|chalet)$"]',
    ],
    "beach": [
        '["natural"="beach"]',
        '["leisure"="beach_resort"]',
    ],
    "surf": [
        '["sport"="surfing"]',
    ],
    "outdoor": [
        '["route"~"^(hiking|bicycle)$"]',
        '["natural"~"^(peak|cliff)$"]',
        '["sport"="climbing"]',
    ],
    "culture": [
        '["tourism"~"^(museum|attraction|gallery|viewpoint)$"]',
        '["historic"]',
    ],
    "food_nightlife": [
        '["amenity"~"^(restaurant|cafe|bar|pub|nightclub)$"]',
    ],
}


# Safety fallback used only when Overpass is unavailable or rejects the request.
# This keeps the pipeline reproducible for the course demo instead of failing.
FALLBACK_COUNTS = {
    "antalya": {
        "accommodation": 120,
        "beach": 16,
        "surf": 0,
        "outdoor": 18,
        "culture": 90,
        "food_nightlife": 350,
    },
    "tbilisi": {
        "accommodation": 100,
        "beach": 0,
        "surf": 0,
        "outdoor": 24,
        "culture": 160,
        "food_nightlife": 450,
    },
    "batumi": {
        "accommodation": 90,
        "beach": 12,
        "surf": 0,
        "outdoor": 18,
        "culture": 45,
        "food_nightlife": 220,
    },
    "cappadocia": {
        "accommodation": 70,
        "beach": 0,
        "surf": 0,
        "outdoor": 48,
        "culture": 80,
        "food_nightlife": 110,
    },
    "athens": {
        "accommodation": 150,
        "beach": 7,
        "surf": 0,
        "outdoor": 15,
        "culture": 300,
        "food_nightlife": 700,
    },
    "rome": {
        "accommodation": 240,
        "beach": 0,
        "surf": 0,
        "outdoor": 12,
        "culture": 800,
        "food_nightlife": 900,
    },
    "barcelona": {
        "accommodation": 220,
        "beach": 12,
        "surf": 1,
        "outdoor": 15,
        "culture": 420,
        "food_nightlife": 950,
    },
    "lisbon": {
        "accommodation": 160,
        "beach": 8,
        "surf": 4,
        "outdoor": 20,
        "culture": 250,
        "food_nightlife": 650,
    },
    "tenerife": {
        "accommodation": 140,
        "beach": 20,
        "surf": 10,
        "outdoor": 60,
        "culture": 120,
        "food_nightlife": 350,
    },
    "dubai": {
        "accommodation": 300,
        "beach": 15,
        "surf": 2,
        "outdoor": 8,
        "culture": 250,
        "food_nightlife": 1200,
    },
}


def build_count_query(
    lat: float,
    lon: float,
    category: str,
    radius: int = SEARCH_RADIUS_METERS,
) -> str:
    selectors = []

    for osm_filter in CATEGORY_FILTERS[category]:
        selectors.append(f"node(around:{radius},{lat},{lon}){osm_filter};")
        selectors.append(f"way(around:{radius},{lat},{lon}){osm_filter};")
        selectors.append(f"relation(around:{radius},{lat},{lon}){osm_filter};")

    selectors_sql = "\n      ".join(selectors)

    return f"""
    [out:json][timeout:35];
    (
      {selectors_sql}
    );
    out count;
    """


def fetch_count_from_overpass(query: str) -> int:
    headers = {
        "User-Agent": "travel-destination-intelligence-pipeline/1.0 (student project)",
        "Accept": "application/json",
    }

    last_error: Exception | None = None

    for url in OVERPASS_URLS:
        try:
            response = requests.post(
                url,
                data={"data": query},
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()
            elements = response.json().get("elements", [])

            if not elements:
                return 0

            tags = elements[0].get("tags", {})
            return int(tags.get("total", 0))

        except Exception as exc:
            last_error = exc
            time.sleep(1.0)

    if last_error:
        raise last_error

    return 0


def fallback_counts_for_destination(destination_id: str) -> dict[str, int]:
    return FALLBACK_COUNTS.get(
        destination_id,
        {
            "accommodation": 0,
            "beach": 0,
            "surf": 0,
            "outdoor": 0,
            "culture": 0,
            "food_nightlife": 0,
        },
    )


def fetch_osm_counts_for_destination(row: pd.Series) -> list[dict[str, Any]]:
    extracted_at = datetime.now(timezone.utc).isoformat()
    counts: dict[str, int] = {}

    try:
        for category in CATEGORY_FILTERS:
            query = build_count_query(row["latitude"], row["longitude"], category)
            counts[category] = fetch_count_from_overpass(query)
            time.sleep(0.3)

    except Exception as exc:
        print(
            f"WARNING: OSM count query failed for {row['destination_name']}: {exc}. "
            "Using fallback activity counts."
        )
        counts = fallback_counts_for_destination(row["destination_id"])

    return [
        {
            "destination_id": row["destination_id"],
            "destination_name": row["destination_name"],
            "category": category,
            "poi_count": count,
            "radius_meters": SEARCH_RADIUS_METERS,
            "extracted_at_utc": extracted_at,
        }
        for category, count in counts.items()
    ]


def extract_osm_poi_counts() -> pd.DataFrame:
    destinations = read_destinations(DESTINATIONS_CSV)
    records: list[dict[str, Any]] = []

    for _, row in destinations.iterrows():
        print(f"Fetching OSM POI counts for {row['destination_name']}...")
        records.extend(fetch_osm_counts_for_destination(row))
        time.sleep(0.5)

    df = pd.DataFrame(records)
    write_csv(df, POI_COUNTS_CSV)
    print(f"Wrote {len(df)} OSM POI category rows to {POI_COUNTS_CSV}")
    return df


if __name__ == "__main__":
    extract_osm_poi_counts()