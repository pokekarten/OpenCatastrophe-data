-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READY NOW on insurance-risk-core (no schema migration required).
-- This SELECT reads existing source_sample_v0 metadata-only PR-source proof
-- samples and rights, never raw original source data. A public Actions link
-- is referenced, not cryptographically verified by the database itself.
-- DO NOT confuse this branch-evidence overlay with trusted main receipt v1.
WITH fixed_expected(source_id,github_run_id,original_sha256) AS (
 VALUES
  ('dwd.radklim.rw.v2017.002',43488656039::bigint,
   '741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867'::text),
  ('noaa.swpc.real-time-solar-wind',43489514680::bigint,
   'bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159'::text),
  ('gfz.geomagnetic-kp',43491158483::bigint,
   'f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a'::text)
),
rights AS (
 SELECT source_id,
  COUNT(*)::int AS use_case_rights_rows,
  COUNT(*) FILTER (
   WHERE use_case='internal_neon_metadata' AND rights_result='allowed'
  )::int AS metadata_rights_allowed_rows,
  COUNT(*) FILTER (
   WHERE use_case='external_raw_redistribution' AND rights_result='allowed'
  )::int AS raw_unconditionally_allowed_rows,
  BOOL_OR(scientific_model_admission) AS any_rights_science_admission,
  BOOL_OR(original_asset_admitted) AS any_rights_original_asset_admission
 FROM research.source_usage_rights_v0
 GROUP BY source_id
),
checked AS (
 SELECT s.sample_id,s.source_id,s.sample_kind,s.provider_response_sha256,
  s.retrieved_at,s.sample_json,
  s.sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
   AS canonical_sample_sha_valid,
  (s.sample_json->>'github_run_id')::bigint AS source_github_run_id,
  s.sample_json->>'github_run_url' AS source_github_run_url,
  s.sample_json->>'github_head_sha' AS source_github_head_sha,
  COALESCE(s.sample_json->>'original_provider_response_sha256',
           s.sample_json->>'original_response_sha256') AS source_original_sha_json,
  s.model_input_approved,s.source_byte_persistence_authorized,s.research_only,
  (s.sample_json->>'model_input_approved')::boolean AS noaa_legacy_model_approved,
  (s.sample_json->>'insurer_cat_model_admitted')::boolean AS other_model_admitted,
  (s.sample_json->>'trusted_main_run')::boolean AS other_trusted_main,
  (s.sample_json->>'original_provider_body_stored')::boolean AS other_original_body_stored,
  (s.sample_json->>'provider_body_or_sensor_rows_stored')::boolean AS noaa_original_body_stored
 FROM research.source_sample_v0 s
 WHERE s.sample_kind='public_metadata'
  AND s.sample_json->>'profile' IN (
   'noaa-swpc-rtsw-2026-direct-public-github-source-metadata-v1',
   'strict_public_original_pr_branch_github_receipt_metadata_v1'
  )
)
SELECT c.source_id,c.sample_id AS neon_metadata_sample_id,c.sample_kind,
 c.source_github_run_id,c.source_github_run_url,c.source_github_head_sha,
 c.provider_response_sha256 AS original_provider_sha256,
 c.canonical_sample_sha_valid,
 c.provider_response_sha256=f.original_sha256
  AND c.source_original_sha_json=f.original_sha256 AS fixed_original_sha_matches,
 c.source_github_run_url =
  'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/'||
  f.github_run_id::text AS github_run_url_matches,
 c.source_github_run_id=f.github_run_id AS run_id_matches,
 COALESCE(r.use_case_rights_rows,0) AS product_scoped_use_case_rights_rows,
 COALESCE(r.metadata_rights_allowed_rows,0)>0 AS internal_metadata_licence_scoped,
 COALESCE(r.raw_unconditionally_allowed_rows,0)>0 AS raw_redistribution_unconditionally_allowed,
 (c.research_only AND NOT c.model_input_approved
  AND NOT c.source_byte_persistence_authorized
  AND NOT COALESCE(c.noaa_legacy_model_approved,false)
  AND NOT COALESCE(c.other_model_admitted,false)
  AND NOT COALESCE(c.other_trusted_main,false)
  AND NOT COALESCE(c.other_original_body_stored,false)
  AND NOT COALESCE(c.noaa_original_body_stored,false)
  AND NOT COALESCE(r.any_rights_science_admission,false)
  AND NOT COALESCE(r.any_rights_original_asset_admission,false))
  AS metadata_only_no_admission,
 EXISTS (SELECT 1 FROM research.all_source_inventory_v0 i
         WHERE i.source_id=c.source_id) AS canonical_source_present,
 EXISTS (SELECT 1 FROM research.source_strict_original_probe_receipt_v1 m
         WHERE m.source_id=c.source_id) AS separately_trusted_main_range_exists,
 EXISTS (SELECT 1 FROM research.source_strict_metadata_probe_receipt_v1 m
         WHERE m.source_id=c.source_id) AS separately_trusted_main_metadata_exists,
 false AS grants_cat_scientific_admission
FROM checked c JOIN fixed_expected f
 ON f.source_id=c.source_id AND f.github_run_id=c.source_github_run_id
LEFT JOIN rights r ON r.source_id=c.source_id
ORDER BY c.source_id,c.sample_id;
