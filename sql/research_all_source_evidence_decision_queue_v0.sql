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
            AND provider_response_sha256 ~ '^[0-9a-f]{64}
        COUNT(*) FILTER(
          WHERE sample_sha256 IS DISTINCT FROM
            encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
        )::int AS bad_sample_json_hashes,
        COUNT(*) FILTER(WHERE model_input_approved)::int AS sample_model_approvals,
        ARRAY_AGG(sample_id ORDER BY sample_id) AS sample_ids,
        MAX(created_at) AS most_recent_sample
 FROM research.source_sample_v0
 GROUP BY source_id
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
  WHEN last_api_shape_status='inconclusive'
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
  WHEN last_api_shape_status='inconclusive' THEN 1
  WHEN sample_rows=0 AND registry_commercial_verdict='allowed_verified'
    THEN 1
  WHEN sample_rows>0 AND registry_commercial_verdict='allowed_verified'
    THEN 2
  WHEN candidate_snapshot_stale THEN 2
  ELSE 3 END,
 source_id,record_type,source_registry_path;

        )::int AS native_pixel_receipts_classified_preview,
        COUNT(*) FILTER(
          WHERE sample_sha256 IS DISTINCT FROM
            encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
        )::int AS bad_sample_json_hashes,
        COUNT(*) FILTER(WHERE model_input_approved)::int AS sample_model_approvals,
        ARRAY_AGG(sample_id ORDER BY sample_id) AS sample_ids,
        MAX(created_at) AS most_recent_sample
 FROM research.source_sample_v0
 GROUP BY source_id
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
        COALESCE(s.bad_sample_json_hashes,0)::int AS bad_sample_json_hashes,
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
  WHEN last_api_shape_status='inconclusive'
    THEN 'P1_retest_provider_with_trusted_runner'
  WHEN sample_rows=0 AND registry_commercial_verdict='allowed_verified'
    THEN 'P1_review_bounded_first_source_sample'
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
  WHEN last_api_shape_status='inconclusive' THEN 1
  WHEN sample_rows=0 AND registry_commercial_verdict='allowed_verified'
    THEN 1
  WHEN sample_rows>0 AND registry_commercial_verdict='allowed_verified'
    THEN 2
  WHEN candidate_snapshot_stale THEN 2
  ELSE 3 END,
 source_id,record_type,source_registry_path;
