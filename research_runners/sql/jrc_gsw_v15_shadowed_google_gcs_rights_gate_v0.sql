-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Append-only, product-specific research RIGHTS TRIAGE for the overwritten
-- Google Storage GSW v1.5 Occurrence TIFF candidate on JRC publisher HTML.
-- This is NOT a credential grant, original TIFF GET, licence to poll, or
-- scientific model admission. Data product reuse and actual GCS object
-- service access/version are independent.
--
-- Grounded by original JRC publisher HTML SHA from GitHub run 43606072894
-- and metadata-only Neon sample #130, not raw publisher HTML or TIFF bytes.
WITH facts AS (
 SELECT
   'ec-jrc.global-surface-water.1984-2024'::text AS source_id,
   'JRC GSW v1.5 1984-2024 shadowed Google water-world GeoTIFF Occurrence candidate (NOT current publisher tile-click CloudFerro route; 2026-11-10 correction unverified)'::text AS product_scope,
   'https://global-surface-water.appspot.com/download'::text AS publisher_evidence_url,
   'https://docs.cloud.google.com/storage/docs/access-public-data'::text AS generic_gcs_public_object_doc,
   'https://storage.googleapis.com/water-world/download2024/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif'::text AS candidate_file_url
),
decisions(use_case,rights_result,evidence_url,rationale) AS (
 VALUES
 ('automated_api_access','unknown',
  'https://docs.cloud.google.com/storage/docs/access-public-data',
  'Google generally permits anonymous GET of an actually public GCS object, but THIS candidate GSW v1.5 source URL is overwritten in the JRC publisher JavaScript; current public object status, revised November 2026 pixel identity, request quota, Range behaviour and commercial unattended usage have NOT been verified. Approved original asset requests remain zero.'),
 ('commercial_cat_modelling','unknown',
  'https://global-surface-water.appspot.com/download',
  'The underlying JRC Copernicus dataset permits attributed commercial reuse. This alternate shadowed GCS object is NOT verified as the currently corrected original JRC v1.5 asset and has NO CAT flood hazard, loss, insured TIV or scientific model admission. Object-specific commercial readiness unknown.'),
 ('internal_neon_metadata','allowed',
  'https://global-surface-water.appspot.com/download',
  'May record ONLY a derivative metadata link and original JRC publisher HTML JavaScript source-route receipt #130, not source Google TIFF bytes, pixel/raster data or a Google object full-body checksum. Product identity remains unverified.'),
 ('internal_neon_source_sample','unknown',
  'https://global-surface-water.appspot.com/download',
  'Raw Google TIFF source sample NOT authorised: this overwritten Google object has no proven current publication vintage, verified original body SHA, corrected 2026-11-10 occurrence pixels, access policy or scientific admission.'),
 ('internal_research','conditional',
  'https://global-surface-water.appspot.com/download',
  'Publisher JRC dataset is generally reusable with attribution; only offline metadata comparison of GCS candidate versus active CloudFerro path is permitted until object identity/transport and corrected vintage are verified.'),
 ('published_derived_results','conditional',
  'https://global-surface-water.appspot.com/download',
  'May publish original JRC attributed source-route research metadata with Source: EC JRC/Google; no Google object numeric values or inferred insurer CAT loss results, since no original raster was acquired.'),
 ('external_raw_redistribution','unknown',
  'https://global-surface-water.appspot.com/download',
  'No original Google v1.5 TIFF bytes have been seen or verified; publisher dataset reuse rights do not prove this shadowed object is the corrected original asset or that raw byte redistribution is authorised under its host policy.')
),
inserted AS (
 INSERT INTO research.source_usage_rights_v0 (
  source_id,product_scope,use_case,rights_result,evidence_url,
  evidence_observed_on,rationale,scientific_model_admission,original_asset_admitted
 )
 SELECT f.source_id,f.product_scope,d.use_case,d.rights_result,d.evidence_url,
        DATE '2026-11-14',d.rationale,FALSE,FALSE
 FROM facts f CROSS JOIN decisions d
 WHERE EXISTS (
  SELECT 1 FROM research.source_sample_v0 sample
  WHERE sample.sample_id=130 AND sample.source_id=f.source_id
    AND sample.source_url=f.publisher_evidence_url
    AND sample.sample_kind='public_metadata'
    AND sample.sample_sha256=encode(sha256(convert_to(sample.sample_json::text,'UTF8')),'hex')
    AND sample.research_only IS TRUE
    AND sample.model_input_approved IS FALSE
    AND sample.source_byte_persistence_authorized IS FALSE
    AND sample.sample_json->>'profile'='jrc_gsw_v15_first_party_js_inline_route_github_trusted_html_proof_v0'
    AND sample.sample_json->>'verified_trusted_github_ci_run'='43606072894'
    AND sample.sample_json->>'verified_trusted_github_html_job'='132480916985'
    AND sample.sample_json->'source_code_only_original_publisher_inline_js'->>'candidate_google_v15_tile_url_from_overwritten_JS_only'=f.candidate_file_url
    AND sample.sample_json->'source_code_only_original_publisher_inline_js'->>'google_v15_candidate_overwritten_before_tile_links'='true'
    AND sample.sample_json->>'source_original_data_asset_requests'='0'
    AND sample.sample_json->>'model_input_approved'='false'
 )
 AND EXISTS (
  SELECT 1 FROM research.source_usage_rights_v0 publisher_rights
  WHERE publisher_rights.source_id=f.source_id
    AND publisher_rights.use_case='internal_neon_metadata'
    AND publisher_rights.rights_result='allowed'
    AND publisher_rights.scientific_model_admission IS FALSE
    AND publisher_rights.original_asset_admitted IS FALSE
    AND publisher_rights.evidence_url=f.publisher_evidence_url
 )
 AND NOT EXISTS (
  SELECT 1 FROM research.source_usage_rights_v0 existing
  WHERE existing.source_id=f.source_id
    AND existing.product_scope=f.product_scope
    AND existing.use_case=d.use_case
 )
 RETURNING source_id,product_scope,use_case,rights_result,
           scientific_model_admission,original_asset_admitted
)
SELECT * FROM inserted ORDER BY use_case;
