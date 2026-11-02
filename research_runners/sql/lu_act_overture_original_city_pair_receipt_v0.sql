-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Apply only to ISOLATED insurance Neon research branch, never production.
-- Research-only aggregate of actual original Luxembourg ACT 2026 + Overture
-- 2026 geometries; no original provider WKB, geometry coordinates, source
-- building IDs, insurer accounts or TIV stored. Both source products retain
-- independent rights and scientific model-admission requirements.
-- Evidence: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41498511267

CREATE TABLE IF NOT EXISTS research.lu_act_overture_original_city_pair_receipt_v0 (
 act_release text NOT NULL CHECK (act_release = '2026-10-01'),
 overture_release text NOT NULL CHECK (overture_release = '2026-10-21.0'),
 act_original_zip_sha256 text NOT NULL
   CHECK (act_original_zip_sha256 = '6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3'),
 overture_source_row_group integer NOT NULL CHECK (overture_source_row_group = 182),
 act_original_source_rows integer NOT NULL CHECK (act_original_source_rows = 230353),
 act_topologically_invalid_source_rows integer NOT NULL CHECK (act_topologically_invalid_source_rows >= 0),
 act_city_footprints integer NOT NULL CHECK (act_city_footprints >= 0),
 overture_city_footprints integer NOT NULL CHECK (overture_city_footprints >= 0),
 candidate_iou_threshold numeric(5,4) NOT NULL CHECK (candidate_iou_threshold = 0.7500),
 above_threshold_overlap_pairs integer NOT NULL CHECK (above_threshold_overlap_pairs >= 0),
 reciprocal_one_to_one_geometric_candidates integer NOT NULL
   CHECK (reciprocal_one_to_one_geometric_candidates >= 0),
 ambiguous_act_candidate_features integer NOT NULL CHECK (ambiguous_act_candidate_features >= 0),
 source_run_url text NOT NULL,
 original_provider_geometry_persisted boolean NOT NULL DEFAULT false
   CHECK (original_provider_geometry_persisted IS FALSE),
 independent_physical_identity_verified boolean NOT NULL DEFAULT false
   CHECK (independent_physical_identity_verified IS FALSE),
 source_licensing_scientifically_approved boolean NOT NULL DEFAULT false
   CHECK (source_licensing_scientifically_approved IS FALSE),
 insured_TIV_inferred boolean NOT NULL DEFAULT false
   CHECK (insured_TIV_inferred IS FALSE),
 insurance_CAT_model_input_approved boolean NOT NULL DEFAULT false
   CHECK (insurance_CAT_model_input_approved IS FALSE),
 recorded_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY (act_release,overture_release,overture_source_row_group)
);

INSERT INTO research.lu_act_overture_original_city_pair_receipt_v0
(act_release,overture_release,act_original_zip_sha256,overture_source_row_group,act_original_source_rows,
 act_topologically_invalid_source_rows,act_city_footprints,overture_city_footprints,
 candidate_iou_threshold,above_threshold_overlap_pairs,reciprocal_one_to_one_geometric_candidates,
 ambiguous_act_candidate_features,source_run_url)
VALUES
('2026-10-01','2026-10-21.0','6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3',
 182,230353,66,139,69,0.7500,5,5,0,
 'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41498511267')
ON CONFLICT (act_release,overture_release,overture_source_row_group) DO NOTHING;

-- Verified isolated Neon: 1 source comparison receipt, 139 ACT source polygons,
-- 69 Overture source polygons, 5 reciprocal geometric overlap candidates
-- (IoU >= 0.75), 0 source identity/rights/insurance model admissions.
-- Production insurance/main does not have this table; source features remain
-- strictly transient in GitHub runners, with no raw provider data retained.
