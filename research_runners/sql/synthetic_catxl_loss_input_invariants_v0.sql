-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY. Intended only for isolated Neon validation-schema-20261031 branch.
-- Exactly fictional 12-position portfolio and invented four-event loss schedule.
-- Does not admit exposures, compute insured CAT model losses, or write results.
WITH p AS (
    SELECT * FROM exposure.portfolio
    WHERE portfolio_key = 'oc-synthetic-exposure-smoke-v0'
), v AS (
    SELECT pv.* FROM exposure.portfolio_version pv
    JOIN p ON p.portfolio_id = pv.portfolio_id
    WHERE pv.version_label = 'v0'
), u AS (
    SELECT eu.* FROM exposure.exposure_unit eu
    JOIN v ON v.portfolio_version_id = eu.portfolio_version_id
), c AS (
    SELECT ct.* FROM insurance.contract ct
    JOIN insurance.portfolio_contract pc ON pc.contract_id = ct.contract_id
    JOIN v ON v.portfolio_version_id = pc.portfolio_version_id
    WHERE ct.contract_key = 'oc-synthetic-cat-xl-smoke-v0'
), expected_position AS (
    SELECT 'SYNTH-' || lpad(n::text, 2, '0') AS external_unit_id,
           (100000 + n * 25000)::numeric AS expected_value
    FROM generate_series(1,12) AS n
), invented_losses (event_id, event_date, peril, external_unit_id, loss_eur) AS (
    VALUES
    ('FICTIONAL-WIND-001',DATE '2026-11-02','windstorm','SYNTH-01',100000::numeric),
    ('FICTIONAL-FLOOD-002',DATE '2026-11-08','flood','SYNTH-05',200000::numeric),
    ('FICTIONAL-FLOOD-002',DATE '2026-11-08','flood','SYNTH-06',200000::numeric),
    ('FICTIONAL-WIND-003',DATE '2026-11-15','windstorm','SYNTH-03',150000::numeric),
    ('FICTIONAL-WIND-003',DATE '2026-11-15','windstorm','SYNTH-04',150000::numeric),
    ('FICTIONAL-WIND-003',DATE '2026-11-15','windstorm','SYNTH-05',150000::numeric),
    ('FICTIONAL-WIND-003',DATE '2026-11-15','windstorm','SYNTH-06',150000::numeric),
    ('FICTIONAL-WIND-003',DATE '2026-11-15','windstorm','SYNTH-07',150000::numeric),
    ('FICTIONAL-WIND-003',DATE '2026-11-15','windstorm','SYNTH-08',150000::numeric),
    ('FICTIONAL-WIND-004',DATE '2026-11-22','windstorm','SYNTH-09',150000::numeric),
    ('FICTIONAL-WIND-004',DATE '2026-11-22','windstorm','SYNTH-10',150000::numeric),
    ('FICTIONAL-WIND-004',DATE '2026-11-22','windstorm','SYNTH-11',150000::numeric),
    ('FICTIONAL-WIND-004',DATE '2026-11-22','windstorm','SYNTH-12',150000::numeric)
), row_integrity AS (
    SELECT count(*) AS n,
           count(*) FILTER (WHERE u.unit_id IS NOT NULL) AS joined,
           count(*) FILTER (WHERE il.loss_eur > u.insured_value OR il.loss_eur < 0) AS invalid_values,
           count(*) FILTER (WHERE il.event_date <= v.as_of_date) AS invalid_vintage,
           count(*) FILTER (WHERE il.peril <> ALL(ARRAY['windstorm','flood']::text[])) AS invalid_peril
    FROM invented_losses il
    LEFT JOIN u ON u.external_unit_id = il.external_unit_id
    CROSS JOIN v
), event_sums AS (
    SELECT event_id, sum(loss_eur) AS gross_eur FROM invented_losses GROUP BY event_id
), expected_event_sums (event_id, expected_eur) AS (
    VALUES ('FICTIONAL-WIND-001',100000::numeric),
           ('FICTIONAL-FLOOD-002',400000::numeric),
           ('FICTIONAL-WIND-003',900000::numeric),
           ('FICTIONAL-WIND-004',600000::numeric)
), checks AS (
    SELECT 'synthetic_portfolio_unlinked'::text AS check_name,
           (SELECT count(*)=1 FROM p WHERE portfolio_type='synthetic' AND organization_id IS NULL AND country_code='DE') AS passed
    UNION ALL SELECT 'exact_portfolio_vintage',
           (SELECT count(*)=1 FROM v WHERE as_of_date=DATE '2026-11-01' AND assumption_metadata ->> 'model_input_approved'='false')
    UNION ALL SELECT 'exact_twelve_synthetic_units',
           (SELECT count(*)=12 FROM u WHERE assumption_status='synthetic' AND source_key IS NULL AND insured_value_currency='EUR')
    UNION ALL SELECT 'positions_match_closed_form',
           (SELECT count(*)=12 AND count(*) FILTER (WHERE u.insured_value=ep.expected_value)=12 FROM expected_position ep LEFT JOIN u USING(external_unit_id))
    UNION ALL SELECT 'one_unlinked_fictional_catxl',
           (SELECT count(*)=1 FROM c WHERE is_synthetic AND cedent_id IS NULL AND counterparty_id IS NULL
                   AND attachment_amount=200000 AND limit_amount=500000 AND reinstatement_count=1
                   AND contract_terms ->> 'model_input_approved'='false'
                   AND contract_terms ->> 'loss_ordering'='not_specified')
    UNION ALL SELECT 'thirteen_invented_loss_cells_joinable',
           (SELECT n=13 AND joined=13 FROM row_integrity)
    UNION ALL SELECT 'no_loss_above_exposure',
           (SELECT invalid_values=0 FROM row_integrity)
    UNION ALL SELECT 'fictional_events_after_portfolio_snapshot',
           (SELECT invalid_vintage=0 FROM row_integrity)
    UNION ALL SELECT 'loss_perils_in_sample_scope',
           (SELECT invalid_peril=0 FROM row_integrity)
    UNION ALL SELECT 'all_four_event_gross_sums',
           (SELECT count(*)=4 AND count(*) FILTER (WHERE s.gross_eur=e.expected_eur)=4
            FROM expected_event_sums e LEFT JOIN event_sums s USING (event_id))
    UNION ALL SELECT 'no_database_cat_simulations',
           (SELECT count(*)=0 FROM model.simulation_run)
)
SELECT check_name, passed FROM checks ORDER BY check_name;
