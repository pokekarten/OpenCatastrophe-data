-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- READ ONLY. Run ONLY against explicitly selected Neon branch
-- validation-schema-20261031 (br-summer-sky-bawujqu8), database insurance.
-- No real insurer, observed building, private insured value, model input or
-- financial treaty is in scope. Export a single JSON object (not a CSV).
-- The Python exporter strictly rejects anything other than the fixed fixture.
WITH chosen AS (
    SELECT p.portfolio_key, p.portfolio_type, p.organization_id,
           v.portfolio_version_id, v.version_label, v.generation_method,
           v.assumption_metadata AS assumptions
    FROM exposure.portfolio p
    JOIN exposure.portfolio_version v USING (portfolio_id)
    WHERE p.portfolio_key = 'oc-synthetic-exposure-smoke-v0'
      AND p.portfolio_type = 'synthetic' AND p.organization_id IS NULL
      AND v.version_label = 'v0'
      AND v.seed = 20261101 AND v.source_key IS NULL
      AND v.generation_method = 'deterministic_independent_synthetic_sql_v0'
      AND v.assumption_metadata ->> 'synthetic' = 'true'
      AND v.assumption_metadata ->> 'model_input_approved' = 'false'
), units AS (
    SELECT e.portfolio_version_id, count(*) AS n_units,
           jsonb_agg(jsonb_build_object(
               'external_unit_id', e.external_unit_id,
               'source_key', e.source_key,
               'assumption_status', e.assumption_status,
               'unit_type', e.unit_type,
               'country_code', e.country_code,
               'insured_value_currency', e.insured_value_currency,
               'value_basis', e.value_basis,
               'building_count', e.building_count::text,
               'insured_value', e.insured_value::text,
               'latitude', ST_Y(e.location)::text,
               'longitude', ST_X(e.location)::text
           ) ORDER BY e.external_unit_id) AS records
    FROM exposure.exposure_unit e
    WHERE e.portfolio_version_id IN (SELECT portfolio_version_id FROM chosen)
      AND e.location IS NOT NULL AND ST_SRID(e.location) = 4326
    GROUP BY e.portfolio_version_id
)
SELECT jsonb_build_object(
    'portfolio_key', c.portfolio_key,
    'portfolio_type', c.portfolio_type,
    'organization_id', c.organization_id,
    'version_label', c.version_label,
    'generation_method', c.generation_method,
    'assumptions', c.assumptions,
    'units', u.records
) AS synthetic_snapshot
FROM chosen c
JOIN units u USING (portfolio_version_id)
WHERE u.n_units = 12
  AND NOT EXISTS (
      SELECT 1 FROM exposure.exposure_unit e
      WHERE e.portfolio_version_id = c.portfolio_version_id
        AND (e.location IS NULL OR ST_SRID(e.location) <> 4326)
  );
