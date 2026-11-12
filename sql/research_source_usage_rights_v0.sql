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
