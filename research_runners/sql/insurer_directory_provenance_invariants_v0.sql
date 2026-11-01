-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only audit of third-party insurer-directory RESEARCH rows.
-- Run against insurance-risk-core/main. False is an observed blocker, not
-- a reason to invent missing source evidence or change model approval flags.
-- Portable SQL: also executed in synthetic offline SQLite tests.
WITH checks AS (
    SELECT 'staging_nonempty' AS check_id,
           (SELECT count(*) > 0 FROM research.insurer_directory_candidate_v0) AS passed
    UNION ALL SELECT 'source_slugs_unique',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       GROUP BY source_slug HAVING count(*) > 1)
    UNION ALL SELECT 'source_identity_not_blank',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       WHERE source_slug IS NULL OR trim(source_slug) = ''
                          OR country_slug IS NULL OR trim(country_slug) = ''
                          OR display_name IS NULL OR trim(display_name) = ''
                          OR dataset_version IS NULL OR trim(dataset_version) = '')
    UNION ALL SELECT 'provider_claim_is_not_a_regulator_decision',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       WHERE provider_verification_claim IS NULL
                          OR provider_verification_claim NOT IN ('verified','partial','unverified')
                          OR review_status IS NULL
                          OR review_status <> 'secondary_source_pending_regulator_reconciliation')
    UNION ALL SELECT 'model_input_never_approved_from_secondary_directory',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       WHERE model_input_approved IS NULL OR model_input_approved)
    UNION ALL SELECT 'terms_url_is_https',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       WHERE source_terms_url IS NULL
                          OR substr(lower(trim(source_terms_url)),1,8) <> 'https://')
    UNION ALL SELECT 'declared_license_is_reviewable',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       WHERE license_spdx IS NULL OR trim(license_spdx) = '')
    UNION ALL SELECT 'original_dataset_url_is_not_missing_or_placeholder',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       WHERE source_dataset_url IS NULL OR lower(trim(source_dataset_url))
                          IN ('','undefined','null','none','n/a'))
    UNION ALL SELECT 'original_dataset_url_is_https',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       WHERE source_dataset_url IS NULL
                          OR substr(lower(trim(source_dataset_url)),1,8) <> 'https://')
    UNION ALL SELECT 'original_bytes_have_sha256_evidence',
           NOT EXISTS (SELECT 1 FROM research.insurer_directory_candidate_v0
                       WHERE raw_provider_sha256 IS NULL OR length(raw_provider_sha256) <> 64
                          OR trim(raw_provider_sha256,'0123456789abcdef') <> '')
)
SELECT check_id, CASE WHEN passed THEN 1 ELSE 0 END AS passed
FROM checks ORDER BY check_id;
