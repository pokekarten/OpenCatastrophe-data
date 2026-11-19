-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only, source-version-aware *context* QA; no provider response bytes
-- retrieved here, no permanent DB writes, and no model-use rights inferred.
-- Official source: https://hydro.eaufrance.fr/stationhydro/F700000103/evenements
-- Official station incident records: 2016-06-02 ~23:00 automatic outage,
-- stage manually read by observers from 2016-06-03; impaired velocity-sonde
-- cabling reported 2016-06-06. Exact restoration time is NOT established.
-- Review ONLY June 3-7, 2016; these five days must not be described as a
-- fully verified duration of outage or as independent continuous telemetry.
-- Compare Paris F700000103 with Ponthierry F447000302 without conflating
-- measured stage HIXnJ and reconstructed/calculated daily mean flow QmnJ.
WITH observed AS (
    SELECT code_station,
           count(*) FILTER (WHERE observed_date BETWEEN DATE '2016-06-03'
                                                      AND DATE '2016-06-07')::bigint AS compared_days,
           count(*) FILTER (WHERE observed_date BETWEEN DATE '2016-06-03'
                                                      AND DATE '2016-06-07'
                             AND source_method_code = 4)::bigint AS reconstructed_days,
           count(*) FILTER (WHERE observed_date BETWEEN DATE '2016-06-03'
                                                      AND DATE '2016-06-07'
                             AND source_method_code = 8)::bigint AS calculated_days,
           count(*) FILTER (WHERE observed_date BETWEEN DATE '2016-06-03'
                                                      AND DATE '2016-06-07'
                             AND source_method_code = 10)::bigint AS expert_assessed_days,
           count(*) FILTER (WHERE observed_date BETWEEN DATE '2016-06-03'
                                                      AND DATE '2016-06-07'
                             AND source_quality_code = 12)::bigint AS doubtful_quality_days,
           count(*) FILTER (WHERE observed_date BETWEEN DATE '2016-06-03'
                                                      AND DATE '2016-06-07'
                             AND source_quality_code = 20)::bigint AS good_quality_days,
           count(*) FILTER (WHERE observed_date BETWEEN DATE '2016-06-03'
                                                      AND DATE '2016-06-07'
                             AND source_status_code = 16)::bigint AS validated_days,
           count(*) FILTER (WHERE observed_date BETWEEN DATE '2016-06-03'
                                                      AND DATE '2016-06-07'
                             AND model_input_admitted IS TRUE)::bigint AS approved_days
    FROM research.hubeau_seine_47day_daily_q_research_v0
    WHERE code_station IN ('F700000103', 'F447000302')
    GROUP BY code_station
)
SELECT code_station, compared_days, reconstructed_days, calculated_days,
       expert_assessed_days, doubtful_quality_days, good_quality_days,
       validated_days, approved_days,
       CASE
         WHEN compared_days <> 5 THEN 'WINDOW_INCOMPLETE'
         WHEN code_station = 'F700000103'
           AND reconstructed_days = 5
           AND validated_days = 5
           AND good_quality_days = 5
           THEN 'INCIDENT_CONTEXT_VALIDATED_RECONSTRUCTED_QMNJ_NOT_DIRECT'
         WHEN code_station = 'F447000302'
           AND calculated_days = 5
           AND doubtful_quality_days = 5
           THEN 'DOUBTFUL_CALCULATED_QMNJ_NOT_CALIBRATION'
         ELSE 'UNEXPECTED_CODE_PROFILE_REVIEW_REQUIRED'
       END AS scientific_caution,
       'HISTORICAL_INCIDENT_CROSS_REFERENCE_NOT_MODEL_ADMISSION' AS source_role
FROM observed
ORDER BY code_station;
