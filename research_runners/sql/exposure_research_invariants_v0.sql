-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only invariants for the isolated validation-schema-20261031 branch.
-- Passes mean source fidelity, not insurer-CAT loss/model-input approval.
WITH checks AS (
    SELECT
        'fl_exact_company_key_cardinality'::text AS check_id,
        (SELECT count(*) FROM research.fl_oir_company_exposure_readiness_v0) =
        (SELECT count(DISTINCT (source_key, report_as_of, naic_code))
           FROM exposure.fl_oir_mir_company_statewide_original_v1) AS passed
    UNION ALL
    SELECT 'fl_policy_count_preserved',
        (SELECT sum(policies_in_force_sum_by_reported_type)
           FROM research.fl_oir_company_exposure_readiness_v0) =
        (SELECT sum(reported_policies_in_force)
           FROM exposure.fl_oir_mir_company_statewide_original_v1)
    UNION ALL
    SELECT 'fl_reported_exposure_preserved',
        (SELECT sum(reported_exposure_usd_sum_by_type)
           FROM research.fl_oir_company_exposure_readiness_v0) =
        (SELECT sum(reported_exposure_usd)
           FROM exposure.fl_oir_mir_company_statewide_original_v1)
    UNION ALL
    SELECT 'fl_premium_preserved',
        (SELECT sum(direct_premium_usd_sum_by_type)
           FROM research.fl_oir_company_exposure_readiness_v0) =
        (SELECT sum(reported_direct_premium_usd)
           FROM exposure.fl_oir_mir_company_statewide_original_v1)
    UNION ALL
    SELECT 'fl_all_component_reconciliation',
        NOT EXISTS (
            SELECT 1 FROM research.fl_oir_company_exposure_readiness_v0
            WHERE malformed_rows > 0 OR component_reconciliation_failures > 0
        )
    UNION ALL
    SELECT 'fl_no_model_promotion',
        NOT EXISTS (
            SELECT 1 FROM research.fl_oir_company_exposure_readiness_v0
            WHERE model_input_approved
        )
    UNION ALL
    SELECT 'fl_never_confuse_reporting_universe',
        NOT EXISTS (
            SELECT 1 FROM research.fl_oir_company_exposure_readiness_v0
            WHERE NOT all_regulatory_filers_included AND model_input_approved
        )
    UNION ALL
    SELECT 'tx_zip_policy_key_cardinality',
        (SELECT sum(distinct_zip_policy_type_pairs)
           FROM research.tx_market_policy_stock_quality_v0) =
        (SELECT count(*)
           FROM exposure.market_policy_stock_research_v0)
    UNION ALL
    SELECT 'tx_nonnegative_research_sum',
        (SELECT sum(reported_nonnegative_policy_count_sum)
           FROM research.tx_market_policy_stock_quality_v0) =
        (SELECT sum(reported_policy_count_signed)
           FROM exposure.market_policy_stock_research_v0
           WHERE quality_status = 'RESEARCH_MARKET_ONLY'
             AND reported_policy_count_signed >= 0)
    UNION ALL
    SELECT 'tx_negative_rows_only_quarantined',
        NOT EXISTS (
            SELECT 1 FROM exposure.market_policy_stock_research_v0
            WHERE reported_policy_count_signed < 0 AND quality_status <> 'QUARANTINED_NEGATIVE'
        )
    UNION ALL
    SELECT 'tx_no_carrier_or_tiv_inference',
        NOT EXISTS (
            SELECT 1 FROM research.tx_market_policy_stock_quality_v0
            WHERE rows_with_legal_carrier > 0 OR rows_with_actual_insured_tiv > 0
               OR model_input_approved
        )
)
SELECT check_id, coalesce(passed, false) AS passed
FROM checks
ORDER BY check_id;
