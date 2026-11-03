-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY: CAT-only Neon insurance-risk-core / insurance / main.
-- Three *distinct USGS catalogue earthquake IDs* in the 2023 Kahramanmaras
-- sequence; these are NOT a preselected single contractual occurrence.
-- Read-only research-row inspection. Never source/catalogue/model admission.
--
-- USGS official sequence description:
-- https://www.usgs.gov/programs/earthquake-hazards/science/frequently-asked-questions-about-2023-earthquakes-turkiye
-- This query validates only three chosen anchors, NOT the full aftershock
-- sequence or complete model earthquake occurrence catalogue.
WITH expected_anchors (usgs_event_id, anchor_label) AS (
    VALUES
      ('us6000jllz'::text, 'M7.8 mainshock'::text),
      ('us6000jlm1'::text, 'M6.7 subsequent earthquake'::text),
      ('us6000jlqa'::text, 'M7.5 subsequent earthquake'::text)
),
anchor_rows AS (
    SELECT e.usgs_event_id AS expected_id, e.anchor_label,
           s.usgs_event_id, s.origin_time_utc, s.magnitude,
           s.latitude, s.longitude, s.source_event_url,
           s.raw_response_sha256, s.model_admitted, s.source_provider,
           s.source_review_status
    FROM expected_anchors e
    LEFT JOIN research.usgs_comcat_origin_observation_v0 s
      ON s.usgs_event_id = e.usgs_event_id
),
anchor_quality AS (
    SELECT count(DISTINCT expected_id)::bigint AS selected_expected_anchors,
           count(usgs_event_id)::bigint AS stored_anchor_rows,
           count(DISTINCT usgs_event_id)::bigint AS distinct_stored_event_ids,
           count(*) FILTER (WHERE usgs_event_id IS NULL)::bigint AS missing_anchor_ids,
           count(*) FILTER (WHERE usgs_event_id IS NOT NULL
                            AND (origin_time_utc IS NULL
                               OR origin_time_utc::date <> DATE '2023-02-06'
                               OR magnitude IS NULL OR magnitude <= 0 OR magnitude > 10
                               OR latitude IS NULL OR longitude IS NULL
                               OR latitude NOT BETWEEN -90 AND 90
                               OR longitude NOT BETWEEN -180 AND 180
                               OR source_event_url IS NULL
                               OR source_provider IS DISTINCT FROM 'USGS ComCat'
                               OR source_review_status IS DISTINCT FROM 'reviewed'
                            ))::bigint AS inconsistent_stored_anchors,
           count(*) FILTER (WHERE usgs_event_id IS NOT NULL
                            AND raw_response_sha256 IS NULL)::bigint AS missing_original_response_sha,
           count(*) FILTER (WHERE usgs_event_id IS NOT NULL
                            AND raw_response_sha256 IS NOT NULL
                            AND raw_response_sha256 !~ '^[0-9a-f]{64}$')::bigint AS malformed_original_sha,
           count(*) FILTER (WHERE usgs_event_id IS NOT NULL
                            AND raw_response_sha256 ~ '^[0-9a-f]{64}$')::bigint AS sha_shaped_rows,
           count(*) FILTER (WHERE model_admitted IS TRUE)::bigint AS unexpected_model_admissions,
           min(origin_time_utc) AS first_origin_time,
           max(origin_time_utc) AS last_origin_time
    FROM anchor_rows
),
source_access AS (
    SELECT count(*)::bigint AS matching_access_contracts,
           count(*) FILTER (WHERE admissible_for_raw IS TRUE)::bigint AS source_raw_admission_flags,
           max(review_status) AS access_review_status,
           max(rights_status) AS access_rights_status
    FROM registry.source_record
    WHERE classification = 'access_contract'
      AND source_id = 'usgs.anss.comcat'
      AND git_path = 'access/usgs.anss.comcat.json'
)
SELECT *,
       CASE
         WHEN stored_anchor_rows <> selected_expected_anchors
           OR distinct_stored_event_ids <> selected_expected_anchors
           OR missing_anchor_ids > 0 THEN 'MISSING_OR_DUPLICATE_ANCHOR_ROWS'
         WHEN inconsistent_stored_anchors > 0 THEN 'RESEARCH_ORIGIN_QUALITY_BLOCKED'
         WHEN unexpected_model_admissions > 0 THEN 'UNEXPECTED_ADMISSION_REQUIRES_REVIEW'
         WHEN missing_original_response_sha > 0
           OR malformed_original_sha > 0
           OR sha_shaped_rows <> selected_expected_anchors
           THEN 'ORIGINAL_USGS_RESPONSE_BYTES_NOT_PINNED'
         ELSE 'RESEARCH_ORIGIN_METADATA_CHECKED_NOT_ADMITTED'
       END AS origin_evidence_status,
       CASE
         WHEN matching_access_contracts <> 1 THEN 'ACCESS_CONTRACT_MISSING_OR_AMBIGUOUS'
         WHEN source_raw_admission_flags <> 0 THEN 'UNEXPECTED_RAW_ADMISSION_REQUIRES_REVIEW'
         ELSE 'RAW_ACCESS_NOT_ADMITTED'
       END AS source_access_status,
       FALSE AS physical_event_family_crosswalk_verified,
       FALSE AS single_contractual_occurrence_verified,
       FALSE AS historic_product_vintages_verified,
       FALSE AS hazard_ground_motion_verified,
       FALSE AS insurance_portfolio_loss_verified,
       FALSE AS annual_cat_capital_metric_justified
FROM anchor_quality CROSS JOIN source_access;
