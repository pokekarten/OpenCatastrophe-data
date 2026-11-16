-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY: strictly pinned Natural Earth v5.1.1 DE/FR two-country
-- PostGIS research-stage point-join challenge. Source geometries are
-- ALREADY staged privately; this query reads them but exports none.
--
-- Binding a 177-feature public provider release does not establish
-- scientifically valid *global* country geometry. The observed original
-- full-source audit run 43756585370 found 2 OGC-invalid features,
-- 1 interior overlap among eligible pairs and 3 excluded dateline
-- geometries. This two-country pilot is a much narrower exception.
--
-- Source-only: immutable original GitHub blob, feature-level sha256
-- hashes, source ISO sentinel and geographic query semantics must agree.
-- Point testing is research-only; no insured site, flood hazard,
-- political boundary authority or model admission follows.
WITH features AS (
  SELECT *, ST_IsValid(original_geojson_geometry) AS geometry_valid,
         ST_SRID(original_geojson_geometry) AS geometry_srid,
         ST_IsEmpty(original_geojson_geometry) AS geometry_empty
  FROM research.natural_earth_country_locator_v0
), expected(country_code,adm0_a3,original_iso_a2,geometry_json_sha256) AS (
  VALUES
  ('DE'::bpchar,'DEU'::text,'DE'::text,
   'efa19daffd0b199f2f007013b8e1a8050c7f1ecbc0ee70aa9b344eb8bf990201'::text),
  ('FR'::bpchar,'FRA'::text,'-99'::text,
   'a21e6b65309cea90a2b463d4268537de52060fa8c9c1ba3d5d3b078130df7125'::text)
), anchor_points(name,expected_country,longitude,latitude) AS (
  VALUES ('munich'::text,'DE'::bpchar,11.576::double precision,48.137::double precision),
         ('paris','FR'::bpchar,2.3522::double precision,48.8566::double precision),
         ('north_sea_outside',NULL::bpchar,2.0::double precision,55.5::double precision)
), point_matches AS (
  SELECT p.name,p.expected_country,
         count(f.country_code) FILTER(
           WHERE ST_Covers(f.original_geojson_geometry,
                     ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326))
         )::int AS matched_count,
         max(f.country_code) FILTER(
           WHERE ST_Covers(f.original_geojson_geometry,
                     ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326))
         ) AS matched_code
  FROM anchor_points p CROSS JOIN features f
  GROUP BY p.name,p.expected_country
), pairwise AS (
  SELECT ST_Area(ST_Intersection(de.original_geojson_geometry,
                                 fr.original_geojson_geometry))
                                 AS overlap_crs84_square_degrees
  FROM features de JOIN features fr ON de.country_code='DE'
                                    AND fr.country_code='FR'
), adversarial AS (
  -- Invented rectangles with a real overlap; a point inside both
  -- MUST NOT be assigned to whichever feature is returned first.
  SELECT ST_GeomFromText('POLYGON((0 0,2 0,2 2,0 2,0 0))',4326) AS a,
         ST_GeomFromText('POLYGON((1 1,3 1,3 3,1 3,1 1))',4326) AS b,
         ST_SetSRID(ST_MakePoint(1.5,1.5),4326) AS p
), checks AS (
  SELECT 'exactly_two_research_stage_countries'::text AS check_id,
         (SELECT count(*)=2 FROM features) AS passed
  UNION ALL SELECT 'only_DE_FR_no_extra_country',
         (SELECT count(*)=2 AND count(*) FILTER(
           WHERE country_code IN ('DE','FR'))=2 FROM features)
  UNION ALL SELECT 'country_and_source_iso_identity_exact',
         (SELECT count(*)=2 AND count(*) FILTER(
            WHERE f.country_code=e.country_code
              AND f.original_adm0_a3=e.adm0_a3
              AND f.original_iso_a2=e.original_iso_a2)=2
          FROM features f JOIN expected e USING(country_code))
  UNION ALL SELECT 'original_feature_hashes_match_pinned_baseline',
         (SELECT count(*)=2 AND count(*) FILTER(
           WHERE f.original_geometry_json_sha256=e.geometry_json_sha256)=2
          FROM features f JOIN expected e USING(country_code))
  UNION ALL SELECT 'source_repository_release_and_blob_are_pinned',
         NOT EXISTS(SELECT 1 FROM features
           WHERE source_git_repository IS DISTINCT FROM 'nvkelso/natural-earth-vector'
              OR source_git_commit_sha IS DISTINCT FROM
                  'ca96624a56bd078437bca8184e78163e5039ad19'
              OR source_geojson_git_blob_sha IS DISTINCT FROM
                  '1e6ab74c7042f97013be69ceec798be8e1aff27d'
              OR source_geojson_path IS DISTINCT FROM
                  'geojson/ne_110m_admin_0_countries.geojson'
              OR source_country_version IS DISTINCT FROM '5.1.1')
  UNION ALL SELECT 'licensed_research_only_no_exposure_or_hazard_admission',
         NOT EXISTS(SELECT 1 FROM features
           WHERE licence_assertion IS DISTINCT FROM 'NATURAL_EARTH_PUBLIC_DOMAIN'
              OR geometry_role IS DISTINCT FROM 'coarse_country_locator_only'
              OR hazard_input_admitted IS DISTINCT FROM FALSE
              OR insured_exposure_admitted IS DISTINCT FROM FALSE
              OR flood_footprint_validated IS DISTINCT FROM FALSE)
  UNION ALL SELECT 'native_nonempty_valid_crs84_polygons',
         NOT EXISTS(SELECT 1 FROM features WHERE
           NOT geometry_valid OR geometry_srid<>4326 OR geometry_empty OR
           ST_Area(original_geojson_geometry)<=0 OR
           ST_GeometryType(original_geojson_geometry)
             NOT IN ('ST_MultiPolygon','ST_Polygon'))
  UNION ALL SELECT 'no_DE_FR_material_interior_overlap',
         (SELECT count(*)=1 AND COALESCE(max(overlap_crs84_square_degrees)<=1e-12,FALSE)
          FROM pairwise)
  UNION ALL SELECT 'munich_uniquely_inside_DE',
         (SELECT matched_count=1 AND matched_code='DE' FROM point_matches
          WHERE name='munich')
  UNION ALL SELECT 'paris_uniquely_inside_FR',
         (SELECT matched_count=1 AND matched_code='FR' FROM point_matches
          WHERE name='paris')
  UNION ALL SELECT 'north_sea_point_not_assigned',
         (SELECT matched_count=0 AND matched_code IS NULL FROM point_matches
          WHERE name='north_sea_outside')
  UNION ALL SELECT 'source_geometry_sha_not_same_for_both_countries',
         (SELECT count(DISTINCT original_geometry_json_sha256)=2 FROM features)
  UNION ALL SELECT 'sourced_France_minus99_sentinel_not_an_ISO2_code',
         (SELECT count(*)=1 FROM features
           WHERE country_code='FR' AND original_iso_a2='-99'
             AND original_iso_a2 !~ '^[A-Z]{2}$')
  UNION ALL SELECT 'synthetic_overlap_is_detected',
         (SELECT ST_Area(ST_Intersection(a,b))>1e-12 FROM adversarial)
  UNION ALL SELECT 'synthetic_ambiguous_point_has_two_matches',
         (SELECT ST_Covers(a,p) AND ST_Covers(b,p) FROM adversarial)
)
SELECT check_id,COALESCE(passed,FALSE) AS passed,
       (SELECT count(*)::bigint FROM features) AS pilot_feature_count,
       FALSE AS global_country_coverage_proven,
       FALSE AS original_worldwide_topology_qa_pass,
       FALSE AS insurer_geolocation_approved,
       FALSE AS hazard_exposure_admitted
FROM checks ORDER BY check_id;
