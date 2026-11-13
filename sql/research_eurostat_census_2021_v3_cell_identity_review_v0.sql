-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Independent *spatial identity* check of one research-only original Census
-- Grid 2021 V3 TIFF pixel, against two different original GISCO ID API GETs.
-- Requires prior research_eurostat_census_2021_v3_pixel_research_v0.sql.
-- Read-only projected view: all providers' original response JSON is kept out
-- of this public Git repository. Response SHA-256 stored privately in Neon.
--
-- Do not infer V3 population T-value validation from the independent GISCO
-- ID service, which returns grid/country metadata, not the population count.
-- Model, person, individual underwriting or raw-source release remains false.

CREATE OR REPLACE VIEW research.eurostat_census_2021_v3_cell_identity_review_v0 AS
WITH source_grid_id AS (
 SELECT s.sample_id AS independent_gisco_sample_id,
        (s.sample_json->>'source_sample_link')::bigint AS source_pixel_sample_id,
        s.sample_json->>'census_grid_id' AS gisco_grid_id,
        s.sample_json->>'census_grid_nuts3' AS gisco_nuts3,
        s.sample_json->>'administrative_country_2024' AS independent_country_2024,
        s.sample_json->>'source_version_caveat' AS version_limit,
        s.provider_response_sha256 AS original_gisco_response_sha256,
        s.sample_json->>'original_country_api_sha256' AS original_country_response_sha256
 FROM research.source_sample_v0 s
 WHERE s.source_id = 'eurostat.gisco.census-population-grid.2021'
   AND s.sample_kind = 'public_metadata'
   AND s.sample_json->>'profile' =
       'eurostat-gisco-2021-independent-official-grid-id-v0'
   AND s.sample_sha256 =
       encode(sha256(convert_to(s.sample_json::text,'UTF8')),'hex')
   AND s.research_only = true AND s.model_input_approved = false
),
linked AS (
 SELECT p.sample_id AS original_pixel_sample_id,
        g.independent_gisco_sample_id,
        p.source_id,
        p.product_version,
        p.raster_row, p.raster_column,
        p.population_total,
        p.centroid_etrs89_laea, p.centroid_wgs84,
        g.gisco_grid_id, g.gisco_nuts3, g.independent_country_2024,
        g.original_gisco_response_sha256,
        g.original_country_response_sha256,
        g.version_limit,
        (g.gisco_grid_id = g.independent_country_2024 ||
          '_CRS3035RES1000mN' ||
          (floor((ST_Y(p.centroid_etrs89_laea)-500)/1000)::bigint * 1000)::text ||
          'E' ||
          (floor((ST_X(p.centroid_etrs89_laea)-500)/1000)::bigint * 1000)::text
        ) AS original_grid_id_matches_raster_cell,
        p.research_only, p.model_input_approved
 FROM research.eurostat_census_2021_v3_pixel_research_v0 p
 JOIN source_grid_id g ON p.sample_id = g.source_pixel_sample_id
)
SELECT *,
       false AS independent_population_count_verification,
       false AS full_zip_archive_sha256_verified,
       false AS production_exposure_model_admitted
FROM linked
WHERE original_grid_id_matches_raster_cell = true;

-- Research verification in Neon:
-- SELECT original_pixel_sample_id, independent_gisco_sample_id,
--        gisco_grid_id, gisco_nuts3, independent_country_2024,
--        original_grid_id_matches_raster_cell,
--        independent_population_count_verification,
--        production_exposure_model_admitted
-- FROM research.eurostat_census_2021_v3_cell_identity_review_v0;
