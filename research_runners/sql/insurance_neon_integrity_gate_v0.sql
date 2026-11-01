-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only, shared-schema integrity preflight for the independent CAT-only
-- Neon "insurance" database. Run separately against main and validation,
-- explicitly selecting the branch in your client. Never infer branch
-- identity from current_database(): both branches use "insurance".
--
-- This does NOT validate source licences, CAT calibration, model fitness,
-- provenance of external provider bytes, or scientific data admission.
-- "passed=true" on an empty table may be vacuous; audit row counts separately.
-- Zero writes, no extension requirement, no passwords / connection strings.
-- A nonzero violations count needs investigation before promoting any input.
WITH checks AS (
    SELECT 'duplicate_verified_identifiers_across_organizations'::text AS check_id,
        (SELECT count(*) FROM (
            SELECT identifier_scheme, identifier_value
            FROM entity.organization_identifier
            WHERE is_verified
            GROUP BY identifier_scheme, identifier_value
            HAVING count(DISTINCT organization_id) > 1
        ) d)::bigint AS violations

    UNION ALL SELECT 'verified_identifiers_without_organization',
        (SELECT count(*)
         FROM entity.organization_identifier i
         LEFT JOIN entity.organization o ON o.organization_id = i.organization_id
         WHERE i.is_verified AND o.organization_id IS NULL)

    UNION ALL SELECT 'organization_candidates_with_broken_verified_link',
        (SELECT count(*)
         FROM entity.organization_candidate c
         LEFT JOIN entity.organization o
           ON o.organization_id = c.verified_organization_id
         WHERE c.verified_organization_id IS NOT NULL
           AND o.organization_id IS NULL)

    UNION ALL SELECT 'source_record_git_sha_invalid',
        (SELECT count(*) FROM registry.source_record
         WHERE git_blob_sha IS NULL OR git_commit_sha IS NULL
            OR git_blob_sha !~ '^[0-9a-f]{40}$'
            OR git_commit_sha !~ '^[0-9a-f]{40}$')

    UNION ALL SELECT 'repository_asset_git_sha_invalid',
        (SELECT count(*) FROM registry.repository_asset
         WHERE git_blob_sha IS NULL OR git_commit_sha IS NULL
            OR git_blob_sha !~ '^[0-9a-f]{40}$'
            OR git_commit_sha !~ '^[0-9a-f]{40}$')

    UNION ALL SELECT 'admitted_sources_with_unreviewed_rights',
        (SELECT count(*) FROM registry.source_record
         WHERE admissible_for_raw
           AND (rights_status IS NULL OR rights_status IN
             ('not_reviewed', 'unknown', 'restricted', 'conflicting', 'to_review')))

    UNION ALL SELECT 'admitted_assets_with_unreviewed_rights',
        (SELECT count(*) FROM registry.repository_asset
         WHERE raw_import_allowed
           AND (rights_status IS NULL OR rights_status IN
             ('to_review', 'private_unresolved', 'metadata_only')))

    UNION ALL SELECT 'real_portfolios_without_legal_org',
        (SELECT count(*) FROM exposure.portfolio
         WHERE portfolio_type IS DISTINCT FROM 'synthetic'
           AND organization_id IS NULL)

    UNION ALL SELECT 'synthetic_portfolios_with_non_synthetic_exposure',
        (SELECT count(*) FROM exposure.exposure_unit u
         JOIN exposure.portfolio_version v
           ON u.portfolio_version_id = v.portfolio_version_id
         JOIN exposure.portfolio p ON v.portfolio_id = p.portfolio_id
         WHERE p.portfolio_type = 'synthetic'
           AND u.assumption_status IS DISTINCT FROM 'synthetic')

    UNION ALL SELECT 'non_synthetic_exposure_without_source',
        (SELECT count(*) FROM exposure.exposure_unit
         WHERE assumption_status IS DISTINCT FROM 'synthetic'
           AND (source_key IS NULL OR trim(source_key) = ''))

    UNION ALL SELECT 'non_synthetic_contract_without_source',
        (SELECT count(*) FROM insurance.contract
         WHERE NOT is_synthetic
           AND (source_key IS NULL OR trim(source_key) = ''))

    UNION ALL SELECT 'completed_simulations_missing_sha_or_years',
        (SELECT count(*) FROM model.simulation_run
         WHERE run_status = 'completed'
           AND (config_sha256 IS NULL
             OR config_sha256 !~ '^[0-9a-f]{64}$'
             OR simulation_years IS NULL
             OR simulation_years < 1))
)
SELECT check_id, violations, (violations = 0) AS passed
FROM checks
ORDER BY check_id;
