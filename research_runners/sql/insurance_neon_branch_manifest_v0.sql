-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only metadata export. Execute SEPARATELY against explicitly selected
-- insurance-risk-core/main and validation-schema-20261031 database branches.
-- Save each ONE-ROW JSON result separately, then compare using:
-- python -m scripts.insurance_neon_branch_merge_preflight_v0 \
--   --main /private/main.json --validation /private/validation.json
--
-- Never include original source bytes, credentials, personal insurer/customer
-- records, or branch connection strings in a repo/issue/PR.
-- This output does not authorize identity links, licence approval or merging.
SELECT jsonb_build_object(
    'format', 'OC-NEON-BRANCH-METADATA-V0',
    'sources',
      coalesce((
        SELECT jsonb_agg(
          jsonb_build_object(
            'source_key', source_key,
            'git_blob_sha', git_blob_sha,
            'review_status', review_status,
            'rights_status', rights_status,
            'admissible_for_raw', admissible_for_raw
          ) ORDER BY source_key)
        FROM registry.source_record
      ), '[]'::jsonb),
    'candidates',
      coalesce((
        SELECT jsonb_agg(
          jsonb_build_object(
            'source_row_key', source_row_key,
            'identity_resolution_status', identity_resolution_status,
            'verified_organization_id', verified_organization_id
          ) ORDER BY source_row_key)
        FROM entity.organization_candidate
      ), '[]'::jsonb)
) AS metadata_manifest;
