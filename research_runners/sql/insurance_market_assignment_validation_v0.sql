-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY: run against Neon insurance-risk-core/insurance
-- branch validation-schema-20261031 (br-summer-sky-bawujqu8).
-- Source-level aggregates only; NO inferred insurer x ZIP joins, no TIV,
-- no portfolio admission and no raw source export.
WITH fl AS (
  SELECT count(*) AS report_rows,
         count(DISTINCT naic_code) AS reported_naic_codes,
         count(*) FILTER (WHERE original_xlsx_sha256 ~ '^[0-9a-f]{64}$') AS original_sha_rows,
         count(*) FILTER (WHERE commercial_rights_reviewed) AS rights_reviewed_rows,
         count(*) FILTER (WHERE legal_carrier_at_zip_level_observed) AS carrier_zip_rows,
         count(*) FILTER (WHERE parcel_level_building_tiv_observed) AS parcel_tiv_rows,
         count(*) FILTER (WHERE cat_loss_calibration_admissible) AS calibrated_rows,
         min(report_as_of) AS earliest_asof, max(report_as_of) AS latest_asof
    FROM exposure.fl_oir_mir_company_statewide_original_v1
), tx AS (
  SELECT count(*) AS report_rows,
         count(DISTINCT zip_text) AS zip5_count,
         count(*) FILTER (WHERE original_http_sha256 ~ '^[0-9a-f]{64}$') AS original_sha_rows,
         count(*) FILTER (WHERE legal_insurer_id_observed) AS carrier_rows,
         count(*) FILTER (WHERE actual_insured_tiv IS NOT NULL) AS insured_tiv_rows,
         count(*) FILTER (WHERE reported_policy_count_signed < 0) AS negative_rows,
         count(*) FILTER (WHERE quality_status = 'QUARANTINED_NEGATIVE') AS quarantined_rows,
         count(*) FILTER (WHERE
           (reported_policy_count_signed < 0 AND quality_status <> 'QUARANTINED_NEGATIVE')
           OR (reported_policy_count_signed >= 0 AND quality_status = 'QUARANTINED_NEGATIVE')
           OR quality_status NOT IN ('RESEARCH_MARKET_ONLY','QUARANTINED_NEGATIVE')
         ) AS quarantine_mismatches,
         min(source_effective_date) AS earliest_asof, max(source_effective_date) AS latest_asof
    FROM exposure.market_policy_stock_research_v0
)
SELECT 'validation_florida_texas'::text AS evidence_scope,
       current_database() AS database_name,
       (current_database()='insurance') AS expected_database,
       fl.report_rows AS florida_report_rows,
       fl.reported_naic_codes AS florida_naic_codes,
       fl.original_sha_rows AS florida_original_sha_rows,
       fl.rights_reviewed_rows AS florida_rights_reviewed_rows,
       fl.carrier_zip_rows AS florida_carrier_zip_rows,
       fl.parcel_tiv_rows AS florida_parcel_tiv_rows,
       fl.calibrated_rows AS florida_calibrated_rows,
       fl.earliest_asof AS florida_earliest_asof,
       fl.latest_asof AS florida_latest_asof,
       tx.report_rows AS texas_report_rows,
       tx.zip5_count AS texas_zip5_count,
       tx.original_sha_rows AS texas_original_sha_rows,
       tx.carrier_rows AS texas_carrier_rows,
       tx.insured_tiv_rows AS texas_insured_tiv_rows,
       tx.negative_rows AS texas_negative_rows,
       tx.quarantined_rows AS texas_quarantined_rows,
       tx.quarantine_mismatches AS texas_quarantine_mismatches,
       tx.earliest_asof AS texas_earliest_asof,
       tx.latest_asof AS texas_latest_asof,
       false::boolean AS direct_insurer_zip_join_admitted,
       false::boolean AS model_input_approved,
       CASE
         WHEN current_database()<>'insurance' THEN 'BLOCKED_WRONG_DATABASE'
         WHEN fl.report_rows=0 OR tx.report_rows=0 THEN 'BLOCKED_EMPTY_SOURCE_COHORT'
         WHEN tx.quarantine_mismatches<>0 THEN 'BLOCKED_TEXAS_QUARANTINE_INTEGRITY'
         WHEN fl.original_sha_rows<>fl.report_rows OR tx.original_sha_rows<>tx.report_rows
           THEN 'BLOCKED_ORIGINAL_SOURCE_PROVENANCE'
         WHEN fl.rights_reviewed_rows<>fl.report_rows THEN 'BLOCKED_SOURCE_RIGHTS_REVIEW'
         WHEN fl.carrier_zip_rows=0 OR tx.carrier_rows=0 THEN 'BLOCKED_NO_SHARED_CARRIER_ZIP_GRAIN'
         WHEN fl.parcel_tiv_rows=0 OR tx.insured_tiv_rows=0 THEN 'BLOCKED_NO_LOCATION_INSURED_TIV'
         ELSE 'BLOCKED_INDEPENDENT_RIGHTS_AND_SCIENTIFIC_ADMISSION'
       END AS first_gate
  FROM fl CROSS JOIN tx;
