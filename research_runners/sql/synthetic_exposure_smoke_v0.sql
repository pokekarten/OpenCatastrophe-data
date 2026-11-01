-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- VALIDATION-BRANCH ONLY: create one independently synthetic research smoke fixture.
-- No input records from external insurers, real buildings, market totals or hazards.
-- Never apply on production/main; never call this insured or model-calibrated exposure.
-- All 12 locations and values are deterministic, arbitrary and invented from scratch.
-- No insurer/legal-entity linkage, no externally sourced rows, no CAT-model approval.
--
-- Intended database: dedicated insurance DB, Neon validation-schema-20261031 branch.
-- The validation-only gate below blocks the current Neon main branch.
DO $synthetic_exposure_smoke_v0$
DECLARE
    portfolio_uuid uuid;
    version_uuid uuid;
    contract_uuid uuid;
    n_units integer;
    n_distinct_locations integer;
    n_bad integer;
    tiv_sum numeric;
BEGIN
    IF current_database() <> 'insurance'
       OR to_regclass('exposure.market_policy_stock_research_v0') IS NULL
       OR to_regclass('research.fl_nc_legal_naic_overlap_research_v1') IS NULL
    THEN
        RAISE EXCEPTION 'Synthetic exposure smoke fixture must run on the isolated insurance validation branch, never main';
    END IF;

    INSERT INTO exposure.portfolio (
        portfolio_key, organization_id, portfolio_name, portfolio_type,
        country_code, peril_scope, business_line_scope
    ) VALUES (
        'oc-synthetic-exposure-smoke-v0', NULL,
        'SYNTHETIC DEMO ONLY - 12 hypothetical locations, no real insurer',
        'synthetic', 'DE', ARRAY['windstorm', 'flood']::text[],
        ARRAY['synthetic_property']::text[]
    ) ON CONFLICT (portfolio_key) DO NOTHING;

    SELECT p.portfolio_id INTO portfolio_uuid
    FROM exposure.portfolio p
    WHERE p.portfolio_key = 'oc-synthetic-exposure-smoke-v0'
      AND p.organization_id IS NULL AND p.portfolio_type = 'synthetic'
      AND p.country_code = 'DE';
    IF portfolio_uuid IS NULL THEN
        RAISE EXCEPTION 'Existing portfolio key has incompatible identity or type';
    END IF;

    INSERT INTO exposure.portfolio_version (
        portfolio_id, version_label, as_of_date, generation_method,
        seed, assumption_metadata, source_key
    ) VALUES (
        portfolio_uuid, 'v0', DATE '2026-11-01',
        'deterministic_independent_synthetic_sql_v0',
        20261101,
        jsonb_build_object(
            'synthetic', true,
            'real_insurer', false,
            'real_buildings', false,
            'external_source_rows_used', 0,
            'model_input_approved', false,
            'purpose', 'relational_PostGIS_plumbing_smoke_test_only',
            'location_semantics', 'arbitrary_coordinate_grid_not_real_properties',
            'valuation_semantics', 'invented_EUR_amounts_not_calibrated',
            'canonical_recipe', 'research_runners/sql/synthetic_exposure_smoke_v0.sql'
        ), NULL
    ) ON CONFLICT (portfolio_id, version_label) DO NOTHING;

    SELECT v.portfolio_version_id INTO version_uuid
    FROM exposure.portfolio_version v
    WHERE v.portfolio_id = portfolio_uuid
      AND v.version_label = 'v0'
      AND v.generation_method = 'deterministic_independent_synthetic_sql_v0'
      AND v.seed = 20261101
      AND v.source_key IS NULL
      AND v.assumption_metadata ->> 'synthetic' = 'true'
      AND v.assumption_metadata ->> 'model_input_approved' = 'false';
    IF version_uuid IS NULL THEN
        RAISE EXCEPTION 'Existing version conflicts with synthetic assumptions';
    END IF;

    INSERT INTO exposure.exposure_unit (
        portfolio_version_id, external_unit_id, region_code, country_code,
        unit_type, location, occupancy_code, construction_code,
        insured_value, insured_value_currency, building_count,
        value_basis, source_key, assumption_status
    )
    SELECT version_uuid,
           'SYNTH-' || lpad(g.n::text, 2, '0'),
           'SYNTHETIC-DE-REGION', 'DE', 'asset',
           ST_SetSRID(ST_MakePoint(
               9.9 + (g.n % 4) * 0.1,
               50.0 + ((g.n - 1) / 4) * 0.1
           ), 4326),
           CASE WHEN g.n % 3 = 0 THEN 'SYNTHETIC_COMMERCIAL'
                ELSE 'SYNTHETIC_RESIDENTIAL' END,
           CASE WHEN g.n % 2 = 0 THEN 'SYNTHETIC_CONCRETE'
                ELSE 'SYNTHETIC_MASONRY' END,
           (100000 + 25000 * g.n)::numeric,
           'EUR', 1, 'invented_smoke_test_value_not_insured_observation',
           NULL, 'synthetic'
    FROM generate_series(1, 12) AS g(n)
    ON CONFLICT (portfolio_version_id, external_unit_id) DO NOTHING;

    SELECT count(*)::integer, count(DISTINCT ST_AsText(u.location))::integer,
           sum(u.insured_value),
           count(*) FILTER (
               WHERE u.assumption_status <> 'synthetic'
                  OR u.source_key IS NOT NULL OR u.insured_value_currency <> 'EUR'
                  OR u.country_code <> 'DE' OR u.unit_type <> 'asset'
                  OR u.location IS NULL OR ST_SRID(u.location) <> 4326
                  OR u.building_count <> 1
           )::integer
    INTO n_units, n_distinct_locations, tiv_sum, n_bad
    FROM exposure.exposure_unit u
    WHERE u.portfolio_version_id = version_uuid;

    IF n_units <> 12 OR n_distinct_locations <> 12
       OR tiv_sum <> 3150000 OR n_bad <> 0 THEN
        RAISE EXCEPTION 'Synthetic smoke fixture failed conservation/guard checks: units %, places %, value %, invalid %',
            n_units, n_distinct_locations, tiv_sum, n_bad;
    END IF;

    -- Illustrative, synthetic CAT-XL treaty with no real cedent or reinsurer.
    -- The monetary amounts and reinstatement count are NOT actual contract terms.
    INSERT INTO insurance.contract (
        contract_key, cedent_id, counterparty_id, contract_type,
        is_synthetic, effective_from, effective_to, currency_code,
        attachment_amount, limit_amount, quota_share, reinstatement_count,
        covered_perils, contract_terms, source_key
    ) VALUES (
        'oc-synthetic-cat-xl-smoke-v0', NULL, NULL, 'cat_xl',
        true, DATE '2026-01-01', DATE '2026-12-31', 'EUR',
        200000, 500000, NULL, 1,
        ARRAY['windstorm', 'flood']::text[],
        jsonb_build_object(
            'synthetic', true,
            'actual_insurer_contract', false,
            'model_input_approved', false,
            'reinstatement_premium', 'unspecified_not_zero',
            'loss_ordering', 'not_specified',
            'purpose', 'relational_contract_link_smoke_test_only'
        ), NULL
    ) ON CONFLICT (contract_key) DO NOTHING;

    SELECT c.contract_id INTO contract_uuid
    FROM insurance.contract c
    WHERE c.contract_key = 'oc-synthetic-cat-xl-smoke-v0'
      AND c.is_synthetic = true AND c.contract_type = 'cat_xl'
      AND c.cedent_id IS NULL AND c.counterparty_id IS NULL
      AND c.currency_code = 'EUR'
      AND c.attachment_amount = 200000 AND c.limit_amount = 500000
      AND c.reinstatement_count = 1 AND c.source_key IS NULL
      AND c.contract_terms ->> 'model_input_approved' = 'false';
    IF contract_uuid IS NULL THEN
        RAISE EXCEPTION 'Existing contract conflicts with illustrative synthetic CAT-XL terms';
    END IF;

    INSERT INTO insurance.portfolio_contract (portfolio_version_id, contract_id, contract_order)
    VALUES (version_uuid, contract_uuid, 1)
    ON CONFLICT (portfolio_version_id, contract_id) DO NOTHING;

    IF (SELECT count(*) FROM insurance.portfolio_contract pc
        WHERE pc.portfolio_version_id = version_uuid) <> 1 THEN
        RAISE EXCEPTION 'Synthetic demo version must link to exactly one fictional treaty';
    END IF;
END;
$synthetic_exposure_smoke_v0$;
