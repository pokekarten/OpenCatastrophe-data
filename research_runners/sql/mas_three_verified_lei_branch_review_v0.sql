-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only, evidence-scoped *candidate* joins. This DOES NOT create a
-- licence-to-organization link, prove a legal branch relationship for all
-- companies, authorise CAT exposure, or replace home_country in Neon.
-- GLEIF original parent LEIs independently checked on 2026-11-01;
-- MAS institution detail names and country labels independently checked.
-- Three cases have matching pre-existing verified parent LEIs in CAT Neon.
-- Separate caution for AGCS: a distinct GLEIF BRANCH LEI
-- 984500D1360HXAUAEF86, registration T11FC0131K, relationship
-- IS_INTERNATIONAL_BRANCH_OF F240A7PWJB2BLKELB442, exists with a
-- LAPSED branch LEI/relationship registration. Parent is ISSUED;
-- neither registration state may be copied to the other.
WITH expected(
  mas_record_key, mas_display_name, mas_category, expected_parent_lei,
  expected_parent_name, expected_parent_jurisdiction,
  mas_detail_url, original_first_party_source_url,
  separate_branch_lei, separate_branch_register_id,
  branch_relationship_registration_state
) AS (VALUES
  ('other_001', 'ALLIANZ SE, SINGAPORE BRANCH',
   'Reinsurer (Composite)', '529900K9B0N5BT694847',
   'Allianz SE', 'DE',
   'https://eservices.mas.gov.sg/fid/institution/detail/3329-ALLIANZ-SE-SINGAPORE-BRANCH',
   'https://www.allianz.com/en/about-us/company/contact/singapore.html',
   NULL::text, NULL::text, NULL::text),
  ('other_010', 'ALLIANZ GLOBAL CORPORATE & SPECIALTY SE SINGAPORE BRANCH',
   'Direct Insurer (General)', 'F240A7PWJB2BLKELB442',
   'Allianz Global Corporate & Specialty SE', 'DE',
   'https://eservices.mas.gov.sg/fid/institution/detail/3526-ALLIANZ-GLOBAL-CORPORATE-SPECIALTY-SE-SINGAPORE-BRANCH',
   'https://commercial.allianz.com/content/dam/onemarketing/commercial/commercial/countries/singapore/AGCS-SG-Annual-Report-2022.pdf',
   '984500D1360HXAUAEF86', 'T11FC0131K', 'LAPSED'),
  ('other_006', 'MUNCHENER RUCKVERSICHERUNGS-GESELLSCHAFT, SINGAPORE BRANCH',
   'Reinsurer (Composite)', '529900MUF4C20K50JS49',
   'Münchener Rückversicherungs-Gesellschaft Aktiengesellschaft in München',
   'DE',
   'https://eservices.mas.gov.sg/fid/institution/detail/3092-MUNCHENER-RUCKVERSICHERUNGS-GESELLSCHAFT-SINGAPORE-BRANCH',
   'https://www.munichre.com/en/company/about-munich-re/munich-re-worldwide.html',
   NULL::text, NULL::text, NULL::text)
), observed AS (
 SELECT e.*, l.observation_id, l.listed_name, l.licence_class,
        l.jurisdiction AS mas_jurisdiction, l.organization_id AS existing_mas_organization_id,
        l.identity_resolution_status, l.home_country,
        o.organization_id AS candidate_parent_org_id, o.legal_name AS database_parent_name,
        o.domicile_country AS parent_domicile_country, o.identity_status AS parent_identity_status,
        i.identifier_value AS database_parent_lei
 FROM expected e
 LEFT JOIN entity.licence_observation l
   ON l.feed_id='ffbk_mas_curated_20261030'
  AND l.observed_record_key=e.mas_record_key
 LEFT JOIN entity.organization_identifier i
   ON i.identifier_scheme='GLEIF_LEI'
  AND i.identifier_value=e.expected_parent_lei
  AND i.is_verified IS TRUE
 LEFT JOIN entity.organization o
   ON o.organization_id=i.organization_id
)
SELECT mas_record_key, mas_display_name, mas_category,
       mas_detail_url, original_first_party_source_url,
       expected_parent_lei, expected_parent_name, expected_parent_jurisdiction,
       candidate_parent_org_id, separate_branch_lei,
       separate_branch_register_id, branch_relationship_registration_state,
       (observation_id IS NOT NULL
        AND listed_name=mas_display_name
        AND licence_class=mas_category
        AND mas_jurisdiction='SG'
        AND existing_mas_organization_id IS NULL
        AND identity_resolution_status='unmatched') AS mas_observation_eligible_for_review,
       (candidate_parent_org_id IS NOT NULL
        AND database_parent_lei=expected_parent_lei
        AND database_parent_name=expected_parent_name
        AND parent_domicile_country=expected_parent_jurisdiction
        AND parent_identity_status='verified') AS parent_identity_independently_present,
       (home_country IS NULL) AS mas_home_country_not_overwritten,
       'manual_branch_parent_identity_review_only' AS disposition,
       false AS relationship_auto_created,
       false AS original_branch_lei_currently_issued_claim,
       false AS new_cat_exposure_approved
FROM observed
ORDER BY mas_record_key;
