-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0

-- Read-only cross-check. Distinct from the weaker original intermediary
-- smoke ledger (which intentionally has strict_repository_runner_executed=false).
SELECT
 p.source_id, p.github_run_id, p.github_job_id, p.github_head_sha,
 p.provider_observed_at, p.original_http_status, p.original_content_range,
 p.original_response_bytes, p.original_response_sha256,
 p.contract_sha256, p.runner_code_sha256,
 COUNT(s.sample_id) AS older_matching_original_sha_samples,
 BOOL_AND(s.provider_response_sha256 = p.original_response_sha256) AS previous_prefix_hashes_agree,
 p.original_provider_body_persisted, p.full_source_sha256_verified,
 p.insurer_model_input_approved
FROM research.source_strict_original_probe_receipt_v1 p
LEFT JOIN research.source_sample_v0 s
  ON s.source_id = p.source_id AND s.provider_response_sha256 = p.original_response_sha256
WHERE p.github_run_id = 43480623017
GROUP BY p.receipt_id
ORDER BY p.source_id;
