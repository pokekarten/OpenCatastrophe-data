-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- Source: esa.worldcover.2021.v200, exactly existing private research sample #30.
-- Product: ESA WorldCover 2021 v200, tile N48E009, one stored decoded block.
-- Reference: https://worldcover2021.esa.int/data/docs/WorldCover_PUM_V2.0.pdf
-- Run each SELECT independently using the authorized Neon research connection.
-- SELECT-only: no external provider access, stored source bytes, migrations or writes.
-- The actual source compressed-range and TIFF-header SHA strings are checked for
-- syntax here, NOT independently rehashed from original provider response bytes.
-- Exact input-table evidence can change: re-review original source receipt if so.
-- A passing result is limited to one stored research aggregate and not admission.

WITH s AS (
 SELECT source_id, sample_id, sample_json AS j,
        model_input_approved, source_byte_persistence_authorized
 FROM research.source_sample_v0
 WHERE source_id = 'esa.worldcover.2021.v200' AND sample_id = 30
), c AS (
 SELECT s.*, kv.key AS class_code, kv.value AS class_count
 FROM s CROSS JOIN LATERAL jsonb_each_text(s.j->'observed_class_counts') kv
), m AS (
 SELECT min(source_id) AS source_id, min(sample_id) AS sample_id,
        count(*) AS nonzero_class_count,
        sum(class_count::bigint) AS sum_class_counts,
        bool_and(class_code IN ('0','10','20','30','40','50','60','70','80','90','95','100')) AS known_esa_codes,
        bool_and(class_count ~ '^[0-9]+$' AND class_count::bigint >= 0) AS nonnegative_integer_counts,
        min((j->>'decoded_original_pixel_count')::bigint) AS declared_pixel_count,
        bool_and(j->>'tile_id'='N48E009' AND j->>'product_version'='2021 v200') AS exact_product_and_tile,
        bool_and((j->>'compressed_original_sha256') ~ '^[0-9a-f]{64}$') AS compressed_slice_hash_syntax,
        bool_and((j->>'original_tiff_header_sha256') ~ '^[0-9a-f]{64}$') AS header_hash_syntax,
        bool_and((j->>'full_original_tiff_verified')='false'
          AND (j->>'raw_raster_pixels_persisted')='false'
          AND model_input_approved=false AND source_byte_persistence_authorized=false) AS no_false_full_source_or_admission
 FROM c
)
SELECT source_id, sample_id, nonzero_class_count, sum_class_counts,
       declared_pixel_count, (sum_class_counts=declared_pixel_count) AS class_count_conserved,
       known_esa_codes, nonnegative_integer_counts, exact_product_and_tile,
       compressed_slice_hash_syntax, header_hash_syntax,
       no_false_full_source_or_admission
FROM m;

-- Synthetic-only negative and positive controls; never modify the source row.
WITH cases(id, counts, expected_pixels, should_pass) AS (
 VALUES
 ('valid_synthetic', '{"10":1,"50":1}'::jsonb, 2::bigint, true),
 ('bad_code', '{"10":1,"42":1}'::jsonb, 2::bigint, false),
 ('missing_pixel', '{"10":1}'::jsonb, 2::bigint, false),
 ('negative_class', '{"10":-1,"50":3}'::jsonb, 2::bigint, false),
 ('nodata_allowed', '{"0":1,"10":1}'::jsonb, 2::bigint, true)
), checked AS (
 SELECT id, should_pass,
 (SELECT count(*)>0
         AND bool_and(key IN ('0','10','20','30','40','50','60','70','80','90','95','100')
                      AND value ~ '^[0-9]+$')
         AND sum(value::bigint)=expected_pixels
  FROM jsonb_each_text(counts)) AS actual_pass
 FROM cases
)
SELECT id, should_pass, actual_pass,
       (should_pass=actual_pass) AS control_pass
FROM checked ORDER BY id;
