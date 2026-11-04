# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Render a private, read-only PostGIS area-overlay SELECT from bounded PDOK GeoJSON.

Only non-personal, already obtained source snapshots are accepted. No download,
no DDL/DML, no database connection, no model admission, no public source bytes.
Output SQL includes provider object IDs and geometries: NEVER commit it to Git.
Execute only against an isolated PostGIS research/validation database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

if __package__:
    from .audit_pdok_brk_bag_centroid_v0 import (
        ALLOWED_SNAPSHOT_GAP_SECONDS, ParcelBagError, _bbox, _collection, load,
    )
else:
    from audit_pdok_brk_bag_centroid_v0 import (
        ALLOWED_SNAPSHOT_GAP_SECONDS, ParcelBagError, _bbox, _collection, load,
    )

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"[A-Za-z0-9_.:-]{1,80}\Z")
MAX_SQL_BYTES = 1_500_000


def _lit(value):
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ParcelBagError("source ID unsafe for SQL research template")
    return "'" + value + "'"


def _geometry(rings):
    # _collection validates ring closure, CRS84 coordinates, finite numerics,
    # bounds and no oversized geometry. We never make invalid originals valid.
    if len(rings) == 1:
        geom = {"type": "Polygon", "coordinates": rings[0]}
    else:
        geom = {"type": "MultiPolygon", "coordinates": rings}
    value = json.dumps(geom, separators=(",", ":"), allow_nan=False)
    if "'" in value:
        raise ParcelBagError("unexpected quote in GeoJSON geometry")
    return "ST_SetSRID(ST_GeomFromGeoJSON('" + value + "'),4326)"


def _values(rows, label):
    if not rows:
        raise ParcelBagError(label + ": source has no rows")
    return ",\n".join("(" + ",".join(fields) + ")" for fields in rows)


def render(parcels, bgt, bag, *, bbox):
    """Produce a no-writes SQL SELECT; returns SQL string with private source IDs."""
    bounds = _bbox(bbox)
    ptime, par = _collection(parcels, "parcel", bounds)
    btime, bgt_rows = _collection(bgt, "parcel", bounds)
    atime, bag_rows = _collection(bag, "building", bounds)
    if (max(ptime, btime, atime) - min(ptime, btime, atime)).total_seconds() > ALLOWED_SNAPSHOT_GAP_SECONDS:
        raise ParcelBagError("source timestamps too far apart")

    bag_status = {}
    bag_sql = []
    for ident, props, _ in bag_rows:
        status = props.get("status")
        if not isinstance(status, str) or not status:
            raise ParcelBagError("BAG status missing")
        bag_status[ident] = status
        bag_sql.append([_lit(ident), "'Pand in gebruik'" if status == "Pand in gebruik" else "'OTHER'"])

    parcel_sql = []
    for ident, props, rings in par:
        eligible = "Geldig" if props.get("status_historie_waarde") == "Geldig" else "OTHER"
        parcel_sql.append([_lit(ident), _lit(eligible), _geometry(rings)])

    bgt_sql = []
    for ident, props, rings in bgt_rows:
        bag_id = props.get("identificatie_bag_pnd")
        if not isinstance(bag_id, str) or not bag_id or bag_id.strip() != bag_id:
            raise ParcelBagError("BGT source missing official BAG identifier")
        status = props.get("bgt_status")
        if not isinstance(status, str) or not status:
            raise ParcelBagError("BGT status missing")
        bgt_sql.append([_lit(ident), _lit(bag_id),
                        _lit("bestaand" if status == "bestaand" else "OTHER"),
                        _geometry(rings)])
    # No numeric data is taken from provider fields. Recompute metric areas.
    query = (
        "-- RESEARCH ONLY: original PDOK sources are not admitted CAT model inputs.\n"
        "-- Strictly read-only PostGIS SELECT. Never save this generated SQL to public Git.\n"
        "-- Bounding CRS84 window (west,south,east,north): " + ",".join(map(str, bounds)) + "\n"
        "WITH parcels(id,source_status,geo) AS (VALUES " + _values(parcel_sql, "parcels") + "),\n"
        "bgt(id,bag_id,source_status,geo) AS (VALUES " + _values(bgt_sql, "BGT") + "),\n"
        "bag(id,source_status) AS (VALUES " + _values(bag_sql, "BAG") + "),\n"
        "quality AS (\n"
        " SELECT (SELECT count(*) FROM parcels WHERE NOT ST_IsValid(geo)) AS invalid_parcels,\n"
        "        (SELECT count(*) FROM bgt WHERE NOT ST_IsValid(geo)) AS invalid_bgt\n"
        "),\n"
        "p AS (SELECT id,ST_Transform(geo,28992) AS geom FROM parcels\n"
        "      WHERE source_status='Geldig' AND ST_IsValid(geo)),\n"
        "b AS (SELECT g.id,g.bag_id,ST_Transform(g.geo,28992) AS geom\n"
        "      FROM bgt g JOIN bag a ON g.bag_id=a.id\n"
        "      WHERE g.source_status='bestaand' AND a.source_status='Pand in gebruik'\n"
        "      AND ST_IsValid(g.geo)),\n"
        "all_intersections AS (\n"
        " SELECT b.id AS bgt_id,p.id AS parcel_id, ST_Area(ST_Intersection(b.geom,p.geom)) AS sqm\n"
        " FROM b JOIN p ON ST_Intersects(b.geom,p.geom)\n"
        "),\n"
        "positive_edges AS (SELECT * FROM all_intersections WHERE sqm>0.0000001),\n"
        "ranked_edges AS (\n"
        " SELECT *, ROW_NUMBER() OVER (PARTITION BY bgt_id ORDER BY sqm DESC,parcel_id) AS rank\n"
        " FROM positive_edges\n"
        "),\n"
        "per_building AS (\n"
        " SELECT b.id,ST_Area(b.geom) AS building_sqm,\n"
        "        count(e.parcel_id) AS parcels_with_positive_intersection,\n"
        "        count(*) FILTER(WHERE e.sqm>1.0) AS parcels_gt_one_sqm,\n"
        "        count(*) FILTER(WHERE e.sqm>ST_Area(b.geom)*0.05) AS parcels_gt_five_pct,\n"
        "        COALESCE(sum(e.sqm),0) AS overlap_sqm,\n"
        "        COALESCE(max(e.sqm) FILTER (WHERE e.rank=1),0) AS primary_overlap_sqm,\n"
        "        COALESCE(max(e.sqm) FILTER (WHERE e.rank=2),0) AS secondary_overlap_sqm\n"
        " FROM b LEFT JOIN ranked_edges e ON e.bgt_id=b.id GROUP BY b.id,b.geom\n"
        ")\n"
        "SELECT (SELECT count(*) FROM parcels) AS parcel_source_count,\n"
        " (SELECT count(*) FROM bgt) AS bgt_source_count,\n"
        " (SELECT count(*) FROM bag) AS bag_source_count,\n"
        " (SELECT count(*) FROM b) AS active_official_bag_matches,\n"
        " (SELECT invalid_parcels FROM quality) AS invalid_parcels,\n"
        " (SELECT invalid_bgt FROM quality) AS invalid_bgt,\n"
        " count(*) AS eligible_buildings,\n"
        " count(*) FILTER(WHERE parcels_with_positive_intersection=0) AS no_parcel_overlap,\n"
        " count(*) FILTER(WHERE parcels_with_positive_intersection=1) AS one_parcel_overlap,\n"
        " count(*) FILTER(WHERE parcels_with_positive_intersection>1) AS multiple_parcel_overlaps_any,\n"
        " count(*) FILTER(WHERE parcels_gt_one_sqm>1) AS multiple_parcel_overlap_over_one_sqm,\n"
        " count(*) FILTER(WHERE parcels_gt_five_pct>1) AS multiple_parcel_overlap_over_five_pct,\n"
        " count(*) FILTER(WHERE overlap_sqm>building_sqm*1.00001) AS double_count_risk_buildings,\n"
        " round(sum(building_sqm)::numeric,2) AS building_area_sqm,\n"
        " round(sum(overlap_sqm)::numeric,2) AS sum_intersection_area_sqm,\n"
        " round((100*sum(LEAST(overlap_sqm,building_sqm))/NULLIF(sum(building_sqm),0))::numeric,2) AS area_coverage_pct,\n"
        " round((100*sum(primary_overlap_sqm)/NULLIF(sum(building_sqm),0))::numeric,2) AS dominant_parcel_share_pct,\n"
        " round((100*max(secondary_overlap_sqm/NULLIF(building_sqm,0)))::numeric,2) AS largest_secondary_overlap_pct,\n"
        " TRUE AS analysis_only,FALSE AS source_admitted,FALSE AS model_input_approved\n"
        "FROM per_building;\n"
    )
    if len(query.encode("utf-8")) > MAX_SQL_BYTES:
        raise ParcelBagError("generated SQL exceeds research budget")
    return query


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parcels", type=Path, required=True)
    parser.add_argument("--bgt", type=Path, required=True)
    parser.add_argument("--bag", type=Path, required=True)
    parser.add_argument("--bbox", required=True)
    parser.add_argument("--out", type=Path, required=True,
                        help="PRIVATE local output path OUTSIDE the repository")
    args = parser.parse_args(argv)
    try:
        dest = args.out.resolve()
        if dest == ROOT or ROOT in dest.parents:
            raise ParcelBagError("output path may not be inside repository checkout")
        sql = render(load(args.parcels), load(args.bgt), load(args.bag),
                     bbox=[float(v) for v in args.bbox.split(",")])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(sql, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"analysis_only": True,
                      "output_sha256": hashlib.sha256(sql.encode()).hexdigest(),
                      "sql_bytes": len(sql.encode()), "source_admitted": False,
                      "model_input_approved": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
