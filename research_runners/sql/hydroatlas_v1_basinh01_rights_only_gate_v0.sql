-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Exact product/column-scoped read-only HydroATLAS v1.0 BasinATLAS H01 gate.
-- No source bytes; 1971-2000 naturalized, modelled WaterGAP flow,
-- NOT observed flood-event discharge, insured loss or CAT model admission.
-- Official Figshare article: https://doi.org/10.6084/m9.figshare.9890531.v1
-- Original catalog: https://data.hydrosheds.org/file/technical-documentation/BasinATLAS_Catalog_v10.pdf
-- Always returns one PASS/FAIL row, including missing-sample cases.
WITH expected AS (
  SELECT
    'hydrosheds.hydroatlas.v1'::text AS source_id,
    'HydroATLAS v1.0, Figshare 9890531.v1, BasinATLAS H01 natural discharge: dis_m3_pyr/dis_m3_pmn/dis_m3_pmx (WaterGAP v2.2, 1971-2000 naturalized flow); rights-only, no original GIS or model admission'::text AS product_scope,
    'https://data.hydrosheds.org/file/technical-documentation/BasinATLAS_Catalog_v10.pdf'::text AS catalog_url,
    70::bigint AS sample_id
),
rights AS (
  SELECT r.*
  FROM research.source_usage_rights_v0 AS r
  JOIN expected AS e ON r.source_id=e.source_id AND r.product_scope=e.product_scope
),
rights_gate AS (
  SELECT count(*)::int AS rows_checked,
    count(DISTINCT use_case)::int AS distinct_usecases,
    count(*) FILTER (WHERE
      (use_case IN ('internal_research','commercial_cat_modelling','internal_neon_metadata')
       AND rights_result='allowed')
      OR (use_case IN ('internal_neon_source_sample','external_raw_redistribution',
                      'automated_api_access','published_derived_results')
          AND rights_result='conditional')
    )::int AS exact_rights_decisions,
    COALESCE(bool_and(
      NOT scientific_model_admission AND NOT original_asset_admitted
      AND evidence_url=(SELECT catalog_url FROM expected)
      AND evidence_observed_on=DATE '2026-11-15'
    ),false) AS evidence_and_no_admission,
    COALESCE(bool_or(scientific_model_admission),false) AS any_model_admission_in_rights,
    COALESCE(bool_or(original_asset_admitted),false) AS any_original_asset_admitted
  FROM rights
),
sample_gate AS (
  SELECT count(*)::int AS exact_metadata_sample_count,
    COALESCE(bool_and(
      sample_kind='public_metadata'
      AND product_version='HydroATLAS version 1.0, Figshare article 9890531 v1'
      AND research_only AND NOT model_input_approved
      AND NOT source_byte_persistence_authorized
      AND sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
    ),false) AS metadata_sample_research_only_and_hash_valid,
    COALESCE(bool_or(model_input_approved),false) AS any_sample_model_approved
  FROM research.source_sample_v0 AS s
  JOIN expected AS e ON s.source_id=e.source_id AND s.sample_id=e.sample_id
),
candidate_gate AS (
  SELECT count(*)::int AS candidate_rows,
    COALESCE(bool_and(admission_status='not_admitted'),false) AS candidate_not_admitted
  FROM research.source_candidate_review_v0 AS c
  JOIN expected AS e ON c.source_id=e.source_id
)
SELECT
  e.source_id,
  'BasinATLAS v1.0 H01: dis_m3_pyr / dis_m3_pmn / dis_m3_pmx' AS only_reviewed_columns,
  r.rows_checked, r.distinct_usecases, r.exact_rights_decisions,
  r.evidence_and_no_admission, r.any_model_admission_in_rights,
  r.any_original_asset_admitted,
  s.exact_metadata_sample_count, s.metadata_sample_research_only_and_hash_valid,
  s.any_sample_model_approved,
  c.candidate_rows, c.candidate_not_admitted,
  (r.rows_checked=7 AND r.distinct_usecases=7 AND r.exact_rights_decisions=7
   AND r.evidence_and_no_admission AND NOT r.any_model_admission_in_rights
   AND NOT r.any_original_asset_admitted
   AND s.exact_metadata_sample_count=1
   AND s.metadata_sample_research_only_and_hash_valid
   AND NOT s.any_sample_model_approved
   AND c.candidate_rows=1 AND c.candidate_not_admitted) AS exact_H01_rights_only_gate_pass
FROM expected e
CROSS JOIN rights_gate r
CROSS JOIN sample_gate s
CROSS JOIN candidate_gate c;
