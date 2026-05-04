/* @bruin

name: stg_destination_activity
type: duckdb.sql
materialization:
  type: table

depends:
  - load_raw_to_duckdb

columns:
  - name: destination_id
    type: string
    checks:
      - name: not_null
      - name: unique
  - name: activity_total_count
    type: integer
    checks:
      - name: not_null

@bruin */

WITH pivoted_pois AS (
    SELECT
        destination_id,
        SUM(CASE WHEN category = 'accommodation' THEN poi_count ELSE 0 END) AS accommodation_count,
        SUM(CASE WHEN category = 'beach' THEN poi_count ELSE 0 END) AS beach_count,
        SUM(CASE WHEN category = 'surf' THEN poi_count ELSE 0 END) AS surf_count,
        SUM(CASE WHEN category = 'outdoor' THEN poi_count ELSE 0 END) AS outdoor_count,
        SUM(CASE WHEN category = 'culture' THEN poi_count ELSE 0 END) AS culture_count,
        SUM(CASE WHEN category = 'food_nightlife' THEN poi_count ELSE 0 END) AS food_nightlife_count
    FROM raw_poi_counts
    GROUP BY destination_id
)

SELECT
    d.destination_id,
    d.destination_name,
    d.country,
    d.latitude,
    d.longitude,
    d.primary_trip_type,
    COALESCE(p.accommodation_count, 0) AS accommodation_count,
    COALESCE(p.beach_count, 0) AS beach_count,
    COALESCE(p.surf_count, 0) AS surf_count,
    COALESCE(p.outdoor_count, 0) AS outdoor_count,
    COALESCE(p.culture_count, 0) AS culture_count,
    COALESCE(p.food_nightlife_count, 0) AS food_nightlife_count,
    COALESCE(p.beach_count, 0)
      + COALESCE(p.surf_count, 0)
      + COALESCE(p.outdoor_count, 0)
      + COALESCE(p.culture_count, 0)
      + COALESCE(p.food_nightlife_count, 0) AS activity_total_count
FROM raw_destinations d
LEFT JOIN pivoted_pois p USING (destination_id)
