-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
-- Read-only PostGIS v3+ area-weighted parcel/building synthetic invariant test.
-- All coordinates are INVENTED planar metres (EPSG:28992), not real property.
-- Nothing is written. It must never authorise real insured TIV or ownership.

WITH synthetic_buildings(id,geom) AS (
  VALUES
    ('split',      ST_MakeEnvelope(0, 0, 10, 10, 28992)),
    ('single',     ST_MakeEnvelope(20, 0, 30, 10, 28992)),
    ('sliver',     ST_MakeEnvelope(40, 0, 50, 10, 28992)),
    ('overlap',    ST_MakeEnvelope(60, 0, 70, 10, 28992)),
    ('unassigned', ST_MakeEnvelope(80, 0, 90, 10, 28992))
),
synthetic_parcels(id,geom) AS (
  VALUES
    ('s-left',  ST_MakeEnvelope(0, 0, 6, 10, 28992)),
    ('s-right', ST_MakeEnvelope(6, 0, 10, 10, 28992)),
    ('full',    ST_MakeEnvelope(20, 0, 30, 10, 28992)),
    ('sl-main', ST_MakeEnvelope(40, 0, 49.99, 10, 28992)),
    ('sl-tiny', ST_MakeEnvelope(49.99, 0, 50, 10, 28992)),
    ('ov-main', ST_MakeEnvelope(60, 0, 70, 10, 28992)),
    ('ov-dup',  ST_MakeEnvelope(65, 0, 70, 10, 28992))
),
intersections AS (
 SELECT b.id AS building_id, p.id AS parcel_id,
        ST_Area(ST_Intersection(b.geom,p.geom)) AS area_m2
 FROM synthetic_buildings b
 JOIN synthetic_parcels p ON ST_Intersects(b.geom,p.geom)
), positive AS (
 SELECT * FROM intersections WHERE area_m2 > 0.0000001
), per_building AS (
 SELECT b.id, ST_Area(b.geom) AS building_area_m2,
        count(p.parcel_id) AS parcel_links,
        count(*) FILTER (WHERE p.area_m2>1.0) AS meaningful_area_links,
        count(*) FILTER (WHERE p.area_m2>ST_Area(b.geom)*0.05) AS meaningful_percent_links,
        coalesce(sum(p.area_m2),0) AS total_intersection_area_m2
 FROM synthetic_buildings b
 LEFT JOIN positive p ON p.building_id=b.id
 GROUP BY b.id,b.geom
), summary AS (
 SELECT count(*) AS buildings,
        count(*) FILTER (WHERE parcel_links=0) AS zero,
        count(*) FILTER (WHERE parcel_links=1) AS single,
        count(*) FILTER (WHERE parcel_links>1) AS multiple_any,
        count(*) FILTER (WHERE meaningful_area_links>1 AND meaningful_percent_links>1) AS multiple_significant,
        count(*) FILTER (WHERE total_intersection_area_m2>building_area_m2*1.00001) AS overcovered,
        round(sum(total_intersection_area_m2)::numeric,2) AS naive_total_intersection_m2,
        round(sum(least(total_intersection_area_m2,building_area_m2))::numeric,2) AS capped_total_area_m2
 FROM per_building
)
SELECT *, (
  buildings=5 AND zero=1 AND single=1 AND multiple_any=3
  AND multiple_significant=2 AND overcovered=1
  AND naive_total_intersection_m2=450.00
  AND capped_total_area_m2=400.00
  AND (SELECT total_intersection_area_m2 FROM per_building WHERE id='split')=100
  AND (SELECT meaningful_percent_links FROM per_building WHERE id='sliver')=1
  AND (SELECT total_intersection_area_m2 FROM per_building WHERE id='overlap')=150
) AS invariants_passed,
TRUE AS synthetic_only,
FALSE AS source_admitted,
FALSE AS cat_model_approved
FROM summary;
