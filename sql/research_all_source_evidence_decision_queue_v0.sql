-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only research triage of all canonical registered sources.
-- Execute SELECT only in the separate authorized insurance-risk-core Neon DB.
-- No schema changes, provider calls, source bytes, sample writes, API
-- entitlements, model approvals or publication rights are implied.
--
-- Output: one record per canonical inventory *entry*, not per distinct source
-- ID: 692 landscape candidates + 15 manifests = 707 inventory entries
-- in the 2026-11-13 snapshot. Exactly one source ID can occur in two
-- inventory types: copernicus.cems.gfm.v4.1.1.
--
-- Source-sample and source-API ledgers are independent of the older candidate
-- actual_sample_state snapshot. Do not interpret that snapshot as live data.
-- The external API-smoke ledger intentionally enforces
-- CHECK (NOT strict_repository_runner_executed), so api_totals.strict_runner_receipts
-- is NOT the count of actual GitHub direct original source proofs.
-- Separate append-only research.sample metadata rows with individually
-- successful GitHub original-run/job identities and provider SHA/URL evidence
-- are counted separately; counts are OBSERVATIONS, not distinct sources,
-- licence or admission permissions. All CAT model approvals remain false.
-- Additionally count TWO already-observed, original-source GitHub PR-branch
-- receipts: NOAA SWPC rolling magnetometer (#124) and GFZ definitive-day
-- Kp (#126), with independent hashes, source-specific status and no model
-- admission. Their source-specific metadata schema differs from CBS; neither
-- has a trusted-main-run claim. SWPC still has CONDITIONAL automated API
-- rights and unresolved continuous spacecraft/sensor lineage. A former
-- inconclusive external smoke must not overrule a separate successful direct
-- technical proof; missing direct proof still requires retest.
-- The one PEGELONLINE access-contract alias is normalized only for the API
-- receipt join. Individual rights use cases remain product-scoped: aggregate
-- lists are evidence, never a blanket rights entitlement across all versions.
--
-- PostgreSQL + pgcrypto sha256(bytea); exact canonical JSONB digest is checked
-- rather than copying or reading provider data outside the research database.
WITH
sample_evidence AS (
 SELECT source_id,
        COUNT(*)::int AS sample_rows,
        COUNT(*) FILTER(WHERE sample_kind='public_metadata')::int AS metadata_samples,
        COUNT(*) FILTER(WHERE sample_kind='observed_values')::int AS native_or_observed_value_samples,
        COUNT(*) FILTER(WHERE sample_kind='geospatial_preview')::int AS preview_samples,
        COUNT(*) FILTER (
          WHERE sample_kind='geospatial_preview'
            AND sample_json->>'sample_subtype' LIKE 'native_geotiff_lzw_window%'
            AND (sample_json->>'native_pixels_verified'='true'
                 OR sample_json->>'native_class_values_decoded'='true')
            AND provider_response_sha256 ~ '^[0-9a-f]{64}$'
        )::int AS native_pixel_receipts_classified_preview,
        COUNT(*) FILTER(
          WHERE sample_sha256 IS DISTINCT FROM
            encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
        )::int AS bad_sample_json_hashes,
        COUNT(*) FILTER(WHERE sample_kind='public_metadata'
            AND sample_json->>'strict_repository_runner_executed'='true'
            AND sample_json->>'profile' IN (
              'oc-cbs-83673ned-2025-github-trusted-original-direct-https-proof-v0',
              'oc-cbs-github-trusted-direct-original-20261113-v0',
              'oc-cbs-83673ned-2026-regional-two-github-trusted-original-direct-v0'
            )
            AND (sample_json->>'github_job_conclusion'='success'
                 OR sample_json->>'trusted_github_job_conclusion'='success'
                 OR sample_json->>'trusted_github_ci_job_conclusion'='success')
            AND sample_json->>'model_input_approved'='false'
            AND research_only IS TRUE
            AND model_input_approved IS FALSE
            AND source_byte_persistence_authorized IS FALSE
            AND sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex'))::int
          AS recorded_direct_github_original_proof_metadata_rows,
        COUNT(DISTINCT source_url) FILTER(WHERE sample_kind='public_metadata'
            AND sample_json->>'strict_repository_runner_executed'='true'
            AND sample_json->>'profile' IN (
              'oc-cbs-83673ned-2025-github-trusted-original-direct-https-proof-v0',
              'oc-cbs-github-trusted-direct-original-20261113-v0',
              'oc-cbs-83673ned-2026-regional-two-github-trusted-original-direct-v0'
            )
            AND (sample_json->>'github_job_conclusion'='success'
                 OR sample_json->>'trusted_github_job_conclusion'='success'
                 OR sample_json->>'trusted_github_ci_job_conclusion'='success')
            AND sample_json->>'model_input_approved'='false'
            AND research_only IS TRUE
            AND model_input_approved IS FALSE
            AND source_byte_persistence_authorized IS FALSE
            AND sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex'))::int
          AS recorded_direct_github_original_exact_urls,
        COUNT(*) FILTER(WHERE model_input_approved)::int AS sample_model_approvals,
        ARRAY_AGG(sample_id ORDER BY sample_id) AS sample_ids,
        MAX(created_at) AS most_recent_sample
 FROM research.source_sample_v0
 GROUP BY source_id
),
non_cbs_github_originals AS (
 SELECT s.source_id,
   COUNT(*)::int AS verified_additional_github_original_rows,
   COUNT(DISTINCT s.source_url)::int AS verified_additional_github_exact_urls
 FROM research.source_sample_v0 s
 WHERE s.sample_kind='public_metadata' AND s.research_only IS TRUE
   AND s.model_input_approved IS FALSE
   AND s.source_byte_persistence_authorized IS FALSE
   AND s.sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
   AND EXISTS(
      SELECT 1 FROM research.source_usage_rights_v0 rights
      WHERE rights.source_id=s.source_id AND rights.use_case='internal_neon_metadata'
        AND rights.rights_result='allowed' AND rights.scientific_model_admission IS FALSE
   )
   AND s.sample_json->>'source_id'=s.source_id
   AND s.sample_json->>'original_source_url'=s.source_url
   AND s.sample_json->>'http_status'='200'
   AND CASE
     WHEN s.source_id='noaa.swpc.real-time-solar-wind' THEN
       s.sample_id=124
       AND s.source_url='https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json'
       AND s.provider_response_sha256='bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159'
       AND s.sample_json->>'original_provider_response_sha256'=s.provider_response_sha256
       AND s.sample_json->>'original_response_bytes'='1719377'
       AND s.sample_json->>'github_run_id'='43489514680'
       AND s.sample_json->>'github_job_id'='132106651956'
       AND s.sample_json->>'github_head_sha'='4a579279e240c9429e6e66360194446c7c6e48b9'
       AND s.sample_json->>'profile'='noaa-swpc-rtsw-2026-direct-public-github-source-metadata-v1'
       AND s.sample_json->>'verified_shape'='noaa_swpc_rtsw_mag_2026_multispacecraft'
       AND s.sample_json->>'probe_code_sha256'='80b80b5b214c471eb43ae3d303e95748afb7be624dea351f663a057f52333281'
       AND s.sample_json->>'request_sha256'='9c8cff6ed4aa0ba97edb2a8d179728c5696e446c25437fbf9dfc758d20ac31d2'
       AND s.sample_json->>'source_is_rolling'='true'
       AND s.sample_json->>'rolling_window_complete'='false'
       AND s.sample_json->>'scientific_values_verified'='false'
       AND s.sample_json->>'sensor_lineage_verified'='false'
       AND s.sample_json->>'provider_body_or_sensor_rows_stored'='false'
       AND s.sample_json->>'model_input_approved'='false'
     WHEN s.source_id='gfz.geomagnetic-kp' THEN
       s.sample_id=126
       AND s.source_url='https://kp.gfz.de/app/json/?start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&index=Kp&status=def'
       AND s.provider_response_sha256='f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a'
       AND s.sample_json->>'original_response_sha256'=s.provider_response_sha256
       AND s.sample_json->>'original_response_bytes'='361'
       AND s.sample_json->>'github_run_id'='43491158483'
       AND s.sample_json->>'github_job_id'='132112397671'
       AND s.sample_json->>'github_head_sha'='17da6a4a3250bc63e7c363a47f74213472196eeb'
       AND s.sample_json->>'profile'='strict_public_original_pr_branch_github_receipt_metadata_v1'
       AND s.sample_json->>'product_version'='GFZ definitive Kp 2024-01-01 8x3h'
       AND s.sample_json->>'runner_code_sha256'='423e21bda179d5664a74f3c3bbe2a5e6d955aa4386305545d292a627b191affa'
       AND s.sample_json->>'request_sha256'='f766594d3b83d42a9a16ef247c7119f1a435a2ea00d5c004876e4cfab3cd7dfd'
       AND s.sample_json->>'github_pr_branch_proof'='true'
       AND s.sample_json->>'original_response_shape_verified'='true'
       AND s.sample_json->>'scientific_values_verified'='false'
       AND s.sample_json->>'insurer_cat_model_admitted'='false'
       AND s.sample_json->>'original_provider_body_stored'='false'
     ELSE FALSE END
 GROUP BY s.source_id
),
api_norm AS (
 SELECT CASE WHEN source_id='wsv.pegelonline.rest-v2.dresden'
             THEN 'wsv.pegelonline.elbe-dresden-discharge.2020-2023'
             ELSE source_id END AS registry_source_id,
        receipt_id,checked_at,http_read_status,json_shape_status,
        strict_repository_runner_executed,endpoint_url
 FROM research.source_api_smoke_receipt_v0
),
api_totals AS (
 SELECT registry_source_id,
        COUNT(*)::int AS api_smoke_receipts,
        COUNT(*) FILTER(WHERE http_read_status='succeeded')::int
          AS api_smoke_successes,
        COUNT(*) FILTER(WHERE json_shape_status='inconclusive')::int
          AS api_smoke_inconclusive,
        COUNT(*) FILTER(WHERE strict_repository_runner_executed)::int
          AS strict_runner_receipts
 FROM api_norm
 GROUP BY registry_source_id
),
api_recent AS (
 SELECT DISTINCT ON (registry_source_id)
        registry_source_id,
        endpoint_url AS last_exact_api_endpoint,
        checked_at AS last_api_checked_at,
        http_read_status AS last_api_read_status,
        json_shape_status AS last_api_shape_status
 FROM api_norm
 ORDER BY registry_source_id,checked_at DESC,receipt_id DESC
),
rights_evidence AS (
 SELECT source_id,
        COUNT(*)::int AS use_case_rights_records,
        COUNT(DISTINCT product_scope)::int AS reviewed_product_scopes,
        STRING_AGG(DISTINCT product_scope||' => '||rights_result,'; '
                   ORDER BY product_scope||' => '||rights_result)
            FILTER(WHERE use_case='commercial_cat_modelling')
            AS scoped_commercial_results,
        STRING_AGG(DISTINCT rights_result,', ' ORDER BY rights_result)
            FILTER(WHERE use_case='automated_api_access')
            AS scoped_api_automation_results
 FROM research.source_usage_rights_v0
 GROUP BY source_id
),
joined AS (
 SELECT i.record_type,i.source_id,i.source_name,i.source_registry_path,
        i.original_rights_review_status AS landscape_rights_review,
        i.commercial_reuse_verdict AS registry_commercial_verdict,
        i.actual_sample_state AS candidate_snapshot_sample_state,
        i.admission_status AS registry_admission_status,
        COALESCE(s.sample_rows,0)::int AS sample_rows,
        COALESCE(s.metadata_samples,0)::int AS metadata_samples,
        COALESCE(s.native_or_observed_value_samples,0)::int
          AS native_or_observed_value_samples,
        COALESCE(s.preview_samples,0)::int AS preview_samples,
        COALESCE(s.native_pixel_receipts_classified_preview,0)::int
          AS native_pixel_receipts_classified_preview,
        COALESCE(s.bad_sample_json_hashes,0)::int AS bad_sample_json_hashes,
        (COALESCE(s.recorded_direct_github_original_proof_metadata_rows,0)
         + COALESCE(d.verified_additional_github_original_rows,0))::int
          AS recorded_direct_github_original_proof_metadata_rows,
        (COALESCE(s.recorded_direct_github_original_exact_urls,0)
         + COALESCE(d.verified_additional_github_exact_urls,0))::int
          AS recorded_direct_github_original_exact_urls,
        COALESCE(s.sample_model_approvals,0)::int AS sample_model_approvals,
        s.sample_ids,s.most_recent_sample,
        COALESCE(a.api_smoke_receipts,0)::int AS api_smoke_receipts,
        COALESCE(a.api_smoke_successes,0)::int AS api_smoke_successes,
        COALESCE(a.api_smoke_inconclusive,0)::int AS api_smoke_inconclusive,
        COALESCE(a.strict_runner_receipts,0)::int AS strict_runner_receipts,
        r.last_exact_api_endpoint,r.last_api_checked_at,
        r.last_api_read_status,r.last_api_shape_status,
        COALESCE(e.use_case_rights_records,0)::int AS use_case_rights_records,
        COALESCE(e.reviewed_product_scopes,0)::int AS reviewed_product_scopes,
        e.scoped_commercial_results,e.scoped_api_automation_results,
        (COALESCE(s.sample_rows,0)>0 AND i.actual_sample_state='not_collected')
          AS candidate_snapshot_stale
 FROM research.all_source_inventory_v0 i
 LEFT JOIN sample_evidence s ON s.source_id=i.source_id
 LEFT JOIN non_cbs_github_originals d ON d.source_id=i.source_id
 LEFT JOIN api_totals a ON a.registry_source_id=i.source_id
 LEFT JOIN api_recent r ON r.registry_source_id=i.source_id
 LEFT JOIN rights_evidence e ON e.source_id=i.source_id
)
SELECT *,
 CASE
  WHEN bad_sample_json_hashes>0
    THEN 'P0_sample_integrity_failure'
  WHEN registry_commercial_verdict='prohibited'
    THEN 'P5_commercial_use_prohibited'
  WHEN registry_commercial_verdict='restricted'
    THEN 'P4_commercial_use_restricted'
  WHEN record_type='admitted_manifest'
    THEN 'P6_existing_manifest_validate_separately'
  WHEN last_api_shape_status='inconclusive' AND recorded_direct_github_original_exact_urls=0
    THEN 'P1_retest_provider_with_trusted_runner'
  WHEN sample_rows=0 AND registry_commercial_verdict='allowed_verified'
    THEN 'P1_review_bounded_first_source_sample'
  WHEN native_pixel_receipts_classified_preview>0
    AND registry_commercial_verdict='allowed_verified'
    THEN 'P2_validate_native_pixel_preview_provenance'
  WHEN sample_rows>0 AND native_or_observed_value_samples=0
    AND registry_commercial_verdict='allowed_verified'
    THEN 'P2_review_native_observation_sample'
  WHEN native_or_observed_value_samples>0
    AND registry_commercial_verdict='allowed_verified'
    THEN 'P2_scientific_native_sample_validation'
  WHEN candidate_snapshot_stale
    THEN 'P2_reconcile_candidate_snapshot'
  WHEN registry_commercial_verdict='unresolved'
    THEN 'P3_review_rights_and_exact_access'
  ELSE 'P3_review_source_specific_next_gate'
 END AS next_action_priority
FROM joined
ORDER BY
 CASE
  WHEN bad_sample_json_hashes>0 THEN 0
  WHEN registry_commercial_verdict='prohibited' THEN 5
  WHEN registry_commercial_verdict='restricted' THEN 4
  WHEN record_type='admitted_manifest' THEN 6
  WHEN last_api_shape_status='inconclusive' AND recorded_direct_github_original_exact_urls=0 THEN 1
  WHEN sample_rows=0 AND registry_commercial_verdict='allowed_verified'
    THEN 1
  WHEN sample_rows>0 AND registry_commercial_verdict='allowed_verified'
    THEN 2
  WHEN candidate_snapshot_stale THEN 2
  ELSE 3 END,
 source_id,record_type,source_registry_path;
