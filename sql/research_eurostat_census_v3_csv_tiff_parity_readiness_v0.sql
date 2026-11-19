-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Private Neon, read-only, exact-source V3 2021 Census CSV-to-TIFF readiness.
-- Reproduces already-applied view in private insurance-risk-core.
-- Requires existing research.source_sample_v0 and
-- research.eurostat_census_2021_v3_polygon_parity_review_v0.
-- References **only** private research samples #60/#63/#65/#66.
--
-- 'offline_reference_preflight_ready=true' means integrity/identity of frozen
-- pre-existing metadata, NOT source CSV byte acquisition or population parity.
-- Original large GISCO static ZIP is documented_only; its automation terms
-- remain unknown. All admission flags are deliberately false.
--
CREATE OR REPLACE VIEW research.eurostat_census_v3_csv_tiff_parity_readiness_v0 AS
 WITH source_zip AS (
         SELECT s.sample_id AS zip_index_sample_id,
            s.source_id,
            s.sample_sha256 = encode(sha256(convert_to(s.sample_json::text, 'UTF8'::name)), 'hex'::text) AS zip_index_hash_valid,
            m.value ->> 'name'::text AS csv_zip_member,
            (m.value ->> 'compressed_size_bytes'::text)::bigint AS member_compressed_bytes,
            (m.value ->> 'uncompressed_size_bytes'::text)::bigint AS member_uncompressed_bytes,
            m.value ->> 'member_crc32_hex'::text AS member_crc32_hex,
            (m.value ->> 'local_header_offset'::text)::bigint AS local_header_offset
           FROM research.source_sample_v0 s
             CROSS JOIN LATERAL jsonb_array_elements(s.sample_json -> 'zip_members'::text) m(value)
          WHERE s.sample_id = 60 AND s.source_id = 'eurostat.gisco.census-population-grid.2021'::text AND s.sample_kind = 'public_metadata'::text AND s.research_only AND NOT s.model_input_approved AND (m.value ->> 'name'::text) = 'Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.csv'::text
        ), raster AS (
         SELECT p.sample_id AS raster_sample_id,
            p.source_id,
            p.product_version,
            p.sample_sha256 = encode(sha256(convert_to(p.sample_json::text, 'UTF8'::name)), 'hex'::text) AS raster_hash_valid,
            p.sample_json ->> 'source_nodata_value'::text AS raster_nodata,
            ((p.sample_json -> 'selected_original_positive_pixel'::text) ->> 'row_index_zero_based'::text)::integer AS target_row,
            ((p.sample_json -> 'selected_original_positive_pixel'::text) ->> 'column_index_zero_based'::text)::integer AS target_col,
            encode(sha256(convert_to(concat_ws(','::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'T'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'M'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'F'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'Y_LT15'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'Y_1564'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'Y_GE65'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'EMP'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'NAT'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'EU_OTH'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'OTH'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'SAME'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'CHG_IN'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'CHG_OUT'::text, ((p.sample_json -> 'selected_original_positive_pixel'::text) -> 'band_values'::text) ->> 'POPULATED'::text), 'UTF8'::name)), 'hex'::text) AS pinned_tiff_14_band_sha256
           FROM research.source_sample_v0 p
          WHERE p.sample_id = 63 AND p.source_id = 'eurostat.gisco.census-population-grid.2021'::text AND p.sample_kind = 'observed_values'::text AND p.research_only AND NOT p.model_input_approved
        ), spatial AS (
         SELECT eurostat_census_2021_v3_polygon_parity_review_v0.original_pixel_sample_id,
            eurostat_census_2021_v3_polygon_parity_review_v0.independent_gisco_sample_id,
            eurostat_census_2021_v3_polygon_parity_review_v0.independent_official_geometry_sample_id,
            eurostat_census_2021_v3_polygon_parity_review_v0.gisco_grid_id,
            eurostat_census_2021_v3_polygon_parity_review_v0.original_grid_id_matches_raster_cell
           FROM research.eurostat_census_2021_v3_polygon_parity_review_v0
        )
 SELECT z.source_id,
    z.zip_index_sample_id,
    r.raster_sample_id,
    spatial.independent_gisco_sample_id,
    spatial.independent_official_geometry_sample_id,
    z.csv_zip_member,
    z.member_compressed_bytes,
    z.member_uncompressed_bytes,
    z.member_crc32_hex,
    z.local_header_offset,
    r.product_version,
    r.target_row,
    r.target_col,
    r.raster_nodata,
    spatial.gisco_grid_id,
    r.pinned_tiff_14_band_sha256,
    z.zip_index_hash_valid,
    r.raster_hash_valid,
    spatial.original_grid_id_matches_raster_cell,
    z.zip_index_hash_valid AND r.raster_hash_valid AND spatial.original_grid_id_matches_raster_cell AND z.member_compressed_bytes = 49110575 AND z.member_uncompressed_bytes = 339625996 AND z.member_crc32_hex = '54cdc404'::text AND z.local_header_offset = 209230036 AND r.pinned_tiff_14_band_sha256 = '206185ef8953f67e5c8516a8b9d95b2e66907b28b5e5f1a4d98836e913ac7ec8'::text AS offline_reference_preflight_ready,
    'documented_only'::text AS gis_static_zip_acquisition_contract_state,
    'unknown'::text AS gis_static_zip_automation_rights,
    false AS original_full_v3_csv_observed,
    false AS original_14_band_csv_tiff_parity_verified,
    false AS original_zip_archive_sha256_verified,
    false AS production_cat_model_input_admitted
   FROM source_zip z
     JOIN raster r ON r.source_id = z.source_id
     JOIN spatial ON spatial.original_pixel_sample_id = r.raster_sample_id;
