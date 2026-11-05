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
-- The 53 county counts and toy EUR amounts are independently conserved
-- from the pinned 10k physical-source OED research receipt.
expected_nrw_10k_kreise(ags, n, tiv) AS (
 VALUES
    ('05111', 185, 92884500),
    ('05112', 205, 101220750),
    ('05113', 226, 109130625),
    ('05114', 117, 55606500),
    ('05116', 142, 67405500),
    ('05117', 79, 37510875),
    ('05119', 97, 52506000),
    ('05120', 52, 26133750),
    ('05122', 83, 45099000),
    ('05124', 138, 65847375),
    ('05154', 241, 115018875),
    ('05158', 248, 120524625),
    ('05162', 275, 132349500),
    ('05166', 217, 104153625),
    ('05170', 293, 143683875),
    ('05314', 143, 73444500),
    ('05315', 353, 174494250),
    ('05316', 77, 34192125),
    ('05334', 313, 150845625),
    ('05358', 197, 99380250),
    ('05362', 307, 140512500),
    ('05366', 162, 74072250),
    ('05370', 213, 102984750),
    ('05374', 192, 90501750),
    ('05378', 187, 87214500),
    ('05382', 424, 198514125),
    ('05512', 61, 34288875),
    ('05513', 99, 52561125),
    ('05515', 142, 76605750),
    ('05554', 268, 117115875),
    ('05558', 159, 67692375),
    ('05562', 348, 166096125),
    ('05566', 322, 146227500),
    ('05570', 192, 88887375),
    ('05711', 158, 79711875),
    ('05754', 232, 108396000),
    ('05758', 170, 86716125),
    ('05762', 106, 58761000),
    ('05766', 235, 108837000),
    ('05770', 216, 112494375),
    ('05774', 188, 88160625),
    ('05911', 147, 65457000),
    ('05913', 241, 120695625),
    ('05914', 76, 36999000),
    ('05915', 99, 45155250),
    ('05916', 61, 31880250),
    ('05954', 164, 82911375),
    ('05958', 185, 95747625),
    ('05962', 237, 115250625),
    ('05966', 93, 46023750),
    ('05970', 191, 96501375),
    ('05974', 208, 89546625),
    ('05978', 236, 112077000)
),
nrw_county_completeness AS (
 SELECT v.portfolio_version_id, u.region_code,
        count(*)::bigint AS n,
        count(DISTINCT u.external_unit_id)::bigint AS unique_ids,
        count(DISTINCT ST_AsBinary(u.location))::bigint AS unique_points,
        sum(u.insured_value)::numeric AS tiv,
        count(*) FILTER (WHERE
           u.unit_type='asset' AND u.assumption_status='synthetic'
           AND u.country_code='DE'
           AND u.region_code ~ '^05[0-9]{3}$'
           AND u.location IS NOT NULL AND ST_SRID(u.location)=4326
           AND ST_IsValid(u.location)
           AND ST_GeometryType(u.location)='ST_Point'
           AND ST_X(u.location) BETWEEN 5.5 AND 10
           AND ST_Y(u.location) BETWEEN 50 AND 52.8
           AND u.building_count=1 AND u.insured_value>0
           AND u.value_basis LIKE 'FICTIONAL%'
           AND u.source_key=v.source_key
           AND sr.canonical_url='https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip'
           AND sr.rights_status='reviewed_derivative_usage_permitted'
           AND sr.raw_metadata ->> 'original_hu_archive_full_sha256'='10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da'
           AND sr.raw_metadata ->> 'oed_manifest_sha256'=v.scenario_hash
           AND sr.raw_metadata @> '{"original_hu_archive_full_sha256_verified":true,"source_member_CRCs_verified":true,"source_2022_GFK_codebook_verified":true,"source_transformation_EPSG4647_to_4326_verified":true,"publisher_dataset_license_reviewed":true,"fictional_policy_linkage":true}'::jsonb
        )::bigint AS admitted
 FROM exposure.portfolio p
 JOIN exposure.portfolio_version v USING (portfolio_id)
 JOIN exposure.exposure_unit u USING (portfolio_version_id)
 LEFT JOIN registry.source_record sr ON sr.source_key=u.source_key
 WHERE p.organization_id IN (SELECT organization_id FROM solo)
   AND p.portfolio_type='synthetic'
   AND p.portfolio_key='RVA_LIKE_NRW_HU22_FULL_ORIGINAL_10K_53KREIS_GEO_STUDY'
   AND v.scenario_hash='b4713a9a09a55193d39b64550bc1408ba588303d8a4e658f05536b3dbe14b416'
 GROUP BY v.portfolio_version_id,u.region_code
),
nrw_complete_10k AS (
 SELECT count(*)::bigint AS complete_source_admitted_10k_nrw_oed_versions
 FROM (
   SELECT c.portfolio_version_id
   FROM nrw_county_completeness c
   LEFT JOIN expected_nrw_10k_kreise e ON e.ags=c.region_code
   GROUP BY c.portfolio_version_id
   HAVING count(*)=53
     AND sum(c.n)=10000
     AND sum(c.unique_ids)=10000
     AND sum(c.unique_points)=10000
     AND sum(c.admitted)=10000
     AND sum(c.tiv)=4826029500::numeric
     AND count(*) FILTER (WHERE e.ags IS NOT NULL AND c.n=e.n AND c.tiv=e.tiv)=53
 ) complete_version
),
audit AS (
 SELECT si.*,c.*,f.*,b.*,v.*,u.*,z.*
 FROM solo_identity si CROSS JOIN candidates c CROSS JOIN finances f
 CROSS JOIN books b CROSS JOIN versions v CROSS JOIN units u
 CROSS JOIN nrw_complete_10k z
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
         WHEN complete_source_admitted_10k_nrw_oed_versions<>1 THEN 'BLOCKED_NRW_10K_ALL_KREISE_POLICY_TIV_AND_SOURCE_CONSERVATION'
         ELSE 'RESEARCH_ONLY_NEEDS_HAZARD_VULNERABILITY_RIGHTS_AND_TREATY_REVIEW'
       END::text AS next_gate
FROM audit;
