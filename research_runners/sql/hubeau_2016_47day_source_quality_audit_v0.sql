-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- SELECT-only live Hubeau QmJ research QA. Numeric status/quality/method code
-- distribution is preserved, not silently treated as "all validated".
-- No provider observations, station coordinates, or hashes are exported.
-- This does not establish legal or scientific model admission.
WITH series AS (
    SELECT code_station,
           count(*)::bigint AS rows,
           count(DISTINCT observed_date)::bigint AS distinct_days,
           (max(observed_date) - min(observed_date) + 1)::integer AS calendar_days_in_span,
           count(*) FILTER (WHERE source_status_code = 12)::bigint AS status_code_12,
           count(*) FILTER (WHERE source_status_code = 16)::bigint AS status_code_16,
           count(*) FILTER (WHERE source_quality_code = 12)::bigint AS quality_code_12,
           count(*) FILTER (WHERE source_quality_code = 20)::bigint AS quality_code_20,
           count(*) FILTER (WHERE source_method_code = 4)::bigint AS method_code_4,
           count(*) FILTER (WHERE source_method_code = 8)::bigint AS method_code_8,
           count(*) FILTER (WHERE source_method_code = 10)::bigint AS method_code_10,
           count(*) FILTER (WHERE original_response_sha256 IS NULL
                                OR original_response_sha256 !~ '^[a-f0-9]{64}$')::bigint AS malformed_sha_format,
           count(DISTINCT original_response_sha256)::bigint AS distinct_response_hashes,
           count(*) FILTER (WHERE original_licence_reuse_reviewed IS TRUE)::bigint AS rights_reviewed_rows,
           count(*) FILTER (WHERE model_input_admitted IS TRUE)::bigint AS model_admitted_rows,
           count(*) FILTER (WHERE physical_flood_event_identity_verified IS TRUE)::bigint AS event_verified_rows,
           count(*) FILTER (WHERE original_daily_flow_lps IS NULL
                                OR normalized_daily_flow_m3s IS NULL
                                OR abs(original_daily_flow_lps / 1000 - normalized_daily_flow_m3s) > 0.00001)::bigint AS conversion_mismatches,
           min(observed_date)::text AS first_day,
           max(observed_date)::text AS last_day,
           min(normalized_daily_flow_m3s) AS min_q_m3s,
           max(normalized_daily_flow_m3s) AS max_q_m3s
    FROM research.hubeau_seine_47day_daily_q_research_v0
    GROUP BY code_station
)
SELECT *,
       CASE
           WHEN rows <> distinct_days
                OR distinct_days <> calendar_days_in_span
                OR malformed_sha_format <> 0
                OR conversion_mismatches <> 0
               THEN 'TECHNICAL_QA_FAIL'
           WHEN rights_reviewed_rows < rows
                OR event_verified_rows < rows
                OR model_admitted_rows < rows
               THEN 'RESEARCH_ONLY_MODEL_GATES_OPEN'
           ELSE 'REVIEW_UNITS_AND_SOURCE_SEMANTICS'
       END AS technical_gate
FROM series
ORDER BY code_station;
