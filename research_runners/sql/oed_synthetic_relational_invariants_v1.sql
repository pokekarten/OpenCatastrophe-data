-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- Read-only counts and transactional negative probes. Validation branch only.
-- All deliberately failing INSERT statements are rolled back via PL/pgSQL
-- exception subtransactions; no new records survive.
DO $invariants$
DECLARE
    v_id uuid;
    p_id uuid;
    l_id uuid;
    a_id uuid;
    n integer;
    total numeric;
BEGIN
    IF current_database()<>'insurance'
       OR to_regclass('research.fl_nc_legal_naic_overlap_research_v1') IS NULL
       OR to_regclass('insurance.policy_tiv_component_v1') IS NULL
       OR to_regclass('exposure.market_policy_stock_research_v0') IS NULL
    THEN RAISE EXCEPTION 'BLOCKED: not isolated validation database'; END IF;

    SELECT v.portfolio_version_id INTO STRICT v_id
      FROM exposure.portfolio p JOIN exposure.portfolio_version v USING(portfolio_id)
     WHERE p.portfolio_key='oc-synthetic-exposure-smoke-v0'
       AND p.organization_id IS NULL AND p.portfolio_type='synthetic'
       AND v.version_label='v0' AND v.seed=20261101;

    SELECT account_id INTO STRICT a_id
      FROM insurance.account_v1
     WHERE portfolio_version_id=v_id AND account_key='SYNTH-ACC-01'
       AND synthetic AND source_key IS NULL;
    SELECT policy_id INTO STRICT p_id
      FROM insurance.policy_v1
     WHERE portfolio_version_id=v_id AND account_id=a_id
       AND policy_key='SYNTH-POL-01'
       AND policy_perils_oed='WW2;OO1' AND synthetic AND source_key IS NULL;

    SELECT count(*) INTO n FROM insurance.policy_location_v1
     WHERE portfolio_version_id=v_id AND policy_id=p_id;
    IF n<>12 THEN RAISE EXCEPTION 'Expected 12 policy-location joins, got %',n; END IF;
    SELECT count(*) INTO n FROM insurance.policy_tiv_component_v1
     WHERE portfolio_version_id=v_id;
    IF n<>48 THEN RAISE EXCEPTION 'Expected 48 TIV components, got %',n; END IF;
    SELECT sum(amount) INTO total FROM insurance.policy_tiv_component_v1
     WHERE portfolio_version_id=v_id;
    IF total<>3150000 THEN RAISE EXCEPTION 'TIV not conserved: %',total; END IF;
    IF EXISTS (
      SELECT pl.policy_location_id
        FROM insurance.policy_location_v1 pl
        JOIN insurance.policy_tiv_component_v1 t
          ON pl.policy_location_id=t.policy_location_id
         AND pl.portfolio_version_id=t.portfolio_version_id
        JOIN exposure.exposure_unit u
          ON u.unit_id=pl.unit_id AND u.portfolio_version_id=pl.portfolio_version_id
       WHERE pl.portfolio_version_id=v_id
       GROUP BY pl.policy_location_id,u.insured_value
      HAVING count(*)<>4 OR sum(t.amount)<>u.insured_value
    ) THEN RAISE EXCEPTION 'TIV components do not balance per location'; END IF;

    -- Cross-version link MUST be blocked by composite policy/location FKs.
    BEGIN
        INSERT INTO insurance.policy_location_v1
          (portfolio_version_id,policy_id,unit_id,location_perils_oed,synthetic)
        VALUES (gen_random_uuid(),p_id,gen_random_uuid(),'WW2;OO1',true);
        RAISE EXCEPTION 'FAIL: cross-version link was incorrectly permitted';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;

    -- Persisting a "real" account in this synthetic-only research schema MUST fail.
    BEGIN
        INSERT INTO insurance.account_v1
          (portfolio_version_id,account_key,account_currency,synthetic,source_key,as_of_date)
        VALUES (v_id,'SYNTH-NEGATIVE','EUR',false,NULL,DATE '2026-11-01');
        RAISE EXCEPTION 'FAIL: non-synthetic account was permitted';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    SELECT policy_location_id INTO STRICT l_id
      FROM insurance.policy_location_v1
     WHERE portfolio_version_id=v_id AND policy_id=p_id
     ORDER BY policy_location_id LIMIT 1;

    -- Negative value must fail before uniqueness checks.
    BEGIN
        INSERT INTO insurance.policy_tiv_component_v1
          (policy_location_id,portfolio_version_id,component,amount,currency,
           as_of_date,value_basis,synthetic,source_key)
        VALUES (l_id,v_id,'building',-1,'EUR',DATE '2026-11-01',
                'invented_synthetic_oed_demo',true,NULL);
        RAISE EXCEPTION 'FAIL: negative TIV was permitted';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END $invariants$;

SELECT
  (SELECT count(*) FROM insurance.account_v1) AS accounts,
  (SELECT count(*) FROM insurance.policy_v1) AS policies,
  (SELECT count(*) FROM insurance.policy_location_v1) AS policy_locations,
  (SELECT count(*) FROM insurance.policy_tiv_component_v1) AS tiv_components,
  (SELECT sum(amount) FROM insurance.policy_tiv_component_v1) AS tiv_total_eur;
