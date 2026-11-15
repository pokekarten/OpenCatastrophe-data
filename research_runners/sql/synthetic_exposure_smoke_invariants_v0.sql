-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only invariants for the independently synthetic validation-only fixture.
-- All rows must have passed=true; this is NOT a catastrophe-loss model test.
WITH p AS (
    SELECT * FROM exposure.portfolio
    WHERE portfolio_key = 'oc-synthetic-exposure-smoke-v0'
), v AS (
    SELECT v.* FROM exposure.portfolio_version v
    JOIN p ON v.portfolio_id = p.portfolio_id
    WHERE v.version_label = 'v0'
), u AS (
    SELECT e.* FROM exposure.exposure_unit e
    JOIN v ON e.portfolio_version_id = v.portfolio_version_id
), c AS (
    SELECT k.* FROM insurance.contract k
    JOIN insurance.portfolio_contract pc ON pc.contract_id = k.contract_id
    JOIN v ON v.portfolio_version_id = pc.portfolio_version_id
), checks AS (
    SELECT 'single_portfolio' AS check_name, (SELECT count(*) = 1 FROM p) AS passed
    UNION ALL SELECT 'fictional_insurer_unlinked', (SELECT count(*) = 1 FROM p WHERE organization_id IS NULL)
    UNION ALL SELECT 'portfolio_explicitly_synthetic', (SELECT count(*) = 1 FROM p WHERE portfolio_type = 'synthetic' AND country_code = 'DE')
    UNION ALL SELECT 'single_version', (SELECT count(*) = 1 FROM v)
    UNION ALL SELECT 'version_not_model_approved', (SELECT count(*) = 1 FROM v WHERE assumption_metadata ->> 'model_input_approved' = 'false')
    UNION ALL SELECT 'version_has_no_external_source', (SELECT count(*) = 1 FROM v WHERE source_key IS NULL AND assumption_metadata ->> 'external_source_rows_used' = '0')
    UNION ALL SELECT 'twelve_units', (SELECT count(*) = 12 FROM u)
    UNION ALL SELECT 'unique_site_ids', (SELECT count(DISTINCT external_unit_id) = 12 FROM u)
    UNION ALL SELECT 'twelve_distinct_synthetic_points', (SELECT count(DISTINCT ST_AsText(location)) = 12 FROM u)
    UNION ALL SELECT 'all_assumptions_synthetic', (SELECT count(*) = 12 FROM u WHERE assumption_status = 'synthetic')
    UNION ALL SELECT 'no_external_unit_source', (SELECT count(*) = 12 FROM u WHERE source_key IS NULL)
    UNION ALL SELECT 'no_real_construction_taxonomy', (SELECT count(*) = 12 FROM u WHERE construction_code LIKE 'SYNTHETIC_%' AND occupancy_code LIKE 'SYNTHETIC_%')
    UNION ALL SELECT 'valid_4326_points', (SELECT count(*) = 12 FROM u WHERE location IS NOT NULL AND ST_SRID(location) = 4326 AND ST_GeometryType(location) = 'ST_Point')
    UNION ALL SELECT 'one_building_per_synthetic_point', (SELECT coalesce(sum(building_count),0) = 12 FROM u)
    UNION ALL SELECT 'all_eur', (SELECT count(*) = 12 FROM u WHERE insured_value_currency = 'EUR')
    UNION ALL SELECT 'arbitrary_value_conservation', (SELECT coalesce(sum(insured_value),0) = 3150000 FROM u)
    UNION ALL SELECT 'all_values_nonnegative', (SELECT count(*) = 12 FROM u WHERE insured_value >= 0)
    UNION ALL SELECT 'one_fictional_catxl_link', (SELECT count(*) = 1 FROM c WHERE is_synthetic AND contract_type = 'cat_xl' AND cedent_id IS NULL AND counterparty_id IS NULL)
    UNION ALL SELECT 'illustrative_layer_only', (SELECT count(*) = 1 FROM c WHERE currency_code = 'EUR' AND attachment_amount = 200000 AND limit_amount = 500000 AND reinstatement_count = 1)
    UNION ALL SELECT 'treaty_not_model_approved', (SELECT count(*) = 1 FROM c WHERE source_key IS NULL AND contract_terms ->> 'model_input_approved' = 'false' AND contract_terms ->> 'reinstatement_premium' = 'unspecified_not_zero')
    UNION ALL SELECT 'no_model_runs_for_fixture', (SELECT count(*) = 0 FROM model.simulation_run WHERE portfolio_version_id IN (SELECT portfolio_version_id FROM v))
)
SELECT check_name, passed FROM checks ORDER BY check_name;
