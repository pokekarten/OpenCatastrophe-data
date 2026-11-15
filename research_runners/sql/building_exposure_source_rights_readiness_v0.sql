-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY. Exact building-exposure dataset/use-case rights QA.
-- Run against authorized insurance/research Neon; source of truth is the
-- EXISTING research.source_rights_matrix_v0 + source_usage_rights_v0 ledger.
-- Do not infer a licence grant from the official URLs embedded below.
-- This SQL neither downloads source data nor writes permissions/samples.
--
-- Official product license references (not API/service automation consent):
-- https://www.geodaten.bayern.de/odd/m/3/html/nutzungsbedingungen.html
-- https://catalogue.geoservice.dlr.de/web/datasets/wsf_2019
-- https://docs.overturemaps.org/attribution/  (Buildings THEME: ODbL)
-- Overture release reviewed: 2026-10-21.0; per-feature source labels do
-- not override the licensing of the combined ODbL Buildings THEME.
-- DLR geotiff contract: access/dlr.wsf.2019.native-geotiff.json
-- status=documented_only, api_terms_status=unknown, probe.mode=none.
--
-- A 'rights complete' state is never scientific/model/insurer admission.
-- Source-wide samples are not independently authenticated product-scope
-- records when multiple products/versions share a source_id.
WITH targets AS (
 SELECT *
 FROM (VALUES
  ('de.bayern.hausumringe'::text,
   'Oberbayern'::text, 'CC BY 4.0'::text,
   'https://www.geodaten.bayern.de/odd/m/3/html/nutzungsbedingungen.html'::text),
  ('dlr.wsf.2019'::text,
   'WSF2019_v1_10_48.tif'::text, 'CC BY 4.0'::text,
   'https://catalogue.geoservice.dlr.de/web/datasets/wsf_2019'::text),
  ('overture.maps.buildings'::text,
   '2026-10-21.0'::text, 'ODbL (Buildings theme)'::text,
   'https://docs.overturemaps.org/attribution/'::text)
 ) AS v(source_id,required_review_scope_marker,
        published_product_license,product_license_evidence_url)
),
expected_cases AS (
 SELECT use_case
 FROM (VALUES ('internal_research'::text),
              ('commercial_cat_modelling'),
              ('automated_api_access'),
              ('internal_neon_metadata'),
              ('internal_neon_source_sample'),
              ('published_derived_results'),
              ('external_raw_redistribution')
 ) AS v(use_case)
),
source_samples AS (
 SELECT source_id, count(*)::integer AS source_wide_samples,
        count(*) FILTER (
          WHERE sample_sha256 = encode(
             sha256(convert_to(sample_json::text,'UTF8')),'hex')
        )::integer AS canonical_json_shas_ok,
        count(*) FILTER (WHERE model_input_approved IS TRUE)::integer
             AS currently_admitted_samples
 FROM research.source_sample_v0
 WHERE source_id IN (SELECT source_id FROM targets)
 GROUP BY source_id
),
base AS (
 SELECT t.*, m.source_name, m.product_scope,
        m.rights_review_status, m.broad_commercial_verdict,
        m.commercial_cat_modelling, m.automated_api_access,
        m.internal_neon_metadata, m.internal_neon_source_sample,
        m.external_raw_redistribution, m.published_derived_results,
        m.admission_status,
        count(m.product_scope) OVER(PARTITION BY t.source_id)
            AS matrix_scope_rows,
        coalesce(s.source_wide_samples,0) AS source_wide_samples,
        coalesce(s.canonical_json_shas_ok,0) AS canonical_json_shas_ok,
        coalesce(s.currently_admitted_samples,0) AS currently_admitted_samples
 FROM targets t
 LEFT JOIN research.source_rights_matrix_v0 m
   ON m.source_id=t.source_id
 LEFT JOIN source_samples s ON s.source_id=t.source_id
),
reviewed AS (
 SELECT b.*,
        (b.product_scope IS NOT NULL
         AND b.product_scope <> 'no_product_scoped_review'
         AND position(b.required_review_scope_marker IN b.product_scope)>0
         AND b.rights_review_status='verified'
         AND b.matrix_scope_rows=1) AS exact_product_scope_reviewed,
        u.ledger_entries, u.unique_use_cases,
        u.provider_host_evidence_entries,
        u.commercial_allowed_entries, u.automation_allowed_entries,
        u.internal_research_allowed_entries, u.metadata_allowed_entries,
        u.source_sample_allowed_entries,
        u.derived_publish_allowed_entries, u.raw_redistribution_allowed_entries,
        ARRAY(
           SELECT v.use_case FROM expected_cases v
           WHERE NOT EXISTS (
             SELECT 1 FROM research.source_usage_rights_v0 r
             WHERE r.source_id=b.source_id
               AND r.product_scope=b.product_scope
               AND r.use_case=v.use_case
           )
           ORDER BY v.use_case
        ) AS missing_product_scoped_use_cases
 FROM base b
 CROSS JOIN LATERAL (
  SELECT
    count(*)::integer AS ledger_entries,
    count(DISTINCT r.use_case)::integer AS unique_use_cases,
    count(*) FILTER (WHERE r.evidence_url IS NOT NULL AND
      CASE b.source_id
        WHEN 'de.bayern.hausumringe' THEN
          r.evidence_url LIKE 'https://www.geodaten.bayern.de/%'
          OR r.evidence_url LIKE 'https://www.ldbv.bayern.de/%'
        WHEN 'dlr.wsf.2019' THEN
          r.evidence_url LIKE 'https://catalogue.geoservice.dlr.de/%'
          OR r.evidence_url LIKE 'https://geoservice.dlr.de/%'
        WHEN 'overture.maps.buildings' THEN
          r.evidence_url LIKE 'https://docs.overturemaps.org/%'
        ELSE FALSE
      END
    )::integer AS provider_host_evidence_entries,
    count(*) FILTER (WHERE r.use_case='commercial_cat_modelling'
                          AND r.rights_result='allowed')::integer AS commercial_allowed_entries,
    count(*) FILTER (WHERE r.use_case='automated_api_access'
                          AND r.rights_result='allowed')::integer AS automation_allowed_entries,
    count(*) FILTER (WHERE r.use_case='internal_research'
                          AND r.rights_result='allowed')::integer AS internal_research_allowed_entries,
    count(*) FILTER (WHERE r.use_case='internal_neon_metadata'
                          AND r.rights_result='allowed')::integer AS metadata_allowed_entries,
    count(*) FILTER (WHERE r.use_case='internal_neon_source_sample'
                          AND r.rights_result='allowed')::integer AS source_sample_allowed_entries,
    count(*) FILTER (WHERE r.use_case='published_derived_results'
                          AND r.rights_result='allowed')::integer AS derived_publish_allowed_entries,
    count(*) FILTER (WHERE r.use_case='external_raw_redistribution'
                          AND r.rights_result='allowed')::integer AS raw_redistribution_allowed_entries
  FROM research.source_usage_rights_v0 r
  WHERE r.source_id=b.source_id
    AND r.product_scope=b.product_scope
 ) u
),
gates AS (
 SELECT *,
   (exact_product_scope_reviewed
    AND ledger_entries=7 AND unique_use_cases=7
    AND provider_host_evidence_entries=7
    AND commercial_cat_modelling='allowed'
    AND automated_api_access='allowed'
    AND internal_neon_metadata='allowed'
    AND internal_neon_source_sample='allowed'
    AND commercial_allowed_entries=1
    AND automation_allowed_entries=1
    AND internal_research_allowed_entries=1
    AND metadata_allowed_entries=1
    AND source_sample_allowed_entries=1
    AND canonical_json_shas_ok=source_wide_samples) AS commercial_automated_research_rights_complete,
   (exact_product_scope_reviewed
    AND ledger_entries=7 AND unique_use_cases=7
    AND provider_host_evidence_entries=7
    AND published_derived_results='allowed'
    AND derived_publish_allowed_entries=1) AS derived_publication_rights_complete,
   (exact_product_scope_reviewed
    AND ledger_entries=7 AND unique_use_cases=7
    AND provider_host_evidence_entries=7
    AND external_raw_redistribution='allowed'
    AND raw_redistribution_allowed_entries=1) AS raw_redistribution_rights_complete
 FROM reviewed
)
SELECT source_id,product_scope,published_product_license,
       product_license_evidence_url,
       rights_review_status,broad_commercial_verdict,
       automated_api_access,commercial_cat_modelling,
       ledger_entries,unique_use_cases,provider_host_evidence_entries,
       missing_product_scoped_use_cases,
       source_wide_samples,canonical_json_shas_ok,currently_admitted_samples,
       exact_product_scope_reviewed,
       commercial_automated_research_rights_complete,
       derived_publication_rights_complete,
       raw_redistribution_rights_complete,
       CASE
         WHEN NOT exact_product_scope_reviewed
           THEN 'REVIEW_EXACT_PRODUCT_AND_RELEASE_RIGHTS'
         WHEN ledger_entries<>7 OR unique_use_cases<>7
           OR provider_host_evidence_entries<>7
           THEN 'REVIEW_SEVEN_USE_CASES_AND_AUTHORITY_EVIDENCE'
         WHEN commercial_allowed_entries<>1 OR commercial_cat_modelling<>'allowed'
           THEN 'REVIEW_COMMERCIAL_CAT_USE'
         WHEN automation_allowed_entries<>1 OR automated_api_access<>'allowed'
           THEN 'REVIEW_EXACT_API_OR_FILE_SERVICE_AUTOMATION'
         WHEN internal_research_allowed_entries<>1 OR metadata_allowed_entries<>1
            OR source_sample_allowed_entries<>1
            OR internal_neon_metadata<>'allowed'
            OR internal_neon_source_sample<>'allowed'
           THEN 'REVIEW_INTERNAL_RESEARCH_AND_NEON_USE'
         WHEN canonical_json_shas_ok<>source_wide_samples THEN 'BLOCK_INVALID_SAMPLE_SHA'
         ELSE 'RIGHTS_ONLY_COMPLETE_SCIENCE_AND_ASSET_REVIEW_STILL_REQUIRED'
       END AS next_blocker,
       FALSE AS geographic_population_completeness_verified,
       FALSE AS independent_building_identity_verified,
       FALSE AS insurer_policy_or_tiv_available,
       FALSE AS cat_model_input_approved_by_this_audit
FROM gates
ORDER BY CASE source_id WHEN 'de.bayern.hausumringe' THEN 1
                        WHEN 'dlr.wsf.2019' THEN 2 ELSE 3 END;
