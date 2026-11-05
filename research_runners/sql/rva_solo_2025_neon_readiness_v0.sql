-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- Read-only research gate: exactly one legally identified R+V Allgemeine SOLO carrier.
-- Never infer insurer-site locations, sums insured, CAT EP or treaty terms from premiums.
WITH
target AS (
  SELECT 'R+V Allgemeine Versicherung Aktiengesellschaft'::text AS legal_name,
         'R+V Allgemeine Versicherung AG'::text AS issuer_alias,
         '5299009UN4CBXZ336M65'::text AS solo_lei,
         '529900Z5KBA9KJP6EK09'::text AS parent_lei,
         2025::integer AS report_year,
         2223182000::numeric AS sfcr_property_gwp_eur,
         1060546::numeric AS hgb_building_year_end_contracts,
         997710000::numeric AS hgb_building_direct_gwp_eur
),
solo AS (
  SELECT o.organization_id, o.source_key
  FROM entity.organization AS o CROSS JOIN target AS t
  WHERE o.legal_name IN (t.legal_name, t.issuer_alias)
    AND o.identity_status = 'verified'
    AND o.domicile_country = 'DE'
    AND o.organization_type = 'insurer'
    AND (o.valid_from IS NULL OR o.valid_from <= DATE '2025-12-31')
    AND (o.valid_to IS NULL OR o.valid_to >= DATE '2025-12-31')
),
solo_identity AS (
  SELECT count(*)::bigint AS verified_solo_entities,
    (SELECT count(*) FROM solo s JOIN registry.source_record sr ON sr.source_key=s.source_key
     WHERE sr.canonical_url LIKE 'https://www.ruv.de/%')::bigint AS issuer_source_linked_solo_entities,
    (SELECT count(*) FROM entity.organization_identifier i JOIN solo s USING (organization_id)
     WHERE i.is_verified)::bigint AS verified_solo_identifier_rows,
    (SELECT count(*) FROM entity.organization_identifier i JOIN solo s USING (organization_id)
     JOIN registry.source_record sr ON sr.source_key=i.source_key CROSS JOIN target t
     WHERE i.identifier_scheme='GLEIF_LEI' AND i.identifier_value=t.solo_lei
       AND i.is_verified
       AND sr.canonical_url IN ('https://lei.bloomberg.com/leis/view/5299009UN4CBXZ336M65',
                                'https://api.gleif.org/api/v1/lei-records/5299009UN4CBXZ336M65',
                                'https://acpr.banque-france.fr/fr/fiche-detaillee/rv-allgemeine-versicherung-aktiengesellschaft-0')
       AND sr.review_status <> 'non_admission_discovery_only')::bigint AS exact_source_bound_solo_lei_rows,
    (SELECT count(*) FROM entity.organization_identifier i JOIN solo s USING (organization_id)
     CROSS JOIN target t WHERE i.identifier_scheme='GLEIF_LEI'
       AND i.identifier_value=t.parent_lei)::bigint AS parent_lei_wrongly_on_solo_rows
  FROM solo
),
candidates AS (
 SELECT
   (SELECT count(*) FROM entity.organization_candidate
    WHERE display_name IN ('R+V Versicherung', 'R+V Versicherung AG'))::bigint AS group_or_other_candidates,
   (SELECT count(*) FROM research.insurer_directory_candidate_v0
    WHERE display_name IN ('R+V Allgemeine Versicherung AG',
                           'R+V Allgemeine Versicherung Aktiengesellschaft'))::bigint AS solo_directory_candidates,
   (SELECT count(*) FROM research.insurer_directory_candidate_v0
    WHERE display_name LIKE 'R+V%' AND display_name NOT IN
      ('R+V Allgemeine Versicherung AG','R+V Allgemeine Versicherung Aktiengesellschaft')
   )::bigint AS other_rv_directory_candidates
),
finances AS (
  SELECT
   (SELECT count(*) FROM entity.published_metric m JOIN solo s USING (organization_id)
    JOIN registry.source_record sr ON sr.source_key=m.source_key CROSS JOIN target t
    WHERE sr.review_status='verified_original_financial_observation'
      AND sr.raw_metadata @> '{"publisher_original_sha256_verified":true,"accounting_line_and_basis_verified":true}'::jsonb
      AND m.metric_name='fire_and_other_property_gwp'
      AND m.measurement_kind='published_observation'
      AND m.year=t.report_year AND m.value=t.sfcr_property_gwp_eur
      AND m.unit='EUR' AND m.currency_code='EUR'
      AND m.business_scope='solo_direct' AND m.gross_net_basis='gross'
      AND sr.canonical_url LIKE 'https://www.ruv.de/dam/%/2025-SFCR-Allgemeine.pdf'
   )::bigint AS source_bound_exact_sfcr_property_gwp_rows,
   (SELECT count(*) FROM entity.published_metric m JOIN solo s USING (organization_id)
    JOIN registry.source_record sr ON sr.source_key=m.source_key CROSS JOIN target t
    WHERE sr.review_status='verified_original_financial_observation'
      AND sr.raw_metadata @> '{"publisher_original_sha256_verified":true,"accounting_line_and_basis_verified":true}'::jsonb
      AND m.metric_name='connected_buildings_year_end_contracts'
      AND m.measurement_kind='published_observation'
      AND m.year=t.report_year AND m.value=t.hgb_building_year_end_contracts
      AND m.unit='contracts' AND m.business_scope='solo_direct'
      AND m.as_of_date = DATE '2025-12-31'
      AND sr.canonical_url LIKE 'https://www.ruv.de/dam/%'
      AND (sr.canonical_url LIKE 'https://www.ruv.de/dam/%/01_GB%202025_R%Allgemeine%Versicherung%AG_final.2026-04-21-14-59-23.pdf')
   )::bigint AS source_bound_exact_hgb_building_contract_rows,
   (SELECT count(*) FROM entity.published_metric m JOIN solo s USING (organization_id)
    JOIN registry.source_record sr ON sr.source_key=m.source_key CROSS JOIN target t
    WHERE sr.review_status='verified_original_financial_observation'
      AND sr.raw_metadata @> '{"publisher_original_sha256_verified":true,"accounting_line_and_basis_verified":true}'::jsonb
      AND m.metric_name='connected_buildings_direct_gwp'
      AND m.measurement_kind='published_observation'
      AND m.year=t.report_year AND m.value=t.hgb_building_direct_gwp_eur
      AND m.unit='EUR' AND m.currency_code='EUR'
      AND m.business_scope='solo_direct' AND m.gross_net_basis='gross'
      AND sr.canonical_url LIKE 'https://www.ruv.de/dam/%'
      AND (sr.canonical_url LIKE 'https://www.ruv.de/dam/%/01_GB%202025_R%Allgemeine%Versicherung%AG_final.2026-04-21-14-59-23.pdf')
   )::bigint AS source_bound_exact_hgb_building_gwp_rows
),
books AS (
 SELECT count(*)::bigint AS company_linked_portfolios,
        count(*) FILTER (WHERE p.portfolio_type='synthetic')::bigint AS company_linked_synthetic_portfolios,
        count(*) FILTER (WHERE p.portfolio_type='reported_aggregate')::bigint AS company_linked_reported_aggregate_portfolios,
        count(*) FILTER (WHERE p.portfolio_type='real_restricted')::bigint AS company_linked_real_restricted_portfolios
 FROM exposure.portfolio p WHERE p.organization_id IN (SELECT organization_id FROM solo)
),
versions AS (
 SELECT count(*)::bigint AS company_linked_portfolio_versions
 FROM exposure.portfolio_version v JOIN exposure.portfolio p USING (portfolio_id)
 WHERE p.organization_id IN (SELECT organization_id FROM solo)
),
units AS (
 SELECT count(*)::bigint AS company_linked_exposure_units,
        count(*) FILTER (WHERE p.portfolio_type='synthetic' AND u.location IS NOT NULL)::bigint AS synthetic_exposure_units_with_geometry,
        count(*) FILTER (WHERE p.portfolio_type='synthetic' AND u.unit_type='asset' AND u.assumption_status='synthetic' AND u.country_code='DE' AND u.region_code ~ '^05[0-9]{3}$' AND u.location IS NOT NULL AND ST_SRID(u.location)=4326 AND ST_IsValid(u.location) AND CASE WHEN ST_GeometryType(u.location)='ST_Point' THEN ST_X(u.location) BETWEEN 5.5 AND 10.0 AND ST_Y(u.location) BETWEEN 50.0 AND 52.8 ELSE false END AND u.insured_value>0 AND u.value_basis LIKE 'FICTIONAL%')::bigint AS synthetic_nrw_wgs84_source_candidate_units,
        count(*) FILTER (WHERE p.portfolio_type='synthetic' AND u.unit_type='asset' AND u.assumption_status='synthetic' AND u.country_code='DE' AND u.region_code ~ '^05[0-9]{3}$' AND u.location IS NOT NULL AND ST_SRID(u.location)=4326 AND ST_IsValid(u.location) AND CASE WHEN ST_GeometryType(u.location)='ST_Point' THEN ST_X(u.location) BETWEEN 5.5 AND 10.0 AND ST_Y(u.location) BETWEEN 50.0 AND 52.8 ELSE false END AND u.insured_value>0 AND u.value_basis LIKE 'FICTIONAL%' AND sr.canonical_url='https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip' AND sr.rights_status='reviewed_derivative_usage_permitted'
          AND u.source_key=v.source_key
          AND sr.raw_metadata ->> 'original_hu_archive_full_sha256'='10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da'
          AND sr.raw_metadata ->> 'oed_manifest_sha256'=v.scenario_hash
          AND sr.raw_metadata @> '{"original_hu_archive_full_sha256_verified":true,"source_member_CRCs_verified":true,"source_2022_GFK_codebook_verified":true,"source_transformation_EPSG4647_to_4326_verified":true,"publisher_dataset_license_reviewed":true,"fictional_policy_linkage":true}'::jsonb AND v.scenario_hash ~ '^[0-9a-f]{64}$')::bigint AS source_admitted_synthetic_nrw_wgs84_units
 FROM exposure.exposure_unit u
 JOIN exposure.portfolio_version v USING (portfolio_version_id)
 JOIN exposure.portfolio p USING (portfolio_id)
 LEFT JOIN registry.source_record sr ON sr.source_key=u.source_key
 WHERE p.organization_id IN (SELECT organization_id FROM solo)
),
audit AS (
 SELECT si.*,c.*,f.*,b.*,v.*,u.*
 FROM solo_identity si CROSS JOIN candidates c CROSS JOIN finances f
 CROSS JOIN books b CROSS JOIN versions v CROSS JOIN units u
)
SELECT 'RVA_SOLO_2025_RESEARCH_READINESS_V1'::text AS report_id,
       (SELECT report_year FROM target) AS reference_year,
       (SELECT solo_lei FROM target) AS exact_solo_lei_reference,
       (SELECT parent_lei FROM target) AS excluded_parent_lei_reference,
       (SELECT sfcr_property_gwp_eur FROM target) AS issuer_sfcr_property_gwp_eur,
       (SELECT hgb_building_year_end_contracts FROM target) AS issuer_hgb_building_year_end_contracts,
       (SELECT hgb_building_direct_gwp_eur FROM target) AS issuer_hgb_building_direct_gwp_eur,
       audit.*,
       false::boolean AS company_geolocated_insured_tiv_observed_by_these_sources,
       false::boolean AS annual_cat_ep_calibrated_by_these_sources,
       CASE
         WHEN verified_solo_entities<>1 THEN 'BLOCKED_UNVERIFIED_OR_AMBIGUOUS_SOLO_LEGAL_ENTITY'
         WHEN issuer_source_linked_solo_entities<>1 THEN 'BLOCKED_SOLO_ISSUER_SOURCE_LINEAGE'
         WHEN exact_source_bound_solo_lei_rows<>1 OR parent_lei_wrongly_on_solo_rows<>0
              THEN 'BLOCKED_EXACT_SOLO_LEI_OR_PARENT_COLLISION'
         WHEN source_bound_exact_sfcr_property_gwp_rows<>1
              THEN 'BLOCKED_SOLO_SFCR_METRIC_NOT_SOURCE_LINKED'
         WHEN source_bound_exact_hgb_building_contract_rows<>1
              OR source_bound_exact_hgb_building_gwp_rows<>1
              THEN 'BLOCKED_HGB_BUILDING_CONTRACTS_AND_PREMIUM_NOT_SOURCE_LINKED'
         WHEN company_linked_synthetic_portfolios=0 OR company_linked_portfolio_versions=0
              OR company_linked_exposure_units=0
              THEN 'BLOCKED_COMPANY_SYNTHETIC_EXPOSURE_NOT_REGISTERED'
         WHEN synthetic_exposure_units_with_geometry=0 THEN 'BLOCKED_SYNTHETIC_EXPOSURE_HAS_NO_GEOMETRY'
         WHEN synthetic_nrw_wgs84_source_candidate_units=0 THEN 'BLOCKED_NRW_SYNTHETIC_WGS84_ASSET_POINTS_MISSING'
         WHEN source_admitted_synthetic_nrw_wgs84_units=0 THEN 'BLOCKED_FULL_ORIGINAL_HU_CRS_RIGHTS_AND_SCENARIO_PROVENANCE'
         ELSE 'RESEARCH_ONLY_NEEDS_HAZARD_VULNERABILITY_RIGHTS_AND_TREATY_REVIEW'
       END::text AS next_gate
FROM audit;
