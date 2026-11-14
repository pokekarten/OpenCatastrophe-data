-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- NOAA CO-OPS San Francisco 9414290, 2026-01-01, derived research quality check.
-- Run using read-only SQL against the authorized insurance Neon research database.
-- Exactly two previously staged, research-only rows (#3 and #40).
-- No upstream API access, source bytes, writes, licensing promotion or CAT admission.
-- Checks 8 structural/partial semantic conditions; 5 synthetic negative controls.
-- WARNING: only six + twelve selected observations are stored here. The 240-point
-- full-day mean/extrema CANNOT be independently recomputed from these JSONB rows.
-- Only observed water level relative to MLLW, not storm-surge residual, flood depth,
-- flood footprint, return period, vulnerability or insurer loss.
-- Primary NOAA API semantics: https://api.tidesandcurrents.noaa.gov/api/dev/
-- Upstream access contract: access/noaa.coops.water-levels.json
-- Existing original-response hash is read from Neon, not freshly reverified.
--
-- Expected: 8 PASS records (specific research snapshot, not a general provider test).
WITH pair AS (
  SELECT sample_id, source_id, sample_json, provider_response_sha256, sample_sha256,
         research_only, model_input_approved
    FROM research.source_sample_v0
   WHERE source_id='noaa.coops.water-levels' AND sample_id IN (3,40)
), older AS (SELECT * FROM pair WHERE sample_id=3),
newer AS (SELECT * FROM pair WHERE sample_id=40),
six AS (
  SELECT elem,ord FROM older,
  LATERAL jsonb_array_elements(sample_json->'water_level_mllw_meters')
  WITH ORDINALITY AS a(elem,ord)
), two_hour AS (
  SELECT elem,ord FROM newer,
  LATERAL jsonb_array_elements(sample_json->'sampled_every_120min')
  WITH ORDINALITY AS a(elem,ord)
), checks AS (
 SELECT 'identity_and_datum' AS check_id,
  (SELECT count(*)=2 AND count(DISTINCT source_id)=1 AND
   bool_and(coalesce(sample_json->>'datum'='MLLW' AND sample_json->>'station_id'='9414290',false))
   FROM pair) AS passed
 UNION ALL SELECT 'original_and_derived_hash_lineage',
  (SELECT count(*)=2 AND count(DISTINCT provider_response_sha256)=1 AND
   count(DISTINCT sample_sha256)=2 AND
   bool_and(coalesce(provider_response_sha256 ~ '^[0-9a-f]{64}$' AND
                     sample_sha256 ~ '^[0-9a-f]{64}$',false)) FROM pair)
 UNION ALL SELECT 'research_only_not_admitted',
  (SELECT count(*)=2 AND bool_and(coalesce(research_only AND NOT model_input_approved,false)) FROM pair)
 UNION ALL SELECT 'six_consecutive_utc_six_minute_points',
  (SELECT count(*)=6 AND count(DISTINCT elem->>'t')=6 AND
   bool_and(coalesce((elem->>'t')::timestamp=timestamp '2026-01-01 00:00:00'
         +(ord-1)*interval '6 minutes',false)) FROM six)
 UNION ALL SELECT 'twelve_consecutive_utc_two_hour_points',
  (SELECT count(*)=12 AND count(DISTINCT elem->>'time_gmt')=12 AND
   bool_and(coalesce((elem->>'time_gmt')::timestamp=timestamp '2026-01-01 00:00:00'
         +(ord-1)*interval '120 minutes',false)) FROM two_hour)
 UNION ALL SELECT 'observed_values_flags_and_uncertainty',
  (SELECT count(*)=18 AND bool_and(coalesce(level_m BETWEEN -5 AND 10
              AND uncertainty_m>=0 AND flag='v',false))
     FROM (
       SELECT (elem->>'v')::numeric level_m,(elem->>'s')::numeric uncertainty_m,
              elem->>'q' flag FROM six
       UNION ALL
       SELECT (elem->>'water_level_mllw_m')::numeric,
              (elem->>'uncertainty_m')::numeric,elem->>'verified_flag' FROM two_hour
     ) values_checked)
 UNION ALL SELECT 'independent_derived_rows_agree_at_midnight',
  (SELECT EXISTS(SELECT 1 FROM six a JOIN two_hour b ON
      (a.elem->>'t')=(b.elem->>'time_gmt') AND
      (a.elem->>'v')::numeric=(b.elem->>'water_level_mllw_m')::numeric
     WHERE a.ord=1 AND b.ord=1))
 UNION ALL SELECT 'day_summary_structural_bounds_not_full_replay',
  (SELECT coalesce((sample_json->>'original_records')::int=240 AND
        (sample_json->>'cadence_minutes')::int=6 AND
        (sample_json->'quality_flag_counts'->>'v')::int=240 AND
        (sample_json->>'min_level_m')::numeric<=(sample_json->>'mean_level_m')::numeric AND
        (sample_json->>'mean_level_m')::numeric<=(sample_json->>'max_level_m')::numeric AND
        sample_json->>'unit'='metre' AND sample_json->>'timezone'='GMT',false) FROM newer)
)
SELECT check_id,CASE WHEN passed THEN 'PASS' ELSE 'FAIL' END AS result
FROM checks ORDER BY check_id;

-- Entirely synthetic controls for NULL/flag/negative uncertainty/range behavior.
-- Expected: 5 test_pass=true. These do not reproduce the original API response.
WITH cases(case_id,level_m,uncertainty_m,flag,expected_accept) AS (
 VALUES
 ('valid',1.2::numeric,0.03::numeric,'v',true),
 ('missing_flag',1.2,0.03,NULL,false),
 ('missing_value',NULL,0.03,'v',false),
 ('negative_uncertainty',1.2,-0.01,'v',false),
 ('out_of_range',20,0.03,'v',false)
)
SELECT case_id,expected_accept,
       coalesce(level_m BETWEEN -5 AND 10 AND uncertainty_m>=0 AND flag='v',false) AS actual_accept,
       coalesce(level_m BETWEEN -5 AND 10 AND uncertainty_m>=0 AND flag='v',false)=expected_accept AS test_pass
FROM cases ORDER BY case_id;
