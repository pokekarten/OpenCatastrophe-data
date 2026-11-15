-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Run on insurance-risk-core main after the fr Ponthierry QA view.
-- Research assertions do not declare legal rights or model readiness.
WITH checks AS (
  SELECT 'one_gate_row_per_original_building'::text AS check_id,
         (SELECT count(*) FROM research.fr_ponthierry_building_2016_exposure_gate_v0) =
         (SELECT count(*) FROM research.fr_ponthierry_rnb_ign_building_v0) AS passed
  UNION ALL
  SELECT 'unique_rnb_identifiers',
         (SELECT count(*) FROM research.fr_ponthierry_building_2016_exposure_gate_v0) =
         (SELECT count(DISTINCT rnb_id) FROM research.fr_ponthierry_building_2016_exposure_gate_v0)
  UNION ALL
  SELECT 'unique_ign_identifiers',
         (SELECT count(*) FROM research.fr_ponthierry_building_2016_exposure_gate_v0) =
         (SELECT count(DISTINCT ign_cleabs) FROM research.fr_ponthierry_building_2016_exposure_gate_v0)
  UNION ALL
  SELECT 'hydrology_context_rows_preserved',
         (SELECT coalesce(sum(context_join_rows_not_buildings), 0) FROM research.fr_ponthierry_building_2016_exposure_gate_v0) =
         (SELECT count(*) FROM research.fr_ponthierry_current_buildings_2016_q_context_v0)
  UNION ALL
  SELECT 'no_duplicate_gauge_day_per_building',
         NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_building_2016_exposure_gate_v0
                     WHERE context_join_rows_not_buildings <> historical_gauge_days_not_building_count)
  UNION ALL
  SELECT 'one_qa_row_per_building',
         NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_building_2016_exposure_gate_v0
                     WHERE qa_row_count <> 1)
  UNION ALL
  SELECT 'independent_geometry_not_inferred_from_shared_source',
         NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_building_2016_exposure_gate_v0
                     WHERE shared_bdtopo_lineage_not_independent AND geometry_source_independent)
  UNION ALL
  SELECT 'no_2016_building_claim_from_unverified_original',
         NOT EXISTS (
           SELECT 1
           FROM research.fr_ponthierry_building_2016_exposure_gate_v0 AS g
           JOIN research.fr_ponthierry_rnb_ign_building_v0 AS b USING (rnb_id, ign_cleabs)
           WHERE NOT b.original_2016_building_state_proven AND g.historical_2016_building_state_verified
         )
  UNION ALL
  SELECT 'no_flood_depth_claim_without_original',
         NOT EXISTS (
           SELECT 1
           FROM research.fr_ponthierry_building_2016_exposure_gate_v0 AS g
           JOIN research.fr_ponthierry_rnb_ign_building_v0 AS b USING (rnb_id, ign_cleabs)
           WHERE NOT b.original_2016_flood_depth_proven AND g.historical_2016_flood_footprint_and_depth_verified
         )
  UNION ALL
  SELECT 'no_insured_value_claim_without_original',
         NOT EXISTS (
           SELECT 1
           FROM research.fr_ponthierry_building_2016_exposure_gate_v0 AS g
           JOIN research.fr_ponthierry_rnb_ign_building_v0 AS b USING (rnb_id, ign_cleabs)
           WHERE NOT b.insured_replacement_value_proven AND g.historical_insured_value_verified
         )
  UNION ALL
  SELECT 'no_model_admission',
         NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_building_2016_exposure_gate_v0
                     WHERE model_input_approved)
  UNION ALL
  SELECT 'original_metadata_receipts_have_sha256',
         NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_building_2016_exposure_gate_v0
                     WHERE rnb_response_sha256 !~ '^[0-9a-f]{64}$'
                        OR ign_response_sha256 !~ '^[0-9a-f]{64}$'
                        OR rnb_response_sha256 IS NULL OR ign_response_sha256 IS NULL)
  UNION ALL
  SELECT 'footprints_positive_and_iou_bounded',
         NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_building_2016_exposure_gate_v0
                     WHERE observed_rnb_footprint_m2 <= 0
                        OR observed_ign_footprint_m2 <= 0
                        OR observed_source_geometry_iou <= 0
                        OR observed_source_geometry_iou > 1
                        OR observed_rnb_footprint_m2 IS NULL
                        OR observed_ign_footprint_m2 IS NULL
                        OR observed_source_geometry_iou IS NULL)
  UNION ALL
  SELECT 'history_context_is_historical_year_2016',
         NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_building_2016_exposure_gate_v0
                     WHERE first_gauge_date IS NULL OR last_gauge_date IS NULL
                        OR first_gauge_date < DATE '2016-01-01'
                        OR last_gauge_date >= DATE '2017-01-01')
)
SELECT check_id, coalesce(passed,false) AS passed
FROM checks ORDER BY check_id;
