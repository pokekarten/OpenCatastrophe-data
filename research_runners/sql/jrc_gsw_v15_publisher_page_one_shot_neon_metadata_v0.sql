-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- One verified original JRC *publisher HTML* GET; no CloudFerro GET/HEAD/Range,
-- raw HTML body, original catalogue listing or GeoTIFF bytes are stored.
-- Reproduces public successful GitHub Actions job 132438178397, run 43591889218.
-- Schema pre-existing; research metadata-only insertion, zero model approval.
-- Legal metadata right is scoped to GSW v1.5 corrected Occurrence.
-- The original HTML page SHA does NOT equal a selected GeoTIFF or Swift listing SHA.
WITH
facts AS (
 SELECT
  'ec-jrc.global-surface-water.1984-2024'::text AS source_id,
  'https://global-surface-water.appspot.com/download'::text AS source_url,
  '510b4bc273c743b8789afb3ffa57db31077e1f2ac617aca4869870c123995a08'::text AS response_sha,
  'JRC Global Surface Water v1.5 (1984-2024) corrected 2026-11-10 Occurrence only; excludes unresolved Monthly Recurrence and deprecated v1.4'::text AS product_scope,
  'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43591889218/job/132438178397'::text AS job_url,
  '2026-11-14T11:50:14.612603+00:00'::timestamptz AS retrieval_at
),
receipt AS (
 SELECT f.*,
 jsonb_build_object(
  'profile','jrc_gsw_v15_original_publisher_html_one_shot_metadata_v0',
  'source_id',f.source_id,
  'product_version','JRC GSW v1.5 1984-2024 corrected Occurrence publisher documentation',
  'publisher_original_page_url',f.source_url,
  'http_status',200,
  'response_type','text/html',
  'original_publisher_html_response_bytes',85581,
  'original_publisher_html_response_sha256',f.response_sha,
  'original_publisher_http_request_executed',true,
  'published_swift_catalogue_link_url','https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/',
  'published_swift_catalogue_link_found',true,
  'publisher_dataset_rights_statement_found',true,
  'publisher_required_attribution_found',true,
  'november_10_2026_occurrence_correction_announcement_found',true,
  'request_sha256','d2ba746281468b520c5ac3b73db8f40f2d1438d471b2a08c385fbb71b6cfd3f7',
  'github_run_id',43591889218,
  'github_job_id',132438178397,
  'github_head_sha','bf9f5a729bebb069492d1fc94e4d0db6cababd74',
  'github_job_url',f.job_url,
  'github_branch','research/20261113-jrc-gsw-v15-rights-transport-gate',
  'github_event','push',
  'github_conclusion','success',
  'retrieval_utc','2026-11-14T11:50:14.612603+00:00',
  'exact_source_page_get_count',1,
  'no_redirects',true,
  'no_retries',true,
  'no_original_body_stored',true,
  'cloudferro_service_api_terms_reviewed',false,
  'source_original_catalogue_bytes_hashed',false,
  'source_original_catalogue_complete',false,
  'individual_tile_path_in_html_proven',false,
  'individual_tile_original_bytes_hashed',false,
  'individual_tile_post_correction_bytes_verified',false,
  'pixel_values_verified',false,
  'original_asset_admitted',false,
  'scientific_model_admission',false,
  'source_model_input_approved',false,
  'trusted_main_original_probe',false,
  'research_only',true
 ) AS receipt_json
 FROM facts f
)
INSERT INTO research.source_sample_v0 (
  sample_id,source_id,source_url,sample_kind,sample_json,
  provider_response_sha256,sample_sha256,provider_license,
  licence_evidence_url,rights_scope,product_version,request_identity,
  retrieved_at,research_only,model_input_approved,
  source_byte_persistence_authorized
)
SELECT
 (SELECT COALESCE(MAX(sample_id),0)+1 FROM research.source_sample_v0),
 r.source_id,r.source_url,'public_metadata',r.receipt_json,
 r.response_sha,
 encode(sha256(convert_to(r.receipt_json::text,'UTF8')),'hex'),
 'Copernicus JRC GSW data: publisher permits free use with citation and Source: EC JRC/Google attribution',
 r.source_url,
 'Original JRC PUBLISHER HTML page metadata ONLY: exact 85581-byte HTTP200 SHA verified in public GitHub run; publisher advertises public CloudFerro file listing but no original listing or GeoTIFF bytes obtained; automated Swift service rights unknown, no CAT approval.',
 'JRC GSW v1.5 1984-2024 Occurrence, original publisher page 2026-11-14',
 'GET https://global-surface-water.appspot.com/download; Accept: text/html; Accept-Encoding: identity; run 43591889218 job 132438178397',
 r.retrieval_at,true,false,false
FROM receipt r
WHERE EXISTS (
 SELECT 1 FROM research.all_source_inventory_v0 i
 WHERE i.source_id=r.source_id
)
AND EXISTS (
 SELECT 1 FROM research.source_usage_rights_v0 rights
 WHERE rights.source_id=r.source_id
   AND rights.product_scope=r.product_scope
   AND rights.use_case='internal_neon_metadata'
   AND rights.rights_result='allowed'
   AND NOT rights.scientific_model_admission
   AND NOT rights.original_asset_admitted
)
AND NOT EXISTS (
 SELECT 1 FROM research.source_sample_v0 prev
 WHERE prev.source_id=r.source_id
   AND prev.sample_json->>'github_run_id'='43591889218'
)
ON CONFLICT DO NOTHING
RETURNING sample_id,source_id,sample_kind,provider_response_sha256,
          sample_sha256,model_input_approved,source_byte_persistence_authorized;
