-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- SELECT-only lag-sensitivity diagnostics on two 2016 Hub'Eau QmnJ series.
-- Lag L means Paris date = Ponthierry date + L calendar days.
-- Correlation is descriptive, never a wave-travel-time or causal estimate.
-- Full-level and first-difference correlations have different sample sizes;
-- derivative filtering excludes any null first differences.
WITH daily AS (
    SELECT observed_date,
           max(normalized_daily_flow_m3s) FILTER (WHERE code_station = 'F447000302') AS q_ponthierry,
           max(normalized_daily_flow_m3s) FILTER (WHERE code_station = 'F700000103') AS q_paris,
           max(source_quality_code) FILTER (WHERE code_station = 'F447000302') AS quality_ponthierry
    FROM research.hubeau_seine_47day_daily_q_research_v0
    WHERE code_station IN ('F447000302', 'F700000103')
      AND observed_date BETWEEN DATE '2016-05-15' AND DATE '2016-06-30'
    GROUP BY observed_date
),
deltas AS (
    SELECT observed_date, q_ponthierry, q_paris, quality_ponthierry,
           q_ponthierry - lag(q_ponthierry) OVER (ORDER BY observed_date) AS dq_ponthierry,
           q_paris - lag(q_paris) OVER (ORDER BY observed_date) AS dq_paris
    FROM daily
)
SELECT offsets.lag_days,
       count(*)::bigint AS paired_days_for_level,
       count(*) FILTER (WHERE a.dq_ponthierry IS NOT NULL AND b.dq_paris IS NOT NULL)::bigint AS paired_days_for_difference,
       round(corr(a.q_ponthierry, b.q_paris)::numeric, 4) AS level_corr,
       round(corr(a.dq_ponthierry, b.dq_paris)::numeric, 4) AS difference_corr,
       round(corr(a.dq_ponthierry, b.dq_paris)
             FILTER (WHERE a.quality_ponthierry = 20)::numeric, 4) AS quality20_difference_corr
FROM generate_series(-2, 2) AS offsets(lag_days)
JOIN deltas a ON a.q_ponthierry IS NOT NULL
JOIN deltas b ON b.observed_date = a.observed_date + offsets.lag_days
             AND b.q_paris IS NOT NULL
GROUP BY offsets.lag_days
ORDER BY offsets.lag_days;
