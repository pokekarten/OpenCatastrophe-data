-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Isolated research Neon only. NEVER execute on insurance production/main.
-- Source-level aggregate receipt from immutable public Overture 2026-10-21.0
-- part 00226. No provider WKB/IDs, source rows or insurer TIV stored.
-- Original-only proof:
-- https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41497879623
-- Overture Buildings is ODbL 1.0; legal/scientific/model admission not granted.

CREATE TABLE IF NOT EXISTS research.overture_lu_city_one_group_geometry_receipt_v0 (
  source_release text NOT NULL CHECK (source_release = '2026-10-21.0'),
  source_file text NOT NULL
    CHECK (source_file LIKE '%part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet'),
  row_group_ordinal integer NOT NULL CHECK (row_group_ordinal = 182),
  row_group_source_rows integer NOT NULL CHECK (row_group_source_rows = 19095),
  bbox_intersection_candidates integer NOT NULL CHECK (bbox_intersection_candidates >= 0),
  real_geometry_positive_overlap integer NOT NULL CHECK (real_geometry_positive_overlap >= 0),
  invalid_original_geometry integer NOT NULL CHECK (invalid_original_geometry >= 0),
  sample_geodesic_area_median_m2 numeric(14,2),
  sample_geodesic_area_n integer NOT NULL CHECK (sample_geodesic_area_n BETWEEN 0 AND 64),
  declared_selected_column_compressed_bytes bigint NOT NULL
    CHECK (declared_selected_column_compressed_bytes > 0),
  verified_actions_run text NOT NULL,
  original_geometry_bytes_retained boolean NOT NULL DEFAULT false
    CHECK (original_geometry_bytes_retained IS FALSE),
  source_rights_approved boolean NOT NULL DEFAULT false
    CHECK (source_rights_approved IS FALSE),
  insurer_exposure_admitted boolean NOT NULL DEFAULT false
    CHECK (insurer_exposure_admitted IS FALSE),
  CAT_model_input_approved boolean NOT NULL DEFAULT false
    CHECK (CAT_model_input_approved IS FALSE),
  recorded_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(source_release, source_file, row_group_ordinal)
);

INSERT INTO research.overture_lu_city_one_group_geometry_receipt_v0
(source_release,source_file,row_group_ordinal,row_group_source_rows,
 bbox_intersection_candidates,real_geometry_positive_overlap,
 invalid_original_geometry,sample_geodesic_area_median_m2,
 sample_geodesic_area_n,declared_selected_column_compressed_bytes,
 verified_actions_run)
VALUES ('2026-10-21.0',
 'release/2026-10-21.0/theme=buildings/type=building/part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet',
 182,19095,69,69,0,142.24,64,1583294,
 'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41497879623')
ON CONFLICT (source_release,source_file,row_group_ordinal) DO NOTHING;

-- Isolated Neon readback: 1 row, 19,095 source-group rows examined,
-- 69 original polygon overlaps, 0 invalid source city geometries.
-- Production has zero admitted exposures and does not contain this table.
