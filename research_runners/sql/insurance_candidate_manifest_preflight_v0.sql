-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- All-candidate rights/API/sample-to-manifest preflight (v0).
-- SELECT only. Run against the authorized Neon insurance DB, explicitly
-- selecting the intended project and branch. No external HTTP, no DB writes.
--
-- Preserve one row per (candidate source_id, exact reviewed product_scope), NOT
-- one row per source_id: multiple scoped product/asset reviews for one source
-- are legitimate and may have different rights or quality status. For example
-- corrected JRC Global Surface Water Occurrence and its broader v1.5 product
-- must not be flattened into one source-wide rights grant. Distinct source_id
-- coverage must still match the canonical landscape count independently.
-- These joins are research
-- evidence ONLY; no recorded licence verdict, probe or sample here is a
-- scientific admission, source-byte publication right, or a legal decision.
-- Provider/download tests for bulk files must not be mislabelled as API tests.
--
-- Example: psql -X -v ON_ERROR_STOP=1 -f research_runners/sql/insurance_candidate_manifest_preflight_v0.sql
WITH sample_evidence AS (
    SELECT source_id,
           COUNT(*)::integer AS samples,
           COUNT(*) FILTER (
               WHERE sample_sha256 =
                     encode(sha256(convert_to(sample_json::text, 'UTF8')), 'hex')
           )::integer AS verified_sample_hashes,
           COUNT(*) FILTER (WHERE sample_kind = 'public_metadata')::integer AS metadata_samples,
           COUNT(*) FILTER (
               WHERE sample_kind IN ('observed_values', 'geospatial_preview')
           )::integer AS observational_previews,
           COUNT(*) FILTER (WHERE model_input_approved IS TRUE)::integer AS approved_model_samples
    FROM research.source_sample_v0
    GROUP BY source_id
),
probe_evidence AS (
    SELECT source_id,
           COUNT(*)::integer AS smoke_receipts,
           COUNT(*) FILTER (
               WHERE http_read_status = 'succeeded' AND json_shape_status = 'pass'
           )::integer AS successful_smoke_receipts,
           COUNT(*) FILTER (
               WHERE strict_repository_runner_executed IS TRUE
           )::integer AS strict_runner_receipts
    FROM research.source_api_smoke_receipt_v0
    GROUP BY source_id
),
candidate_state AS (
    SELECT m.source_id,
           m.source_name,
           m.product_scope,
           m.broad_commercial_verdict,
           m.commercial_cat_modelling,
           m.automated_api_access,
           m.internal_neon_source_sample,
           m.external_raw_redistribution,
           m.published_derived_results,
           m.explicit_use_cases_checked,
           m.admission_status,
           t.model_relevance_priority,
           t.rights_review_status,
           t.actual_sample_state,
           t.next_required_gate,
           COALESCE(c.bounded_original_requests, 0)::integer AS bounded_original_requests,
           COALESCE(c.last_http_read, 'not_tested') AS last_http_read,
           COALESCE(s.samples, 0)::integer AS samples,
           COALESCE(s.verified_sample_hashes, 0)::integer AS verified_sample_hashes,
           COALESCE(s.metadata_samples, 0)::integer AS metadata_samples,
           COALESCE(s.observational_previews, 0)::integer AS observational_previews,
           COALESCE(s.approved_model_samples, 0)::integer AS approved_model_samples,
           COALESCE(p.smoke_receipts, 0)::integer AS smoke_receipts,
           COALESCE(p.successful_smoke_receipts, 0)::integer AS successful_smoke_receipts,
           COALESCE(p.strict_runner_receipts, 0)::integer AS strict_runner_receipts
    FROM research.source_rights_matrix_v0 AS m
    LEFT JOIN research.source_candidate_triage_v0 AS t
        ON t.source_id = m.source_id
    LEFT JOIN research.all_source_api_coverage_v0 AS c
        ON c.source_id = m.source_id AND c.record_type = 'landscape_candidate'
    LEFT JOIN sample_evidence AS s
        ON s.source_id = m.source_id
    LEFT JOIN probe_evidence AS p
        ON p.source_id = m.source_id
    WHERE m.admission_status = 'not_admitted'
)
SELECT *,
       COUNT(*) OVER (PARTITION BY source_id) AS reviewed_product_scopes_for_source,
       CASE WHEN COUNT(*) OVER (PARTITION BY source_id) > 1
            THEN 'MULTIPLE_PRODUCT_SCOPES_REVIEW_EACH'
            ELSE 'ONE_PRODUCT_SCOPE' END AS source_product_scope_gate,
       CASE
           WHEN commercial_cat_modelling = 'prohibited' THEN 'BLOCKED_COMMERCIAL_USE'
           WHEN commercial_cat_modelling = 'conditional' THEN 'REVIEW_COMMERCIAL_CONDITIONS'
           WHEN commercial_cat_modelling = 'allowed' THEN 'PRODUCT_RIGHTS_RECORDED_REVIEW_SCOPE'
           ELSE 'CHECK_EXACT_PRODUCT_COMMERCIAL_RIGHTS'
       END AS commercial_rights_gate,
       CASE
           WHEN automated_api_access = 'allowed' AND strict_runner_receipts > 0
               THEN 'REVIEW_STRICT_RUN_RECEIPTS'
           WHEN automated_api_access = 'prohibited' THEN 'NO_AUTOMATED_API'
           WHEN automated_api_access = 'conditional' THEN 'REVIEW_API_CONDITIONS'
           WHEN automated_api_access = 'allowed' THEN 'NEEDS_STRICT_API_OR_FILE_RECEIPT'
           ELSE 'REVIEW_INTERFACE_AND_AUTOMATION_TERMS'
       END AS access_gate,
       CASE
           WHEN samples = 0 THEN 'NO_SAMPLES_IN_RESEARCH_STORE'
           WHEN verified_sample_hashes <> samples THEN 'INVALID_STORED_SAMPLE_HASH'
           -- A source_id may cover multiple separately licensed product scopes.
           -- Source-wide samples alone cannot prove which exact product was read.
           WHEN COUNT(*) OVER (PARTITION BY source_id) > 1
               THEN 'MULTI_PRODUCT_SAMPLE_SCOPE_NOT_VERIFIED'
           WHEN observational_previews = 0 THEN 'METADATA_ONLY_NO_OBSERVED_VALUES'
           ELSE 'OBSERVED_PREVIEW_RESEARCH_ONLY'
       END AS research_sample_gate,
       'SOURCE_SPECIFIC_SCIENCE_REVIEW_AND_EXACT_ARTIFACT_GATE_REQUIRED'::text
           AS manifest_promotion_gate,
       'SOURCE_ID_AGGREGATE_NOT_PRODUCT_SCOPE_PROOF'::text
           AS sample_evidence_granularity,
       false AS model_input_admitted_by_this_audit
FROM candidate_state
ORDER BY model_relevance_priority NULLS LAST, source_id;
