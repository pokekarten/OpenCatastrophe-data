-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Exact research scope: EMSC SeismicPortal FDSN Event, source_sample_v0 #12,
-- observed 2026-11-11 earthquake. Single previously staged derived JSON sample.
-- SELECT-only: never fetches external provider bytes and never mutates Neon.
-- The observed third coordinate is -10 and depth property is +10 (source
-- sample units not generalized to every GeoJSON source or future release).
-- PASS means only sample-internal consistency, NOT event accuracy, hazard
-- calibration, commercial admission, or approved CAT-model input.
-- Eleven synthetic mutations must each fail without raising cast exceptions.
-- This query requires PostgreSQL 16+ pg_input_is_valid (Neon PostgreSQL 17 validated).
WITH source AS (
  SELECT sample_json AS j
  FROM research.source_sample_v0
  WHERE sample_id = 12 AND source_id = 'emsc.seismicportal.fdsn-event'
),
cases AS (
  SELECT 'stored_source_sample_12' AS case_id, true AS expected_valid, j FROM source
  UNION ALL SELECT 'negative_latitude_91', false, jsonb_set(j,'{geometry,coordinates,1}','91'::jsonb) FROM source
  UNION ALL SELECT 'negative_longitude_disagreement', false, jsonb_set(j,'{geometry,coordinates,0}','141'::jsonb) FROM source
  UNION ALL SELECT 'negative_depth_sign', false, jsonb_set(j,'{geometry,coordinates,2}','10'::jsonb) FROM source
  UNION ALL SELECT 'negative_missing_depth', false, jsonb_set(j,'{properties,depth}','null'::jsonb) FROM source
  UNION ALL SELECT 'negative_event_identity', false, jsonb_set(j,'{event_id}','"wrong_event"'::jsonb) FROM source
  UNION ALL SELECT 'negative_negative_magnitude', false, jsonb_set(j,'{properties,mag}','-1'::jsonb) FROM source
  UNION ALL SELECT 'negative_update_before_origin', false, jsonb_set(j,'{properties,lastupdate}','"2026-11-10T00:00:00Z"'::jsonb) FROM source
  UNION ALL SELECT 'negative_malformed_longitude_text', false, jsonb_set(j,'{properties,lon}','"not-a-number"'::jsonb) FROM source
  UNION ALL SELECT 'negative_malformed_timestamp', false, jsonb_set(j,'{properties,time}','"invalid-time"'::jsonb) FROM source
  UNION ALL SELECT 'negative_nonboolean_science_flag', false, jsonb_set(j,'{scientific_hazard_intensity_verified}','"maybe"'::jsonb) FROM source
  UNION ALL SELECT 'negative_malformed_magnitude_text', false, jsonb_set(j,'{properties,mag}','"n/a"'::jsonb) FROM source
),
typed AS (
  SELECT case_id, expected_valid, j,
    CASE WHEN jsonb_typeof(j #> '{geometry,coordinates,0}') = 'number'
      THEN (j #>> '{geometry,coordinates,0}')::numeric END AS geo_lon,
    CASE WHEN jsonb_typeof(j #> '{geometry,coordinates,1}') = 'number'
      THEN (j #>> '{geometry,coordinates,1}')::numeric END AS geo_lat,
    CASE WHEN jsonb_typeof(j #> '{geometry,coordinates,2}') = 'number'
      THEN (j #>> '{geometry,coordinates,2}')::numeric END AS geo_z,
    CASE WHEN jsonb_typeof(j #> '{properties,lon}') = 'number'
      THEN (j #>> '{properties,lon}')::numeric END AS prop_lon,
    CASE WHEN jsonb_typeof(j #> '{properties,lat}') = 'number'
      THEN (j #>> '{properties,lat}')::numeric END AS prop_lat,
    CASE WHEN jsonb_typeof(j #> '{properties,depth}') = 'number'
      THEN (j #>> '{properties,depth}')::numeric END AS prop_depth,
    CASE WHEN jsonb_typeof(j #> '{properties,mag}') = 'number'
      THEN (j #>> '{properties,mag}')::numeric END AS prop_mag,
    CASE
      WHEN (j #>> '{properties,time}') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$'
       AND pg_input_is_valid(coalesce(j #>> '{properties,time}',''), 'timestamptz')
      THEN (j #>> '{properties,time}')::timestamptz
    END AS event_utc,
    CASE
      WHEN (j #>> '{properties,lastupdate}') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$'
       AND pg_input_is_valid(coalesce(j #>> '{properties,lastupdate}',''), 'timestamptz')
      THEN (j #>> '{properties,lastupdate}')::timestamptz
    END AS updated_utc
  FROM cases
),
evaluated AS (
 SELECT case_id, expected_valid,
    COALESCE(
      (j #>> '{geometry,type}') = 'Point'
      AND geo_lon BETWEEN -180 AND 180
      AND geo_lat BETWEEN -90 AND 90
      AND geo_lon = prop_lon
      AND geo_lat = prop_lat
      AND geo_z = -prop_depth
      AND prop_depth >= 0
      AND prop_mag > 0
      AND (j ->> 'event_id') = (j #>> '{properties,unid}')
      AND (j ->> 'source_id') = (j #>> '{properties,source_id}')
      AND (j #>> '{properties,source_catalog}') = 'EMSC-RTS'
      AND updated_utc >= event_utc
      AND (j -> 'scientific_hazard_intensity_verified') = 'false'::jsonb
    , false) AS actual_valid
 FROM typed
)
SELECT case_id, expected_valid, actual_valid, (expected_valid = COALESCE(actual_valid,false)) AS pass
FROM evaluated
UNION ALL
SELECT 'missing_source_sample_12', true, false, false WHERE NOT EXISTS (SELECT 1 FROM source)
ORDER BY case_id;
