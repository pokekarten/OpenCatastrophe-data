-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only 2026-11-01 conflict evidence gate: run separately on CAT-only Neon
-- main and validation-schema-20261031 with an explicit branch selector.
-- Matches exact pinned Git blobs, NOT the latest mutable branch content.
-- Passing verifies metadata consistency only: never authorizes branch merge,
-- source rights, model inputs, or real insured CAT exposures.
WITH pinned AS (
 SELECT * FROM (VALUES
  ('landscape_file:sources-exposure-impact-validation'::text,
   'landscape_candidate'::text,'landscape_exposure'::text),
  ('official_api:usgs_comcat_2025_jan_m6_sample'::text,
   'access_contract'::text,'usgs_hypocentres'::text),
  ('official_fl_oir:2025_12_mir_original_full_company_policy_v1'::text,
   'access_contract'::text,'fl_statewide_company_policy'::text)
 ) AS t(source_key,expected_classification,scope)
), evidence AS (
 SELECT p.source_key,p.scope,s.classification,s.git_blob_sha,s.git_commit_sha,
        s.review_status,s.rights_status,s.admissible_for_raw,s.raw_metadata,
        CASE
          WHEN p.scope='landscape_exposure'
          THEN CASE s.git_blob_sha
               WHEN '79d91635a154b6ae20482b953021a6ade52c3491' THEN 'main_13_candidates'
               WHEN 'cecaf867a47e83069a27b179268942b900b771b4' THEN 'validation_11_candidates'
               ELSE 'unknown_version' END
          WHEN p.scope='usgs_hypocentres'
          THEN CASE WHEN s.git_blob_sha='1527daa259d1ac697e1356dc35eb2171438538cc'
                    THEN 'same_7_event_sample' ELSE 'unknown_version' END
          WHEN p.scope='fl_statewide_company_policy'
          THEN CASE WHEN s.git_blob_sha='b4318d9a4c51a628088546c36b2697b6e919ca92'
                    THEN 'same_442_row_workbook_reference' ELSE 'unknown_version' END
          ELSE 'unknown_version'
        END AS pinned_artifact_version,
        p.expected_classification
 FROM pinned p LEFT JOIN registry.source_record s USING (source_key)
)
SELECT source_key,scope,pinned_artifact_version,
       git_blob_sha,git_commit_sha,review_status,rights_status,
       CASE WHEN scope='landscape_exposure'
                 AND jsonb_typeof(raw_metadata->'entries')='array'
            THEN jsonb_array_length(raw_metadata->'entries')
            ELSE NULL END AS landscape_candidate_count,
       CASE WHEN scope='landscape_exposure'
            THEN jsonb_path_exists(coalesce(raw_metadata,'{}'::jsonb),
               '$.entries[*] ? (@.candidate_id == "gem.global-exposure-model.v2026.0.0")')
            ELSE NULL END AS contains_gem_exposure,
       CASE WHEN scope='landscape_exposure'
            THEN jsonb_path_exists(coalesce(raw_metadata,'{}'::jsonb),
               '$.entries[*] ? (@.candidate_id == "gem.global-vulnerability-model.v2026.0.0")')
            ELSE NULL END AS contains_gem_vulnerability,
       CASE WHEN scope='fl_statewide_company_policy'
            THEN coalesce(raw_metadata->>'source_original_sha256',
                          raw_metadata->>'original_XLSX_SHA256')
            ELSE NULL END AS florida_original_xlsx_sha256,
       CASE WHEN scope='usgs_hypocentres'
            THEN coalesce(raw_metadata->>'source_event_rows',
                          raw_metadata->>'event_sample_count')
            ELSE NULL END AS usgs_sample_events,
       (classification=expected_classification
        AND pinned_artifact_version <> 'unknown_version'
        AND admissible_for_raw IS FALSE
        AND CASE WHEN scope='landscape_exposure'
                 THEN (pinned_artifact_version='main_13_candidates'
                            AND jsonb_array_length(raw_metadata->'entries')=13
                            AND jsonb_path_exists(raw_metadata,
                              '$.entries[*] ? (@.candidate_id == "gem.global-exposure-model.v2026.0.0")')
                            AND jsonb_path_exists(raw_metadata,
                              '$.entries[*] ? (@.candidate_id == "gem.global-vulnerability-model.v2026.0.0")'))
                      OR (pinned_artifact_version='validation_11_candidates'
                            AND jsonb_array_length(raw_metadata->'entries')=11
                            AND NOT jsonb_path_exists(raw_metadata,
                              '$.entries[*] ? (@.candidate_id == "gem.global-exposure-model.v2026.0.0")')
                            AND NOT jsonb_path_exists(raw_metadata,
                              '$.entries[*] ? (@.candidate_id == "gem.global-vulnerability-model.v2026.0.0")'))
                 WHEN scope='usgs_hypocentres'
                   THEN coalesce(raw_metadata->>'source_event_rows',
                                 raw_metadata->>'event_sample_count')='7'
                 WHEN scope='fl_statewide_company_policy'
                   THEN coalesce(raw_metadata->>'source_original_sha256',
                                 raw_metadata->>'original_XLSX_SHA256')
                        = 'a4fc7d5e20daed10299b06b2b661480b7c92c2cbaecc697a26567156bf1d4d3a'
                 ELSE FALSE END) IS TRUE AS pinned_evidence_consistent,
       FALSE AS merge_authorized,
       FALSE AS model_input_authorized
FROM evidence ORDER BY source_key;
