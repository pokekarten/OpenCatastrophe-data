-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- OpenCatastrophe synthetic validation-only GUL pilot, v0.
-- Four exact ordered row-series MD5 receipts for independent Python parity;
-- not cryptographic authenticity and not insured-loss or physical calibration.
-- READ-ONLY. Run ONLY against Neon insurance-risk-core / insurance / validation-schema-20261031.
-- Does NOT run OpenCatastrophe's native producer, NextGen, OpenQuake or Oasis.
-- Uses 12 wholly fictional positions and their equally fictional insured values
-- as proxy replacement values. NO real-world CAT inference permitted.
-- Deterministic independent single-event Bernoulli simulations, two synthetic
-- perils/world, hash-specified; one possible event per peril/year.
-- Physical hazard frequency, vulnerability, original policy terms,
-- CAT-XL/reinstatement and retro are NOT calibrated or computed.

WITH assets AS (
  SELECT e.external_unit_id, e.insured_value::numeric AS proxy_value_eur
  FROM exposure.exposure_unit e
  JOIN exposure.portfolio_version pv ON pv.portfolio_version_id=e.portfolio_version_id
  JOIN exposure.portfolio p ON p.portfolio_id=pv.portfolio_id
  WHERE p.portfolio_key='oc-synthetic-exposure-smoke-v0'
    AND p.portfolio_type='synthetic' AND p.organization_id IS NULL
    AND e.unit_type='asset' AND e.assumption_status='synthetic'
    AND e.source_key IS NULL AND e.location IS NOT NULL
),
expected_assets AS (
  SELECT 'SYNTH-' || lpad(i::text,2,'0') AS external_unit_id,
         (100000 + 25000*i)::numeric AS expected_value_eur
  FROM generate_series(1,12) AS s(i)
),
gate_checks AS (
  SELECT COUNT(*) AS n, SUM(a.proxy_value_eur) AS proxy_total,
         COUNT(DISTINCT a.external_unit_id) AS unique_ids,
         COUNT(*) FILTER (
           WHERE a.external_unit_id IS NULL
              OR e.external_unit_id IS NULL
              OR a.proxy_value_eur IS DISTINCT FROM e.expected_value_eur
         ) AS mismatches
  FROM assets a FULL JOIN expected_assets e USING (external_unit_id)
),
gate AS (
  -- Unlike HAVING, this errors on missing/mutated fixtures instead of
  -- silently returning zero annual worlds and misleading NULL statistics.
  SELECT n, proxy_total, unique_ids,
         1 / (CASE WHEN n=12 AND unique_ids=12
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
SELECT
 (SELECT md5(string_agg(yr::text||':'||gross_loss_eur::bigint::text||':'||
  max_event_loss_eur::bigint::text||':'||event_count::text,'|' ORDER BY yr)) FROM annual)
   AS annual_exact_md5,
 (SELECT md5(string_agg(yr::text||':'||peril||':'||event_loss_eur::bigint::text,
  '|' ORDER BY yr,peril)) FROM event_losses) AS event_exact_md5,
 (SELECT md5(string_agg(yr::text||':'||peril||':'||external_unit_id||':'||
  loss_eur::bigint::text,'|' ORDER BY yr,peril,external_unit_id))
  FROM asset_losses) AS event_asset_exact_md5,
 (SELECT md5(string_agg(yr::text||':'||peril||':'||intensity::text,
  '|' ORDER BY yr,peril)) FROM events) AS event_intensity_exact_md5,
 (SELECT count(*) FROM annual) AS years,
 (SELECT count(*) FROM event_losses) AS events,
 (SELECT count(*) FROM asset_losses) AS asset_event_rows
FROM gate WHERE asserted_fixture=1;
