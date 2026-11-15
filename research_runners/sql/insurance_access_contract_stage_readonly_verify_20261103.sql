-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ-ONLY isolated CAT Neon access-contract staging receipt (2026-11-03).
-- Execute ONLY after explicitly selecting branch br-wild-wave-bazb2ck2;
-- never use a default/production branch to infer staged completion.
-- Original GitHub snapshot: 5481c214d5e2c233d4d5cb95204f67d584f53599
-- No original provider bytes, downloads, rights grants or CAT admission.
WITH canonical AS (
 SELECT s.source_key,s.source_id,s.git_path,s.git_blob_sha,s.git_commit_sha,
        s.review_status,s.rights_status,s.admissible_for_raw,s.raw_metadata
 FROM registry.source_record s
 WHERE s.classification='access_contract'
   AND s.git_path ~ '^access/[^/]+[.]json$'
), metrics AS (
 SELECT count(*)::int AS canonical_access_contracts,
        count(*) FILTER(WHERE git_commit_sha=
          '5481c214d5e2c233d4d5cb95204f67d584f53599')::int AS newly_staged_contracts,
        count(*) FILTER(WHERE git_commit_sha IS DISTINCT FROM
          '5481c214d5e2c233d4d5cb95204f67d584f53599')::int AS historical_canonical_contracts,
        count(DISTINCT source_key)::int AS distinct_source_keys,
        count(DISTINCT git_path)::int AS distinct_git_paths,
        count(*) FILTER(WHERE source_key IS DISTINCT FROM
          'access:' || (raw_metadata->>'access_id')
          OR source_id IS DISTINCT FROM (raw_metadata->>'access_id'))::int AS mismatched_access_identity,
        count(*) FILTER(WHERE review_status IS DISTINCT FROM raw_metadata->>'status'
          OR rights_status IS DISTINCT FROM raw_metadata->'rights_and_policy'->>'dataset_rights_status')::int AS altered_contract_rights_or_status,
        count(*) FILTER(WHERE admissible_for_raw IS DISTINCT FROM FALSE)::int AS unexpected_raw_admission,
        count(*) FILTER(WHERE git_blob_sha !~ '^[0-9a-f]{40}$'
          OR git_commit_sha !~ '^[0-9a-f]{40}$')::int AS malformed_provenance,
        count(*) FILTER(WHERE git_path='access/esa.worldcover.2021.v200.json'
          AND git_blob_sha='830fff1705d6b29d8c88dc423a27c7254608ca50'
          AND review_status='documented_only')::int AS esa_worldcover_prior_revision_preserved,
        count(*) FILTER(WHERE git_path='access/noaa.coops.water-levels.json'
          AND git_blob_sha='53aa5e6e9f23dc0ddd153fae1c57a4752f31b0aa'
          AND review_status='documented_only')::int AS noaa_coops_prior_revision_preserved
 FROM canonical
)
SELECT 'ISOLATED_ACCESS_METADATA_STAGE_ONLY_NOT_PRODUCTION'::text AS receipt_scope,
       (SELECT count(*)::int FROM registry.source_record) AS total_registry_rows,
       (SELECT count(*)::int FROM registry.source_record
         WHERE classification='landscape_candidate') AS landscape_shard_rows,
       (SELECT count(*)::int FROM registry.source_record
         WHERE classification='admitted_manifest') AS existing_manifest_rows,
       (SELECT count(*)::int FROM registry.source_record
         WHERE classification='access_contract') AS all_access_classified_rows,
       canonical_access_contracts,newly_staged_contracts,
       historical_canonical_contracts,distinct_source_keys,distinct_git_paths,
       mismatched_access_identity,altered_contract_rights_or_status,
       unexpected_raw_admission,malformed_provenance,
       esa_worldcover_prior_revision_preserved,
       noaa_coops_prior_revision_preserved,
       FALSE AS automatic_production_promotion_authorized,
       FALSE AS restricted_source_probe_authorized,
       FALSE AS provider_bytes_acquired,
       FALSE AS insurance_cat_model_input_authorized
FROM metrics;
