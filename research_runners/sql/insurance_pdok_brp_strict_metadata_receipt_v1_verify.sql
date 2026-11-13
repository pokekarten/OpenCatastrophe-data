-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0

-- One row per exact trusted main metadata receipt; independent of older
-- intermediary-only source_api_smoke_receipt_v0 and separate from 206 range.
SELECT
  p.source_id,p.github_run_id,p.github_job_id,p.github_head_sha,
  p.provider_observed_at,p.response_http_status,p.original_response_bytes,
  p.original_response_sha256,p.original_source_identity_validated,
  p.response_json_schema_validated,
  COUNT(DISTINCT s.sample_id) AS matching_private_research_metadata_samples,
  COUNT(DISTINCT s.sample_id) FILTER (
    WHERE s.sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
  ) AS matching_valid_private_sample_sha256,
  COUNT(DISTINCT u.use_case) AS joined_source_rights_cases,
  p.original_response_body_persisted,p.original_feature_rows_acquired,
  p.raw_source_assets_admitted,p.model_input_approved,
  p.science_or_version_admission_verified
FROM research.source_strict_metadata_probe_receipt_v1 p
LEFT JOIN research.source_sample_v0 s
 ON s.source_id=p.source_id AND s.provider_response_sha256=p.original_response_sha256
 AND s.sample_kind='public_metadata'
LEFT JOIN research.source_usage_rights_v0 u
 ON u.source_id=p.source_id AND u.product_scope LIKE 'RVO/PDOK BRP Gewaspercelen OGC API Features:%'
WHERE p.github_run_id=43489886311
GROUP BY p.receipt_id
ORDER BY p.source_id;
