#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Select LiDAR2024 *candidate tile counts* for the fixed public Luxembourg pilot.

Source byte hash is pinned to successful original index preflight (#931).
Uses provider GPKG RTree only, bounded geographic 250m study window.
Reads only tile URL hostnames, not file download contents, polygon WKB or
personal/building identities. Never downloads tiles or admits CAT model data.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

from research_runners.luxembourg_lidar2024_tile_index_receipt_v0 import (
    LidarIndexError, PUBLISHER_SHA1, inspect,
)

SOURCE_SHA256 = "3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8"
LAYER = "TableauAssemblage"
RTREE = "rtree_TableauAssemblage_geom"
DEFAULT_LON = 6.1319
DEFAULT_LAT = 49.6116
HALF_WIDTH_M = 125.0
MAX_TILE_CANDIDATES = 12


class LidarTileSelectionError(ValueError):
    pass


def select_original_tiles(
    file: Path, *, expected_sha256: str = SOURCE_SHA256,
    expected_sha1: str = PUBLISHER_SHA1,
    longitude: float = DEFAULT_LON, latitude: float = DEFAULT_LAT,
    half_width_m: float = HALF_WIDTH_M, candidate_cap: int = MAX_TILE_CANDIDATES,
) -> dict:
    if (not all(isinstance(v, (int, float)) and math.isfinite(v)
                for v in (longitude, latitude, half_width_m))
            or not (5.7 <= longitude <= 6.6 and 49.4 <= latitude <= 50.2)
            or not (20 <= half_width_m <= 125)
            or not (1 <= candidate_cap <= MAX_TILE_CANDIDATES)):
        raise LidarTileSelectionError("Unbounded or invalid public Luxembourg-city study window")
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise LidarTileSelectionError("Pinned PyProj required for bounded CRS conversion") from exc
    try:
        receipt = inspect(file, expected_sha1=expected_sha1)
    except (LidarIndexError, OSError) as exc:
        raise LidarTileSelectionError("Official LiDAR2024 source preflight rejected") from exc
    if receipt["original_sha256"] != expected_sha256:
        raise LidarTileSelectionError("Original LiDAR2024 index differs from pre-observed SHA256")
    layers = receipt["feature_layers"]
    if (len(layers) != 1 or layers[0]["feature_table"] != LAYER
            or not layers[0]["rtree_present"]
            or not {"fid", "geom", "Fichier", "Dossier", "DownloadLink"}.issubset(
                layers[0]["field_names_only"])):
        raise LidarTileSelectionError("Unreviewed original tile table/fields/spatial index")

    # Replicate the exact study-window coordinate prescription of merged #924:
    # EPSG:4326 public center -> EPSG:3035 equal-area square -> EPSG:2169 bbox.
    to3035 = Transformer.from_crs(4326, 3035, always_xy=True)
    to2169 = Transformer.from_crs(3035, 2169, always_xy=True)
    cx, cy = to3035.transform(longitude, latitude)
    corners = [to2169.transform(x, y) for x, y in (
        (cx-half_width_m, cy-half_width_m),
        (cx-half_width_m, cy+half_width_m),
        (cx+half_width_m, cy-half_width_m),
        (cx+half_width_m, cy+half_width_m),
    )]
    if not all(math.isfinite(v) for point in corners for v in point):
        raise LidarTileSelectionError("Unexpected projected coordinate")
    xmin, xmax = min(x for x, _ in corners), max(x for x, _ in corners)
    ymin, ymax = min(y for _, y in corners), max(y for _, y in corners)
    db = sqlite3.connect(Path(file).resolve().as_uri()+"?mode=ro&immutable=1", uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        # RTree row-level predicate: index *candidate* only. Tile polygon
        # intersections and downloaded LAZ contents are not yet verified.
        rows = db.execute(
            'SELECT t."fid", t."DownloadLink" '
            'FROM "TableauAssemblage" t '
            'JOIN "rtree_TableauAssemblage_geom" r ON t."fid" = r.id '
            'WHERE r.maxx >= ? AND r.minx <= ? AND r.maxy >= ? AND r.miny <= ? '
            'ORDER BY t."fid" LIMIT ?',
            (xmin, xmax, ymin, ymax, candidate_cap + 1),
        ).fetchall()
    except sqlite3.DatabaseError as exc:
        raise LidarTileSelectionError("Unsafe or unreadable original tile RTree data") from exc
    finally:
        db.close()
    if not 1 <= len(rows) <= candidate_cap:
        raise LidarTileSelectionError("No tiles or too many RTree candidates in bounded window")
    ids = [r[0] for r in rows]
    if len(ids) != len(set(ids)):
        raise LidarTileSelectionError("Duplicated original LiDAR tile identities")
    host_counts = Counter()
    link_state = Counter()
    for fid, url in rows:
        if not isinstance(fid, int):
            raise LidarTileSelectionError("Original tile lacks expected integer row identity")
        if not isinstance(url, str) or not url:
            link_state["missing"] += 1
            continue
        parts = urlsplit(url)
        if (parts.scheme == "https" and parts.hostname
                and parts.username is None and parts.password is None):
            host_counts[parts.hostname.lower()] += 1
            link_state["https"] += 1
        else:
            link_state["non_https_or_ambiguous"] += 1
    return {
        "profile": "lu-act-lidar2024-original-fixed-window-rtree-tile-candidates-v0",
        "original_sha1": receipt["original_sha1"],
        "original_sha256": receipt["original_sha256"],
        "index_feature_rows": layers[0]["feature_rows"],
        "study_window": {
            "public_pilot_center_lon": longitude,
            "public_pilot_center_lat": latitude,
            "equal_area_epsg3035_window_side_metres": 2 * half_width_m,
            "epsg2169_coordinate_axis_ground_control_verified": False,
        },
        "rtree_bbox_candidate_tiles": len(rows),
        "download_link_format_counts": dict(sorted(link_state.items())),
        "public_download_link_host_counts": dict(sorted(host_counts.items())),
        "raw_tile_links_or_names_exported": False,
        "actual_tile_polygon_intersection_confirmed": False,
        "point_cloud_downloaded": False,
        "measured_building_heights": False,
        "independent_cross_source_validation_proven": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-gpkg", type=Path, required=True)
    opts = parser.parse_args(argv)
    try:
        report = select_original_tiles(opts.original_gpkg)
    except (OSError, LidarTileSelectionError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
        return 0
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
