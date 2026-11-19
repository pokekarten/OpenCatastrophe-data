-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY. Geographic response-to-building QA for the Ponthierry pilot.
-- This joins ORIGINAL RNB 2D footprints to the exact INPUT polygons sent to
-- a published PPRI ArcGIS zoning intersection service.
--
-- Crucially, the PPRI source response returned features/properties only;
-- its COMPLETE regulatory zone geometries were NOT imported. A zero response
-- is not evidence that a building is safe, and the positive gauge control is
-- not a 2016 flood inundation polygon, stage, depth, damage or insured TIV.
-- Rights on the exact ArcGIS layer are still pending. No model admission.
WITH gauge AS (
 SELECT input_polygon_wgs84 AS control_footprint
 FROM research.fr_ponthierry_ppri_spatial_probe_v0
 WHERE subject_kind='GAUGE_CONTROL'
   AND source_subject_id='F447000302'
), inspected AS (
 SELECT b.rnb_id,b.ign_cleabs,b.ign_last_modified,
        p.probe_key,p.reported_zone_count,p.original_zone_code,
        p.original_response_sha256,p.original_provider_query_url,
        p.per_layer_rights_review,
        ST_Equals(p.input_polygon_wgs84,b.rnb_geom) AS exact_footprint_topology,
        round((
          ST_Area(ST_Intersection(p.input_polygon_wgs84,b.rnb_geom)::geography) /
          NULLIF(ST_Area(ST_Union(p.input_polygon_wgs84,b.rnb_geom)::geography),0)
        )::numeric,8) AS footprint_intersection_over_union,
        round(ST_Distance(
          ST_Centroid(p.input_polygon_wgs84)::geography,
          ST_Centroid(g.control_footprint)::geography
        )::numeric,2) AS distance_to_gauge_control_m,
        b.rnb_response_sha256,b.ign_response_sha256,
        b.geometry_source_independent,b.original_2016_building_state_proven,
        b.original_2016_flood_depth_proven,b.insured_replacement_value_proven,
        b.cat_model_admitted,
        p.complete_original_regulatory_zone_geometry_stored,
        p.inspected_polygon_intersection_is_2016_flood_footprint,
        p.physical_flood_depth_estimated,p.insured_loss_derived,
        p.cat_model_admitted AS ppri_cat_model_admitted
 FROM research.fr_ponthierry_rnb_ign_building_v0 b
 LEFT JOIN research.fr_ponthierry_ppri_spatial_probe_v0 p
   ON p.subject_kind='BUILDING_FOOTPRINT'
  AND p.source_subject_id=b.rnb_id
 LEFT JOIN gauge g ON TRUE
)
SELECT rnb_id,ign_cleabs,probe_key,
       exact_footprint_topology,footprint_intersection_over_union,
       distance_to_gauge_control_m,reported_zone_count,
       CASE WHEN probe_key IS NULL THEN 'NO_PPRI_QUERY_RECEIPT'
            WHEN reported_zone_count=0 THEN 'NO_ZONE_FEATURE_RETURNED_NOT_PROOF_OF_SAFETY'
            WHEN reported_zone_count>0 THEN 'PPRI_REGULATORY_FEATURE_RETURNED_NOT_2016_FLOOD'
            ELSE 'UNINTERPRETABLE_PPRI_RESPONSE' END AS ppri_observation_status,
       original_response_sha256,rnb_response_sha256,ign_response_sha256,
       per_layer_rights_review,
       (original_response_sha256 ~ '^[0-9a-f]{64}$'
         AND rnb_response_sha256 ~ '^[0-9a-f]{64}$'
         AND ign_response_sha256 ~ '^[0-9a-f]{64}$'
         AND original_provider_query_url LIKE 'https://%'
         AND exact_footprint_topology IS TRUE
         AND footprint_intersection_over_union=1
       ) AS exact_query_geometry_and_receipt_valid,
       (complete_original_regulatory_zone_geometry_stored IS TRUE)
         AS regulatory_polygon_available_for_overlay,
       FALSE AS independent_original_2016_flood_depth_derived,
       FALSE AS insured_asset_loss_derived,
       FALSE AS cat_model_admitted
FROM inspected ORDER BY rnb_id;
