-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Reproducible, non-destructive schema for use-case-specific dataset rights
-- in the separate private insurance-risk-core Neon research database.
-- The original source catalogue and manifests remain the canonical public
-- repository authority. Rights observations are narrower than admission.
--
-- Run using an approved Neon connection on the insurance DB:
--   psql ... -f sql/research_source_usage_rights_v0.sql
--
-- This file neither reads nor copies external data bytes and does not allow
-- any source/model admission. Do not use to overwrite a provider contract.

CREATE TABLE IF NOT EXISTS research.source_usage_rights_v0 (
    source_id text NOT NULL
        REFERENCES research.source_candidate_review_v0(source_id),
    product_scope text NOT NULL,
    use_case text NOT NULL
        CHECK (use_case IN (
            'internal_research',
            'commercial_cat_modelling',
            'automated_api_access',
            'internal_neon_metadata',
            'internal_neon_source_sample',
            'external_raw_redistribution',
            'published_derived_results'
        )),
    rights_result text NOT NULL
        CHECK (rights_result IN ('allowed', 'conditional', 'prohibited', 'unknown')),
    evidence_url text NOT NULL
        CHECK (evidence_url ~ '^https://'),
    evidence_observed_on date NOT NULL,
    rationale text NOT NULL,
    scientific_model_admission boolean NOT NULL DEFAULT false
        CHECK (scientific_model_admission = false),
    original_asset_admitted boolean NOT NULL DEFAULT false
        CHECK (original_asset_admitted = false),
    recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_id, product_scope, use_case),
    CONSTRAINT nonempty_scope CHECK (length(trim(product_scope)) >= 3),
    CONSTRAINT nonempty_rationale CHECK (length(trim(rationale)) >= 8)
);

-- The source-rights table alone never authorizes external source downloads
-- or model use; the original source access contract and science gates apply.
-- Example audit only (run separately):
--
-- SELECT source_id, product_scope,
--   max(rights_result) FILTER (WHERE use_case = 'commercial_cat_modelling')
--       AS commercial_use,
--   max(rights_result) FILTER (WHERE use_case = 'automated_api_access')
--       AS api_automation,
--   max(rights_result) FILTER (WHERE use_case = 'internal_neon_source_sample')
--       AS source_byte_storage
-- FROM research.source_usage_rights_v0
-- GROUP BY source_id, product_scope;

-- View is one legal-use dashboard across all existing source candidates.
-- A source with no reviewed use-case is NOT NULL/implicitly allowed:
-- it is explicitly surfaced as "not_checked", and remains not_admitted.
-- The join is product-scoped: distinct release/region rights never overwrite
-- each other, even if they share a generic provider or source_id.
CREATE OR REPLACE VIEW research.source_rights_matrix_v0 AS
SELECT
    c.source_id,
    c.source_name,
    coalesce(r.product_scope, 'no_product_scoped_review') AS product_scope,
    c.commercial_reuse_verdict AS broad_commercial_verdict,
    coalesce(max(r.rights_result) FILTER (
        WHERE r.use_case = 'internal_research'), 'not_checked') AS internal_research,
    coalesce(max(r.rights_result) FILTER (
        WHERE r.use_case = 'commercial_cat_modelling'), 'not_checked') AS commercial_cat_modelling,
    coalesce(max(r.rights_result) FILTER (
        WHERE r.use_case = 'automated_api_access'), 'not_checked') AS automated_api_access,
    coalesce(max(r.rights_result) FILTER (
        WHERE r.use_case = 'internal_neon_metadata'), 'not_checked') AS internal_neon_metadata,
    coalesce(max(r.rights_result) FILTER (
        WHERE r.use_case = 'internal_neon_source_sample'), 'not_checked') AS internal_neon_source_sample,
    coalesce(max(r.rights_result) FILTER (
        WHERE r.use_case = 'external_raw_redistribution'), 'not_checked') AS external_raw_redistribution,
    coalesce(max(r.rights_result) FILTER (
        WHERE r.use_case = 'published_derived_results'), 'not_checked') AS published_derived_results,
    count(r.use_case)::integer AS explicit_use_cases_checked,
    coalesce(s.sample_count, 0)::integer AS research_sample_count,
    c.actual_sample_state,
    c.rights_review_status,
    c.admission_status,
    c.authoritative_url
FROM research.source_candidate_review_v0 AS c
LEFT JOIN research.source_usage_rights_v0 AS r
    ON r.source_id = c.source_id
LEFT JOIN (
    SELECT source_id, count(*) AS sample_count
    FROM research.source_sample_v0
    GROUP BY source_id
) AS s
    ON s.source_id = c.source_id
GROUP BY c.source_id, c.source_name, r.product_scope,
    c.commercial_reuse_verdict, s.sample_count,
    c.actual_sample_state, c.rights_review_status,
    c.admission_status, c.authoritative_url;

-- Usage:
-- SELECT source_id, product_scope, commercial_cat_modelling,
--        automated_api_access, internal_neon_source_sample,
--        research_sample_count, admission_status
-- FROM research.source_rights_matrix_v0
-- WHERE explicit_use_cases_checked > 0
-- ORDER BY source_id;
