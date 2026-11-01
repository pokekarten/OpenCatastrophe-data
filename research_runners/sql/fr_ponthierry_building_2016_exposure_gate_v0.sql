-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Research-only exposure-vintage QA for the *current* Ponthierry RNB/IGN pilot
-- and an unrelated 2016 station discharge context. Never treat time-series
-- context rows as additional buildings; station flow is not flood footprint.
-- Historical building existence/geometry, water depth and insured TIV are
-- independent evidence requirements, not inferred from modern RNB/IGN shape.
CREATE OR REPLACE VIEW research.fr_ponthierry_building_2016_exposure_gate_v0 AS
WITH qa AS (
    SELECT
        rnb_id,
        ign_cleabs,
        count(*) AS qa_row_count,
        max(source_geometry_iou) AS observed_source_geometry_iou,
        max(rnb_footprint_m2) AS observed_rnb_footprint_m2,
        max(ign_footprint_m2) AS observed_ign_footprint_m2,
        bool_and(coalesce(shared_bdtopo_upstream_lineage, false)) AS shared_source_lineage,
        bool_and(coalesce(original_2016_building_state_proven, false)) AS qa_historical_state_proven,
        bool_and(coalesce(original_2016_flood_depth_proven, false)) AS qa_historical_depth_proven,
        bool_and(coalesce(insured_replacement_value_proven, false)) AS qa_insured_value_proven,
        bool_and(coalesce(flood_area_intersection_proven, false)) AS qa_flood_area_proven
    FROM research.fr_ponthierry_rnb_ign_building_qa_v0
    GROUP BY rnb_id, ign_cleabs
),
context_by_building AS (
    SELECT
        rnb_id,
        ign_cleabs,
        count(*) AS context_join_rows,
        count(DISTINCT historical_hydro_date) AS distinct_historical_gauge_days,
        min(historical_hydro_date) AS first_gauge_date,
        max(historical_hydro_date) AS last_gauge_date,
        bool_and(coalesce(historical_2016_building_geometry_proven, false)) AS context_historical_geometry_proven,
        bool_and(coalesce(licensed_2016_flood_polygon_covered_building, false)) AS context_flood_polygon_proven,
        bool_and(coalesce(historical_2016_inundation_depth_known, false)) AS context_historical_depth_proven,
        bool_and(coalesce(insured_exposure_value_known, false)) AS context_insured_value_proven,
        bool_and(coalesce(historical_insurance_loss_calibrated, false)) AS context_loss_calibrated
    FROM research.fr_ponthierry_current_buildings_2016_q_context_v0
    GROUP BY rnb_id, ign_cleabs
)
SELECT
    b.rnb_id,
    b.ign_cleabs,
    b.ign_usage,
    b.ign_height_m,
    b.ign_last_modified,
    b.rnb_response_sha256,
    b.ign_response_sha256,
    b.rights_id,
    coalesce(q.qa_row_count, 0) AS qa_row_count,
    q.observed_source_geometry_iou,
    q.observed_rnb_footprint_m2,
    q.observed_ign_footprint_m2,
    coalesce(q.shared_source_lineage, false) AS shared_bdtopo_lineage_not_independent,
    coalesce(c.context_join_rows, 0) AS context_join_rows_not_buildings,
    coalesce(c.distinct_historical_gauge_days, 0) AS historical_gauge_days_not_building_count,
    c.first_gauge_date,
    c.last_gauge_date,
    (b.ign_last_modified::date > DATE '2016-12-31') AS current_source_modified_after_2016,
    (
        b.original_2016_building_state_proven
        AND coalesce(q.qa_historical_state_proven, false)
        AND coalesce(c.context_historical_geometry_proven, false)
    ) AS historical_2016_building_state_verified,
    (
        b.original_2016_flood_depth_proven
        AND coalesce(q.qa_historical_depth_proven, false)
        AND coalesce(c.context_historical_depth_proven, false)
        AND coalesce(c.context_flood_polygon_proven, false)
        AND coalesce(q.qa_flood_area_proven, false)
    ) AS historical_2016_flood_footprint_and_depth_verified,
    (
        b.insured_replacement_value_proven
        AND coalesce(q.qa_insured_value_proven, false)
        AND coalesce(c.context_insured_value_proven, false)
    ) AS historical_insured_value_verified,
    coalesce(c.context_loss_calibrated, false) AS historical_loss_calibrated,
    b.geometry_source_independent AS geometry_source_independent,
    false::boolean AS model_input_approved,
    'research_current_building_2016_station_time_context_only'::text AS observational_scope,
    CASE
        WHEN coalesce(q.qa_row_count, 0) <> 1 OR coalesce(c.context_join_rows, 0) = 0
            THEN 'BLOCKED_MISSING_OR_AMBIGUOUS_BUILDING_CONTEXT'
        WHEN coalesce(c.context_join_rows, 0) <> coalesce(c.distinct_historical_gauge_days, 0)
            THEN 'BLOCKED_DUPLICATE_HYDROLOGY_CONTEXT'
        WHEN NOT b.original_2016_building_state_proven
          OR NOT coalesce(q.qa_historical_state_proven, false)
          OR NOT coalesce(c.context_historical_geometry_proven, false)
            THEN 'BLOCKED_UNVERIFIED_2016_BUILDING_STATE'
        WHEN NOT b.geometry_source_independent
            THEN 'BLOCKED_SHARED_UPSTREAM_GEOMETRY'
        WHEN NOT b.original_2016_flood_depth_proven
          OR NOT coalesce(q.qa_flood_area_proven, false)
          OR NOT coalesce(c.context_flood_polygon_proven, false)
            THEN 'BLOCKED_NO_VALIDATED_2016_FLOOD_FOOTPRINT'
        WHEN NOT b.insured_replacement_value_proven
          OR NOT coalesce(c.context_insured_value_proven, false)
            THEN 'BLOCKED_NO_INSURED_BUILDING_VALUE'
        ELSE 'BLOCKED_INDEPENDENT_HISTORICAL_AND_MODEL_RIGHTS_REVIEW'
    END AS next_evidence_gate
FROM research.fr_ponthierry_rnb_ign_building_v0 AS b
LEFT JOIN qa AS q
    ON q.rnb_id = b.rnb_id AND q.ign_cleabs = b.ign_cleabs
LEFT JOIN context_by_building AS c
    ON c.rnb_id = b.rnb_id AND c.ign_cleabs = b.ign_cleabs;
