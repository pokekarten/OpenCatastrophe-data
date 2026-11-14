-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY, after separately approved schema+seed. This query cannot
-- cause a branch PR receipt to be misreported as first-party trusted MAIN.
-- It is NOT a scientific/rights/admission process.
WITH original_source_samples AS (
 SELECT source_id,provider_response_sha256,COUNT(*)::int AS sample_rows
 FROM research.source_sample_v0
 GROUP BY source_id,provider_response_sha256
),
latest_branch AS (
 SELECT source_id,COUNT(*)::int AS branch_original_direct_runs,
        MAX(provider_observed_at) AS latest_pr_branch_observation
 FROM research.source_strict_pr_branch_receipt_v1
 GROUP BY source_id
)
SELECT
 b.source_id,b.source_operation,b.github_run_id,b.github_job_id,
 b.github_head_sha,b.github_ref,b.github_run_url,b.provider_observed_at,
 b.original_http_status,b.original_response_bytes,
 b.original_response_sha256,b.original_request_sha256,
 COALESCE(samples.sample_rows,0) AS private_samples_with_matching_original_sha,
 EXISTS(SELECT 1 FROM research.all_source_inventory_v0 inventory
        WHERE inventory.source_id=b.source_id) AS canonical_registry_id_found,
 EXISTS(SELECT 1 FROM research.source_strict_original_probe_receipt_v1 m
        WHERE m.source_id=b.source_id) AS independent_strict_main_range_exists,
 EXISTS(SELECT 1 FROM research.source_strict_metadata_probe_receipt_v1 m
        WHERE m.source_id=b.source_id) AS independent_strict_main_metadata_exists,
 s.branch_original_direct_runs,s.latest_pr_branch_observation,
 b.verified_public_pr_branch_run,
 b.first_party_trusted_main_run,b.original_bytes_persisted,
 b.full_source_sha256_verified,b.physical_science_validated,
 b.insurer_model_input_approved,
 false AS grants_source_data_admission
FROM research.source_strict_pr_branch_receipt_v1 b
JOIN latest_branch s USING(source_id)
LEFT JOIN original_source_samples samples
  ON samples.source_id=b.source_id
 AND samples.provider_response_sha256=b.original_response_sha256
WHERE b.github_run_id IN (43488656039,43489514680,43491158483)
ORDER BY b.source_id,b.github_run_id;
