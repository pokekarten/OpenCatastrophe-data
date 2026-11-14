-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only, fail-closed quality projection for research-only native GeoTIFF
-- 32x32 samples. This deliberately DOES NOT authorize or create model inputs.
-- Run in the separate insurance-risk-core Neon research schema.
CREATE VIEW research.native_raster_sample_quality_v0 AS
WITH native_samples AS (
    SELECT
        sample_id,
        source_id,
        sample_kind,
        provider_response_sha256,
        sample_sha256,
        sample_json,
        research_only,
        model_input_approved,
        (sample_json->>'window_width')::integer AS width_px,
        (sample_json->>'window_height')::integer AS height_px,
        coalesce(
            sample_json->'window_counts',
            sample_json->'window_class_counts'
        ) AS declared_class_counts
    FROM research.source_sample_v0
    WHERE sample_json->>'sample_subtype' LIKE 'native_geotiff_%'
),
rows_checked AS (
    SELECT
        s.sample_id,
        count(*)::integer AS row_count,
        min(length(r.bits))::integer AS min_row_width,
        max(length(r.bits))::integer AS max_row_width,
        bool_and(r.bits ~ '^[01]+$') AS binary_rows_only,
        sum(length(r.bits) - length(replace(r.bits,'1','')))::integer AS settlement_255_px,
        sum(length(r.bits) - length(replace(r.bits,'0','')))::integer AS nonsettlement_0_px,
        encode(
            sha256(convert_to(string_agg(r.bits, E'\n' ORDER BY r.row_num), 'UTF8')),
            'hex'
        ) AS native_rows_sha256
    FROM native_samples s
    CROSS JOIN LATERAL jsonb_array_elements_text(
        s.sample_json->'window_raster_rows_binary_1_is_255'
    ) WITH ORDINALITY AS r(bits, row_num)
    GROUP BY s.sample_id
)
SELECT
    s.sample_id,
    s.source_id,
    s.sample_json->>'sample_subtype' AS native_subtype,
    s.provider_response_sha256 AS compressed_original_range_sha256,
    r.native_rows_sha256,
    s.sample_json->'window_bbox_lonlat' AS bbox_lonlat,
    s.width_px,
    s.height_px,
    r.row_count,
    r.settlement_255_px,
    r.nonsettlement_0_px,
    r.binary_rows_only,
    s.declared_class_counts,
    (
        s.research_only
        AND NOT s.model_input_approved
        AND s.sample_kind='geospatial_preview'
        AND s.width_px=32
        AND s.height_px=32
        AND r.row_count=s.height_px
        AND r.min_row_width=s.width_px
        AND r.max_row_width=s.width_px
        AND r.binary_rows_only
        AND r.settlement_255_px+r.nonsettlement_0_px=s.width_px*s.height_px
        AND r.settlement_255_px=(s.declared_class_counts->>'255')::integer
        AND r.nonsettlement_0_px=(s.declared_class_counts->>'0')::integer
        AND s.sample_json->>'epsg'='4326'
        AND jsonb_typeof(s.sample_json->'window_bbox_lonlat')='array'
        AND jsonb_array_length(s.sample_json->'window_bbox_lonlat')=4
        AND s.sample_sha256=encode(
            sha256(convert_to(s.sample_json::text,'UTF8')),'hex'
        )
    ) AS internal_sample_integrity_ok
FROM native_samples s
JOIN rows_checked r ON r.sample_id=s.sample_id;
