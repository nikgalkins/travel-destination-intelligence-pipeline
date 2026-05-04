# Travel Destination Intelligence Pipeline

A compact end-to-end data engineering project that ranks travel destinations from an Istanbul origin point.

The project answers a practical travel-planning question:

> If a user starts in Istanbul, which destinations look best for a beach trip, outdoor/hiking trip, or city break based on accessibility, weather, activities, and accommodation density?

## Project objective

This project is a prototype for a future travel recommendation service. The product idea is broader: a user selects their current location and intended destination, and the service suggests how to get there, what to do, and where to stay.

For this Data Engineering Zoomcamp submission, the scope is intentionally reduced to an analytics pipeline:

1. Ingest open travel/location/weather data.
2. Store the raw layer locally.
3. Transform the data into scored analytical tables.
4. Build a dashboard that compares destinations by travel-fit score.

## Origin

Current origin city used by the model:

```text
Istanbul, Turkey
```

## Data sources

| Source | Usage |
|---|---|
| `data/seeds/destinations.csv` | Curated seed list of candidate destinations |
| Open-Meteo Forecast API | 7-day weather forecast: max/min temperature and precipitation |
| OurAirports CSV | Nearest airport and distance proxy from Istanbul |
| OpenStreetMap via Overpass API | POI counts for accommodation, beaches, surf, outdoor, culture, and food/nightlife |

## Architecture

```text
Seed destinations
      |
      v
Python extraction assets
  - Open-Meteo weather
  - OurAirports airport access
  - Overpass / OSM POI counts
      |
      v
Raw CSV files in data/raw/
      |
      v
DuckDB raw tables
      |
      v
Bruin SQL transformations
  - stg_destination_activity
  - mart_destination_scores
      |
      v
Streamlit dashboard
```

## Repository structure

```text
.
├── assets/                  # Bruin pipeline assets
├── dashboard/               # Streamlit dashboard
├── data/
│   ├── seeds/               # Versioned seed input
│   └── raw/                 # Generated raw extracts, ignored by git
├── src/                     # Reusable Python pipeline code
├── .bruin.yml               # DuckDB connection
├── pipeline.yml             # Bruin pipeline definition
├── requirements.txt
└── README.md
```

## How to run

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the pipeline with Bruin

```bash
bruin run
```

The Bruin pipeline runs:

1. API extraction assets.
2. Raw CSV loading into DuckDB.
3. SQL transformations.
4. Dashboard CSV export.

### 4. Fallback run without Bruin

If Bruin installation is slow or unavailable, the same project can be run with:

```bash
python -m src.run_all
```

This fallback exists to make the project reproducible during review.

### 5. Launch dashboard

```bash
streamlit run dashboard/app.py
```

## Transformations

### `stg_destination_activity`

Aggregates OSM POI categories per destination:

- `accommodation_count`
- `beach_count`
- `surf_count`
- `outdoor_count`
- `culture_count`
- `food_nightlife_count`
- `activity_total_count`

### `mart_destination_scores`

Combines destination activity, forecast weather, and airport accessibility into analytical scores:

- `weather_score`
- `access_score`
- `stay_score`
- `beach_activity_score`
- `outdoor_activity_score`
- `city_activity_score`
- `beach_trip_score`
- `outdoor_trip_score`
- `city_break_score`
- `final_score`

## Dashboard

The Streamlit dashboard contains:

1. Top destinations by selected trip type.
2. Activity profile by destination.
3. Weather and accessibility table.
4. Destination map.
5. Full scoring table.

## Scoring logic

The scoring model is heuristic and designed for transparency rather than production recommendation quality.

Examples:

- Beach trips prioritize beach/surf POIs, weather, accessibility, and accommodation density.
- Outdoor trips prioritize hiking/outdoor indicators, weather, accessibility, and accommodation density.
- City breaks prioritize culture, food/nightlife, accommodation density, accessibility, and weather.

## Known limitations

- The project uses airport distance as a proxy for travel convenience. It does not ingest live flight schedules or prices.
- OSM POI density is a proxy for available activities and accommodation; it does not measure quality.
- Weather data is a short forecast window, not a full seasonal model.
- Hotel prices and availability are out of scope for the MVP.

## Future work

- Add live flight route/pricing APIs.
- Add hotel prices and availability from a partner or public dataset.
- Add seasonality using historical climate data.
- Add user preference weights.
- Add cloud deployment and scheduled pipeline runs.
- Replace heuristic scoring with a trained ranking model.

## Project status

This is an MVP built for the Data Engineering Zoomcamp final project deadline.
