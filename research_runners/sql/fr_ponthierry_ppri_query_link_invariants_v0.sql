-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ-ONLY, fail-closed and non-vacuous Ponthierry QA.
-- Checks both actual RNB building footprints against the exact submitted
-- PPRI query polygons, plus a separate red-zone gauge control.
-- Regulatory zone feature geometry is NOT stored; a zero PPRI response is
-- NOT a "no flood risk" finding. Current building geometry is NOT a
-- 2016 exposure observation. Rights remain source/layer-specific pending.
WITH sample AS (
 SELECT (SELECT count(*) FROM research.fr_ponthierry_rnb_ign_building_v0) AS buildings,
        (SELECT count(*) FROM research.fr_ponthierry_ppri_spatial_probe_v0) AS probes,
        (SELECT count(*) FROM research.fr_ponthierry_ppri_spatial_probe_v0
         WHERE subject_kind='BUILDING_FOOTPRINT') AS building_probes,
        (SELECT count(*) FROM research.fr_ponthierry_ppri_spatial_probe_v0
         WHERE subject_kind='GAUGE_CONTROL') AS gauge_probes
), paired AS (
 SELECT b.rnb_id,b.ign_cleabs,
        b.rnb_geom,b.ign_geom_3d,b.ign_last_modified,
        b.rnb_response_sha256,b.ign_response_sha256,
        b.geometry_source_independent,b.original_2016_building_state_proven,
        b.original_2016_flood_depth_proven,b.insured_replacement_value_proven,
        b.insurer_loss_calibrated,b.cat_model_admitted,
        p.probe_key,p.reported_zone_count,p.original_response_sha256,
        p.original_provider_query_url,p.input_polygon_wgs84,
        p.complete_original_regulatory_zone_geometry_stored,
        p.inspected_polygon_intersection_is_2016_flood_footprint,
        p.physical_flood_depth_estimated,p.insured_loss_derived,
        p.cat_model_admitted AS ppri_cat_model_admitted,
        p.per_layer_rights_review
 FROM research.fr_ponthierry_rnb_ign_building_v0 b
 LEFT JOIN research.fr_ponthierry_ppri_spatial_probe_v0 p
   ON p.subject_kind='BUILDING_FOOTPRINT'
  AND p.source_subject_id=b.rnb_id
), checks AS (
 SELECT 'pilot_exact_two_buildings_three_responses'::text check_id,
   (SELECT buildings=2 AND probes=3
     AND building_probes=2 AND gauge_probes=1 FROM sample) AS passed
 UNION ALL SELECT 'every_building_has_exact_one_ppri_query_receipt',
   (SELECT count(*)=2 AND count(DISTINCT rnb_id)=2
       AND count(probe_key)=2 AND count(DISTINCT probe_key)=2 FROM paired)
 UNION ALL SELECT 'all_input_query_polygons_match_rnb_geometry',
   NOT EXISTS (SELECT 1 FROM paired
       WHERE input_polygon_wgs84 IS NULL OR rnb_geom IS NULL
          OR ST_Equals(input_polygon_wgs84,rnb_geom) IS NOT TRUE)
 UNION ALL SELECT 'valid_same_crs_source_and_query_geometries',
   NOT EXISTS (SELECT 1 FROM paired
      WHERE ST_IsValid(rnb_geom) IS NOT TRUE
        OR ST_IsValid(ign_geom_3d) IS NOT TRUE
        OR ST_IsValid(input_polygon_wgs84) IS NOT TRUE
        OR ST_SRID(rnb_geom)<>4326 OR ST_SRID(ign_geom_3d)<>4326
        OR ST_SRID(input_polygon_wgs84)<>4326)
 UNION ALL SELECT 'building_and_query_original_receipt_sha_present',
   NOT EXISTS (SELECT 1 FROM paired WHERE
       rnb_response_sha256 !~ '^[0-9a-f]{64}$'
       OR ign_response_sha256 !~ '^[0-9a-f]{64}$'
       OR original_response_sha256 !~ '^[0-9a-f]{64}$'
       OR rnb_response_sha256 IS NULL OR ign_response_sha256 IS NULL
       OR original_response_sha256 IS NULL)
 UNION ALL SELECT 'ppri_original_query_urls_source_stable',
   NOT EXISTS (SELECT 1 FROM paired WHERE
        original_provider_query_url IS NULL OR
        original_provider_query_url NOT LIKE
         'https://sig.seinegrandslacs.fr/arcgis/rest/services/Gestion_Eaux_Inondations_GP/MapServer/17/query?%')
 UNION ALL SELECT 'both_building_polygon_queries_return_zero_zones',
   (SELECT count(*)=2 FROM paired WHERE reported_zone_count=0)
 UNION ALL SELECT 'red_zone_positive_gauge_control_present',
   (SELECT count(*)=1
      FROM research.fr_ponthierry_ppri_spatial_probe_v0
      WHERE subject_kind='GAUGE_CONTROL'
        AND source_subject_id='F447000302'
        AND reported_zone_count=1
        AND original_zone_objectid=574
        AND original_zone_code='zone rouge'
        AND original_response_sha256 ~ '^[0-9a-f]{64}$')
 UNION ALL SELECT 'regulatory_polygon_full_geometry_not_loaded',
   NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_ppri_spatial_probe_v0
     WHERE complete_original_regulatory_zone_geometry_stored)
 UNION ALL SELECT 'all_ppri_layer_rights_still_explicitly_pending',
   NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_ppri_spatial_probe_v0
     WHERE per_layer_rights_review IS DISTINCT FROM 'PENDING_EXACT_ARCGIS_LAYER_RIGHTS')
 UNION ALL SELECT 'no_ppri_2016_flood_depth_damage_or_model_promotion',
   NOT EXISTS (SELECT 1 FROM research.fr_ponthierry_ppri_spatial_probe_v0
      WHERE inspected_polygon_intersection_is_2016_flood_footprint
         OR physical_flood_depth_estimated OR insured_loss_derived
         OR cat_model_admitted)
 UNION ALL SELECT 'no_building_historical_state_value_or_model_promotion',
   NOT EXISTS (SELECT 1 FROM paired
      WHERE geometry_source_independent OR original_2016_building_state_proven
         OR original_2016_flood_depth_proven OR insured_replacement_value_proven
         OR insurer_loss_calibrated OR cat_model_admitted)
 UNION ALL SELECT 'current_ign_versions_are_after_flood_event',
   NOT EXISTS (SELECT 1 FROM paired
      WHERE ign_last_modified IS NULL OR ign_last_modified < TIMESTAMPTZ '2016-07-01')
)
SELECT check_id,coalesce(passed,FALSE) AS passed,
       (SELECT buildings FROM sample) AS observed_buildings,
       (SELECT probes FROM sample) AS observed_ppri_responses,
       FALSE AS proven_2016_flood_footprint,
       FALSE AS proven_insured_exposure,
       FALSE AS model_input_approved
FROM checks ORDER BY check_id;
