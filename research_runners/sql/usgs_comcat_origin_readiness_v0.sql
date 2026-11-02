-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY. Select CAT-only Neon insurance-risk-core / insurance / main.
-- The validation-schema-20261031 branch currently lacks this research relation;
-- a missing relation must error, never be reported as an empty research sample.
-- USGS ComCat research origins are NOT a stochastic hazard event catalogue,
-- shaking/intensity footprints, insured loss records or admitted model inputs.
-- Provider IDs and query URLs do NOT substitute for original-response SHA-256.
WITH observations AS (
    SELECT usgs_event_id, origin_time_utc, magnitude, longitude, latitude,
           depth_km, source_event_url, query_url, raw_response_sha256,
           source_review_status, source_provider, model_admitted
    FROM research.usgs_comcat_origin_observation_v0
),
quality AS (
    SELECT count(*)::bigint AS observations,
           count(DISTINCT usgs_event_id)::bigint AS unique_event_ids,
           count(*) FILTER (WHERE usgs_event_id IS NULL OR btrim(usgs_event_id) = '')::bigint AS missing_event_ids,
           count(*) FILTER (WHERE origin_time_utc IS NULL)::bigint AS missing_origin_times,
           count(*) FILTER (WHERE magnitude IS NULL OR magnitude <= 0 OR magnitude > 10)::bigint AS suspect_magnitudes,
           count(*) FILTER (WHERE longitude IS NULL OR longitude NOT BETWEEN -180 AND 180
                                    OR latitude IS NULL OR latitude NOT BETWEEN -90 AND 90)::bigint AS invalid_coordinates,
           count(*) FILTER (WHERE depth_km IS NULL OR depth_km < 0 OR depth_km > 700)::bigint AS depth_review_candidates,
           count(*) FILTER (WHERE raw_response_sha256 IS NULL)::bigint AS missing_original_response_sha,
           count(*) FILTER (WHERE raw_response_sha256 IS NOT NULL
                                    AND raw_response_sha256 !~ '^[0-9a-f]{64}$')::bigint AS malformed_original_response_sha,
           count(*) FILTER (WHERE raw_response_sha256 ~ '^[0-9a-f]{64}$')::bigint AS original_response_sha_rows,
           count(*) FILTER (WHERE source_event_url IS NULL OR btrim(source_event_url) = ''
                                    OR query_url IS NULL OR btrim(query_url) = '')::bigint AS missing_source_urls,
           count(*) FILTER (WHERE source_review_status IS DISTINCT FROM 'reviewed'
                                    OR source_provider IS DISTINCT FROM 'USGS ComCat')::bigint AS unexpected_research_source_labels,
           count(*) FILTER (WHERE model_admitted IS TRUE)::bigint AS claimed_model_admissions,
           count(DISTINCT query_url)::bigint AS distinct_source_queries,
           min(origin_time_utc) AS earliest_origin,
           max(origin_time_utc) AS latest_origin,
           min(magnitude) AS minimum_magnitude,
           max(magnitude) AS maximum_magnitude
    FROM observations
)
SELECT *,
       CASE
           WHEN observations = 0 THEN 'MISSING_RESEARCH_ROWS'
           WHEN claimed_model_admissions > 0 THEN 'UNEXPECTED_ADMISSION_REQUIRES_REVIEW'
           WHEN unique_event_ids <> observations OR missing_event_ids > 0
                OR missing_origin_times > 0 OR suspect_magnitudes > 0
                OR invalid_coordinates > 0 OR depth_review_candidates > 0
                OR missing_source_urls > 0 OR unexpected_research_source_labels > 0
                THEN 'RESEARCH_RECORD_QUALITY_BLOCKED'
           WHEN missing_original_response_sha > 0
                OR malformed_original_response_sha > 0
                OR original_response_sha_rows <> observations
                THEN 'RESEARCH_ORIGINAL_BYTES_NOT_PINNED'
           ELSE 'RESEARCH_STRUCTURALLY_CHECKED_NOT_ADMITTED'
       END AS evidence_status,
       FALSE AS complete_stochastic_event_catalogue_verified,
       FALSE AS hazard_intensity_footprints_verified,
       FALSE AS scientific_calibration_verified,
       FALSE AS insurer_loss_or_model_input_admitted
FROM quality;
