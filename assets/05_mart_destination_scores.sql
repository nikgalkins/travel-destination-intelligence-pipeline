/* @bruin

name: mart_destination_scores
type: duckdb.sql
materialization:
  type: table

depends:
  - stg_destination_activity

columns:
  - name: destination_id
    type: string
    checks:
      - name: not_null
      - name: unique
  - name: final_score
    type: double
    checks:
      - name: not_null
      - name: positive

custom_checks:
  - name: project returns at least five destinations
    query: SELECT COUNT(*) >= 5 FROM mart_destination_scores
    value: 1

@bruin */

WITH weather AS (
    SELECT
        destination_id,
        ROUND(AVG(temperature_max_c), 1) AS avg_max_temp_c,
        ROUND(AVG(temperature_min_c), 1) AS avg_min_temp_c,
        ROUND(AVG(precipitation_mm), 1) AS avg_daily_precipitation_mm
    FROM raw_weather_daily
    GROUP BY destination_id
),

base AS (
    SELECT
        a.destination_id,
        a.destination_name,
        a.country,
        a.latitude,
        a.longitude,
        a.primary_trip_type,
        aa.origin_city,
        aa.origin_airport_iata,
        aa.nearest_airport_iata,
        aa.nearest_airport_name,
        aa.airport_to_destination_km,
        aa.origin_to_destination_airport_km,
        w.avg_max_temp_c,
        w.avg_min_temp_c,
        w.avg_daily_precipitation_mm,
        a.accommodation_count,
        a.beach_count,
        a.surf_count,
        a.outdoor_count,
        a.culture_count,
        a.food_nightlife_count,
        a.activity_total_count
    FROM stg_destination_activity a
    LEFT JOIN weather w USING (destination_id)
    LEFT JOIN raw_airport_access aa USING (destination_id)
),

component_scores AS (
    SELECT
        *,
        ROUND(GREATEST(0, LEAST(100,
            100 - ABS(COALESCE(avg_max_temp_c, 24) - 26) * 4
                - COALESCE(avg_daily_precipitation_mm, 0) * 4
        )), 1) AS weather_score,

        ROUND(GREATEST(0, LEAST(100,
            100 - COALESCE(origin_to_destination_airport_km, 0) / 55
                - COALESCE(airport_to_destination_km, 0) * 0.6
        )), 1) AS access_score,

        ROUND(LEAST(100, COALESCE(accommodation_count, 0) * 0.7), 1) AS stay_score,
        ROUND(LEAST(100, COALESCE(beach_count, 0) * 8 + COALESCE(surf_count, 0) * 25), 1) AS beach_activity_score,
        ROUND(LEAST(100, COALESCE(outdoor_count, 0) * 7 + COALESCE(culture_count, 0) * 0.5), 1) AS outdoor_activity_score,
        ROUND(LEAST(100, COALESCE(culture_count, 0) * 2.5 + COALESCE(food_nightlife_count, 0) * 0.4), 1) AS city_activity_score
    FROM base
)

SELECT
    *,
    ROUND(
        0.35 * beach_activity_score
      + 0.25 * weather_score
      + 0.20 * access_score
      + 0.20 * stay_score,
      1
    ) AS beach_trip_score,

    ROUND(
        0.40 * outdoor_activity_score
      + 0.25 * weather_score
      + 0.20 * access_score
      + 0.15 * stay_score,
      1
    ) AS outdoor_trip_score,

    ROUND(
        0.40 * city_activity_score
      + 0.25 * stay_score
      + 0.20 * access_score
      + 0.15 * weather_score,
      1
    ) AS city_break_score,

    ROUND(
        0.25 * beach_activity_score
      + 0.25 * outdoor_activity_score
      + 0.25 * city_activity_score
      + 0.15 * weather_score
      + 0.10 * access_score,
      1
    ) AS final_score
FROM component_scores
ORDER BY final_score DESC
