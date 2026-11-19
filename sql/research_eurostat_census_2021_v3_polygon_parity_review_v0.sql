-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only private Neon research view of three independent source checks:
--   original 2021 V3 TIFF cell sample (#63),
--   original 2021 GISCO cell ID + 2024 country ID samples (#65),
--   original 2021 GISCO one-cell GeoJSON polygon geometry metrics (#66).
-- The original GISCO GeoJSON/ZIP source bytes are NOT persisted in Git.
-- Geometry was independently checked against TIFF centre, 1km raster square
-- and verified via PostGIS in private Neon before this summary was admitted.
-- Do not infer Census Grid V3 population count parity: source ID API provides
-- geographic membership only, not numeric census T/M/F values.
-- Must apply the existing per-pixel and per-grid-ID private Neon views first.

CREATE OR REPLACE VIEW research.eurostat_census_2021_v3_polygon_parity_review_v0 AS
SELECT c.original_pixel_sample_id,
       c.independent_gisco_sample_id,
       g.sample_id AS independent_official_geometry_sample_id,
       c.source_id,c.product_version,c.raster_row,c.raster_column,
       c.gisco_grid_id,c.gisco_nuts3,c.independent_country_2024,
       c.population_total,
       c.centroid_etrs89_laea,c.centroid_wgs84,
       (g.sample_json->>'original_official_polygon_area_m2')::numeric
           AS provider_polygon_area_m2,
       (g.sample_json->>'original_polygon_vs_exact_1km_tiff_cell_max_boundary_offset_m')::numeric
           AS provider_polygon_boundary_difference_m,
       g.provider_response_sha256 AS original_provider_geojson_response_sha256,
       c.original_grid_id_matches_raster_cell,
       false AS independent_population_count_verified,
       false AS original_full_archive_sha256_verified,
       false AS nextgen_cat_model_input_approved
FROM research.eurostat_census_2021_v3_cell_identity_review_v0 c
JOIN research.source_sample_v0 g
  ON g.source_id = c.source_id
 AND g.sample_kind = 'public_metadata'
 AND g.sample_json->>'profile' =
     'eurostat-gisco-2021-independent-official-1km-polygon-geometric-parity-v0'
 AND (g.sample_json->>'linked_raster_sample_id')::bigint = c.original_pixel_sample_id
 AND (g.sample_json->>'linked_id_sample_id')::bigint = c.independent_gisco_sample_id
 AND g.sample_json->>'original_geojson_grid_id' = c.gisco_grid_id
 AND g.sample_json->>'official_geojson_feature_type' = 'MultiPolygon'
 AND g.sample_json->>'official_polygon_valid' = 'true'
 AND g.sample_json->>'official_polygon_covers_original_pixel_center' = 'true'
 AND g.sample_json->>'original_response_body_persisted' = 'false'
 AND g.sample_json->>'original_polygon_geometry_persisted' = 'false'
 AND g.sample_json->>'independent_population_count_rechecked' = 'false'
 AND g.sample_json->>'model_input_approved' = 'false'
 AND (g.sample_json->>'original_official_polygon_area_m2')::numeric
     BETWEEN 999999 AND 1000001
 AND (g.sample_json->>'original_polygon_vs_exact_1km_tiff_cell_max_boundary_offset_m')::numeric
     < 0.01
 AND g.sample_sha256 = encode(sha256(convert_to(g.sample_json::text,'UTF8')),'hex')
 AND g.research_only = true
 AND g.model_input_approved = false;

-- SELECT original_pixel_sample_id,independent_gisco_sample_id,
--        independent_official_geometry_sample_id,gisco_grid_id,
--        provider_polygon_area_m2,provider_polygon_boundary_difference_m,
--        independent_population_count_verified,
--        nextgen_cat_model_input_approved
-- FROM research.eurostat_census_2021_v3_polygon_parity_review_v0;
