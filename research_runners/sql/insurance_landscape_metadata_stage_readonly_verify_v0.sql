-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY. Only for the CAT insurance-risk-core / insurance database.
-- Pass an explicit Neon branch ID. Never default to production for stage receipt.
-- This DOES NOT grant source rights or insurance CAT model admission.
-- GitHub snapshot pinned: d156e9e654652717179286caaa8cdf14636f9db2
-- Validated staging Neon branch: br-raspy-cell-ba5j7191
WITH shards AS (
 SELECT source_key,source_id,git_path,git_blob_sha,git_commit_sha,
        review_status,rights_status,admissible_for_raw,
        CASE WHEN jsonb_typeof(raw_metadata->'entries')='array'
             THEN jsonb_array_length(raw_metadata->'entries') ELSE 0 END AS entry_count
 FROM registry.source_record
 WHERE classification='landscape_candidate'
), checked AS (
 SELECT count(*)::integer AS shard_count,
        count(*) FILTER (WHERE git_commit_sha=
           'd156e9e654652717179286caaa8cdf14636f9db2')::integer AS staged_shards,
        count(*) FILTER (WHERE git_commit_sha IS DISTINCT FROM
           'd156e9e654652717179286caaa8cdf14636f9db2')::integer AS historical_shards,
        sum(entry_count)::integer AS source_candidate_entry_count,
        count(*) FILTER (WHERE admissible_for_raw IS DISTINCT FROM FALSE)::integer AS unexpected_raw_admission,
        count(*) FILTER (WHERE rights_status IS DISTINCT FROM 'not_reviewed')::integer AS nonstandard_rights,
        count(*) FILTER (WHERE review_status IS DISTINCT FROM 'non_admission_discovery_only')::integer AS nonstandard_review,
        count(DISTINCT source_key)::integer AS distinct_source_keys,
        count(DISTINCT git_path)::integer AS distinct_shard_paths,
        count(*) FILTER (WHERE source_key IS DISTINCT FROM
          'landscape_file:'||regexp_replace(source_id,'^',''))::integer AS invalid_key,
        count(*) FILTER (WHERE git_blob_sha !~ '^[0-9a-f]{40}$'
          OR git_commit_sha !~ '^[0-9a-f]{40}$')::integer AS malformed_provenance
 FROM shards
)
SELECT 'NON_ADMISSION_METADATA_STAGE_ONLY'::text AS receipt_type,
       shard_count,staged_shards,historical_shards,
       source_candidate_entry_count,
       unexpected_raw_admission,nonstandard_rights,nonstandard_review,
       distinct_source_keys,distinct_shard_paths,invalid_key,
       malformed_provenance,
       FALSE AS automatic_production_sync_authorized,
       FALSE AS raw_provider_data_acquisition_authorized,
       FALSE AS cat_model_input_approved
FROM checked;
