-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Full 707-entry canonical queue + independently source-verified public
-- GitHub PR-BRANCH originals, without rewriting historical API evidence.
-- The embedded baseline is frozen from #1536 (HEAD
-- 71eaa025ebd497d197bed43620b6c4d173c3224e) for a read-only stand-alone
-- execution; future edits in that PR must be reconciled independently.
-- Verified direct provider GET != first-party trusted main != CAT admission.
-- Fixed 3 exact response SHA/run/job/commit identities prevent a generic JSON
-- smoke, a wrong URL or a plausible-looking metadata object from gating.
-- Deliberately never changes restricted/prohibited source rights priorities.
-- JRC GSW 1.5 exception is independently documented-only in PR #1533
-- HEAD e72f8ab853f8b9d4639c0173bb8e70c4f16b53bd; free dataset use and
-- the publisher Python downloader do NOT authorize unconstrained CloudFerro
-- service polling or assert source-native 2026-11-10 corrected pixels.
--
WITH original_prioritized AS (
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
 source_id,record_type,source_registry_path
),
expected_exact(source_id, exact_source_url, github_run_id, github_job_id,
               github_head_sha, original_response_sha256, request_sha256,
               runner_code_sha256, exact_product_rights_scope) AS (
 VALUES
  ('dwd.radklim.rw.v2017.002', 'https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/reproc/2017_002/netCDF/supplement/RW2017.002_2021_netcdf_supplement.tar.gz', 43488656039::bigint, 132103695178::bigint, '01ab7b83d1765fb6bbe590ad772880c65d5e43c9', '741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867', '76b410d2c64e3147bb6932df07c860455d04e097d1ec3fe179ea16a472cb28c3', '635be219e2faf2b2e680f5a3d0f8d0b32cb3f80ba19440f38c6bb68b9672bd71', 'DWD RADKLIM RW2017.002 hourly gauge-corrected precipitation product'),
  ('noaa.swpc.real-time-solar-wind', 'https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json', 43489514680::bigint, 132106651956::bigint, '4a579279e240c9429e6e66360194446c7c6e48b9', 'bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159', '9c8cff6ed4aa0ba97edb2a8d179728c5696e446c25437fbf9dfc758d20ac31d2', '80b80b5b214c471eb43ae3d303e95748afb7be624dea351f663a057f52333281', 'NOAA SWPC RTSW 2026 rtsw_mag_1m.json multi-spacecraft rolling product'),
  ('gfz.geomagnetic-kp', 'https://kp.gfz.de/app/json/?start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&index=Kp&status=def', 43491158483::bigint, 132112397671::bigint, '17da6a4a3250bc63e7c363a47f74213472196eeb', 'f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a', 'f766594d3b83d42a9a16ef247c7119f1a435a2ea00d5c004876e4cfab3cd7dfd', '423e21bda179d5664a74f3c3bbe2a5e6d955aa4386305545d292a627b191affa', 'GFZ definitive Kp index (2024-01-01; not GFZ nowcast or other providers)')
),
original_branch_evidence AS (
 SELECT s.source_id, s.sample_id, e.github_run_id, e.github_job_id,
        e.github_head_sha,
        s.provider_response_sha256 AS verified_original_response_sha256,
        s.retrieved_at
 FROM research.source_sample_v0 s
 JOIN expected_exact e
   ON e.source_id=s.source_id
  AND e.exact_source_url=s.source_url
  AND e.original_response_sha256=s.provider_response_sha256
 WHERE EXISTS (
   SELECT 1 FROM research.source_usage_rights_v0 rights
   WHERE rights.source_id=s.source_id
     AND rights.product_scope=e.exact_product_rights_scope
     AND rights.use_case='internal_neon_metadata'
     AND rights.rights_result='allowed'
     AND rights.scientific_model_admission=false
     AND rights.original_asset_admitted=false
 )
 AND s.sample_kind='public_metadata'
   AND s.sample_json->>'profile' IN
     ('strict_public_original_pr_branch_github_receipt_metadata_v1',
      'noaa-swpc-rtsw-2026-direct-public-github-source-metadata-v1')
   AND s.sample_sha256 =
       encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
   AND COALESCE(s.sample_json->>'original_response_sha256',
                s.sample_json->>'original_provider_response_sha256')
       = e.original_response_sha256
   AND s.sample_json->>'github_run_id'=e.github_run_id::text
   AND s.sample_json->>'github_job_id'=e.github_job_id::text
   AND s.sample_json->>'github_head_sha'=e.github_head_sha
   AND s.sample_json->>'github_run_url'=
     'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/'||
       e.github_run_id::text
   AND s.sample_json->>'request_sha256'=e.request_sha256
   AND COALESCE(s.sample_json->>'runner_code_sha256',
                s.sample_json->>'probe_code_sha256')=e.runner_code_sha256
   AND s.research_only
   AND NOT s.model_input_approved
   AND NOT s.source_byte_persistence_authorized
   AND NOT COALESCE((s.sample_json->>'insurer_cat_model_admitted')::bool,false)
   AND NOT COALESCE((s.sample_json->>'model_input_approved')::bool,false)
   AND NOT COALESCE((s.sample_json->>'trusted_main_run')::bool,false)
   AND NOT COALESCE((s.sample_json->>'original_provider_body_stored')::bool,false)
   AND NOT COALESCE((s.sample_json->>'provider_body_or_sensor_rows_stored')::bool,false)
),
one_per_source AS (
 SELECT source_id, MIN(sample_id)::bigint AS pr_branch_metadata_sample_id,
        COUNT(*)::int AS independently_verified_original_pr_branch_samples,
        MAX(retrieved_at) AS last_original_pr_branch_observed_at
 FROM original_branch_evidence
 GROUP BY source_id
)
SELECT
 q.*,
 COALESCE(v.independently_verified_original_pr_branch_samples,0)::int
    AS verified_original_pr_branch_metadata_receipts,
 v.pr_branch_metadata_sample_id,
 v.last_original_pr_branch_observed_at,
 (v.source_id IS NOT NULL) AS exact_original_public_pr_branch_proof_verified,
 (COALESCE(q.last_api_shape_status='inconclusive',false)
   AND v.source_id IS NOT NULL)
    AS older_intermediary_inconclusive_superseded_for_one_original_proof,
 q.next_action_priority AS historical_queue_priority,
 CASE
   -- Never let independent PR-branch proof override source integrity,
   -- prohibition, restriction or an admitted manifest review.
   WHEN q.bad_sample_json_hashes>0
      OR q.registry_commercial_verdict IN ('prohibited','restricted')
      OR q.record_type='admitted_manifest'
      THEN q.next_action_priority
   WHEN q.source_id='ec-jrc.global-surface-water.1984-2024'
      AND q.record_type='landscape_candidate'
      AND q.registry_commercial_verdict='allowed_verified'
      AND q.sample_rows=0
      THEN 'P1_review_cloudferro_service_terms_before_original_occurrence_sample'
   WHEN q.last_api_shape_status='inconclusive' AND v.source_id IS NOT NULL
      THEN 'P2_review_product_rights_and_science_after_original_probe'
   ELSE q.next_action_priority
 END AS evidence_adjusted_next_action_priority,
 -- Audit the distinction directly; a PR-branch receipt is never a main run.
 false AS newly_grants_trusted_main_status,
 false AS newly_grants_model_input_approval
FROM original_prioritized q
LEFT JOIN one_per_source v ON v.source_id=q.source_id
ORDER BY
 CASE
   WHEN q.bad_sample_json_hashes>0 THEN 0
   WHEN q.registry_commercial_verdict='prohibited' THEN 5
   WHEN q.registry_commercial_verdict='restricted' THEN 4
   WHEN q.record_type='admitted_manifest' THEN 6
   WHEN q.last_api_shape_status='inconclusive' AND v.source_id IS NOT NULL THEN 2
   WHEN q.next_action_priority LIKE 'P1_%' THEN 1
   WHEN q.next_action_priority LIKE 'P2_%' THEN 2
   ELSE 3
 END,
 q.source_id,q.record_type,q.source_registry_path;
