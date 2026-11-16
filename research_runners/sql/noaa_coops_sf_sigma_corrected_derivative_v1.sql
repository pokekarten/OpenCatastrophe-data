-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Source NOAA CO-OPS water_level station 9414290, 2026-01-01, MLLW, m.
-- Exact staged originals: research.source_sample_v0 #3, #40. Source-body
-- SHA stays distinct from the canonical JSONB SHA of THIS NEW derivative.
-- This idempotent manual research-staging SQL does not access the provider,
-- change immutable prior rows, grant model admission, or store raw 240-point
-- responses. The original 12 two-hour derived values are already staged.
--
-- Official CO-OPS API s: sigma = standard deviation of 1-second samples
-- used to compute each 6-minute water-level height; NEVER calibrated
-- CAT secondary uncertainty. Re-map source #40's LEGACY "uncertainty_m".
-- https://api.tidesandcurrents.noaa.gov/api/prod/responseHelp.html
-- NOAA source reuse: https://www.tidesandcurrents.noaa.gov/disclaimers.html
-- Source product scope and research-use permission are checked below.
WITH original AS (
 SELECT * FROM research.source_sample_v0
 WHERE sample_id=3 AND source_id='noaa.coops.water-levels'
), prior AS (
 SELECT * FROM research.source_sample_v0
 WHERE sample_id=40 AND source_id='noaa.coops.water-levels'
), values_120m AS (
 SELECT elem,ord
 FROM prior CROSS JOIN LATERAL jsonb_array_elements(
   CASE WHEN jsonb_typeof(prior.sample_json->'sampled_every_120min')='array'
   THEN prior.sample_json->'sampled_every_120min'
   ELSE '[]'::jsonb END
 ) WITH ORDINALITY AS r(elem,ord)
), permission_gate AS (
 SELECT
 (SELECT provider_response_sha256 FROM original)=(SELECT provider_response_sha256 FROM prior)
 AND (SELECT sample_json #>> '{water_level_mllw_meters,0,s}' FROM original)=
     (SELECT sample_json #>> '{sampled_every_120min,0,uncertainty_m}' FROM prior)
 AND (SELECT count(*)=12 AND bool_and(coalesce(
     jsonb_typeof(elem->'uncertainty_m')='number'
     AND (elem->>'uncertainty_m')::numeric>=0
     AND elem->>'verified_flag'='v'
     AND NOT (elem ? 'sigma_1s_standard_deviation_m')
     AND elem->>'time_gmt'=to_char(timestamp '2026-01-01 00:00:00'
       +(ord-1)*interval '120 minutes','YYYY-MM-DD HH24:MI'),false))
     FROM values_120m)
 AND (SELECT sample_json->>'datum'='MLLW'
     AND sample_json->>'station_id'='9414290'
     AND sample_json->'model_input_approved'='false'::jsonb
     AND sample_json->'raw_full_day_provider_bytes_persisted'='false'::jsonb
     AND research_only AND NOT model_input_approved
     AND NOT source_byte_persistence_authorized FROM prior)
 AND EXISTS(
    SELECT 1 FROM research.source_usage_rights_v0
    WHERE source_id='noaa.coops.water-levels'
      AND product_scope='NOAA CO-OPS Data API v1, 2026-01-01, San Francisco station 9414290, metric MLLW 6-minute water_level; normalized research subset of stored #40'
      AND use_case='internal_neon_source_sample'
      AND rights_result='allowed'
      AND evidence_observed_on=DATE '2026-11-16'
      AND NOT scientific_model_admission
      AND NOT original_asset_admitted
 ) AS permitted
), corrected AS (
 SELECT prior.*,
   (prior.sample_json - 'sampled_every_120min') ||
   jsonb_build_object(
     'profile','noaa-coops-sf-20260101-1sec-sigma-corrected-research-v1',
     'sampled_every_120min',
       (SELECT jsonb_agg((elem - 'uncertainty_m') ||
             jsonb_build_object('sigma_1s_standard_deviation_m',elem->'uncertainty_m')
              ORDER BY ord) FROM values_120m),
     'derived_from_sample_id',40,
     'derived_from_sample_sha256',prior.sample_sha256,
     'original_provider_response_sha256',prior.provider_response_sha256,
     'sigma_definition','Standard deviation of the 1-second samples used to compute the 6-minute water-level height',
     'sigma_documentation_url','https://api.tidesandcurrents.noaa.gov/api/prod/responseHelp.html',
     'legacy_field_uncertainty_m_removed',true,
     'sigma_is_calibrated_cat_uncertainty',false,
     'model_input_approved',false,
     'source_body_retrieved_this_run',false,
     'scientific_role','research_context_only',
     'derived_transform_version','v1'
   ) corrected_json
 FROM prior CROSS JOIN permission_gate WHERE permission_gate.permitted
)
INSERT INTO research.source_sample_v0
 (sample_id,source_id,source_url,sample_kind,sample_json,
  provider_response_sha256,sample_sha256,provider_license,licence_evidence_url,
  rights_scope,product_version,request_identity,retrieved_at,
  research_only,model_input_approved,source_byte_persistence_authorized)
SELECT (SELECT COALESCE(MAX(sample_id),0)+1 FROM research.source_sample_v0),
 source_id,source_url,'observed_values',corrected_json,
 provider_response_sha256,encode(sha256(convert_to(corrected_json::text,'UTF8')),'hex'),
 provider_license,licence_evidence_url,
 'Research-only 12 original-day sampled values with correctly named 1-second sigma; public NOAA provenance retained; no provider-original bytes, no calibrated uncertainty or CAT-model input admitted.',
 product_version,
 'DERIVED_NO_PROVIDER_GET: prior research sample #40; correct NOAA sigma field name v1',
 retrieved_at,true,false,false
FROM corrected
ON CONFLICT DO NOTHING
RETURNING sample_id,source_id,sample_kind,provider_response_sha256,
 sample_sha256,retrieved_at,model_input_approved,source_byte_persistence_authorized;
