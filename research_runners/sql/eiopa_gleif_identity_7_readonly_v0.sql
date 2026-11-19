-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only check that precisely seven EIOPA research observations are present.
-- Independent GLEIF Level-1 record checks are in scripts/eiopa_gleif_seven_identity_receipt_v0.py.
-- This query neither creates organizations nor claims a current EIOPA licence.
WITH expected(lei, jurisdiction, observed_record_key, local_registration_id) AS (
  VALUES
    ('259400VDTC20UW6M5D80','LV','LV-049-DOMESTIC','049'),
    ('63670018BQ5R7IKA8T76','DK','DK-53118-DOMESTIC','53118'),
    ('213800AEQ6JQDLCWQN31','ES','ES-M0328-DOMESTIC','M0328'),
    ('213800LXNGNQ5O1XBW47','MT','MT-C 51071-DOMESTIC','C 51071'),
    ('529900SURJXJXSY5O039','LT','LT-110051834-DOMESTIC','110051834'),
    ('95980020140005024486','ES','ES-P3159-DOMESTIC','P3159'),
    ('7437008CXP8UX8KITQ76','FI','FI-01450820-DOMESTIC','01450820')
), joined AS (
  SELECT e.lei, e.jurisdiction, e.observed_record_key, e.local_registration_id,
         l.observation_id, l.lei AS stored_lei,
         l.organization_id, l.identity_resolution_status,
         l.source_as_of, l.listed_name
  FROM expected e LEFT JOIN entity.licence_observation l
    ON l.feed_id='eiopa_insurers'
   AND l.observed_record_key=e.observed_record_key
), summary AS (
  SELECT count(*) AS expected_observations,
         count(observation_id) AS observations_present,
         count(*) FILTER (WHERE observation_id IS NULL OR stored_lei IS DISTINCT FROM lei
             OR listed_name IS NULL OR trim(listed_name) = '') AS unexpected_or_missing_source_identity,
         count(*) FILTER (WHERE organization_id IS NOT NULL) AS already_linked_entities,
         count(*) FILTER (WHERE identity_resolution_status <> 'unmatched'
                               OR identity_resolution_status IS NULL) AS no_longer_unmatched,
         count(*) FILTER (WHERE source_as_of IS NULL) AS regulator_export_date_not_pinned
  FROM joined
)
SELECT expected_observations, observations_present,
       unexpected_or_missing_source_identity, already_linked_entities,
       no_longer_unmatched, regulator_export_date_not_pinned,
       (SELECT count(*) FROM entity.licence_observation
        WHERE feed_id='eiopa_insurers') AS all_eiopa_observations,
       (SELECT count(*) FROM entity.licence_observation l
        WHERE l.feed_id='eiopa_insurers'
          AND NOT EXISTS (SELECT 1 FROM expected e WHERE e.lei=l.lei
                          AND e.observed_record_key=l.observed_record_key)) AS unexpected_extra_eiopa_observations,
       false AS new_legal_entities_created,
       false AS cat_model_input_admitted
FROM summary;
