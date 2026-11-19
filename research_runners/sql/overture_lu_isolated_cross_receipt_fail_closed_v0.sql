-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- ISOLATED NEON RESEARCH BRANCH ONLY. SELECT-only Overture 2026-10-21.0
-- Luxembourg-city geometric-candidate evidence gate and 9 synthetic challenges.
-- Requires the pre-existing research.lu_act_overture_geometry_readiness_v0
-- view, NOT the main production Neon branch. Never copies provider Parquet,
-- GERS/building identifiers, original coordinates, TIV or insured locations.
-- This is receipt consistency, NOT independent building identity, ODbL
-- downstream-derivative clearance, original complete Parquet SHA or CAT model use.
-- Always returns all ten controls even when the source view has ZERO rows;
-- positive gate must fail if there are zero OR multiple underlying receipt rows.
WITH receipt AS (
 SELECT COUNT(*)::integer AS n,
        COALESCE(jsonb_agg(to_jsonb(v))->0,'{}'::jsonb) AS j
 FROM research.lu_act_overture_geometry_readiness_v0 v
),
cases(id, expected_pass) AS (
 VALUES ('observed_isolated_original_metadata',true),
        ('synthetic_missing_view_row',false),
        ('synthetic_wrong_release',false),
        ('synthetic_wrong_city_count',false),
        ('synthetic_bad_source_lineage',false),
        ('synthetic_false_identity',false),
        ('synthetic_false_rights',false),
        ('synthetic_false_full_parquet_sha',false),
        ('synthetic_false_global_coverage',false),
        ('synthetic_false_model_admission',false)
),
variants AS (
 SELECT c.id,c.expected_pass,
   CASE WHEN c.id='synthetic_missing_view_row' THEN 0 ELSE r.n END AS n,
   CASE c.id
    WHEN 'synthetic_wrong_release' THEN jsonb_set(r.j,'{overture_release}','"2026-09-23.1"')
    WHEN 'synthetic_wrong_city_count' THEN jsonb_set(r.j,'{overture_city_research_window_features}','68')
    WHEN 'synthetic_bad_source_lineage' THEN jsonb_set(r.j,'{osm_dataset_label_rows}','63')
    WHEN 'synthetic_false_identity' THEN jsonb_set(r.j,'{physical_same_building_identity_verified}','true')
    WHEN 'synthetic_false_rights' THEN jsonb_set(r.j,'{independent_source_rights_approved}','true')
    WHEN 'synthetic_false_full_parquet_sha' THEN jsonb_set(r.j,'{original_source_files_complete_sha256_verified}','true')
    WHEN 'synthetic_false_global_coverage' THEN jsonb_set(r.j,'{complete_global_footprint_coverage_verified}','true')
    WHEN 'synthetic_false_model_admission' THEN jsonb_set(r.j,'{cat_model_input_approved}','true')
    ELSE r.j END AS j
 FROM cases c CROSS JOIN receipt r
),
checks AS (
 SELECT id,expected_pass,
   (n=1
    AND j->>'profile'='overture-luxembourg-city-original-geometry-crosswalk-readiness-v0'
    AND j->>'overture_release'='2026-10-21.0'
    AND j->>'act_release'='2026-10-01'
    AND j->>'row_group_ordinal'='182'
    AND j->>'source_parquet_files_metadata_checked'='3'
    AND j->>'parquet_rows_across_three_files'='15059017'
    AND j->>'parquet_bytes_across_three_files'='1675937964'
    AND j->>'row_group_source_rows'='19095'
    AND j->>'overture_city_research_window_features'='69'
    AND j->>'act_city_footprints'='139'
    AND j->>'geometric_one_to_one_candidates'='5'
    AND j->>'osm_dataset_label_rows'='64'
    AND j->>'microsoft_ml_dataset_label_rows'='5'
    AND j->>'original_odbl_license_tag_rows'='69'
    AND j->>'invalid_original_geometry'='0'
    AND j->>'complete_global_footprint_coverage_verified'='false'
    AND j->>'original_source_files_complete_sha256_verified'='false'
    AND j->>'physical_same_building_identity_verified'='false'
    AND j->>'insurer_policy_or_tiv_available'='false'
    AND j->>'original_geometries_or_ids_persisted'='false'
    AND j->>'independent_source_rights_approved'='false'
    AND j->>'cat_model_input_approved'='false'
    ) AS gate_pass
 FROM variants
)
SELECT id,expected_pass,gate_pass,gate_pass=expected_pass AS control_pass,
       false AS original_data_approved,
       false AS insurer_building_exposure_or_cat_input_admitted
FROM checks ORDER BY id;
