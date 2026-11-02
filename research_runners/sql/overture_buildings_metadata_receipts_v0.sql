-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Research-only, non-destructive metadata RECEIPT for three exact Overture
-- building Parquet originals. Apply ONLY to a Neon isolation/test branch,
-- never directly to production. No source Parquet row or geometry is imported.
-- Rights and scientific model admission are explicitly false.
-- Evidence: docs/research/overture-global-building-crosswalk-preflight-20261102.md

CREATE TABLE IF NOT EXISTS research.overture_original_building_file_probe_v0 (
  source_candidate_id text NOT NULL DEFAULT 'overture.maps.buildings'
    CHECK (source_candidate_id = 'overture.maps.buildings'),
  release_id text NOT NULL CHECK (release_id = '2026-10-21.0'),
  original_s3_key text NOT NULL
    CHECK (original_s3_key LIKE 'release/2026-10-21.0/theme=buildings/type=building/part-%'),
  original_last_modified timestamptz NOT NULL,
  original_bytes bigint NOT NULL CHECK (original_bytes > 0),
  reported_parquet_rows bigint NOT NULL CHECK (reported_parquet_rows > 0),
  footer_metadata_bytes integer NOT NULL CHECK (footer_metadata_bytes > 0),
  schema_entry_count integer NOT NULL CHECK (schema_entry_count = 63),
  s3_etag text NOT NULL,
  parquet_magic_verified boolean NOT NULL DEFAULT true CHECK (parquet_magic_verified IS TRUE),
  metadata_header_decoded boolean NOT NULL DEFAULT true CHECK (metadata_header_decoded IS TRUE),
  original_rows_ingested boolean NOT NULL DEFAULT false CHECK (original_rows_ingested IS FALSE),
  entire_object_sha256_verified boolean NOT NULL DEFAULT false CHECK (entire_object_sha256_verified IS FALSE),
  source_rights_approved boolean NOT NULL DEFAULT false CHECK (source_rights_approved IS FALSE),
  actual_geometry_validated boolean NOT NULL DEFAULT false CHECK (actual_geometry_validated IS FALSE),
  insurer_exposure_admitted boolean NOT NULL DEFAULT false CHECK (insurer_exposure_admitted IS FALSE),
  cat_model_input_approved boolean NOT NULL DEFAULT false CHECK (cat_model_input_approved IS FALSE),
  recorded_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(release_id, original_s3_key)
);

INSERT INTO research.overture_original_building_file_probe_v0
(source_candidate_id,release_id,original_s3_key,original_last_modified,original_bytes,
 reported_parquet_rows,footer_metadata_bytes,schema_entry_count,s3_etag)
VALUES
('overture.maps.buildings','2026-10-21.0',
 'release/2026-10-21.0/theme=buildings/type=building/part-00000-85375c54-5dfb-57c7-b21d-8b5e5245ad06-c000.zstd.parquet',
 '2026-10-21T17:38:24Z',533137080,5002132,668264,63,'"852e6e08cf4815b05e085cf89ab1648d-8"'),
('overture.maps.buildings','2026-10-21.0',
 'release/2026-10-21.0/theme=buildings/type=building/part-00001-25a868c6-9ddc-5e1c-8e0e-8286ae2005d9-c000.zstd.parquet',
 '2026-10-21T17:41:59Z',533341551,5001978,703774,63,'"84781de4549ff5d211bce1ca02e2c9e6-8"'),
-- Provider STAC item 00226: verified Luxembourg-city *file extent* candidate.
-- S3 original file header and footer metadata verified; no rows ingested.
('overture.maps.buildings','2026-10-21.0',
 'release/2026-10-21.0/theme=buildings/type=building/part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet',
 '2026-10-21T17:46:03Z',609459333,5054907,1461640,63,'"a4a0d16d3ca5f460b2626facb71daae5-10"')
ON CONFLICT (release_id,original_s3_key) DO NOTHING;

-- Reviewable isolated-branch assertions (read-only):
-- SELECT COUNT(*) AS files, SUM(reported_parquet_rows) AS rows_in_sampled_files,
-- SUM(original_bytes) AS original_file_bytes,
-- COUNT(*) FILTER (WHERE cat_model_input_approved OR source_rights_approved OR
--   original_rows_ingested OR insurer_exposure_admitted) AS accidentally_approved
-- FROM research.overture_original_building_file_probe_v0;
-- Expected: files=3, rows_in_sampled_files=15059017,
-- original_file_bytes=1675937964, accidentally_approved=0.
