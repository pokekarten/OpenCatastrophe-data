-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only 2026-11-01 MAS details audit; 20 selected research observations.
-- These exact MAS URLs and their "Incorporated in" UI labels were independently
-- checked live. They are REGULATOR DETAIL PAGE labels, not proven legal parents
-- or independent Singapore incorporation of a branch office.
--
-- XL RE EUROPE SE SINGAPORE BRANCH: MAS detail displays "Incorporated in
-- Singapore", while GLEIF LEI 6354005OC5UTPXJQ9E28 locates the parent
-- legal entity in Ireland, registration 423311. Keep both with scopes;
-- do NOT overwrite home_country or auto-link to legal organization.
WITH mas_detail(record_key, detail_url, licence_category, mas_incorporated_label) AS (
 VALUES
  ('other_011', 'https://eservices.mas.gov.sg/fid/institution/detail/232430-ALLIANZ-INSURANCE-SINGAPORE-PTE-LTD', 'Direct Insurer (Composite)', 'Singapore'),
  ('other_010', 'https://eservices.mas.gov.sg/fid/institution/detail/3526-ALLIANZ-GLOBAL-CORPORATE-SPECIALTY-SE-SINGAPORE-BRANCH', 'Direct Insurer (General)', 'Germany'),
  ('other_001', 'https://eservices.mas.gov.sg/fid/institution/detail/3329-ALLIANZ-SE-SINGAPORE-BRANCH', 'Reinsurer (Composite)', 'Germany'),
  ('other_003', 'https://eservices.mas.gov.sg/fid/institution/detail/200782-CHINA-REINSURANCE-GROUP-CORPORATION-SINGAPORE-BRANCH', 'Reinsurer (Composite)', 'China'),
  ('other_004', 'https://eservices.mas.gov.sg/fid/institution/detail/3097-GENERAL-REINSURANCE-AG-SINGAPORE-BRANCH', 'Reinsurer (Composite)', 'Germany'),
  ('other_005', 'https://eservices.mas.gov.sg/fid/institution/detail/200508-MAPFRE-RE-COMPANIA-DE-REASEGUROS-S-A-SINGAPORE-BRANCH', 'Reinsurer (Composite)', 'Spain'),
  ('other_006', 'https://eservices.mas.gov.sg/fid/institution/detail/3092-MUNCHENER-RUCKVERSICHERUNGS-GESELLSCHAFT-SINGAPORE-BRANCH', 'Reinsurer (Composite)', 'Germany'),
  ('general_001', 'https://eservices.mas.gov.sg/fid/institution/detail/239249-ASPEN-BERMUDA-LIMITED-SINGAPORE-BRANCH', 'Reinsurer (General)', 'Bermuda'),
  ('general_002', 'https://eservices.mas.gov.sg/fid/institution/detail/3474-ASPEN-INSURANCE-UK-LIMITED-SINGAPORE-BRANCH', 'Reinsurer (General)', 'United Kingdom'),
  ('general_004', 'https://eservices.mas.gov.sg/fid/institution/detail/4038-DAVINCI-REINSURANCE-LTD-SINGAPORE-BRANCH', 'Reinsurer (General)', 'Bermuda'),
  ('general_005', 'https://eservices.mas.gov.sg/fid/institution/detail/3473-ENDURANCE-SPECIALTY-INSURANCE-LTD-SINGAPORE-BRANCH', 'Reinsurer (General)', 'Bermuda'),
  ('general_006', 'https://eservices.mas.gov.sg/fid/institution/detail/3312-EVEREST-REINSURANCE-COMPANY', 'Reinsurer (General)', 'United States'),
  ('general_007', 'https://eservices.mas.gov.sg/fid/institution/detail/200339-HELVETIA-SWISS-INSURANCE-COMPANY-LTD-SINGAPORE-BRANCH', 'Reinsurer (General)', 'Switzerland'),
  ('general_009', 'https://eservices.mas.gov.sg/fid/institution/detail/3101-KOREAN-REINSURANCE-COMPANY', 'Reinsurer (General)', 'Korea, South'),
  ('general_011', 'https://eservices.mas.gov.sg/fid/institution/detail/3460-MILLI-REASURANS-T-A-S-SINGAPORE-BRANCH', 'Reinsurer (General)', 'Turkey'),
  ('general_013', 'https://eservices.mas.gov.sg/fid/institution/detail/3341-ODYSSEY-REINSURANCE-COMPANY', 'Reinsurer (General)', 'United States'),
  ('general_016', 'https://eservices.mas.gov.sg/fid/institution/detail/3543-RENAISSANCE-REINSURANCE-LTD-SINGAPORE-BRANCH', 'Reinsurer (General)', 'Bermuda'),
  ('general_018', 'https://eservices.mas.gov.sg/fid/institution/detail/3304-THE-TOA-REINSURANCE-COMPANY-LIMITED-SINGAPORE-BRANCH', 'Reinsurer (General)', 'Japan'),
  ('general_021', 'https://eservices.mas.gov.sg/fid/institution/detail/3548-TRANSATLANTIC-REINSURANCE-COMPANY-SINGAPORE-BRANCH', 'Reinsurer (General)', 'United States'),
  ('general_022', 'https://eservices.mas.gov.sg/fid/institution/detail/419759-XL-RE-EUROPE-SE-SINGAPORE-BRANCH', 'Reinsurer (General)', 'Singapore')
), joined AS (
 SELECT d.record_key, d.detail_url, d.licence_category,
        d.mas_incorporated_label, l.observation_id, l.listed_name,
        l.licence_class, l.jurisdiction, l.home_country,
        l.organization_id, l.identity_resolution_status,
        CASE WHEN upper(coalesce(l.listed_name, '')) LIKE '%SINGAPORE BRANCH%'
             THEN 1 ELSE 0 END AS explicit_branch_name,
        CASE WHEN d.mas_incorporated_label <> 'Singapore' THEN 1 ELSE 0 END
             AS mas_foreign_incorporation_label,
        CASE WHEN d.record_key = 'general_022'
             AND d.mas_incorporated_label = 'Singapore' THEN 1 ELSE 0 END
             AS conflicting_scope_xl_re_europe
 FROM mas_detail d
 LEFT JOIN entity.licence_observation l
   ON l.feed_id='ffbk_mas_curated_20261030'
  AND l.observed_record_key=d.record_key
)
SELECT count(*) AS source_detail_pages,
       count(observation_id) AS matching_neon_observations,
       count(DISTINCT record_key) AS unique_mas_record_keys,
       count(*) FILTER (WHERE observation_id IS NULL OR
            licence_class IS DISTINCT FROM licence_category OR
            jurisdiction IS DISTINCT FROM 'SG') AS missing_or_wrong_licence_category,
       count(*) FILTER (WHERE organization_id IS NOT NULL
              OR identity_resolution_status IS DISTINCT FROM 'unmatched')
            AS research_rows_already_admitted_or_linked,
       count(*) FILTER (WHERE home_country IS NULL) AS neon_home_country_still_unknown,
       sum(explicit_branch_name) AS observation_names_explicit_sg_branch,
       sum(mas_foreign_incorporation_label) AS mas_label_incorporated_outside_sg,
       count(*) FILTER (WHERE mas_incorporated_label='Singapore')
            AS mas_label_incorporated_in_sg,
       sum(conflicting_scope_xl_re_europe) AS xl_re_europe_parent_branch_scope_conflicts,
       false AS parent_legal_entity_country_auto_applied,
       false AS new_organization_link_created,
       false AS insurer_exposure_verified,
       false AS model_input_approved
FROM joined;
