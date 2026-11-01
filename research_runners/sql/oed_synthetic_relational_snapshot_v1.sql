-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- READ-ONLY. Run ONLY on Neon isolated branch br-summer-sky-bawujqu8,
-- database insurance. Result is one synthetic OED JSON object or zero rows.
-- This does not identify the Neon branch independently: operator MUST pass
-- an explicit branch ID and never target main.
WITH selected AS (
    SELECT p.portfolio_key,p.portfolio_type,p.organization_id,
           v.portfolio_version_id,v.version_label,v.generation_method,
           v.assumption_metadata AS assumptions
      FROM exposure.portfolio p
      JOIN exposure.portfolio_version v USING(portfolio_id)
     WHERE p.portfolio_key='oc-synthetic-exposure-smoke-v0'
       AND p.portfolio_type='synthetic' AND p.organization_id IS NULL
       AND v.version_label='v0' AND v.seed=20261101
       AND v.generation_method='deterministic_independent_synthetic_sql_v0'
       AND v.source_key IS NULL AND v.assumption_metadata ->> 'synthetic'='true'
       AND v.assumption_metadata ->> 'model_input_approved'='false'
), account_policy AS (
    SELECT s.*,a.account_id,a.account_key,a.account_currency,a.synthetic AS account_synthetic,
           a.source_key AS account_source_key,p.policy_id,p.policy_key,
           p.policy_perils_oed,p.synthetic AS policy_synthetic,
           p.source_key AS policy_source_key
      FROM selected s
      JOIN insurance.account_v1 a
        ON a.portfolio_version_id=s.portfolio_version_id
      JOIN insurance.policy_v1 p
        ON p.account_id=a.account_id AND p.portfolio_version_id=s.portfolio_version_id
     WHERE a.account_key='SYNTH-ACC-01' AND p.policy_key='SYNTH-POL-01'
       AND a.account_currency='EUR' AND a.synthetic AND p.synthetic
       AND a.source_key IS NULL AND p.source_key IS NULL
       AND p.policy_perils_oed='WW2;OO1'
       AND p.policy_terms ->> 'model_input_approved'='false'
), t_components AS (
    SELECT pl.policy_location_id,
           count(*) AS n_tiv,
           jsonb_object_agg(t.component,t.amount::text) AS values_json
      FROM insurance.policy_location_v1 pl
      JOIN insurance.policy_tiv_component_v1 t
        ON t.policy_location_id=pl.policy_location_id
       AND t.portfolio_version_id=pl.portfolio_version_id
     WHERE t.currency='EUR' AND t.synthetic AND t.source_key IS NULL
       AND t.value_basis='invented_synthetic_oed_demo'
       AND t.amount IS NOT NULL
     GROUP BY pl.policy_location_id
    HAVING count(*)=4
       AND count(DISTINCT t.component)=4
), rows AS (
    SELECT ap.portfolio_version_id,ap.policy_id,u.external_unit_id,
           jsonb_build_object(
               'external_unit_id',u.external_unit_id,
               'source_key',u.source_key,
               'assumption_status',u.assumption_status,
               'unit_type',u.unit_type,'country_code',u.country_code,
               'insured_value_currency',u.insured_value_currency,
               'value_basis',u.value_basis,'building_count',u.building_count::text,
               'insured_value',u.insured_value::text,
               'latitude',ST_Y(u.location)::text,
               'longitude',ST_X(u.location)::text,
               'location_perils_oed',pl.location_perils_oed,
               'tiv_components',tc.values_json
           ) AS unit_json
      FROM account_policy ap
      JOIN insurance.policy_location_v1 pl
        ON pl.policy_id=ap.policy_id AND pl.portfolio_version_id=ap.portfolio_version_id
      JOIN exposure.exposure_unit u
        ON u.unit_id=pl.unit_id AND u.portfolio_version_id=pl.portfolio_version_id
      JOIN t_components tc ON tc.policy_location_id=pl.policy_location_id
     WHERE pl.synthetic AND pl.location_perils_oed='WW2;OO1'
       AND u.location IS NOT NULL AND ST_SRID(u.location)=4326
)
SELECT jsonb_build_object(
    'portfolio_key',ap.portfolio_key,'portfolio_type',ap.portfolio_type,
    'organization_id',ap.organization_id,'version_label',ap.version_label,
    'generation_method',ap.generation_method,'assumptions',ap.assumptions,
    'account',jsonb_build_object('account_key',ap.account_key,
      'currency',ap.account_currency,'synthetic',ap.account_synthetic,
      'source_key',ap.account_source_key),
    'policy',jsonb_build_object('policy_key',ap.policy_key,
      'policy_perils_oed',ap.policy_perils_oed,'synthetic',ap.policy_synthetic,
      'source_key',ap.policy_source_key),
    'units',jsonb_agg(rows.unit_json ORDER BY rows.external_unit_id)
) AS synthetic_relational_snapshot
FROM account_policy ap
JOIN rows ON rows.portfolio_version_id=ap.portfolio_version_id
         AND rows.policy_id=ap.policy_id
WHERE (SELECT count(*) FROM insurance.account_v1 a
       WHERE a.portfolio_version_id=ap.portfolio_version_id)=1
  AND (SELECT count(*) FROM insurance.policy_v1 p
       WHERE p.portfolio_version_id=ap.portfolio_version_id)=1
  AND (SELECT count(*) FROM insurance.policy_location_v1 pl
       WHERE pl.portfolio_version_id=ap.portfolio_version_id)=12
  AND (SELECT count(*) FROM insurance.policy_tiv_component_v1 t
       WHERE t.portfolio_version_id=ap.portfolio_version_id)=48
GROUP BY ap.portfolio_key,ap.portfolio_type,ap.organization_id,ap.version_label,
         ap.generation_method,ap.assumptions,ap.portfolio_version_id,ap.policy_id,
         ap.account_key,ap.account_currency,ap.account_synthetic,ap.account_source_key,
         ap.policy_key,ap.policy_perils_oed,ap.policy_synthetic,ap.policy_source_key
HAVING count(*)=12
   AND count(DISTINCT rows.external_unit_id)=12;
