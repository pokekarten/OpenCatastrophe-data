-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- HydroATLAS v1, Figshare 9890531 v1: independently repeatable, read-only
-- research sample #70 metadata/rights/lineage gate in authorized Neon.
-- Run each SELECT independently. No database writes, provider requests or assets.
-- Exact original metadata SHA compared against the stored receipt and an
-- independent 2026-11-15 intermediary original-body replay (7212 bytes).
-- Intermediary does NOT expose HTTP status, redirect or header evidence:
-- never claim trusted strict T1, GIS T3, original asset hashes or admission.
-- Official product https://doi.org/10.6084/m9.figshare.9890531.v1
-- Collective CC BY 4.0; HydroATLAS attributes may carry CC BY or ODbL.
-- Sample #70 is NOT a full original GIS file or scientific CAT model input.

SELECT sample_id, source_id,
 (source_id='hydrosheds.hydroatlas.v1'
   AND sample_kind='public_metadata'
   AND product_version='HydroATLAS version 1.0, Figshare article 9890531 v1') AS product_ok,
 (provider_response_sha256='87ed43e0dd02e6fba1228566878b17e1ad35d9a903f1ef4d26eb9dc2a9a45e38'
   AND sample_json->>'original_metadata_response_sha256'=provider_response_sha256
   AND sample_json->>'original_metadata_response_bytes'='7212') AS replay_receipt_match,
 (sample_json->>'article_id'='9890531'
   AND sample_json->>'article_version'='1'
   AND sample_json->>'original_provider_doi'='10.6084/m9.figshare.9890531.v1'
   AND sample_json->>'provider_article_public'='true') AS release_identity_ok,
 (sample_json->>'provider_declared_file_count'='7'
   AND sample_json->>'provider_declared_gis_archives'='4'
   AND sample_json->>'provider_declared_technical_pdfs'='3'
   AND sample_json->>'provider_declared_original_asset_bytes'='12027317200') AS published_inventory_ok,
 (sample_json->>'provider_md5_labels_equal'='true'
   AND sample_json->>'original_asset_sha256_verified'='false'
   AND sample_json->>'original_asset_bytes_fetched'='0'
   AND sample_json->>'original_metadata_bytes_persisted'='false') AS original_asset_boundary_ok,
 (sample_json->>'strict_repository_runner_executed'='false'
   AND sample_json->>'provider_body_observed_via_intermediary'='true'
   AND model_input_approved=false
   AND research_only=true
   AND source_byte_persistence_authorized=false) AS no_false_repository_or_admission,
 (provider_license LIKE '%CC BY 4.0%'
   AND provider_license LIKE '%ODbL%'
   AND sample_json->>'attribute_licence_caveat' LIKE '%per-column%') AS per_attribute_licence_gate_noted
FROM research.source_sample_v0
WHERE sample_id=70 AND source_id='hydrosheds.hydroatlas.v1';

-- Independent, invented-value controls challenge the exact source-scope gate.
WITH cases(id, article, version, file_count, zip_count, pdf_count,
           asset_bytes, raw_fetched, admitted, expected_pass) AS (
 VALUES
 ('valid_synthetic',9890531,1,7,4,3,12027317200::bigint,0,false,true),
 ('wrong_release',9890531,2,7,4,3,12027317200::bigint,0,false,false),
 ('missing_document',9890531,1,6,4,2,12027317200::bigint,0,false,false),
 ('wrong_total_bytes',9890531,1,7,4,3,12027317201::bigint,0,false,false),
 ('false_model_admission',9890531,1,7,4,3,12027317200::bigint,0,true,false),
 ('raw_download_claim',9890531,1,7,4,3,12027317200::bigint,1,false,false)
), result AS (
 SELECT id, expected_pass,
   (article=9890531 AND version=1 AND file_count=7
    AND zip_count=4 AND pdf_count=3
    AND asset_bytes=12027317200::bigint
    AND raw_fetched=0 AND admitted=false) AS actual_pass
 FROM cases
)
SELECT id, expected_pass, actual_pass,
       (expected_pass=actual_pass) AS control_pass
FROM result ORDER BY id;
