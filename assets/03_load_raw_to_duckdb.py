"""@bruin
name: load_raw_to_duckdb
depends:
  - extract_weather
  - extract_airport_access
  - extract_osm_poi_counts
@bruin"""

from src.load_duckdb import load_raw_to_duckdb

load_raw_to_duckdb()
