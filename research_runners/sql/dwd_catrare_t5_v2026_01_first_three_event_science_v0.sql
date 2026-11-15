-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- DWD CatRaRE T5 Eta v2026.01, frozen original 4096-byte CSV prefix
-- and 3 complete first event records staged in private Neon sample #27.
-- Historical original Range digest only; no new provider request/hash.
-- SELECT-only scientific event semantics, not full catalogue or CAT admission.
-- Date_START/END are UNTYPED timezone-naive values, NOT validated UTC.
-- W3 shares RADKLIM input: do not infer independent event frequencies.
WITH s AS (
 SELECT sample_json j,provider_response_sha256 original_range_sha,sample_kind
 FROM research.source_sample_v0
 WHERE sample_id=27 AND source_id='dwd.catrare.t5-eta.v2026.01'
), ev AS (
 SELECT s.*,r,ord::int n
 FROM s CROSS JOIN LATERAL jsonb_array_elements(s.j->'original_source_records')
 WITH ORDINALITY v(r,ord)
), cases AS (
 SELECT n,'source_prefix_row' test,true expected,j,r,original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'bad_event_id',false,j,jsonb_set(r,'{Event_ID}','"99999"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'bad_key',false,j,jsonb_set(r,'{KEY_FIELD}','"W3_Eta_000001"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'wrong_version',false,j,jsonb_set(r,'{CatVersion}','"W3_Eta_v2026_01"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'wrong_duration',false,j,jsonb_set(r,'{Duration}','"999"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'end_before_start',false,j,jsonb_set(r,'{Date_END}','"2000-01-01 00:00:00"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'bad_start_code',false,j,jsonb_set(r,'{Start_Time}','"999999999999"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'rain_max_below_mean',false,j,jsonb_set(r,'{RRmax}','"0.01"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'bad_rain_mean',false,j,jsonb_set(r,'{RRmean}','"null"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'area_zero',false,j,jsonb_set(r,'{Area}','"0"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'area_in_g_too_large',false,j,jsonb_set(r,'{Area_in_G}','"9999"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'bad_area_share',false,j,jsonb_set(r,'{AShare_in_G}','"-1"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'wrong_country',false,j,jsonb_set(r,'{Country_RRmax}','"Unknown"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'tmax_below_threshold',false,j,jsonb_set(r,'{Tmax}','"1"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'bad_time_syntax',false,j,jsonb_set(r,'{Date_START}','"not-a-time"'),original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'false_utc_verified',false,jsonb_set(j,'{source_event_time_zone_not_validated}','false'),r,original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'false_crs_verified',false,jsonb_set(j,'{coordinate_reference_projection_not_validated}','false'),r,original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'false_w3_independence',false,jsonb_set(j,'{overlap_with_w3_catalogue_possible}','false'),r,original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'false_full_file_digest',false,jsonb_set(j,'{full_csv_sha256_verified}','true'),r,original_range_sha,sample_kind FROM ev
 UNION ALL SELECT n,'false_model_admission',false,jsonb_set(j,'{model_input_approved}','true'),r,original_range_sha,sample_kind FROM ev
), typed AS (
 SELECT cases.*,
 CASE WHEN r->>'Duration' ~ '^[0-9]{1,3}$' THEN (r->>'Duration')::int END h,
 CASE WHEN r->>'RRmax' ~ '^[0-9]{1,6}([.][0-9]{1,3})?$' THEN (r->>'RRmax')::numeric END rrmax,
 CASE WHEN r->>'RRmean' ~ '^[0-9]{1,6}([.][0-9]{1,3})?$' THEN (r->>'RRmean')::numeric END rrmean,
 CASE WHEN r->>'Area' ~ '^[0-9]{1,8}([.][0-9]{1,3})?$' THEN (r->>'Area')::numeric END area,
 CASE WHEN r->>'Area_in_G' ~ '^[0-9]{1,8}([.][0-9]{1,3})?$' THEN (r->>'Area_in_G')::numeric END within_g,
 CASE WHEN r->>'Area_LAEA' ~ '^[0-9]{1,8}([.][0-9]{1,3})?$' THEN (r->>'Area_LAEA')::numeric END laea,
 CASE WHEN r->>'AShare_in_G' ~ '^[0-9]{1,3}([.][0-9]{1,3})?$' THEN (r->>'AShare_in_G')::numeric END pct,
 CASE WHEN r->>'Eta' ~ '^[0-9]{1,6}([.][0-9]{1,4})?$' THEN (r->>'Eta')::numeric END eta,
 CASE WHEN r->>'Tmax' ~ '^[0-9]{1,6}([.][0-9]{1,3})?$' THEN (r->>'Tmax')::numeric END tmax,
 CASE WHEN r->>'Tmean' ~ '^[0-9]{1,6}([.][0-9]{1,3})?$' THEN (r->>'Tmean')::numeric END tmean,
 CASE WHEN r->>'Date_START' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$'
      AND pg_input_is_valid(coalesce(r->>'Date_START',''),'timestamp')
      THEN (r->>'Date_START')::timestamp END start_unzoned,
 CASE WHEN r->>'Date_END' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$'
      AND pg_input_is_valid(coalesce(r->>'Date_END',''),'timestamp')
      THEN (r->>'Date_END')::timestamp END end_unzoned
 FROM cases
), checked AS (
 SELECT n,test,expected,coalesce(
 sample_kind='observed_values'
 AND original_range_sha='5dc4b6f0dac14f0a442103b78c16f647556bd870898aabff6d9f62aa4534f542'
 AND j->>'product'='DWD CatRaRE T5 Eta v2026.01'
 AND j->>'release_doi'='10.5676/DWD/CatRaRE_T5_Eta_v2026.01'
 AND j->>'source_radar_parent'='RADKLIM-RW v2017.002'
 AND j->>'source_time_window'='2001-01-01 through 2025-12-31'
 AND j->'row_count'='3'::jsonb
 AND j->'range_bytes'='4096'::jsonb
 AND j->>'original_range_request'='bytes=0-4095'
 AND jsonb_array_length(j->'original_schema_header')=67
 AND jsonb_array_length(j->'original_source_records')=3
 AND j->'full_csv_sha256_verified'='false'::jsonb
 AND j->'source_event_time_zone_not_validated'='true'::jsonb
 AND j->'coordinate_reference_projection_not_validated'='true'::jsonb
 AND j->'overlap_with_w3_catalogue_possible'='true'::jsonb
 AND j->'model_input_approved'='false'::jsonb
 AND r->>'CatVersion'='T5_Eta_v2026_01'
 AND r->>'KEY_FIELD'='T5_Eta_'||lpad(n::text,6,'0')
 AND r->>'Event_ID'=n::text
 AND r->>'Country_RRmax'='Deutschland'
 AND start_unzoned IS NOT NULL AND end_unzoned>start_unzoned
 AND start_unzoned>='2001-01-01'::timestamp AND end_unzoned<'2026-01-01'::timestamp
 AND r->>'Start_Time'=to_char(start_unzoned,'YYYYMMDDHH24MI')
 AND r->>'End_Time'=to_char(end_unzoned,'YYYYMMDDHH24MI')
 AND h=extract(epoch FROM (end_unzoned-start_unzoned))/3600
 AND h=ANY(ARRAY[1,2,3,4,6,9,12,18,24,48,72])
 AND area>0 AND within_g BETWEEN 0 AND area AND laea>0
 AND pct BETWEEN 0 AND 100
 AND abs(pct-100*within_g/NULLIF(area,0))<=0.75
 AND rrmax>=rrmean AND rrmean>0
 AND eta>0 AND tmax>=5 AND tmean>0 AND tmean<=tmax
 ,false) actual FROM typed
), distinct_set AS (
 SELECT
  (SELECT count(*)=3 AND count(DISTINCT r->>'Event_ID')=3
      AND count(DISTINCT r->>'KEY_FIELD')=3 FROM ev)
  AND
  (SELECT count(DISTINCT h.value)=67 FROM s,
    jsonb_array_elements_text(j->'original_schema_header') h(value)) valid
)
SELECT n,test,expected,actual,expected=actual pass FROM checked
UNION ALL SELECT NULL::int,'three_unique_events_67_headers',true,
coalesce((SELECT valid FROM distinct_set),false),
coalesce((SELECT valid FROM distinct_set),false)
ORDER BY n NULLS FIRST,test;
