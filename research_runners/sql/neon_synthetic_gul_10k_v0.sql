-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- OpenCatastrophe synthetic validation-only GUL pilot, v0.
-- READ-ONLY. Run ONLY against Neon insurance-risk-core / insurance / validation-schema-20261031.
-- Does NOT run OpenCatastrophe's native producer, NextGen, OpenQuake or Oasis.
-- Uses 12 wholly fictional positions and their equally fictional insured values
-- as proxy replacement values. NO real-world CAT inference permitted.
-- Deterministic independent single-event Bernoulli simulations, two synthetic
-- perils/world, hash-specified; one possible event per peril/year.
-- Physical hazard frequency, vulnerability, original policy terms,
-- CAT-XL/reinstatement and retro are NOT calibrated or computed.

WITH selected_versions AS (
  -- Pin the exact synthetic OED v0 source. Do not infer identity from only
  -- twelve matching unit IDs and an aggregate synthetic EUR amount.
  SELECT pv.portfolio_version_id
  FROM exposure.portfolio p
  JOIN exposure.portfolio_version pv USING (portfolio_id)
  WHERE p.portfolio_key='oc-synthetic-exposure-smoke-v0'
    AND p.portfolio_type='synthetic' AND p.organization_id IS NULL
    AND p.country_code='DE'
    AND p.peril_scope=ARRAY['windstorm','flood']::text[]
    AND p.business_line_scope=ARRAY['synthetic_property']::text[]
    AND pv.version_label='v0'
    AND pv.as_of_date=DATE '2026-11-01' AND pv.seed=20261101
    AND pv.generation_method='deterministic_independent_synthetic_sql_v0'
    AND pv.source_key IS NULL
    AND pv.assumption_metadata ->> 'synthetic'='true'
    AND pv.assumption_metadata ->> 'model_input_approved'='false'
    AND pv.assumption_metadata ->> 'real_insurer'='false'
    AND pv.assumption_metadata ->> 'real_buildings'='false'
    AND pv.assumption_metadata ->> 'external_source_rows_used'='0'
    AND pv.assumption_metadata ->> 'location_semantics'='arbitrary_coordinate_grid_not_real_properties'
),
raw_assets AS (
  SELECT e.*
  FROM exposure.exposure_unit e
  JOIN selected_versions sv ON sv.portfolio_version_id=e.portfolio_version_id
),
assets AS (
  SELECT e.external_unit_id, e.insured_value::numeric AS proxy_value_eur,
         e.location, e.country_code, e.region_code, e.building_count,
         e.occupancy_code, e.construction_code
  FROM raw_assets e
  WHERE e.unit_type='asset' AND e.assumption_status='synthetic'
    AND e.source_key IS NULL AND e.location IS NOT NULL
    AND ST_SRID(e.location)=4326
    AND e.insured_value_currency='EUR'
    AND e.value_basis='invented_smoke_test_value_not_insured_observation'
),
expected_assets AS (
  SELECT 'SYNTH-' || lpad(i::text,2,'0') AS external_unit_id,
         (100000 + 25000*i)::numeric AS expected_value_eur,
         ST_SetSRID(ST_MakePoint(9.9 + (i % 4)*0.1,
            50.0 + ((i - 1)/4)*0.1),4326) AS expected_location,
         CASE WHEN i % 3=0 THEN 'SYNTHETIC_COMMERCIAL'
              ELSE 'SYNTHETIC_RESIDENTIAL' END AS expected_occupancy,
         CASE WHEN i % 2=0 THEN 'SYNTHETIC_CONCRETE'
              ELSE 'SYNTHETIC_MASONRY' END AS expected_construction
  FROM generate_series(1,12) AS s(i)
),
gate_checks AS (
  SELECT (SELECT COUNT(*) FROM selected_versions) AS selected_version_count,
         (SELECT COUNT(*) FROM exposure.portfolio_version v
           JOIN exposure.portfolio p USING (portfolio_id)
          WHERE p.portfolio_key='oc-synthetic-exposure-smoke-v0') AS all_version_count,
         (SELECT COUNT(*) FROM raw_assets) AS all_unit_count,
         COUNT(*) AS n, SUM(a.proxy_value_eur) AS proxy_total,
         COUNT(DISTINCT a.external_unit_id) AS unique_ids,
         COUNT(*) FILTER (
           WHERE a.external_unit_id IS NULL
              OR e.external_unit_id IS NULL
              OR a.proxy_value_eur IS DISTINCT FROM e.expected_value_eur
              OR a.country_code IS DISTINCT FROM 'DE'
              OR a.region_code IS DISTINCT FROM 'SYNTHETIC-DE-REGION'
              OR a.building_count IS DISTINCT FROM 1
              OR a.occupancy_code IS DISTINCT FROM e.expected_occupancy
              OR a.construction_code IS DISTINCT FROM e.expected_construction
              OR ST_AsEWKB(a.location) IS DISTINCT FROM ST_AsEWKB(e.expected_location)
         ) AS mismatches
  FROM assets a FULL JOIN expected_assets e USING (external_unit_id)
),
gate AS (
  -- Unlike HAVING, this errors on missing/mutated fixtures instead of
  -- silently returning zero annual worlds and misleading NULL statistics.
  SELECT n, proxy_total, unique_ids,
         1 / (CASE WHEN selected_version_count=1 AND all_version_count=1
                      AND all_unit_count=12 AND n=12 AND unique_ids=12
                      AND proxy_total=3150000 AND mismatches=0
                   THEN 1 ELSE 0 END) AS asserted_fixture
  FROM gate_checks
),
years AS (SELECT generate_series(0,9999)::int AS yr
          FROM gate WHERE asserted_fixture=1),
-- The 8-bit thresholds of 26/256 wind and 13/256 flood are arbitrary.
perils(peril,threshold) AS (VALUES ('windstorm',26),('flood',13)),
candidate_events AS (
 SELECT y.yr, p.peril,
   md5('OC_NEON_10K_SYNTH_GUL_V0|'||y.yr::text||'|'||p.peril) AS event_hash,
   p.threshold
 FROM years y CROSS JOIN perils p
),
events AS (
 SELECT yr,peril,1+(get_byte(decode(event_hash,'hex'),1)%5) AS intensity
 FROM candidate_events
 WHERE get_byte(decode(event_hash,'hex'),0)<threshold
),
asset_losses AS (
 SELECT ev.yr,ev.peril,a.external_unit_id,
    (a.proxy_value_eur*ev.intensity*
      (1+get_byte(decode(md5('OC_NEON_10K_SYNTH_GUL_V0|local|'||ev.yr::text||'|'||ev.peril||'|'||a.external_unit_id),'hex'),2)%3)/100)::numeric AS loss_eur
 FROM events ev CROSS JOIN assets a
),
event_losses AS (SELECT yr,peril,SUM(loss_eur) AS event_loss_eur FROM asset_losses GROUP BY yr,peril),
annual AS (
 SELECT y.yr,COALESCE(SUM(l.event_loss_eur),0)::numeric AS gross_loss_eur,
        COALESCE(MAX(l.event_loss_eur),0)::numeric AS max_event_loss_eur,
        COUNT(l.peril)::int AS event_count
 FROM years y LEFT JOIN event_losses l USING(yr) GROUP BY y.yr
)
SELECT (SELECT n FROM gate) AS synthetic_assets,
       (SELECT proxy_total FROM gate) AS synthetic_value_eur,
       count(*) AS worlds,
       sum(event_count)::bigint AS physical_synthetic_events,
       count(*) FILTER(WHERE event_count=0) AS zero_event_years,
       sum(gross_loss_eur)::numeric AS total_annual_loss_eur,
       ROUND(avg(gross_loss_eur),2) AS aal_eur,
       percentile_disc(0.99) WITHIN GROUP(ORDER BY gross_loss_eur) AS aep99_loss_eur,
       percentile_disc(0.995) WITHIN GROUP(ORDER BY gross_loss_eur) AS aep995_loss_eur,
       percentile_disc(0.99) WITHIN GROUP(ORDER BY max_event_loss_eur) AS oep99_loss_eur,
       percentile_disc(0.995) WITHIN GROUP(ORDER BY max_event_loss_eur) AS oep995_loss_eur,
       MAX(gross_loss_eur) AS max_annual_eur,
       (SELECT count(*) FROM event_losses WHERE peril='windstorm') AS wind_events,
       (SELECT count(*) FROM event_losses WHERE peril='flood') AS flood_events,
       (SELECT sum(event_loss_eur) FROM event_losses WHERE peril='windstorm') AS wind_total,
       (SELECT sum(event_loss_eur) FROM event_losses WHERE peril='flood') AS flood_total
FROM annual;
