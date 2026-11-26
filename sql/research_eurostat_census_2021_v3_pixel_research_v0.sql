-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Reproducible add-only private Neon insurance-risk-core research projection.
-- Only sample_json with a validated SHA-256, explicitly research_only and
-- NOT model_input_approved is eligible. No provider originals, individual
-- exposure, person, policy or insurer portfolio is contained in this view.
-- Requires the existing PostGIS extension; no extension is modified here.
-- Source rights and scientific usability must still be separately reviewed.
CREATE OR REPLACE VIEW research.eurostat_census_2021_v3_pixel_research_v0 AS
WITH verified AS (
 SELECT
   s.sample_id,
   s.source_id,
   s.product_version,
   s.source_url,
   s.provider_response_sha256,
   s.sample_sha256,
   (s.sample_json->'selected_original_positive_pixel'->>'row_index_zero_based')::integer
      AS raster_row,
   (s.sample_json->'selected_original_positive_pixel'->>'column_index_zero_based')::integer
      AS raster_column,
   ST_SetSRID(ST_MakePoint(
      (s.sample_json->'selected_original_positive_pixel'->>'epsg3035_cell_center_x_m')::double precision,
      (s.sample_json->'selected_original_positive_pixel'->>'epsg3035_cell_center_y_m')::double precision
   ),3035)::geometry(Point,3035) AS centroid_etrs89_laea,
   (s.sample_json->'selected_original_positive_pixel'->'band_values'->>'T')::integer
      AS population_total,
   (s.sample_json->'selected_original_positive_pixel'->'band_values'->>'M')::integer
      AS population_male,
   (s.sample_json->'selected_original_positive_pixel'->'band_values'->>'F')::integer
      AS population_female,
   (s.sample_json->'selected_original_positive_pixel'->'band_values'->>'Y_LT15')::integer
      AS population_under15,
   (s.sample_json->'selected_original_positive_pixel'->'band_values'->>'Y_1564')::integer
      AS population_15_64,
   (s.sample_json->'selected_original_positive_pixel'->'band_values'->>'Y_GE65')::integer
      AS population_over65,
   (s.sample_json->'selected_original_positive_pixel'->'band_values'->>'EMP')::integer
      AS employed,
   (s.sample_json->'selected_original_positive_pixel'->'band_values'->>'POPULATED')::integer
      AS populated_flag,
   (s.sample_json->>'source_nodata_value')::integer AS source_nodata,
   s.research_only,
   s.model_input_approved
 FROM research.source_sample_v0 AS s
 WHERE s.source_id='eurostat.gisco.census-population-grid.2021'
   AND s.sample_kind='observed_values'
   AND s.sample_json->>'profile'='eurostat-gisco-2021-v3-original-tiff-positive-pixel-v0'
   AND s.sample_sha256=encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
   AND s.research_only=true
   AND s.model_input_approved=false
)
SELECT verified.*,
 ST_Transform(verified.centroid_etrs89_laea,4326)::geometry(Point,4326)
      AS centroid_wgs84,
 false AS commercial_underwriting_authorized,
 false AS nextgen_cat_model_input_admitted
FROM verified;

-- Query source-limited research result:
-- SELECT sample_id,raster_row,raster_column,
--        ST_AsText(centroid_etrs89_laea) AS etrs89_laea,
--        ST_AsText(centroid_wgs84) AS wgs84,
--        population_total,population_male,population_female,
--        source_nodata,model_input_approved
-- FROM research.eurostat_census_2021_v3_pixel_research_v0;
--
-- WARNING: this WGS84 view can be mapped but does not locate an insured
-- building, identify a private household, or support policy decisions.
