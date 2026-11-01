-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- ADDITIVE DDL ONLY on Neon insurance-risk-core validation branch
-- br-summer-sky-bawujqu8, database insurance. NEVER execute on main.
-- Explicit validation-branch and exact synthetic source fixture guards.
DO $guard$
BEGIN
  IF current_database() <> 'insurance'
     OR to_regclass('exposure.market_policy_stock_research_v0') IS NULL
     OR to_regclass('research.fl_nc_legal_naic_overlap_research_v1') IS NULL
     OR NOT EXISTS (
         SELECT 1 FROM exposure.portfolio p
         JOIN exposure.portfolio_version v USING (portfolio_id)
         WHERE p.portfolio_key = 'oc-synthetic-exposure-smoke-v0'
           AND p.portfolio_type = 'synthetic' AND p.organization_id IS NULL
           AND v.version_label = 'v0' AND v.seed = 20261101
           AND v.assumption_metadata ->> 'model_input_approved' = 'false'
     )
  THEN RAISE EXCEPTION 'BLOCKED: incorrect Neon DB/branch or missing synthetic fixture'; END IF;
END $guard$;

-- Composite identity: prohibit cross-version links at the database level.
CREATE UNIQUE INDEX IF NOT EXISTS exposure_unit_id_version_oed_v1_uk
    ON exposure.exposure_unit (unit_id, portfolio_version_id);

CREATE TABLE IF NOT EXISTS insurance.account_v1 (
    account_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id uuid NOT NULL REFERENCES exposure.portfolio_version(portfolio_version_id),
    account_key text NOT NULL CHECK (account_key ~ '^[A-Z0-9][A-Z0-9_-]{2,63}$'),
    account_currency char(3) NOT NULL CHECK (account_currency ~ '^[A-Z]{3}$'),
    synthetic boolean NOT NULL CHECK (synthetic),
    source_key text NULL REFERENCES registry.source_record(source_key),
    as_of_date date NOT NULL,
    CONSTRAINT account_v1_only_invented CHECK (synthetic AND source_key IS NULL),
    CONSTRAINT account_v1_version_key_uk UNIQUE (portfolio_version_id, account_key),
    CONSTRAINT account_v1_id_version_uk UNIQUE (account_id, portfolio_version_id)
);

CREATE TABLE IF NOT EXISTS insurance.policy_v1 (
    policy_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id uuid NOT NULL,
    account_id uuid NOT NULL,
    policy_key text NOT NULL CHECK (policy_key ~ '^[A-Z0-9][A-Z0-9_-]{2,63}$'),
    policy_perils_oed text NOT NULL
       CHECK (policy_perils_oed ~ '^[A-Z0-9]{3}(;[A-Z0-9]{3})*$'),
    effective_from date NOT NULL,
    effective_to date NOT NULL,
    policy_terms jsonb NOT NULL DEFAULT '{}'::jsonb,
    synthetic boolean NOT NULL CHECK (synthetic),
    source_key text NULL REFERENCES registry.source_record(source_key),
    CONSTRAINT policy_v1_dates_ck CHECK (effective_to >= effective_from),
    CONSTRAINT policy_v1_only_invented CHECK (synthetic AND source_key IS NULL),
    CONSTRAINT policy_v1_account_fkey FOREIGN KEY (account_id, portfolio_version_id)
       REFERENCES insurance.account_v1(account_id, portfolio_version_id),
    CONSTRAINT policy_v1_version_key_uk UNIQUE (portfolio_version_id, policy_key),
    CONSTRAINT policy_v1_id_version_uk UNIQUE (policy_id, portfolio_version_id)
);

CREATE TABLE IF NOT EXISTS insurance.policy_location_v1 (
    policy_location_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id uuid NOT NULL,
    policy_id uuid NOT NULL,
    unit_id uuid NOT NULL,
    location_perils_oed text NOT NULL
       CHECK (location_perils_oed ~ '^[A-Z0-9]{3}(;[A-Z0-9]{3})*$'),
    synthetic boolean NOT NULL CHECK (synthetic),
    CONSTRAINT policy_location_v1_policy_fkey
       FOREIGN KEY (policy_id, portfolio_version_id)
       REFERENCES insurance.policy_v1(policy_id, portfolio_version_id),
    CONSTRAINT policy_location_v1_unit_fkey
       FOREIGN KEY (unit_id, portfolio_version_id)
       REFERENCES exposure.exposure_unit(unit_id, portfolio_version_id),
    CONSTRAINT policy_location_v1_policy_unit_uk UNIQUE (policy_id, unit_id),
    CONSTRAINT policy_location_v1_id_version_uk UNIQUE (policy_location_id, portfolio_version_id)
);

CREATE TABLE IF NOT EXISTS insurance.policy_tiv_component_v1 (
    component_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_location_id uuid NOT NULL,
    portfolio_version_id uuid NOT NULL,
    component text NOT NULL CHECK (component IN ('building','contents','bi','other')),
    amount numeric NULL CHECK (amount >= 0),
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    as_of_date date NOT NULL,
    value_basis text NOT NULL CHECK (value_basis = 'invented_synthetic_oed_demo'),
    synthetic boolean NOT NULL CHECK (synthetic),
    source_key text NULL REFERENCES registry.source_record(source_key),
    CONSTRAINT policy_tiv_v1_only_invented CHECK (synthetic AND source_key IS NULL),
    CONSTRAINT policy_tiv_v1_location_fkey
       FOREIGN KEY (policy_location_id, portfolio_version_id)
       REFERENCES insurance.policy_location_v1(policy_location_id, portfolio_version_id),
    CONSTRAINT policy_tiv_v1_component_uk UNIQUE (policy_location_id, component)
);
