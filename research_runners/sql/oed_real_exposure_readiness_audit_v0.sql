-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- Read-only insurance/OED model-input readiness audit; runs on both Neon
-- insurance main and isolated validation branch. Returns aggregates ONLY.
-- These counters are NOT a rights or model-admission decision and cannot
-- turn any source, research receipt, company-level aggregate or synthetic
-- property into a real insured location or policy.

WITH facts AS (
 SELECT
   (SELECT count(*) FROM registry.source_record) AS registered_source_records,
   (SELECT count(*) FROM registry.source_record
     WHERE classification = 'landscape_candidate') AS landscape_only_records,
   (SELECT count(*) FROM registry.source_record
     WHERE classification = 'admitted_manifest'
       AND review_status = 'approved_metadata_only') AS metadata_only_manifest_records,
   (SELECT count(*) FROM registry.source_record
     WHERE classification = 'admitted_manifest'
       AND admissible_for_raw IS TRUE) AS manifest_raw_import_allowed_records,
   (SELECT count(*) FROM exposure.portfolio) AS total_portfolios,
   (SELECT count(*) FROM exposure.portfolio
     WHERE portfolio_type = 'real_restricted') AS real_restricted_portfolios,
   (SELECT count(*) FROM exposure.portfolio
     WHERE portfolio_type = 'synthetic') AS invented_portfolios,
   (SELECT count(*) FROM exposure.exposure_unit) AS all_exposure_units,
   (SELECT count(*) FROM exposure.exposure_unit
     WHERE assumption_status = 'synthetic') AS invented_exposure_units,
   (SELECT count(*) FROM exposure.exposure_unit u
     JOIN exposure.portfolio_version v ON u.portfolio_version_id = v.portfolio_version_id
     JOIN exposure.portfolio p ON v.portfolio_id = p.portfolio_id
     WHERE p.portfolio_type = 'real_restricted' AND u.unit_type = 'asset'
       AND u.source_key IS NOT NULL AND u.insured_value IS NOT NULL) AS source_linked_real_asset_values,
   (SELECT count(*) FROM insurance.contract WHERE is_synthetic IS FALSE) AS real_treaties
)
SELECT current_database() AS database_name,
       registered_source_records, landscape_only_records,
       metadata_only_manifest_records, manifest_raw_import_allowed_records,
       total_portfolios, real_restricted_portfolios, invented_portfolios,
       all_exposure_units, invented_exposure_units, source_linked_real_asset_values,
       real_treaties,
       to_regclass('insurance.account_v1') IS NOT NULL AS has_synthetic_account_tables,
       -- Even when structural prerequisites appear, actual rights, privacy,
       -- policy-level claims and model science require a separate review.
       FALSE AS real_oed_model_input_approved,
       array_remove(ARRAY[
         CASE WHEN real_restricted_portfolios=0 THEN 'no_real_insurer_portfolio'::text END,
         CASE WHEN source_linked_real_asset_values=0 THEN 'no_source_linked_real_asset_values'::text END,
         CASE WHEN manifest_raw_import_allowed_records=0 THEN 'no_admitted_raw_source_access'::text END,
         'policy_level_coverage_and_provenance_requires_separate_review'::text,
         'commercial_rights_privacy_and_model_science_requires_separate_review'::text
       ],NULL) AS model_input_blockers
FROM facts;
