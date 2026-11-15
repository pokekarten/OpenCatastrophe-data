-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only source/regulator identity triage after 2026-11-01 checks.
-- This is DATABASE state only; live APRA/MAS/GLEIF primary-source proof is
-- documented at docs/research/regulator-45-source-crosscheck-20261101.md.
-- Matching names and issued LEIs do not establish insured CAT portfolios.
WITH source_rows AS (
 SELECT feed_id, licence_class, organization_id, identity_resolution_status,
        lei, local_registration_id, source_as_of, listed_name, observed_record_key
 FROM entity.licence_observation
 WHERE feed_id IN ('apra_general','eiopa_insurers','ffbk_mas_curated_20261030')
), groups AS (
 SELECT feed_id,
        CASE
          WHEN feed_id='ffbk_mas_curated_20261030' THEN licence_class
          ELSE 'all observed classes' END AS cohort,
        count(*) AS all_observations,
        count(*) FILTER (WHERE organization_id IS NULL) AS unmatched_legal_entities,
        count(*) FILTER (WHERE organization_id IS NOT NULL) AS preexisting_verified_links,
        count(*) FILTER (WHERE organization_id IS NULL AND lei IS NOT NULL
                             AND length(lei)=20) AS unmatched_with_lei,
        count(*) FILTER (WHERE organization_id IS NULL AND local_registration_id IS NOT NULL
                             AND trim(local_registration_id)<>'') AS unmatched_with_local_registry,
        count(*) FILTER (WHERE organization_id IS NULL AND source_as_of IS NULL)
              AS unmatched_missing_regulator_as_of_date,
        count(*) FILTER (WHERE organization_id IS NULL AND
                         (listed_name IS NULL OR trim(listed_name)=''))
              AS unmatched_missing_display_name
 FROM source_rows
 GROUP BY feed_id, CASE WHEN feed_id='ffbk_mas_curated_20261030'
                         THEN licence_class ELSE 'all observed classes' END
)
SELECT feed_id, cohort, all_observations, unmatched_legal_entities,
       preexisting_verified_links, unmatched_with_lei,
       unmatched_with_local_registry, unmatched_missing_regulator_as_of_date,
       unmatched_missing_display_name,
       false AS newly_admitted_legal_identity,
       false AS insured_cat_exposure_verified
FROM groups ORDER BY feed_id,cohort;
