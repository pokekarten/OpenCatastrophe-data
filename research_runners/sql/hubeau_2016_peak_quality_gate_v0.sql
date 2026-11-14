-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- SELECT-only scientific research audit: Hub'Eau v2.0.1 QmnJ, Seine 2016.
-- Codes verified against bounded original-provider API fields (2026-11-03):
-- statut 12=prevalidated, 16=validated; qualification 12=doubtful, 20=good;
-- method 4=reconstructed, 8=calculated, 10=expert-assessed.
-- None of these codes alone creates rights, event identity or model admission.
WITH series AS (
    SELECT code_station, observed_date, normalized_daily_flow_m3s AS q_m3s,
           source_status_code AS status_code,
           source_quality_code AS quality_code,
           source_method_code AS method_code,
           original_licence_reuse_reviewed AS rights_reviewed,
           model_input_admitted AS model_admitted,
           physical_flood_event_identity_verified AS flood_event_verified
    FROM research.hubeau_seine_47day_daily_q_research_v0
    WHERE code_station IN ('F447000302', 'F700000103')
      AND observed_date BETWEEN DATE '2016-05-15' AND DATE '2016-06-30'
),
peak AS (
    SELECT DISTINCT ON (code_station)
           code_station, observed_date AS peak_day,
           q_m3s AS peak_q_m3s, status_code AS peak_status_code,
           quality_code AS peak_quality_code, method_code AS peak_method_code
    FROM series
    ORDER BY code_station, q_m3s DESC, observed_date
),
station_summary AS (
    SELECT code_station, count(*)::bigint AS days,
           count(*) FILTER (WHERE quality_code = 12)::bigint AS doubtful_days,
           count(*) FILTER (WHERE quality_code = 12
                             AND observed_date BETWEEN DATE '2016-06-01' AND DATE '2016-06-07')::bigint AS doubtful_flood_window_days,
           count(*) FILTER (WHERE status_code = 12)::bigint AS prevalidated_days,
           count(*) FILTER (WHERE status_code = 16)::bigint AS validated_days,
           count(*) FILTER (WHERE quality_code = 20)::bigint AS good_quality_days,
           count(*) FILTER (WHERE method_code = 4)::bigint AS reconstructed_days,
           count(*) FILTER (WHERE method_code = 8)::bigint AS calculated_days,
           max(q_m3s) FILTER (WHERE quality_code = 20) AS max_good_quality_q_m3s,
           max(q_m3s) FILTER (WHERE quality_code = 20 AND status_code = 16) AS max_validated_good_q_m3s,
           count(*) FILTER (WHERE rights_reviewed IS TRUE)::bigint AS rights_cleared_rows,
           count(*) FILTER (WHERE flood_event_verified IS TRUE)::bigint AS event_verified_rows,
           count(*) FILTER (WHERE model_admitted IS TRUE)::bigint AS model_admitted_rows
    FROM series
    GROUP BY code_station
)
SELECT s.*, p.peak_day::text AS peak_day, p.peak_q_m3s,
       p.peak_status_code, p.peak_quality_code, p.peak_method_code,
       CASE
           WHEN p.peak_quality_code = 12 THEN 'PEAK_DOUBTFUL_NOT_CALIBRATION'
           WHEN p.peak_status_code = 12 THEN 'PEAK_PREVALIDATED_NOT_CALIBRATION'
           WHEN p.peak_method_code IN (4, 8) THEN 'PEAK_NON_DIRECT_METHOD_REVIEW'
           ELSE 'PEAK_METHOD_AND_ORIGIN_REVIEW'
       END AS peak_scientific_gate,
       CASE
           WHEN s.rights_cleared_rows < s.days
              OR s.event_verified_rows < s.days
              OR s.model_admitted_rows < s.days
           THEN 'RESEARCH_ONLY_SOURCE_GATES_OPEN'
           ELSE 'CHECK_HYDRAULIC_AND_VINTAGE_FITNESS'
       END AS model_usage_gate
FROM station_summary s
JOIN peak p USING (code_station)
ORDER BY s.code_station;
