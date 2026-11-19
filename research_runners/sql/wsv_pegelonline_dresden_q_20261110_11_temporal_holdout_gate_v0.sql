-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- PEGELONLINE WSV Dresden Elbe Q, historical read-only Neon sample #21
-- (2026-11-10/11), crosslinked station metadata source sample #13.
-- Temporal role in admitted manifest: 2020-2023 holdout; this source snippet
-- CANNOT validate the historical role. Never promote 2026 rolling P1D API data
-- to the 2020-2023 long-term holdout, flood hazard, damage or insurance loss.
-- Provider: https://pegelonline.wsv.de/webservice/guideRestapi
-- Raw WSV data: DL-DE Zero 2.0, unvalidated, REST covers <=31 days.
WITH source AS (
 SELECT s.sample_json j, m.sample_json mj,
   s.provider_response_sha256 original_sha,
   s.sample_kind,s.request_identity
 FROM research.source_sample_v0 s
 JOIN research.source_sample_v0 m
 ON m.sample_id=13 AND m.source_id=s.source_id
 WHERE s.sample_id=21
 AND s.source_id='wsv.pegelonline.elbe-dresden-discharge.2020-2023'
), observations AS (
 SELECT s.*, obs.r, obs.ord::int n
 FROM source s
 CROSS JOIN LATERAL jsonb_array_elements(
   CASE WHEN jsonb_typeof(s.j->'first_twelve_raw_observations')='array'
     THEN s.j->'first_twelve_raw_observations' ELSE '[]'::jsonb END
 ) WITH ORDINALITY obs(r,ord)
), cases AS (
 SELECT n,'source_observed_Q' test,true expected,j,mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'wrong_Q_unit',false,jsonb_set(j,'{unit}','"cm"'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'wrong_station_uuid',false,jsonb_set(j,'{station_uuid}','"00000000-0000-0000-0000-000000000000"'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'wrong_parameter_W',false,jsonb_set(j,'{observation_parameter}','"W"'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'false_2020_2023_holdout',false,jsonb_set(j,'{does_not_validate_source_2020_2023_historical_period}','false'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'false_qualified',false,jsonb_set(j,'{provisional_observations_without_external_quality_review}','false'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'false_cat_admission',false,jsonb_set(j,'{cat_model_admitted}','true'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'bad_original_hash',false,jsonb_set(j,'{original_response_sha256}','"bad"'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'wrong_original_response_count',false,jsonb_set(j,'{original_response_count}','12'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'wrong_relative_window',false,jsonb_set(j,'{derived_from_relative_window}','"P4Y"'),mj,r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'negative_discharge',false,j,mj,jsonb_set(r,'{value}','-1'),original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'text_discharge',false,j,mj,jsonb_set(r,'{value}','"not-measured"'),original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'timestamp_without_utc_offset',false,j,mj,jsonb_set(r,'{timestamp}','"2026-11-10T20:15:00"'),original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'timestamp_wrong_cadence',false,j,mj,jsonb_set(r,'{timestamp}','"2026-11-11T00:00:00+01:00"'),original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'station_metadata_id_mismatch',false,j,jsonb_set(mj,'{raw_station_metadata,uuid}','"00000000-0000-0000-0000-000000000000"'),r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'station_metadata_bad_Q_unit',false,j,jsonb_set(mj,'{raw_station_metadata,timeseries,0,unit}','"cm"'),r,original_sha,sample_kind,request_identity FROM observations
 UNION ALL SELECT n,'station_metadata_bad_Q_cadence',false,j,jsonb_set(mj,'{raw_station_metadata,timeseries,0,equidistance}','60'),r,original_sha,sample_kind,request_identity FROM observations
), typed AS (
 SELECT *,
 CASE WHEN jsonb_typeof(r->'value')='number'
  AND r->>'value' ~ '^[0-9]{1,6}([.][0-9]{1,4})?$'
  THEN (r->>'value')::numeric END q_cms,
 CASE WHEN (r->>'timestamp') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([+-][0-9]{2}:[0-9]{2}|Z)$'
  AND pg_input_is_valid(coalesce(r->>'timestamp',''),'timestamptz')
  THEN (r->>'timestamp')::timestamptz END obs_utc,
 CASE WHEN (j->>'first_measurement_timestamp') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*([+-][0-9]{2}:[0-9]{2}|Z)$'
  AND pg_input_is_valid(coalesce(j->>'first_measurement_timestamp',''),'timestamptz')
  THEN (j->>'first_measurement_timestamp')::timestamptz END source_first,
 CASE WHEN (j->>'last_measurement_timestamp') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*([+-][0-9]{2}:[0-9]{2}|Z)$'
  AND pg_input_is_valid(coalesce(j->>'last_measurement_timestamp',''),'timestamptz')
  THEN (j->>'last_measurement_timestamp')::timestamptz END source_last
 FROM cases
), checked AS (
SELECT n,test,expected,coalesce(
 sample_kind='observed_values'
 AND request_identity='https://pegelonline.wsv.de/webservices/rest-api/v2/stations/70272185-b2b3-4178-96b8-43bea330dcae/Q/measurements.json?start=P1D'
 AND j->>'station_uuid'='70272185-b2b3-4178-96b8-43bea330dcae'
 AND mj #>> '{raw_station_metadata,uuid}'='70272185-b2b3-4178-96b8-43bea330dcae'
 AND mj->>'station_uuid'='70272185-b2b3-4178-96b8-43bea330dcae'
 AND j->>'station'='DRESDEN'
 AND j->>'river'='ELBE'
 AND j->>'observation_parameter'='Q'
 AND j->>'unit'='m³/s'
 AND EXISTS(
   SELECT 1 FROM jsonb_array_elements(CASE
     WHEN jsonb_typeof(mj #> '{raw_station_metadata,timeseries}')='array'
     THEN mj #> '{raw_station_metadata,timeseries}' ELSE '[]'::jsonb END
   ) t(v) WHERE v->>'shortname'='Q' AND v->>'unit'='m³/s'
     AND v->'equidistance'='15'::jsonb
 )
 AND j->>'derived_from_relative_window'='P1D'
 AND j->'original_response_count'='95'::jsonb
 AND jsonb_array_length(CASE WHEN jsonb_typeof(j->'first_twelve_raw_observations')='array'
   THEN j->'first_twelve_raw_observations' ELSE '[]'::jsonb END)=12
 AND j->>'original_response_sha256'=original_sha
 AND j->'cat_model_admitted'='false'::jsonb
 AND j->'does_not_validate_source_2020_2023_historical_period'='true'::jsonb
 AND j->'provisional_observations_without_external_quality_review'='true'::jsonb
 AND source_first IS NOT NULL AND source_last IS NOT NULL
 AND extract(epoch from (source_last-source_first))=94*15*60
 AND source_first>='2026-11-01T00:00:00Z'::timestamptz
 AND source_first<'2026-12-01T00:00:00Z'::timestamptz
 AND obs_utc=source_first+((n-1)*interval '15 minutes')
 AND q_cms>=0 AND q_cms<100000
,false) actual
FROM typed
)
SELECT n,test,expected,actual,expected=actual pass FROM checked
UNION ALL SELECT NULL::int,'exact_twelve_observations_present',true,
 (SELECT count(*)=12 FROM observations),(SELECT count(*)=12 FROM observations)
ORDER BY n NULLS FIRST,test;
