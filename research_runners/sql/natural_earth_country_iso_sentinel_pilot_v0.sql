-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY. Pilot only: Natural Earth country geometry in CAT-only Neon main.
-- A source ISO_A2 placeholder such as '-99' is not an ISO country code.
-- Do not silently overwrite source fields, infer country joins from names
-- or treat basemap coverage as approved hazard / insured exposure.
WITH features AS (
 SELECT *,ST_IsValid(original_geojson_geometry) geometry_valid,
        ST_SRID(original_geojson_geometry) geometry_srid,
        ST_IsEmpty(original_geojson_geometry) geometry_empty
 FROM research.natural_earth_country_locator_v0
), checks AS (
 SELECT 'at_least_two_pilot_country_geometries'::text check_id,
        (SELECT count(*)>=2 FROM features) passed
 UNION ALL SELECT 'germany_and_france_both_pinned',
        (SELECT count(DISTINCT country_code)=2
         FROM features WHERE country_code IN ('DE','FR'))
 UNION ALL SELECT 'normalized_country_code_unique',
        (SELECT count(*)=count(DISTINCT country_code) FROM features)
 UNION ALL SELECT 'source_blob_and_original_geometry_sha_valid',
        NOT EXISTS (
         SELECT 1 FROM features WHERE
           source_git_commit_sha !~ '^[0-9a-f]{40}$' OR
           source_geojson_git_blob_sha !~ '^[0-9a-f]{40}$' OR
           original_geometry_json_sha256 !~ '^[0-9a-f]{64}$' OR
           original_geometry_json_sha256 IS NULL)
 UNION ALL SELECT 'valid_nonempty_wgs84_polygons',
        NOT EXISTS (
         SELECT 1 FROM features WHERE
           NOT geometry_valid OR geometry_srid<>4326 OR geometry_empty OR
           ST_GeometryType(original_geojson_geometry)
             NOT IN ('ST_MultiPolygon','ST_Polygon'))
 UNION ALL SELECT 'non_admission_is_preserved',
        NOT EXISTS (SELECT 1 FROM features WHERE hazard_input_admitted
                                              OR insured_exposure_admitted)
 UNION ALL SELECT 'france_original_sentinel_mapped_explicitly',
        EXISTS (SELECT 1 FROM features WHERE country_code='FR'
          AND original_iso_a2='-99' AND original_adm0_a3='FRA')
 UNION ALL SELECT 'no_unknown_source_iso_sentinels',
        NOT EXISTS (SELECT 1 FROM features WHERE original_iso_a2='-99'
          AND NOT (country_code='FR' AND original_adm0_a3='FRA'))
)
SELECT check_id,coalesce(passed,FALSE) passed,
       (SELECT count(*) FROM features)::bigint pilot_feature_count,
       (SELECT count(*) FROM features WHERE original_iso_a2='-99')::bigint original_iso_sentinel_rows,
       FALSE AS global_country_coverage_proven,
       FALSE AS insurer_geolocation_approved,
       FALSE AS hazard_exposure_admitted
FROM checks ORDER BY check_id;
