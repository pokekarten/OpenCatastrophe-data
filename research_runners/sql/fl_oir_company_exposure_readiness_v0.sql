-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- RESEARCH ONLY. Apply solely to Neon insurance-risk-core
-- branch validation-schema-20261031, where the staged tables exist.
-- Source: Florida OIR 2025-12-31 MIR company x policy-type report.
-- Never confuse statewide source-reported structure exposure with
-- geocoded company policies or individual building TIV.
CREATE OR REPLACE VIEW research.fl_oir_company_exposure_readiness_v0 AS
WITH cross_state_naic AS (
    SELECT DISTINCT naic_5digit
    FROM research.fl_nc_legal_naic_overlap_research_v1
),
company_group AS (
    SELECT
        source_key,
        report_as_of,
        naic_code,
        min(reported_company_name) AS reported_company_name,
        count(DISTINCT reported_company_name) AS different_reported_names,
        count(*) AS source_policy_type_rows,
        count(DISTINCT reported_policy_type) AS distinct_policy_types,
        sum(reported_policies_in_force) AS policies_in_force_sum_by_reported_type,
        sum(reported_including_wind_policies) AS including_wind_policies_sum_by_type,
        sum(reported_excluding_wind_policies) AS excluding_wind_policies_sum_by_type,
        sum(reported_exposure_usd) AS reported_exposure_usd_sum_by_type,
        sum(reported_exposure_including_wind_usd) AS exposure_including_wind_usd_sum_by_type,
        sum(reported_exposure_excluding_wind_usd) AS exposure_excluding_wind_usd_sum_by_type,
        sum(reported_direct_premium_usd) AS direct_premium_usd_sum_by_type,
        count(DISTINCT original_xlsx_sha256) AS distinct_original_xlsx_hashes,
        count(*) FILTER (
            WHERE source_excel_row IS NULL
               OR naic_code !~ '^[0-9]{5}$'
               OR original_xlsx_sha256 IS NULL
               OR original_xlsx_sha256 !~ '^[0-9a-f]{64}$'
               OR reported_policies_in_force IS NULL
               OR reported_exposure_usd IS NULL
               OR reported_direct_premium_usd IS NULL
               OR reported_policies_in_force < 0
               OR reported_exposure_usd < 0
               OR reported_direct_premium_usd < 0
        ) AS malformed_rows,
        count(*) FILTER (
            WHERE reported_policies_in_force
                      IS DISTINCT FROM (reported_including_wind_policies + reported_excluding_wind_policies)
               OR abs(reported_exposure_usd - (reported_exposure_including_wind_usd + reported_exposure_excluding_wind_usd)) > 0.01
               OR abs(reported_direct_premium_usd - (reported_premium_including_wind_usd + reported_premium_excluding_wind_usd)) > 0.01
               OR reported_exposure_including_wind_usd IS NULL
               OR reported_exposure_excluding_wind_usd IS NULL
               OR reported_premium_including_wind_usd IS NULL
               OR reported_premium_excluding_wind_usd IS NULL
        ) AS component_reconciliation_failures,
        bool_and(coalesce(complete_published_workbook, false)) AS source_workbook_complete,
        bool_and(coalesce(all_regulatory_filers_included, false)) AS all_regulatory_filers_included,
        bool_and(coalesce(commercial_rights_reviewed, false)) AS commercial_rights_reviewed,
        bool_and(coalesce(legal_carrier_at_zip_level_observed, false)) AS legal_carrier_zip_level_observed,
        bool_and(coalesce(parcel_level_building_tiv_observed, false)) AS parcel_level_building_tiv_observed,
        bool_and(coalesce(cat_loss_calibration_admissible, false)) AS source_cat_loss_calibration_admissible
    FROM exposure.fl_oir_mir_company_statewide_original_v1
    GROUP BY source_key, report_as_of, naic_code
)
SELECT
    g.*,
    (c.naic_5digit IS NOT NULL) AS fl_nc_exact_naic_research_overlap,
    'statewide_company_by_reported_policy_type'::text AS observational_grain,
    'source_reported_exposure_not_individual_insured_tiv'::text AS scientific_role,
    false::boolean AS model_input_approved,
    CASE
        WHEN g.malformed_rows > 0
          OR g.component_reconciliation_failures > 0
          OR g.different_reported_names <> 1
          OR g.distinct_original_xlsx_hashes <> 1 THEN 'BLOCKED_SOURCE_RECONCILIATION'
        WHEN NOT g.source_workbook_complete THEN 'BLOCKED_WORKBOOK_INCOMPLETE'
        WHEN NOT g.all_regulatory_filers_included THEN 'BLOCKED_REPORTING_UNIVERSE_UNKNOWN'
        WHEN NOT g.commercial_rights_reviewed THEN 'BLOCKED_RIGHTS_REVIEW'
        WHEN NOT g.legal_carrier_zip_level_observed THEN 'BLOCKED_NO_CARRIER_ZIP_EXPOSURE'
        WHEN NOT g.parcel_level_building_tiv_observed THEN 'BLOCKED_NO_BUILDING_TIV'
        ELSE 'BLOCKED_COVERAGE_AND_MODEL_VALIDATION'
    END AS next_evidence_gate
FROM company_group g
LEFT JOIN cross_state_naic c ON c.naic_5digit = g.naic_code;