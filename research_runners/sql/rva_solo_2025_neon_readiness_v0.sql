-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- Research-only read-only R+V Allgemeine 2025 SOLO insurer-to-CAT admission preflight.
-- The official SFCR accounting value is a guard, NEVER insured TIV or loss.

WITH
target AS (
  SELECT 'R+V Allgemeine Versicherung AG'::text AS legal_name,
         2025::integer AS report_year,
         2223182000::numeric AS property_gwp_eur
),
solo AS (
  SELECT o.organization_id
  FROM entity.organization AS o CROSS JOIN target AS t
  WHERE (o.legal_name = t.legal_name OR o.display_name = t.legal_name)
    AND o.identity_status = 'verified'
    AND o.domicile_country = 'DE'
    AND o.organization_type = 'insurer'
),
solo_counts AS (
  SELECT count(*)::bigint AS verified_solo_entities,
         (SELECT count(*) FROM entity.organization_identifier AS i
          WHERE i.organization_id IN (SELECT organization_id FROM solo)
            AND i.is_verified) AS verified_solo_identifiers
  FROM solo
),
candidates AS (
  SELECT
    (SELECT count(*) FROM entity.organization_candidate
     WHERE display_name IN ('R+V Versicherung','R+V Versicherung AG'))::bigint
      AS non_solo_group_or_other_candidates,
    (SELECT count(*) FROM research.insurer_directory_candidate_v0
     WHERE display_name IN ('R+V Allgemeine Versicherung AG',
                            'R+V Allgemeine Versicherung Aktiengesellschaft'))::bigint
      AS solo_directory_candidates,
    (SELECT count(*) FROM research.insurer_directory_candidate_v0
     WHERE display_name LIKE 'R+V%' AND
           display_name NOT IN ('R+V Allgemeine Versicherung AG',
                                'R+V Allgemeine Versicherung Aktiengesellschaft'))::bigint
      AS other_rv_directory_candidates
),
finances AS (
  SELECT count(*)::bigint AS source_linked_exact_property_gwp_rows
  FROM entity.published_metric AS m
  JOIN solo AS s USING (organization_id)
  JOIN registry.source_record AS sr ON sr.source_key = m.source_key
  CROSS JOIN target AS t
  WHERE m.metric_name = 'fire_and_other_property_gwp'
    AND m.measurement_kind = 'published_observation'
    AND m.year = t.report_year
    AND m.value = t.property_gwp_eur
    AND m.unit = 'EUR'
    AND m.currency_code = 'EUR'
    AND m.business_scope = 'solo_direct'
    AND m.gross_net_basis = 'gross'
),
p AS (
  SELECT count(*)::bigint AS company_linked_portfolios
  FROM exposure.portfolio AS p
  WHERE p.organization_id IN (SELECT organization_id FROM solo)
),
pv AS (
  SELECT count(*)::bigint AS company_linked_portfolio_versions
  FROM exposure.portfolio_version AS v
  JOIN exposure.portfolio AS p ON p.portfolio_id = v.portfolio_id
  WHERE p.organization_id IN (SELECT organization_id FROM solo)
),
eu AS (
  SELECT count(*)::bigint AS company_linked_exposure_units
  FROM exposure.exposure_unit AS u
  JOIN exposure.portfolio_version AS v ON v.portfolio_version_id = u.portfolio_version_id
  JOIN exposure.portfolio AS p ON p.portfolio_id = v.portfolio_id
  WHERE p.organization_id IN (SELECT organization_id FROM solo)
),
combined AS (
  SELECT sc.*, c.*, f.*, p.*, pv.*, eu.*
  FROM solo_counts AS sc CROSS JOIN candidates AS c
  CROSS JOIN finances AS f CROSS JOIN p AS p CROSS JOIN pv CROSS JOIN eu
)
SELECT 'RVA_SOLO_2025_RESEARCH_READINESS_V0'::text AS report_id,
       (SELECT report_year FROM target) AS reference_year,
       (SELECT property_gwp_eur FROM target) AS official_solo_property_gwp_eur,
       combined.*,
       false::boolean AS insurer_tiv_observed_from_sfcr,
       false::boolean AS annual_cat_ep_calibrated_from_sfcr,
       CASE
         WHEN verified_solo_entities <> 1 THEN 'BLOCKED_UNVERIFIED_OR_AMBIGUOUS_SOLO_LEGAL_ENTITY'
         WHEN verified_solo_identifiers = 0 THEN 'BLOCKED_SOLO_IDENTIFIER_EVIDENCE'
         WHEN source_linked_exact_property_gwp_rows = 0 THEN 'BLOCKED_SOLO_SFCR_METRIC_NOT_SOURCE_LINKED'
         WHEN company_linked_portfolio_versions = 0 OR company_linked_exposure_units = 0
              THEN 'BLOCKED_COMPANY_EXPOSURE_NOT_REGISTERED'
         ELSE 'RESEARCH_ONLY_NEEDS_HAZARD_VULNERABILITY_RIGHTS_AND_TREATY_REVIEW'
       END::text AS next_gate
FROM combined;
