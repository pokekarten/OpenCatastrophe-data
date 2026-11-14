-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ-ONLY research SQL against existing insurance/main Neon records.
-- No CREATE/INSERT/UPDATE/DELETE, no unreviewed source HTTP, no source bytes,
-- coordinates, footprint polygons, raster-row payload or insurer TIV returned.
-- Original HU-BY SHP full member research source: run 43317649994.
-- WSF native LZW/GDAL independent original-mask check: run 43226483288.
-- Source study: docs/research/bvv-hu-by-original-shp-vs-wsf2019-first-real-overlap-20261112.md.
--
-- This measures fractional footprint-vs-settlement area at TWO Munich windows,
-- not same-physical-building identity and not accuracy/coverage of a
-- population-wide buildings inventory. Source ages differ (2019 vs later).
-- Sample #28 genuinely has zero WSF class-255 cells: its "WSF share covered"
-- is mathematically NULL, not zero. Fail CLOSED on receipt or formula drift.
WITH expected AS (
 SELECT *
 FROM (VALUES
 (56::bigint,28::bigint,
  'bc27b801f795125a3e5d0b9b930473fc4abda765b564f14c8ced2b07c64650f8'::text,
  '46277a0fdcc4a59664275639786828a21333ba5f27a23fa1781cbc192fd138de'::text,
  'ff08ea1f4b89475bb4bcf8d4a453e55058f21eba2de2daa1fb5943d1706293df'::text,
  '11fda6f33fb45e374078ceb6c5d1f4ea849800c7d753ff0d0dc4b5d92d4da83e'::text,
  0::integer,2::integer),
 (57::bigint,29::bigint,
  '11d2ba5ace6cc3ba3caf627470b2c02efbc81037f566793c89ded1868834ac65'::text,
  'd0cd4985307a72190e4a6033e0ecbdf32d1b8d119f33cfa76a398a277aa89994'::text,
  '85aaf92c2b87fc7ea80359498680bca371aaa0e974d65476328bb70e314b3fce'::text,
  '405d0fdb003646973b38d9a24c7580e3d5d6e4d18271d206e19b89ef6655f17c'::text,
  482::integer,94::integer)
 ) AS v(bvv_sample_id,wsf_sample_id,bvv_sample_json_sha,wsf_sample_json_sha,
        wsf_native_mask_sha,bvv_derived_grid_sha,wsf_settled_cells,bvv_bbox_candidates)
),
source_pairs AS (
 SELECT e.*, b.sample_json AS bj, w.sample_json AS wj,
   (b.sample_json->>'official_footprint_area_native_cell_equivalents')::numeric AS bvv_area,
   (b.sample_json->>'area_weighted_intersection_in_native_cells')::numeric AS intersection_area,
   (b.sample_json->>'area_weighted_union_in_native_cells')::numeric AS union_area,
   (b.sample_json->>'two_vintage_exploratory_area_iou')::numeric AS stored_iou,
   (b.sample_json->>'official_footprint_area_inside_wsf_positive')::numeric AS stored_bvv_recall,
   (b.sample_json->>'wsf_positive_area_covered_by_official_footprint')::numeric AS stored_wsf_coverage
 FROM expected e
 JOIN research.source_sample_v0 b ON b.sample_id=e.bvv_sample_id
 JOIN research.source_sample_v0 w ON w.sample_id=e.wsf_sample_id
 WHERE b.source_id='de.bayern.hausumringe'
   AND w.source_id='dlr.wsf.2019'
   AND b.sample_kind='public_metadata'
   AND w.sample_kind='geospatial_preview'
   AND b.model_input_approved IS FALSE AND w.model_input_approved IS FALSE
   AND b.sample_sha256=e.bvv_sample_json_sha
   AND w.sample_sha256=e.wsf_sample_json_sha
   AND b.sample_sha256=encode(sha256(convert_to(b.sample_json::text,'UTF8')),'hex')
   AND w.sample_sha256=encode(sha256(convert_to(w.sample_json::text,'UTF8')),'hex')
   AND b.provider_response_sha256='22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615'
   AND w.provider_response_sha256='8f06d03fcc3cc63930d216a834bca6c51275da6b436e1b2639a39952ddbf0503'
   AND b.sample_json->>'profile'='oc-bvv-oberbayern-original-shp-wsf2019-two-grid-exploratory-overlap-v0'
   AND b.sample_json->>'actual_independent_workflow'='https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43317649994'
   AND b.sample_json->>'official_shp_original_compressed_deflate_sha256'='22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615'
   AND b.sample_json->>'official_shp_original_uncompressed_sha256'='977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c'
   AND b.sample_json->>'official_shp_original_crc32'='55540a66'
   AND b.sample_json->>'original_shp_records_verified'='2703736'
   AND b.sample_json->>'original_shp_source_full_member_verified'='true'
   AND b.sample_json->>'original_wsf_raster_compressed_tile_sha256'='8f06d03fcc3cc63930d216a834bca6c51275da6b436e1b2639a39952ddbf0503'
   AND b.sample_json->>'original_wsf_raster_mask_sha256'=e.wsf_native_mask_sha
   AND b.sample_json->>'official_derived_coverage_grid_sha256'=e.bvv_derived_grid_sha
   AND b.sample_json->>'reference_dlr_wsf2019_neon_sample_id'=e.wsf_sample_id::text
   AND b.sample_json->>'wsf2019_settlement_positive_native_cells'=e.wsf_settled_cells::text
   AND b.sample_json->>'official_polygon_candidates_in_broad_utm_bbox'=e.bvv_bbox_candidates::text
   AND b.sample_json->>'mask_and_derived_grid_hashes_verified_in_read_only_neon_sql'='true'
   AND b.sample_json->>'source_2019_vs_2026_temporal_mismatch'='true'
   AND b.sample_json->>'official_survey_vintage_verified'='false'
   AND b.sample_json->>'population_representativeness_verified'='false'
   AND b.sample_json->>'insurer_exposure_or_tiv_inferred'='false'
   AND b.sample_json->>'model_input_approved'='false'
   AND w.sample_json->>'model_input_approved'='false'
   AND w.sample_json->>'epsg'='4326'
   AND w.sample_json->>'window_width'='32'
   AND w.sample_json->>'window_height'='32'
   AND COALESCE(w.sample_json->'window_counts',w.sample_json->'window_class_counts')->>'255'
       =e.wsf_settled_cells::text
   AND COALESCE(w.sample_json->'window_counts',w.sample_json->'window_class_counts')->>'0'
       =(1024-e.wsf_settled_cells)::text
),
checked AS (
 SELECT p.*,
   m.raster_row_count,m.valid_binary_row_count,m.settlement_ones,m.mask_sha
 FROM source_pairs p
 CROSS JOIN LATERAL (
   SELECT count(*) AS raster_row_count,
     count(*) FILTER(WHERE x.row_txt ~ '^[01]{32}$') AS valid_binary_row_count,
     SUM(length(x.row_txt)-length(replace(x.row_txt,'1',''))) AS settlement_ones,
     encode(sha256(convert_to(string_agg(x.row_txt,E'\n' ORDER BY x.ord),'UTF8')),'hex') AS mask_sha
   FROM jsonb_array_elements_text(p.wj->'window_raster_rows_binary_1_is_255')
       WITH ORDINALITY AS x(row_txt,ord)
 ) m
 WHERE m.raster_row_count=32
   AND m.valid_binary_row_count=32
   AND m.settlement_ones=p.wsf_settled_cells
   AND m.mask_sha=p.wsf_native_mask_sha
   AND p.bvv_area>0
   AND p.intersection_area>=0
   AND p.intersection_area<=p.bvv_area
   AND p.intersection_area<=p.wsf_settled_cells
   AND p.union_area>0
   AND p.union_area<=1024.000001
   AND abs(p.union_area-(p.bvv_area+p.wsf_settled_cells-p.intersection_area))<0.000003
   AND abs(p.stored_iou-p.intersection_area/p.union_area)<0.00000051
   AND abs(p.stored_bvv_recall-p.intersection_area/p.bvv_area)<0.00000051
   AND (
        (p.wsf_settled_cells=0 AND p.stored_wsf_coverage IS NULL)
     OR (p.wsf_settled_cells>0 AND
         abs(p.stored_wsf_coverage-p.intersection_area/p.wsf_settled_cells)<0.00000051)
   )
)
SELECT
 'bavaria-hu-by-wsf2019-original-two-window-readiness-v0'::text AS research_profile,
 bvv_sample_id,wsf_sample_id,wsf_settled_cells,bvv_bbox_candidates,
 bvv_area AS official_footprint_area_native_wsf_cell_equivalents,
 intersection_area AS footprint_settlement_intersection_native_cell_equivalents,
 union_area AS footprint_settlement_union_native_cell_equivalents,
 stored_iou AS exploratory_iou_two_different_scientific_classes,
 stored_bvv_recall AS fraction_footprint_inside_settlement_class,
 stored_wsf_coverage AS fraction_settlement_class_covered_by_footprints,
 raster_row_count,valid_binary_row_count,
 'EPSG:25832 native cadastral geometry vs original DLR EPSG:4326 mask'::text AS coordinate_support,
 '2019 WSF settlement class versus later-vintage BVV footprints; NOT building-vs-building IoU'::text AS semantic_limit,
 false AS population_representativeness_verified,
 false AS comparable_to_luxembourg_building_identity_recall,
 false AS historical_same_year_ground_truth_verified,
 false AS insurer_tiv_available,
 false AS cat_model_input_approved
FROM checked ORDER BY bvv_sample_id;
