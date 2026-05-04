from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = PROJECT_ROOT / "data" / "travel.duckdb"

SCORE_COLUMNS = {
    "Overall": "final_score",
    "Beach trip": "beach_trip_score",
    "Outdoor / hiking trip": "outdoor_trip_score",
    "City break": "city_break_score",
}


@st.cache_data
def load_scores() -> pd.DataFrame:
    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(
            "DuckDB database was not found. Run `bruin run` or `python -m src.run_all` first."
        )

    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as con:
        return con.execute("SELECT * FROM mart_destination_scores").df()


st.set_page_config(page_title="Travel Destination Intelligence", layout="wide")
st.title("Travel Destination Intelligence Pipeline")
st.caption("Origin city: Istanbul. Destination scoring from weather, OSM POIs, and airport accessibility.")

try:
    df = load_scores()
except Exception as exc:
    st.error(str(exc))
    st.stop()

trip_type = st.sidebar.selectbox("Trip type", list(SCORE_COLUMNS))
score_col = SCORE_COLUMNS[trip_type]

df = df.copy()
df["selected_score"] = df[score_col]
df = df.sort_values("selected_score", ascending=False)

top = df.head(10)

col1, col2, col3 = st.columns(3)
col1.metric("Destinations evaluated", len(df))
col2.metric("Best destination", top.iloc[0]["destination_name"])
col3.metric(f"Best {trip_type} score", f"{top.iloc[0]['selected_score']:.1f}")

st.subheader(f"Top destinations for: {trip_type}")
st.bar_chart(top.set_index("destination_name")["selected_score"])

st.subheader("Activity profile by destination")
activity_cols = [
    "accommodation_count",
    "beach_count",
    "surf_count",
    "outdoor_count",
    "culture_count",
    "food_nightlife_count",
]
st.bar_chart(top.set_index("destination_name")[activity_cols])

st.subheader("Weather and accessibility")
st.dataframe(
    top[
        [
            "destination_name",
            "country",
            "nearest_airport_iata",
            "nearest_airport_name",
            "origin_to_destination_airport_km",
            "airport_to_destination_km",
            "avg_max_temp_c",
            "avg_daily_precipitation_mm",
            "weather_score",
            "access_score",
            "stay_score",
            "selected_score",
        ]
    ],
    use_container_width=True,
)

st.subheader("Destination map")
map_df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
st.map(map_df[["lat", "lon"]])

with st.expander("Full scoring table"):
    st.dataframe(df, use_container_width=True)
