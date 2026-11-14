-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- ISOLATED NEON RESEARCH BRANCH ONLY; NEVER main/production.
-- Read-only derived exposure-crosswalk research view over FOUR independently
-- sourced metadata receipts in the 2026-10-21.0 Overture building pilot.
-- Does not store any original building ID, WKB, location, TIV or policy data.
-- One row proves this *specific* Luxembourg-city research slice's internal
-- receipt consistency, NOT global building coverage or insured CAT exposure.
--
-- Upstream evidence:
-- https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41497879623
-- https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41500090059
-- https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41498511267
-- Original Parquet file SHA256/permissions and independent building identity
-- remain unverified, irrespective of this view's arithmetic.

CREATE VIEW research.lu_act_overture_geometry_readiness_v0 AS
WITH original_file_receipts AS (
 SELECT
   release_id,
   COUNT(*)::integer AS source_parquet_files_metadata_checked,
   SUM(reported_parquet_rows)::bigint AS parquet_rows_across_three_files,
   SUM(original_bytes)::bigint AS parquet_bytes_across_three_files,
   BOOL_AND(parquet_magic_verified AND metadata_header_decoded
     AND NOT original_rows_ingested
     AND NOT entire_object_sha256_verified
     AND NOT source_rights_approved
     AND NOT actual_geometry_validated
     AND NOT insurer_exposure_admitted
     AND NOT cat_model_input_approved) AS all_file_receipts_not_admitted
 FROM research.overture_original_building_file_probe_v0
 WHERE release_id = '2026-10-21.0'
 GROUP BY release_id
),
receipts AS (
 SELECT
   geom.source_release,
   geom.row_group_ordinal,
   geom.source_file,
   geom.row_group_source_rows,
   geom.bbox_intersection_candidates,
   geom.real_geometry_positive_overlap,
   geom.invalid_original_geometry,
   geom.sample_geodesic_area_median_m2,
   geom.sample_geodesic_area_n,
   family.city_bbox_source_rows,
   family.osm_dataset_label_rows,
   family.microsoft_ml_dataset_label_rows,
   family.original_odbl_license_tag_rows,
   family.source_rows_missing_lineage,
   pair.act_release,
   pair.act_original_source_rows,
   pair.act_city_footprints,
   pair.overture_city_footprints,
   pair.candidate_iou_threshold,
   pair.positive_area_source_polygon_pairs,
   pair.reciprocal_one_to_one_geometric_candidates,
   pair.above_threshold_overlap_pairs,
   pair.act_best_iou_histogram,
   pair.overture_best_iou_histogram,
   pair.strict_candidate_overture_source_family_counts,
   pair.act_city_digitizing_source_family_counts,
   pair.act_strict_candidate_digitizing_source_family_counts,
   geom.verified_actions_run AS geometry_proof_url,
   family.source_proof_url AS source_family_proof_url,
   pair.source_run_url AS crosswalk_proof_url,
   pair.histogram_source_run_url,
   pair.strict_candidate_source_family_run_url,
   pair.act_digitizing_source_original_run_url
 FROM research.overture_lu_city_one_group_geometry_receipt_v0 AS geom
 JOIN research.lu_overture_original_source_family_receipt_v0 AS family
   ON geom.source_release = family.source_release
  AND geom.row_group_ordinal = family.rowgroup_ordinal
  AND geom.real_geometry_positive_overlap = family.city_bbox_source_rows
 JOIN research.lu_act_overture_original_city_pair_receipt_v0 AS pair
   ON geom.source_release = pair.overture_release
  AND geom.row_group_ordinal = pair.overture_source_row_group
  AND geom.real_geometry_positive_overlap = pair.overture_city_footprints
 WHERE geom.source_release = '2026-10-21.0'
   AND geom.row_group_ordinal = 182
   AND pair.act_release = '2026-10-01'
   AND geom.source_file = 'release/2026-10-21.0/theme=buildings/type=building/part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet'
   AND geom.original_geometry_bytes_retained IS FALSE
   AND geom.source_rights_approved IS FALSE
   AND geom.insurer_exposure_admitted IS FALSE
   AND geom.cat_model_input_approved IS FALSE
   AND family.original_gers_ids_persisted IS FALSE
   AND family.source_provider_rights_independently_reviewed IS FALSE
   AND family.physical_building_identity_proven IS FALSE
   AND family.insurance_model_input_admitted IS FALSE
   AND pair.original_provider_geometry_persisted IS FALSE
   AND pair.independent_physical_identity_verified IS FALSE
   AND pair.source_licensing_scientifically_approved IS FALSE
   AND pair.insured_tiv_inferred IS FALSE
   AND pair.insurance_cat_model_input_approved IS FALSE
)
SELECT
 'overture-luxembourg-city-original-geometry-crosswalk-readiness-v0'::text AS profile,
 r.source_release AS overture_release,
 r.act_release,
 r.row_group_ordinal,
 f.source_parquet_files_metadata_checked,
 f.parquet_rows_across_three_files,
 f.parquet_bytes_across_three_files,
 r.row_group_source_rows,
 r.bbox_intersection_candidates,
 r.real_geometry_positive_overlap AS overture_city_research_window_features,
 r.invalid_original_geometry,
 r.osm_dataset_label_rows,
 r.microsoft_ml_dataset_label_rows,
 r.original_odbl_license_tag_rows,
 r.act_city_footprints,
 r.positive_area_source_polygon_pairs,
 r.candidate_iou_threshold,
 r.reciprocal_one_to_one_geometric_candidates AS geometric_one_to_one_candidates,
 ROUND(100.0 * r.reciprocal_one_to_one_geometric_candidates
       / NULLIF(r.overture_city_footprints,0),2)
       AS percent_of_overture_window_features_with_strict_candidate,
 ROUND(100.0 * r.reciprocal_one_to_one_geometric_candidates
       / NULLIF(r.act_city_footprints,0),2)
       AS percent_of_act_window_features_with_strict_candidate,
 r.sample_geodesic_area_n AS area_profiled_polygons,
 r.sample_geodesic_area_median_m2 AS area_median_profiled_only_m2,
 r.act_best_iou_histogram,
 r.overture_best_iou_histogram,
 r.strict_candidate_overture_source_family_counts,
 r.act_city_digitizing_source_family_counts,
 r.act_strict_candidate_digitizing_source_family_counts,
 r.geometry_proof_url,
 r.source_family_proof_url,
 r.crosswalk_proof_url,
 r.histogram_source_run_url,
 r.strict_candidate_source_family_run_url,
 r.act_digitizing_source_original_run_url,
 FALSE AS complete_global_footprint_coverage_verified,
 FALSE AS original_source_files_complete_sha256_verified,
 FALSE AS physical_same_building_identity_verified,
 FALSE AS insurer_policy_or_tiv_available,
 FALSE AS original_geometries_or_ids_persisted,
 FALSE AS independent_source_rights_approved,
 FALSE AS cat_model_input_approved
FROM receipts r
JOIN original_file_receipts f ON r.source_release = f.release_id
WHERE f.source_parquet_files_metadata_checked = 3
 AND f.parquet_rows_across_three_files = 15059017
 AND f.parquet_bytes_across_three_files = 1675937964
 AND f.all_file_receipts_not_admitted IS TRUE
 AND r.row_group_source_rows = 19095
 AND r.bbox_intersection_candidates = 69
 AND r.real_geometry_positive_overlap = 69
 AND r.invalid_original_geometry = 0
 AND r.city_bbox_source_rows = 69
 AND r.osm_dataset_label_rows + r.microsoft_ml_dataset_label_rows = 69
 AND r.original_odbl_license_tag_rows = 69
 AND r.source_rows_missing_lineage = 0
 AND r.act_city_footprints = 139
 AND r.overture_city_footprints = 69
 AND r.candidate_iou_threshold = 0.7500
 AND r.above_threshold_overlap_pairs = 5
 AND r.reciprocal_one_to_one_geometric_candidates = 5
 AND r.positive_area_source_polygon_pairs = 282
 AND COALESCE((r.act_best_iou_histogram->>'no_positive_area_overlap')::int, -1)
   + COALESCE((r.act_best_iou_histogram->>'iou_below_0_25')::int, -1)
   + COALESCE((r.act_best_iou_histogram->>'iou_0_25_to_0_50')::int, -1)
   + COALESCE((r.act_best_iou_histogram->>'iou_0_50_to_0_75')::int, -1)
   + COALESCE((r.act_best_iou_histogram->>'iou_at_least_0_75')::int, -1) = 139
 AND COALESCE((r.overture_best_iou_histogram->>'no_positive_area_overlap')::int, -1)
   + COALESCE((r.overture_best_iou_histogram->>'iou_below_0_25')::int, -1)
   + COALESCE((r.overture_best_iou_histogram->>'iou_0_25_to_0_50')::int, -1)
   + COALESCE((r.overture_best_iou_histogram->>'iou_0_50_to_0_75')::int, -1)
   + COALESCE((r.overture_best_iou_histogram->>'iou_at_least_0_75')::int, -1) = 69
 AND (r.strict_candidate_overture_source_family_counts->>'OpenStreetMap')::int = 5
 AND (r.strict_candidate_overture_source_family_counts->>'Microsoft ML Buildings')::int = 0
 AND (r.act_city_digitizing_source_family_counts->>'Bati3DVDL')::int = 139
 AND (r.act_strict_candidate_digitizing_source_family_counts->>'Bati3DVDL')::int = 5;
