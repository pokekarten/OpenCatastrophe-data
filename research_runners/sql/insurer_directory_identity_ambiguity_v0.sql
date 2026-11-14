-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only identity ambiguity audit for a SECONDARY insurer names directory.
-- Not a deduplicated insurer count, proof of corporate structure, jurisdiction,
-- live insurer authorization, insured exposure, or model-input admission.
-- Lower(trim(name)) is only a lexical heuristic. It must never create links.
-- The home-market name match below covers only explicitly mapped DE/FR/SG.
WITH directory_names AS (
  SELECT country_slug, lower(trim(display_name)) AS normalized_name,
         count(*) AS n
  FROM research.insurer_directory_candidate_v0
  GROUP BY country_slug, lower(trim(display_name))
), legal_name_matches AS (
  SELECT o.organization_id, o.domicile_country, d.country_slug
  FROM entity.organization o
  JOIN research.insurer_directory_candidate_v0 d
    ON lower(trim(o.legal_name)) = lower(trim(d.display_name))
), counts AS (
  SELECT count(*) AS total_entries,
         count(DISTINCT source_slug) AS distinct_slugs,
         count(DISTINCT lower(trim(display_name))) AS global_name_strings
  FROM research.insurer_directory_candidate_v0
)
SELECT
  (SELECT total_entries FROM counts) AS directory_entries,
  (SELECT distinct_slugs FROM counts) AS directory_distinct_slugs,
  (SELECT global_name_strings FROM counts) AS directory_distinct_global_name_strings,
  (SELECT count(*) FROM directory_names) AS distinct_market_name_strings,
  (SELECT count(*) FROM directory_names WHERE n > 1) AS repeat_market_name_groups,
  (SELECT coalesce(sum(n-1),0) FROM directory_names WHERE n > 1) AS repeat_market_name_excess_entries,
  (SELECT count(*) FROM legal_name_matches) AS lexical_match_directory_rows,
  (SELECT count(DISTINCT organization_id) FROM legal_name_matches) AS lexical_match_verified_organizations,
  (SELECT count(*) FROM legal_name_matches
   WHERE (domicile_country='DE' AND country_slug='germany')
      OR (domicile_country='FR' AND country_slug='france')
      OR (domicile_country='SG' AND country_slug='singapore')) AS lexical_home_market_match_rows_de_fr_sg,
  (SELECT count(DISTINCT organization_id) FROM legal_name_matches
   WHERE (domicile_country='DE' AND country_slug='germany')
      OR (domicile_country='FR' AND country_slug='france')
      OR (domicile_country='SG' AND country_slug='singapore')) AS lexical_home_market_matched_orgs_de_fr_sg,
  (SELECT count(*) FROM entity.licence_observation WHERE organization_id IS NULL) AS regulator_licences_unlinked,
  (SELECT count(*) FROM entity.regulator_registration_crosswalk
   WHERE lei_verified_against_registration IS NOT TRUE) AS registration_crosswalks_without_verified_lei;
