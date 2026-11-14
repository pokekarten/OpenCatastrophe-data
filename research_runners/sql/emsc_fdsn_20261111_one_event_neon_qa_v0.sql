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
-- Seven synthetic mutations must each fail the same strict science gate.
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
),
evaluated AS (
 SELECT case_id, expected_valid,
    (
      COALESCE(j #>> '{geometry,type}' = 'Point',false)
      AND jsonb_typeof(j #> '{geometry,coordinates,0}') = 'number'
      AND jsonb_typeof(j #> '{geometry,coordinates,1}') = 'number'
      AND jsonb_typeof(j #> '{geometry,coordinates,2}') = 'number'
      AND jsonb_typeof(j #> '{properties,depth}') = 'number'
      AND jsonb_typeof(j #> '{properties,mag}') = 'number'
      AND COALESCE((j #>> '{geometry,coordinates,0}')::numeric BETWEEN -180 AND 180,false)
      AND COALESCE((j #>> '{geometry,coordinates,1}')::numeric BETWEEN -90 AND 90,false)
      AND COALESCE((j #>> '{geometry,coordinates,0}')::numeric = (j #>> '{properties,lon}')::numeric,false)
      AND COALESCE((j #>> '{geometry,coordinates,1}')::numeric = (j #>> '{properties,lat}')::numeric,false)
      AND COALESCE((j #>> '{geometry,coordinates,2}')::numeric = -(j #>> '{properties,depth}')::numeric,false)
      AND COALESCE((j #>> '{properties,depth}')::numeric >= 0,false)
      AND COALESCE((j #>> '{properties,mag}')::numeric > 0,false)
      AND COALESCE(j ->> 'event_id' = j #>> '{properties,unid}',false)
      AND COALESCE(j ->> 'source_id' = j #>> '{properties,source_id}',false)
      AND COALESCE(j #>> '{properties,source_catalog}' = 'EMSC-RTS',false)
      AND COALESCE((j #>> '{properties,lastupdate}')::timestamptz >= (j #>> '{properties,time}')::timestamptz,false)
      AND COALESCE((j ->> 'scientific_hazard_intensity_verified')::boolean = false,false)
    ) AS actual_valid
 FROM cases
)
SELECT case_id, expected_valid, actual_valid, (expected_valid = COALESCE(actual_valid,false)) AS pass
FROM evaluated
UNION ALL
SELECT 'missing_source_sample_12', true, false, false WHERE NOT EXISTS (SELECT 1 FROM source)
ORDER BY case_id;
