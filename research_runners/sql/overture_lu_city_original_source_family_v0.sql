-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Isolated insurance Neon research ONLY. Never run in production main.
-- Provider Overture Maps release 2026-10-21.0, original part 00226,
-- source-family fields for the same 69 Luxembourg-city bbox candidate rows.
-- Upstream metadata labels are not legal/scientific licence certification.
-- Original-only source evidence: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41500090059
-- No original feature IDs, record IDs, geometry bytes, location coordinates or TIV.

CREATE TABLE IF NOT EXISTS research.lu_overture_original_source_family_receipt_v0 (
 source_release text NOT NULL CHECK (source_release='2026-10-21.0'),
 rowgroup_ordinal integer NOT NULL CHECK (rowgroup_ordinal=182),
 city_bbox_source_rows integer NOT NULL CHECK(city_bbox_source_rows=69),
 osm_dataset_label_rows integer NOT NULL CHECK(osm_dataset_label_rows>=0),
 microsoft_ml_dataset_label_rows integer NOT NULL CHECK(microsoft_ml_dataset_label_rows>=0),
 original_odbl_license_tag_rows integer NOT NULL CHECK(original_odbl_license_tag_rows>=0),
 source_rows_missing_lineage integer NOT NULL CHECK(source_rows_missing_lineage>=0),
 source_rows_multiple_distinct_datasets integer NOT NULL CHECK(source_rows_multiple_distinct_datasets>=0),
 original_gers_ids_persisted boolean NOT NULL DEFAULT false
   CHECK (original_gers_ids_persisted IS FALSE),
 source_provider_rights_independently_reviewed boolean NOT NULL DEFAULT false
   CHECK (source_provider_rights_independently_reviewed IS FALSE),
 physical_building_identity_proven boolean NOT NULL DEFAULT false
   CHECK (physical_building_identity_proven IS FALSE),
 insurance_model_input_admitted boolean NOT NULL DEFAULT false
   CHECK (insurance_model_input_admitted IS FALSE),
 source_proof_url text NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(source_release,rowgroup_ordinal)
);

INSERT INTO research.lu_overture_original_source_family_receipt_v0
 (source_release,rowgroup_ordinal,city_bbox_source_rows,osm_dataset_label_rows,
  microsoft_ml_dataset_label_rows,original_odbl_license_tag_rows,
  source_rows_missing_lineage,source_rows_multiple_distinct_datasets,source_proof_url)
VALUES ('2026-10-21.0',182,69,64,5,69,0,0,
 'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41500090059')
ON CONFLICT (source_release,rowgroup_ordinal) DO NOTHING;

-- 64 source polygons list OpenStreetMap, 5 list Microsoft ML Buildings.
-- 69 source rows have original ODbL-1.0 licence tags; neither ODbL tag nor
-- OSM/Microsoft upstream category proves legal derivative use, independence
-- from ACT source, policyholders, or permitted CAT model admission.
