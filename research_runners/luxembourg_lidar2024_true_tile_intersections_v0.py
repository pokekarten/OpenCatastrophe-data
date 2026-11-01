#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact polygon intersection of ACT LiDAR2024 tile index in fixed Luxembourg pilot.

Research-only: reads SHA-pinned 3.5 MB original GPKG index, bounded RTree hits,
decodes individual tile polygons *ephemerally*, verifies actual intersections and
reports ONLY aggregates. No tile URL, tile ID, geometry or building data emitted.
Never fetches LAZ/COG, no source admission or building-height measurements.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

from research_runners.luxembourg_lidar2024_fixed_tile_candidates_v0 import (
    DEFAULT_LAT, DEFAULT_LON, HALF_WIDTH_M, LAYER,
    LidarTileSelectionError, MAX_TILE_CANDIDATES, RTREE, SOURCE_SHA256,
    select_original_tiles,
)
from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, decode_gpkg_wkb,
)


class TileIntersectionError(ValueError):
    """Stop if original byte pin, tile geometry, scope or link semantics are invalid."""


def fixed_window(*, lon: float, lat: float, half_width_m: float):
    """One 250m equal-area square expressed as a closed EPSG:2169 polygon."""
    from pyproj import Transformer
    from shapely.geometry import Polygon

    to3035 = Transformer.from_crs(4326, 3035, always_xy=True)
    to2169 = Transformer.from_crs(3035, 2169, always_xy=True)
    cx, cy = to3035.transform(lon, lat)
    ring = [to2169.transform(x, y) for x, y in (
        (cx-half_width_m, cy-half_width_m),
        (cx+half_width_m, cy-half_width_m),
        (cx+half_width_m, cy+half_width_m),
        (cx-half_width_m, cy+half_width_m),
    )]
    polygon = Polygon(ring)
    if (not polygon.is_valid or polygon.is_empty or polygon.area <= 0
            or not all(math.isfinite(v) for v in polygon.bounds)):
        raise TileIntersectionError("Nonfinite/unusable transformed equal-area research polygon")
    return polygon


def inspect_actual_tile_intersections(
    original: Path, *, longitude: float = DEFAULT_LON,
    latitude: float = DEFAULT_LAT, half_width_m: float = HALF_WIDTH_M,
    expected_sha256: str = SOURCE_SHA256,
) -> dict:
    # Existing verified gate hard-caps study area, geometry candidate count,
    # source SHA-1 and source SHA-256 and validates declared EPSG/fields/RTree.
    try:
        receipt = select_original_tiles(
            original, expected_sha256=expected_sha256,
            longitude=longitude, latitude=latitude,
            half_width_m=half_width_m,
        )
    except (LidarTileSelectionError, OSError) as exc:
        raise TileIntersectionError("Original index source or pilot window rejected") from exc
    try:
        from shapely import wkb
        from shapely.ops import unary_union
    except ImportError as exc:
        raise TileIntersectionError("Pinned Shapely runtime required") from exc
    target = fixed_window(lon=longitude, lat=latitude, half_width_m=half_width_m)
    xmin, ymin, xmax, ymax = target.bounds

    db = sqlite3.connect(
        Path(original).resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        rows = db.execute(
            'SELECT t."fid",t."geom",t."Fichier",t."Dossier",t."DownloadLink" '
            'FROM "TableauAssemblage" t '
            'JOIN "rtree_TableauAssemblage_geom" r ON t."fid"=r.id '
            'WHERE r.maxx>=? AND r.minx<=? AND r.maxy>=? AND r.miny<=? '
            'ORDER BY t."fid" LIMIT ?',
            (xmin, xmax, ymin, ymax, MAX_TILE_CANDIDATES+1),
        ).fetchall()
    except sqlite3.DatabaseError as exc:
        raise TileIntersectionError("Unreadable original LiDAR RTree/feature metadata") from exc
    finally:
        db.close()
    if len(rows) != receipt["rtree_bbox_candidate_tiles"]:
        raise TileIntersectionError("Observed RTree candidate count changed during exact geometry check")

    polygons = []
    intersects = []
    groups = set()
    links = set()
    scheme_counts = Counter()
    for fid, blob, filename, folder, source_link in rows:
        if not isinstance(fid, int) or not isinstance(blob, bytes) or len(blob) > 1_000_000:
            raise TileIntersectionError("Unexpected tile ID or oversized/nonbinary original GPKG geometry")
        try:
            geom = wkb.loads(decode_gpkg_wkb(blob, 2169))
        except (GeoPackageGateError, ValueError, TypeError) as exc:
            raise TileIntersectionError("Original tile polygon could not be decoded") from exc
        if (geom.geom_type not in ("Polygon", "MultiPolygon")
                or geom.is_empty or not geom.is_valid or geom.area <= 0
                or not all(math.isfinite(x) for x in geom.bounds)):
            raise TileIntersectionError("Original LiDAR tile index has invalid polygon geometry")
        polygons.append(geom)
        if not geom.intersects(target):
            continue
        clip = geom.intersection(target)
        if clip.is_empty or clip.area <= 0:
            # touching a boundary is not a tile carrying measurable interior
            continue
        intersects.append(clip)
        if not all(isinstance(v, str) and 0 < len(v) <= 2048
                   for v in (filename, folder, source_link)):
            raise TileIntersectionError("Intersecting source tile lacks bounded download fields")
        url = urlsplit(source_link)
        if (url.scheme != "https" or url.hostname not in ("data.public.lu", "download.data.public.lu")
                or url.username or url.password or url.fragment
                or url.query or url.port not in (None, 443)):
            raise TileIntersectionError("Original intersecting tile has unreviewed provider URL")
        scheme_counts[url.hostname.lower()] += 1
        groups.add(folder)
        links.add(source_link)
    if not intersects:
        raise TileIntersectionError("RTree candidates do not actually cover the fixed original pilot")
    union = unary_union(intersects)
    actual_covered_fraction = min(1.0, union.area / target.area)
    if not 0 < actual_covered_fraction <= 1.0:
        raise TileIntersectionError("Unusable target-coverage polygon result")
    return {
        "schema_version": "lu-lidar2024-original-250m-actual-tile-intersection-v0",
        "original_index_sha256": receipt["original_sha256"],
        "original_index_rows": receipt["index_feature_rows"],
        "fixed_study_window": "Luxembourg city 250m x 250m equal-area, same as ACT/EUBUCCO original research",
        "rtree_bbox_candidates": len(rows),
        "decoded_valid_candidate_tile_polygons": len(polygons),
        "positive_area_tile_intersections": len(intersects),
        "intersection_union_coverage_fraction_rounded_6dp": round(actual_covered_fraction, 6),
        "distinct_intersecting_download_link_count": len(links),
        "distinct_intersecting_directory_count": len(groups),
        "intersecting_public_https_hosts": dict(sorted(scheme_counts.items())),
        "original_tile_ids_or_download_urls_exported": False,
        "original_tile_polygons_exported": False,
        "provider_laz_downloaded": False,
        "height_measurement_performed": False,
        "source_axis_ground_control_approved": False,
        "independent_building_height_validation_proven": False,
        "cat_model_input_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-gpkg", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        data = inspect_actual_tile_intersections(args.original_gpkg)
    except (TileIntersectionError, OSError, ValueError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
