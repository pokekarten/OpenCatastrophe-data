-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0

-- Immutable original-provider metadata-receipt-derived research summary.
-- Source response JSON (3730 bytes) is NOT inserted, no crop/parcel/person data.
-- JSONB hash is generated in Postgres from exactly the persisted jsonb text.
-- Specific narrow rights decisions must already exist for metadata-only scope.
WITH candidate AS (
  SELECT '{"provider":"Rijksdienst voor Ondernemend Nederland via PDOK","source_id":"nl.rvo.brp-gewaspercelen.2025","research_evidence_kind":"original_first_party_public_collection_metadata_only","original_request_url":"https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json","original_request_method":"GET","collection_id_verified":"brpgewas","collection_title_verified":"BRP Gewaspercelen","collection_item_type_verified":"feature","http_200_verified_by_first_party_runner":true,"json_schema_validated":true,"bbox_overlaps_netherlands_verified":true,"crs84_and_epsg28992_verified":true,"source_service_mutable_current_version":true,"exact_final_2025_archive_verified":false,"original_response_sha256":"99a64145c7b198bbe2e2a78f248c24845e212210d482e805cb581d6aaa61ca79","original_response_bytes":3730,"original_request_sha256":"f50ae18fd344ff4c201dd3e1db6fd75f321bb302e4f84fda642d6a1750696eb2","original_source_access_contract_sha256":"7164465a21b3cfb7e0dae2b77e89e31fcfd034297a156c7781083e53717ad396","original_runner_code_sha256":"be00542bed9b6b5a2e41773a32421b41aba0d5b3b8ade4ca8d293c133eb10d66","github_run_id":43489886311,"github_job_id":132108208702,"github_main_commit":"526303e78974ed234610bf0a65fac4786512da13","retrieval_utc":"2026-11-13T19:12:32.658210+00:00","source_original_json_persisted":false,"original_parcel_geometry_downloaded":false,"original_feature_rows_retrieved":0,"commercial_cat_source_dataset_rights_admitted":false,"scientific_model_input_approved":false}'::jsonb AS sample_json
)
INSERT INTO research.source_sample_v0 (
  source_id, source_url, sample_kind, sample_json,
  provider_response_sha256, sample_sha256,
  provider_license, licence_evidence_url, rights_scope, product_version,
  request_identity, retrieved_at, research_only, model_input_approved,
  source_byte_persistence_authorized
)
SELECT
  'nl.rvo.brp-gewaspercelen.2025', 'https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json', 'public_metadata', c.sample_json,
  '99a64145c7b198bbe2e2a78f248c24845e212210d482e805cb581d6aaa61ca79',
  encode(sha256(convert_to(c.sample_json::text, 'UTF8')), 'hex'),
  'Public Domain Mark 1.0 (PDOK provider source/metadata status marker, not a 2025 archived-product licence)',
  'https://api.pdok.nl/rvo/gewaspercelen/ogc/v1?f=html&lang=en',
  'CURRENT LIVE brpgewas collection metadata-only structural digest/CRS proof; no 2025 original asset, crop parcel rows, geometry, TIV, raw source JSON or model admission',
  'current_live_ogc_service_2026-11-13; frozen_2025_archive_not_verified',
  'GET https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json (original trusted-main HTTP 200; no redirects)',
  TIMESTAMPTZ '2026-11-13T19:12:32.658210+00:00', TRUE, FALSE, FALSE
FROM candidate c
WHERE EXISTS (
  SELECT 1 FROM research.source_usage_rights_v0 u
  WHERE u.source_id = 'nl.rvo.brp-gewaspercelen.2025'
    AND u.use_case='internal_neon_source_sample' AND u.rights_result='allowed'
    AND u.product_scope LIKE 'RVO/PDOK BRP Gewaspercelen OGC API Features:%'
)
ON CONFLICT (source_id, sample_sha256, sample_kind)
DO NOTHING;
