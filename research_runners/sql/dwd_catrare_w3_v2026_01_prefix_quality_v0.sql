-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- CatRaRE W3 Eta v2026.01, DWD, first 4096 original CSV bytes only.
-- Research-only SELECT SQL against existing private Neon sample #26.
-- 7 structural and scientific-semantic checks; 7 synthetic negative controls.
-- Source-native receipt SHA is compared with the pinned original 4-KiB prefix
-- receipt, NOT independently hashed from original provider bytes here.
-- This does not prove the other 12,406,505 original bytes, the whole event set,
-- spatial polygons, native projection, source frequency, return periods,
-- vendor independence, insured loss or CAT-model readiness.
-- Original provider: DOI 10.5676/DWD/CatRaRE_W3_Eta_v2026.01
-- DWD licence: CDC data CC BY 4.0 (requires DWD attribution).
-- Reviewed access: access/dwd.catrare.w3-eta.v2026.01.json
-- SQL timestamps have no attached UTC offset in the stored source CSV slice;
-- verify elapsed durations without asserting a timezone.
--
-- Expected 7 PASS rows for exactly the existing source sample #26.
WITH original AS (
 SELECT source_id,product_version,provider_response_sha256,sample_sha256,
        research_only,model_input_approved,request_identity,sample_json
 FROM research.source_sample_v0
 WHERE sample_id=26 AND source_id='dwd.catrare.w3-eta.v2026.01'
), events AS (
 SELECT elem,ord FROM original,
 LATERAL jsonb_array_elements(sample_json->'original_source_records') WITH ORDINALITY AS e(elem,ord)
), typed AS (
 SELECT ord,elem->>'KEY_FIELD' event_key,(elem->>'Event_ID')::int event_id,
        (elem->>'Date_START')::timestamp start_time,(elem->>'Date_END')::timestamp end_time,
        (elem->>'Duration')::int duration_hours,
        (elem->>'RRmax')::numeric max_rain_mm,(elem->>'RRmean')::numeric mean_rain_mm,
        (elem->>'Area')::numeric area_native,(elem->>'Area_LAEA')::numeric area_laea,
        (elem->>'Eta')::numeric eta
 FROM events
), checks AS (
 SELECT 'pinned_w3_identity_and_hash' check_id,
 (SELECT count(*)=1 AND bool_and(source_id='dwd.catrare.w3-eta.v2026.01'
  AND product_version='2026.01'
  AND provider_response_sha256='a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12'
  AND sample_sha256 ~ '^[0-9a-f]{64}$'
  AND request_identity LIKE '%CatRaRE_2001_2025_W3_Eta_v2026_01.csv Range:bytes=0-4095') FROM original) pass
 UNION ALL SELECT 'single_4096byte_67column_three_row_scope',
 (SELECT count(*)=1 AND bool_and((sample_json->>'range_bytes')::int=4096
  AND jsonb_array_length(sample_json->'original_schema_header')=67
  AND jsonb_array_length(sample_json->'original_source_records')=3
  AND (sample_json->>'row_count')::int=3
  AND sample_json->>'delimiter'=';'
  AND sample_json->>'csv_encoding'='UTF-8') FROM original)
 UNION ALL SELECT 'header_first_three_source_fields',
 (SELECT count(*)=1 AND bool_and(sample_json->'original_schema_header'->>0='CatVersion'
  AND sample_json->'original_schema_header'->>1='KEY_FIELD'
  AND sample_json->'original_schema_header'->>2='Event_ID') FROM original)
 UNION ALL SELECT 'sample_event_identifiers_unique_and_version_qualified',
 (SELECT count(*)=3 AND count(DISTINCT event_id)=3 AND count(DISTINCT event_key)=3
  AND bool_and(event_key='W3_Eta_'||lpad(event_id::text,6,'0')) FROM typed)
 UNION ALL SELECT 'duration_matches_start_end_no_timezone_assumed',
 (SELECT count(*)=3 AND bool_and(end_time>start_time
  AND end_time-start_time=duration_hours*interval '1 hour'
  AND duration_hours IN (1,2,3,4,6,9,12,18,24,48,72)
  AND start_time>=timestamp '2001-01-01' AND end_time<timestamp '2026-01-01') FROM typed)
 UNION ALL SELECT 'positive_rain_and_nonzero_area_eta',
 (SELECT count(*)=3 AND bool_and(max_rain_mm>=mean_rain_mm AND mean_rain_mm>0
  AND area_native>0 AND area_laea>0 AND eta>0) FROM typed)
 UNION ALL SELECT 'research_only_no_model_admission',
 (SELECT count(*)=1 AND bool_and(research_only AND NOT model_input_approved) FROM original)
)
SELECT check_id,CASE WHEN pass THEN 'PASS' ELSE 'FAIL' END result
FROM checks ORDER BY check_id;

-- Synthetic negative controls. Expected 7 rows with test_pass=true.
WITH synthetic(case_id,event_id,prior_event_id,duration_h,elapsed_h,rain_max,rain_mean,expected_accept) AS (
 VALUES
 ('valid',1,0,4::int,4::int,51.5::numeric,37.97::numeric,true),
 ('duplicate_id',1,1,4,4,51.5,37.97,false),
 ('invalid_duration',2,0,5,5,51.5,37.97,false),
 ('time_mismatch',3,0,6,7,51.5,37.97,false),
 ('negative_rain',4,0,6,6,-1,1,false),
 ('mean_above_max',5,0,6,6,1,2,false),
 ('missing_event_id',NULL,0,6,6,1,0.5,false)
)
SELECT case_id,expected_accept,
 coalesce(event_id IS NOT NULL AND event_id<>prior_event_id
 AND duration_h IN (1,2,3,4,6,9,12,18,24,48,72) AND elapsed_h=duration_h
 AND rain_max>=rain_mean AND rain_mean>0,false) actual_accept,
 coalesce(event_id IS NOT NULL AND event_id<>prior_event_id
 AND duration_h IN (1,2,3,4,6,9,12,18,24,48,72) AND elapsed_h=duration_h
 AND rain_max>=rain_mean AND rain_mean>0,false)=expected_accept test_pass
 FROM synthetic ORDER BY case_id;
