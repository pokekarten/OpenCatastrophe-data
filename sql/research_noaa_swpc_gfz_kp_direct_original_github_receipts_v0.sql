-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only NOAA RTSW and GFZ Kp exact original GitHub-run receipt validation.
-- Pins actual successful provider PR-run/job, source URL, original body SHA,
-- bytes, canonical research JSONB SHA and original technical source shape.
-- This is NOT a licence for polling, not full source-history verification,
-- and NOT scientific validation, CAT model input or insurer replacement TIV.
WITH expected(source_id,sample_id,original_url,original_sha,original_bytes,
              gh_run,gh_job,gh_head) AS (
 VALUES
 ('noaa.swpc.real-time-solar-wind',124::bigint,
 'https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json',
 'bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159',
 1719377::bigint,43489514680::bigint,132106651956::bigint,
 '4a579279e240c9429e6e66360194446c7c6e48b9'),
 ('gfz.geomagnetic-kp',126::bigint,
 'https://kp.gfz.de/app/json/?start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&index=Kp&status=def',
 'f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a',
 361::bigint,43491158483::bigint,132112397671::bigint,
 '17da6a4a3250bc63e7c363a47f74213472196eeb')
),
checked AS (
 SELECT e.*,
 CASE WHEN s.sample_id IS NULL THEN FALSE ELSE
   (s.source_id=e.source_id
    AND s.source_url=e.original_url
    AND s.provider_response_sha256=e.original_sha
    AND s.sample_kind='public_metadata'
    AND s.research_only IS TRUE
    AND s.model_input_approved IS FALSE
    AND s.source_byte_persistence_authorized IS FALSE
    AND s.sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
    AND s.sample_json->>'source_id'=e.source_id
    AND s.sample_json->>'original_source_url'=e.original_url
    AND s.sample_json->>'github_run_id'=e.gh_run::text
    AND s.sample_json->>'github_job_id'=e.gh_job::text
    AND s.sample_json->>'github_head_sha'=e.gh_head
    AND s.sample_json->>'http_status'='200'
    AND (s.sample_json->>'original_response_bytes')::bigint=e.original_bytes
    AND EXISTS(
       SELECT 1 FROM research.source_usage_rights_v0 r
       WHERE r.source_id=e.source_id
         AND r.use_case='internal_neon_metadata'
         AND r.rights_result='allowed'
         AND r.scientific_model_admission IS FALSE)
    AND CASE WHEN e.source_id='noaa.swpc.real-time-solar-wind' THEN
       (s.sample_json->>'profile'='noaa-swpc-rtsw-2026-direct-public-github-source-metadata-v1'
        AND s.sample_json->>'verified_shape'='noaa_swpc_rtsw_mag_2026_multispacecraft'
        AND s.sample_json->>'response_type'='application/json'
        AND s.sample_json->>'original_provider_response_sha256'=e.original_sha
        AND s.sample_json->>'request_sha256'='9c8cff6ed4aa0ba97edb2a8d179728c5696e446c25437fbf9dfc758d20ac31d2'
        AND s.sample_json->>'probe_code_sha256'='80b80b5b214c471eb43ae3d303e95748afb7be624dea351f663a057f52333281'
        AND s.sample_json->>'access_contract_sha256'='28a80ab81521d4b4a3b5332cfd0d38343b7b41bdb9168cc8833c8aa0320292ca'
        AND s.sample_json->>'source_is_rolling'='true'
        AND s.sample_json->>'rolling_window_complete'='false'
        AND s.sample_json->>'spacecraft_identity_fields_present'='true'
        AND s.sample_json->>'active_stream_flags_typed'='true'
        AND s.sample_json->>'magnetic_reading_present_in_original_response'='true'
        AND s.sample_json->>'sensor_lineage_verified'='false'
        AND s.sample_json->>'scientific_values_verified'='false'
        AND s.sample_json->>'model_input_approved'='false'
        AND s.sample_json->>'provider_body_or_sensor_rows_stored'='false'
        AND s.sample_json->>'raw_source_redistribution_authorized'='false')
      WHEN e.source_id='gfz.geomagnetic-kp' THEN
       (s.sample_json->>'profile'='strict_public_original_pr_branch_github_receipt_metadata_v1'
        AND s.sample_json->>'product_version'='GFZ definitive Kp 2024-01-01 8x3h'
        AND s.sample_json->>'original_response_sha256'=e.original_sha
        AND s.sample_json->>'request_sha256'='f766594d3b83d42a9a16ef247c7119f1a435a2ea00d5c004876e4cfab3cd7dfd'
        AND s.sample_json->>'runner_code_sha256'='423e21bda179d5664a74f3c3bbe2a5e6d955aa4386305545d292a627b191affa'
        AND s.sample_json->>'code_or_access_contract_sha256'='1c57d8e1147c511e14af0d9468b4a55fc80c5000c3c441b30660679673f1c02d'
        AND s.sample_json->>'github_pr_branch_proof'='true'
        AND s.sample_json->>'trusted_main_run'='false'
        AND s.sample_json->>'original_response_shape_verified'='true'
        AND s.sample_json->>'original_provider_body_stored'='false'
        AND s.sample_json->>'scientific_values_verified'='false'
        AND s.sample_json->>'insurer_cat_model_admitted'='false'
        AND s.sample_json->>'full_source_sha256_verified'='false')
      ELSE FALSE END
   ) END AS technical_direct_source_receipt_ok
 FROM expected e LEFT JOIN research.source_sample_v0 s ON s.sample_id=e.sample_id
)
SELECT source_id,sample_id,original_url,original_sha,original_bytes,
       gh_run AS trusted_github_run_id,gh_job AS trusted_github_job_id,
       CASE WHEN technical_direct_source_receipt_ok
         THEN 'DIRECT_ORIGINAL_HTTP_SHAPE_RESEARCH_ONLY_NOT_MODEL_ADMITTED'
         ELSE 'BLOCKED_MISSING_INVALID_TECHNICAL_ORIGINAL_SOURCE_RECEIPT'
       END AS research_gate
FROM checked ORDER BY source_id;
