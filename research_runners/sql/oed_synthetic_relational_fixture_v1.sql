-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- VALIDATION-BRANCH ONLY. 12 invented locations and 100%-building TIV
-- allocations. No real policies, insured property, customers or treaties.
-- Run after oed_synthetic_relational_schema_v1.sql on branch
-- br-summer-sky-bawujqu8, database insurance. DO block is atomic.
DO $synthetic_oed_fixture_v1$
DECLARE
    v_id uuid;
    a_id uuid;
    p_id uuid;
    bad integer;
    tiv numeric;
BEGIN
    IF current_database() <> 'insurance'
       OR to_regclass('exposure.market_policy_stock_research_v0') IS NULL
       OR to_regclass('research.fl_nc_legal_naic_overlap_research_v1') IS NULL
       OR to_regclass('insurance.policy_tiv_component_v1') IS NULL
    THEN RAISE EXCEPTION 'BLOCKED: wrong database or validation branch'; END IF;

    SELECT v.portfolio_version_id INTO STRICT v_id
      FROM exposure.portfolio p JOIN exposure.portfolio_version v USING (portfolio_id)
     WHERE p.portfolio_key = 'oc-synthetic-exposure-smoke-v0'
       AND p.portfolio_type = 'synthetic' AND p.organization_id IS NULL
       AND v.version_label = 'v0'
       AND v.generation_method = 'deterministic_independent_synthetic_sql_v0'
       AND v.seed = 20261101 AND v.source_key IS NULL
       AND v.assumption_metadata ->> 'real_insurer' = 'false'
       AND v.assumption_metadata ->> 'real_buildings' = 'false'
       AND v.assumption_metadata ->> 'model_input_approved' = 'false';

    SELECT count(*) FILTER (WHERE assumption_status <> 'synthetic'
                            OR source_key IS NOT NULL
                            OR insured_value_currency <> 'EUR'
                            OR value_basis <> 'invented_smoke_test_value_not_insured_observation')
      INTO bad
      FROM exposure.exposure_unit WHERE portfolio_version_id = v_id;
    IF (SELECT count(*) FROM exposure.exposure_unit WHERE portfolio_version_id=v_id) <> 12
       OR bad <> 0
       OR (SELECT sum(insured_value) FROM exposure.exposure_unit WHERE portfolio_version_id=v_id) <> 3150000
    THEN RAISE EXCEPTION 'BLOCKED: initial source fixture drift'; END IF;

    INSERT INTO insurance.account_v1
        (portfolio_version_id, account_key, account_currency, synthetic, source_key, as_of_date)
    VALUES (v_id,'SYNTH-ACC-01','EUR',true,NULL,DATE '2026-11-01')
    ON CONFLICT (portfolio_version_id,account_key) DO NOTHING;

    SELECT account_id INTO STRICT a_id FROM insurance.account_v1
     WHERE portfolio_version_id=v_id AND account_key='SYNTH-ACC-01'
       AND account_currency='EUR' AND synthetic AND source_key IS NULL
       AND as_of_date=DATE '2026-11-01';

    INSERT INTO insurance.policy_v1
      (portfolio_version_id,account_id,policy_key,policy_perils_oed,
       effective_from,effective_to,policy_terms,synthetic,source_key)
    VALUES
      (v_id,a_id,'SYNTH-POL-01','WW2;OO1',DATE '2026-01-01',
       DATE '2026-12-31',
       '{"synthetic":true,"real_policy":false,"model_input_approved":false,"scope":"OED relational mapping only; financial terms not specified"}'::jsonb,
       true,NULL)
    ON CONFLICT (portfolio_version_id,policy_key) DO NOTHING;

    SELECT policy_id INTO STRICT p_id FROM insurance.policy_v1
     WHERE portfolio_version_id=v_id AND account_id=a_id
       AND policy_key='SYNTH-POL-01' AND policy_perils_oed='WW2;OO1'
       AND effective_from=DATE '2026-01-01' AND effective_to=DATE '2026-12-31'
       AND synthetic AND source_key IS NULL
       AND policy_terms ->> 'model_input_approved' = 'false';

    INSERT INTO insurance.policy_location_v1
      (portfolio_version_id,policy_id,unit_id,location_perils_oed,synthetic)
    SELECT v_id,p_id,u.unit_id,'WW2;OO1',true
      FROM exposure.exposure_unit u WHERE u.portfolio_version_id=v_id
    ON CONFLICT (policy_id,unit_id) DO NOTHING;

    INSERT INTO insurance.policy_tiv_component_v1
      (policy_location_id,portfolio_version_id,component,amount,currency,
       as_of_date,value_basis,synthetic,source_key)
    SELECT pl.policy_location_id,v_id,parts.component,
           CASE WHEN parts.component='building' THEN u.insured_value ELSE 0 END,
           'EUR',DATE '2026-11-01','invented_synthetic_oed_demo',true,NULL
      FROM insurance.policy_location_v1 pl
      JOIN exposure.exposure_unit u
        ON u.unit_id=pl.unit_id AND u.portfolio_version_id=pl.portfolio_version_id
      CROSS JOIN (VALUES ('building'),('contents'),('bi'),('other')) AS parts(component)
     WHERE pl.policy_id=p_id AND pl.portfolio_version_id=v_id
    ON CONFLICT (policy_location_id,component) DO NOTHING;

    SELECT count(*) FILTER (WHERE t.currency<>'EUR'
                               OR t.amount IS NULL OR t.amount<0
                               OR t.source_key IS NOT NULL
                               OR t.value_basis<>'invented_synthetic_oed_demo'
                               OR NOT t.synthetic
                               OR t.amount IS DISTINCT FROM
                                 CASE WHEN t.component='building' THEN u.insured_value ELSE 0 END)
      INTO bad
      FROM insurance.policy_tiv_component_v1 t
      JOIN insurance.policy_location_v1 pl USING (policy_location_id,portfolio_version_id)
      JOIN exposure.exposure_unit u ON u.unit_id=pl.unit_id
      WHERE pl.policy_id=p_id AND pl.portfolio_version_id=v_id;
    SELECT sum(t.amount) INTO tiv
      FROM insurance.policy_tiv_component_v1 t
      JOIN insurance.policy_location_v1 pl USING (policy_location_id,portfolio_version_id)
      WHERE pl.policy_id=p_id AND pl.portfolio_version_id=v_id;

    IF (SELECT count(*) FROM insurance.policy_location_v1 WHERE policy_id=p_id)<>12
       OR (SELECT count(*) FROM insurance.policy_tiv_component_v1 t
           JOIN insurance.policy_location_v1 pl USING (policy_location_id,portfolio_version_id)
           WHERE pl.policy_id=p_id)<>48
       OR bad<>0 OR tiv<>3150000
       OR (SELECT count(DISTINCT t.policy_location_id) FROM insurance.policy_tiv_component_v1 t
           JOIN insurance.policy_location_v1 pl USING (policy_location_id,portfolio_version_id)
           WHERE pl.policy_id=p_id)<>12
    THEN RAISE EXCEPTION 'BLOCKED: invalid relational OED synthetic fixture'; END IF;
END $synthetic_oed_fixture_v1$;
