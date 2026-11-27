-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Append ONLY a strict public ORIGINAL JRC publisher *instructions HTML*
-- GitHub job receipt, not original CloudFerro/Google TIFF, source ZIP,
-- unbounded 360-tile downloader, numeric pixels, or CAT model admission.
--
-- Actually completed: CI 43609265244, job 132490599513 (success).
-- Timestamp: 2026-11-14T15:16:47.965340+00:00.
-- Original direct HTTP200 response was exactly 11,638 bytes; complete
-- original HTML SHA256 pinned below; response body NOT persisted.
WITH facts AS (
 SELECT
  'ec-jrc.global-surface-water.1984-2024'::text source_id,
  'https://global-surface-water.appspot.com/gsw/Download_Instructions.html'::text url,
  'd6760ede56052bdda84ec5d069bd56ad0dc255ad522a60332b911cab57ccf994'::text full_original_sha,
  'https://global-surface-water.appspot.com/download'::text authoritative_license_url,
  'JRC Global Surface Water v1.5 (1984-2024) corrected 2026-11-10 Occurrence only; excludes unresolved Monthly Recurrence and deprecated v1.4'::text product_rights_scope,
  TIMESTAMPTZ '2026-11-14T15:16:47.965340+00:00' original_get_at
),
receipt AS (
 SELECT f.*,
 jsonb_build_object(
   'profile','jrc_gsw_v15_original_public_publisher_downloader_instructions_github_proof_v0',
   'source_id',f.source_id,
   'publisher_original_instructions_url',f.url,
   'publisher_documentation_original_body_sha256',f.full_original_sha,
   'publisher_documentation_original_body_bytes',11638,
   'publisher_http_status',200,
   'publisher_ec_python_downloader_documented',true,
   'publisher_script_filename','downloadWaterData_Python3_v1_5.py',
   'publisher_cloudferro_aggregated_delivery_root_documented',true,
   'publisher_aggregated_default_tiles',360,
   'aggregated_single_tile_option_documented',false,
   'monthlyhistory_unscoped_is_bulk',true,
   'publisher_exact_original_tile_candidate','https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif',
   'official_html_retrieved_utc','2026-11-14T15:16:47.965340+00:00',
   'actual_github_run_id',43609265244,
   'actual_github_job_id',132490599513,
   'actual_github_head_sha','8548e417827c72386a0b028ed425d1a15832906e',
   'actual_github_job_conclusion','success',
   'official_documentation_get_count',1,
   'offline_source_scoped_tests_passed',8,
   'publisher_python_script_executed',false,
   'cloudferro_original_tile_get_performed',false,
   'anonymous_cloudferro_host_rate_cap_verified',false,
   'original_source_asset_request_allowance',0,
   'raw_original_publisher_html_persisted',false,
   'original_geo_tiff_persisted',false,
   'original_tiff_correction_proved',false,
   'original_raster_pixel_verified',false,
   'scientific_cat_model_input_approved',false,
   'research_only',true
 ) receipt_json
 FROM facts f
),
inserted AS (
 INSERT INTO research.source_sample_v0
 (source_id,source_url,sample_kind,sample_json,provider_response_sha256,
 sample_sha256,provider_license,licence_evidence_url,rights_scope,
 product_version,request_identity,retrieved_at,research_only,
 model_input_approved,source_byte_persistence_authorized)
 SELECT r.source_id,r.url,'public_metadata',r.receipt_json,r.full_original_sha,
 encode(sha256(convert_to(r.receipt_json::text,'UTF8')),'hex'),
 'Official JRC Copernicus attributed reuse: Source: EC JRC/Google. No standalone CloudFerro anonymous machine quota verified.',
 r.authoritative_license_url,
 'Original JRC Python v1.5 DOWNLOAD-INSTRUCTIONS HTML only; source docs advertise 360-tile default; neither JRC Python downloader nor CloudFerro TIFF was executed. Original full page SHA from trusted direct GitHub job, not source pixels.',
 'JRC GSW v1.5 1984-2024, aggregated Occurrence source publisher downloader instructions',
 'GET https://global-surface-water.appspot.com/gsw/Download_Instructions.html; HTTP 200, identity HTML, GitHub run 43609265244 job 132490599513',
 r.original_get_at,TRUE,FALSE,FALSE
 FROM receipt r
 WHERE EXISTS (
  SELECT 1 FROM research.source_sample_v0 previous
  WHERE previous.sample_id=130
   AND previous.source_id=r.source_id
   AND previous.source_url=r.authoritative_license_url
   AND previous.sample_sha256=encode(sha256(convert_to(previous.sample_json::text,'UTF8')),'hex')
   AND previous.research_only IS TRUE
   AND previous.model_input_approved IS FALSE
   AND previous.source_byte_persistence_authorized IS FALSE
   AND previous.sample_json->>'profile'='jrc_gsw_v15_first_party_js_inline_route_github_trusted_html_proof_v0'
   AND previous.sample_json->'source_code_only_original_publisher_inline_js'->>'effective_download_host'='s3.waw4-1.cloudferro.com'
 )
 AND EXISTS (
  SELECT 1 FROM research.source_usage_rights_v0 permissions
  WHERE permissions.source_id=r.source_id
    AND permissions.product_scope=r.product_rights_scope
    AND permissions.use_case='internal_neon_metadata'
    AND permissions.rights_result='allowed'
    AND permissions.scientific_model_admission IS FALSE
    AND permissions.original_asset_admitted IS FALSE
 )
 AND NOT EXISTS (
  SELECT 1 FROM research.source_sample_v0 s
  WHERE s.source_id=r.source_id
    AND s.sample_json->>'profile'='jrc_gsw_v15_original_public_publisher_downloader_instructions_github_proof_v0'
    AND s.sample_json->>'actual_github_run_id'='43609265244'
 )
 RETURNING sample_id,source_id,source_url,sample_kind,
 provider_response_sha256,sample_sha256,research_only,
 model_input_approved,source_byte_persistence_authorized
)
SELECT * FROM inserted ORDER BY sample_id;
