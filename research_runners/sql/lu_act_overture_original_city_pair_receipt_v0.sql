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


-- Follow-up independently verified full original-source IoU histogram:
-- https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41499209669
-- Schema change and UPDATE apply ONLY to the isolated CAT research Neon branch.
ALTER TABLE research.lu_act_overture_original_city_pair_receipt_v0
 ADD COLUMN IF NOT EXISTS positive_area_source_polygon_pairs integer,
 ADD COLUMN IF NOT EXISTS act_best_iou_histogram jsonb,
 ADD COLUMN IF NOT EXISTS overture_best_iou_histogram jsonb,
 ADD COLUMN IF NOT EXISTS histogram_source_run_url text;

UPDATE research.lu_act_overture_original_city_pair_receipt_v0
SET positive_area_source_polygon_pairs=282,
    act_best_iou_histogram='{"no_positive_area_overlap":3,"iou_below_0_25":72,"iou_0_25_to_0_50":40,"iou_0_50_to_0_75":19,"iou_at_least_0_75":5}'::jsonb,
    overture_best_iou_histogram='{"no_positive_area_overlap":6,"iou_below_0_25":6,"iou_0_25_to_0_50":33,"iou_0_50_to_0_75":19,"iou_at_least_0_75":5}'::jsonb,
    histogram_source_run_url='https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41499209669'
WHERE act_release='2026-10-01' AND overture_release='2026-10-21.0'
 AND overture_source_row_group=182
 AND original_provider_geometry_persisted=FALSE
 AND insurance_CAT_model_input_approved=FALSE;
-- Verified: all 139 ACT and 69 Overture candidate polygons conserved in
-- the separate source-best-IoU histograms; 282 positive-area polygon pairs
-- and 5 reciprocal geometric candidates. Not distinct real-world buildings.


-- Independently verified source attribution for the 5 strict original
-- ACT–Overture geometric candidates, original workflow SUCCESS with 16 tests:
-- https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41500592616
-- Aggregates only; no row-level OSM ID/ACT building ID/geometry persisted.
ALTER TABLE research.lu_act_overture_original_city_pair_receipt_v0
 ADD COLUMN IF NOT EXISTS strict_candidate_overture_source_family_counts jsonb,
 ADD COLUMN IF NOT EXISTS strict_candidate_source_family_run_url text;

UPDATE research.lu_act_overture_original_city_pair_receipt_v0
SET strict_candidate_overture_source_family_counts =
    '{"OpenStreetMap":5,"Microsoft ML Buildings":0,"unknown_or_multiple":0}'::jsonb,
    strict_candidate_source_family_run_url =
    'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41500592616'
WHERE act_release='2026-10-01' AND overture_release='2026-10-21.0'
 AND overture_source_row_group=182
 AND original_provider_geometry_persisted=FALSE
 AND independent_physical_identity_verified=FALSE
 AND insurance_CAT_model_input_approved=FALSE;
-- Verified isolated Neon readback: 5 OSM-sourced shape candidates,
-- 0 Microsoft ML-sourced and 0 unidentified. Source identity and insurance
-- CAT model source use remain explicitly NOT approved.


-- Exact original ACT per-feature Source provenance, aggregate only.
-- [Original full ACT ZIP x Overture run 41538722511]:
-- 26/26 synthetic tests PASS; publisher SHA-pinned ACT ZIP and GPKG; all 139
-- sampled ACT city polygons are Bati3DVDL, including all five strict ACT
-- geometry candidates; the five Overture candidate labels are OpenStreetMap.
-- The official ACT value describes the source of *digitisation*, not
-- independent survey or verified same-physical-building identity.
-- Apply ONLY on isolated insurance Neon research branch br-bold-unit-baf2smqf.
-- No geometry, IDs, source feature rows, policy records or insured TIV.
ALTER TABLE research.lu_act_overture_original_city_pair_receipt_v0
 ADD COLUMN IF NOT EXISTS act_city_digitizing_source_family_counts jsonb,
 ADD COLUMN IF NOT EXISTS act_strict_candidate_digitizing_source_family_counts jsonb,
 ADD COLUMN IF NOT EXISTS act_digitizing_source_original_run_url text;

DO $act_original_source_precondition$
BEGIN
 IF (
  SELECT count(*)
  FROM research.lu_act_overture_original_city_pair_receipt_v0
  WHERE act_release='2026-10-01'
    AND overture_release='2026-10-21.0'
    AND overture_source_row_group=182
    AND act_original_zip_sha256='6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3'
    AND act_city_footprints=139
    AND overture_city_footprints=69
    AND positive_area_source_polygon_pairs=282
    AND reciprocal_one_to_one_geometric_candidates=5
    AND strict_candidate_overture_source_family_counts=
      '{"OpenStreetMap":5,"Microsoft ML Buildings":0,"unknown_or_multiple":0}'::jsonb
    AND original_provider_geometry_persisted IS FALSE
    AND independent_physical_identity_verified IS FALSE
    AND source_licensing_scientifically_approved IS FALSE
    AND insured_TIV_inferred IS FALSE
    AND insurance_CAT_model_input_approved IS FALSE
    AND (act_city_digitizing_source_family_counts IS NULL
         OR act_city_digitizing_source_family_counts=
          '{"Bati3DACT":0,"Bati3DVDL":139,"PCN":0,"MO":0,"Ortho":0,"unknown_or_missing":0}'::jsonb)
    AND (act_strict_candidate_digitizing_source_family_counts IS NULL
         OR act_strict_candidate_digitizing_source_family_counts=
          '{"Bati3DACT":0,"Bati3DVDL":5,"PCN":0,"MO":0,"Ortho":0,"unknown_or_missing":0}'::jsonb)
    AND (act_digitizing_source_original_run_url IS NULL
         OR act_digitizing_source_original_run_url=
          'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41538722511')
 ) <> 1 THEN
  RAISE EXCEPTION 'Pinned ACT city-source evidence drift; refuse aggregate receipt';
 END IF;
END;
$act_original_source_precondition$;

UPDATE research.lu_act_overture_original_city_pair_receipt_v0
SET act_city_digitizing_source_family_counts=
      '{"Bati3DACT":0,"Bati3DVDL":139,"PCN":0,"MO":0,"Ortho":0,"unknown_or_missing":0}'::jsonb,
    act_strict_candidate_digitizing_source_family_counts=
      '{"Bati3DACT":0,"Bati3DVDL":5,"PCN":0,"MO":0,"Ortho":0,"unknown_or_missing":0}'::jsonb,
    act_digitizing_source_original_run_url=
      'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41538722511'
WHERE act_release='2026-10-01'
  AND overture_release='2026-10-21.0'
  AND overture_source_row_group=182
  AND original_provider_geometry_persisted IS FALSE
  AND independent_physical_identity_verified IS FALSE
  AND insurance_CAT_model_input_approved IS FALSE;

DO $act_original_source_final$
BEGIN
 IF (SELECT count(*)
     FROM research.lu_act_overture_original_city_pair_receipt_v0
     WHERE act_city_digitizing_source_family_counts->>'Bati3DVDL'='139'
       AND act_strict_candidate_digitizing_source_family_counts->>'Bati3DVDL'='5'
       AND act_digitizing_source_original_run_url=
         'https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41538722511'
       AND independent_physical_identity_verified IS FALSE
       AND source_licensing_scientifically_approved IS FALSE
       AND insurance_CAT_model_input_approved IS FALSE
       AND original_provider_geometry_persisted IS FALSE
       AND insured_TIV_inferred IS FALSE) <> 1 THEN
    RAISE EXCEPTION 'ACT original-source aggregate receipt failed strict readback';
 END IF;
END;
$act_original_source_final$;
