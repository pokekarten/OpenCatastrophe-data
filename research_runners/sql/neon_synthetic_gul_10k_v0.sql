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
gate AS (
  SELECT COUNT(*) AS n, SUM(proxy_value_eur) AS proxy_total,
         COUNT(DISTINCT external_unit_id) AS unique_ids
  FROM assets
  HAVING COUNT(*)=12 AND COUNT(DISTINCT external_unit_id)=12
     AND SUM(proxy_value_eur)=3150000
),
years AS (SELECT generate_series(0,9999)::int AS yr FROM gate),
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
