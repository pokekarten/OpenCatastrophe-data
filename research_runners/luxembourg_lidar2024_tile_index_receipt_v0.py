#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect only the original CC0 ACT BD-L-Lidar2024 tile assembly GPKG metadata.

Requires the publisher-listed SHA1 of the exact small 2025-01-17 tile-index
resource; hashes original bytes with SHA256, checks GeoPackage structure, layer
count/CRS/fields/RTree and aggregate counts. Does NOT open LAS/LAZ/COG,
read any tile URL or identity, download tiles, emit geometry, or admit model data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

SOURCE_RESOURCE_ID = "04cfeb86-c9df-4ee6-a45a-8671af98a114"
SOURCE_URL = ("https://download.data.public.lu/resources/"
              "lidar-2024-releve-3d-du-territoire-luxembourgeois/"
              "20250117-095958/lidar2024-ta.gpkg")
PUBLISHER_SHA1 = "3269aecb189271e7c3f86127c0e96f4e213557c9"
MAX_BYTES = 10 * 1024 * 1024
MAX_FEATURE_LAYERS = 10
MAX_LAYER_ROWS = 100000
MAX_FIELDS_PER_LAYER = 64
HEX_SHA1 = re.compile(r"[0-9a-f]{40}\Z")


class LidarIndexError(ValueError):
    """Source index not independently pinned or schema fails conservative checks."""


def hashes(file: Path) -> tuple[str, str]:
    sha1, sha256 = hashlib.sha1(), hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha1.update(block)
            sha256.update(block)
    return sha1.hexdigest(), sha256.hexdigest()


def _ident(name: str) -> str:
    if not isinstance(name, str) or not name or len(name) > 128 or "\x00" in name:
        raise LidarIndexError("Unsafe source layer identifier")
    return '"' + name.replace('"', '""') + '"'


def inspect(file: Path, *, expected_sha1: str = PUBLISHER_SHA1) -> dict:
    file = Path(file)
    if not HEX_SHA1.fullmatch(expected_sha1):
        raise LidarIndexError("Malformed published SHA1")
    if (not file.is_file() or file.is_symlink()
            or not 0 < file.stat().st_size <= MAX_BYTES):
        raise LidarIndexError("Missing, symlinked or oversized original GeoPackage")
    original_sha1, original_sha256 = hashes(file)
    if original_sha1 != expected_sha1:
        raise LidarIndexError("Original file SHA1 differs from publisher-listed value")
    with file.open("rb") as original:
        if original.read(16) != b"SQLite format 3\x00":
            raise LidarIndexError("Original file is not SQLite")
    db = None
    try:
        db = sqlite3.connect(file.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
        db.execute("PRAGMA query_only=ON")
        if db.execute("PRAGMA application_id").fetchone()[0] not in (
            0x47504B47, 0x47503130, 0x47503131
        ):
            raise LidarIndexError("Original SQLite has no recognized GeoPackage application ID")
        required = {"gpkg_contents", "gpkg_geometry_columns", "gpkg_spatial_ref_sys"}
        present = {x[0] for x in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if not required <= present:
            raise LidarIndexError("Original GeoPackage mandatory tables missing")
        layers = list(db.execute(
            "SELECT c.table_name,c.srs_id,g.column_name,g.geometry_type_name,g.srs_id,"
            "c.min_x,c.min_y,c.max_x,c.max_y "
            "FROM gpkg_contents c JOIN gpkg_geometry_columns g "
            "ON c.table_name=g.table_name WHERE c.data_type='features' "
            "ORDER BY c.table_name"))
        if not 1 <= len(layers) <= MAX_FEATURE_LAYERS:
            raise LidarIndexError("Unexpected source tile-index feature-layer count")
        result = []
        for table_name, csrs, geom_col, geom_type, gsrs, minx, miny, maxx, maxy in layers:
            if (csrs != 2169 or gsrs != 2169 or
                    not isinstance(geom_type, str) or
                    geom_type.upper() not in ("POLYGON", "MULTIPOLYGON", "GEOMETRY")):
                raise LidarIndexError("Unexpected LiDAR index geometry CRS/type")
            source_name = _ident(table_name)
            if table_name not in present:
                raise LidarIndexError("Declared tile layer table missing")
            cols = list(db.execute("PRAGMA table_info(" + source_name + ")"))
            if not 1 <= len(cols) <= MAX_FIELDS_PER_LAYER or geom_col not in [c[1] for c in cols]:
                raise LidarIndexError("Original GPKG geometry field missing or too many fields")
            count = db.execute("SELECT count(*) FROM " + source_name).fetchone()[0]
            if not isinstance(count, int) or not 1 <= count <= MAX_LAYER_ROWS:
                raise LidarIndexError("Original tile layer outside size budget")
            rtree = "rtree_" + table_name + "_" + geom_col
            result.append({
                "feature_table": table_name,
                "declared_geometry_type": geom_type,
                "declared_epsg": csrs,
                "feature_rows": count,
                "geometry_column": geom_col,
                "field_names_only": [c[1] for c in cols],
                "rtree_present": rtree in present,
                "aggregate_extent_declared": all(v is not None for v in (minx, miny, maxx, maxy))
            })
        return {
            "profile": "lu-act-lidar2024-original-tile-assembly-source-receipt-v0",
            "provider_resource_id": SOURCE_RESOURCE_ID,
            "provider_url": SOURCE_URL,
            "publisher_sha1_verified": True,
            "original_sha1": original_sha1,
            "original_sha256": original_sha256,
            "original_bytes": file.stat().st_size,
            "feature_layers": result,
            "original_provider_tile_rows_exported": False,
            "individual_tile_urls_or_identifiers_read": False,
            "point_cloud_laz_downloaded": False,
            "actual_building_heights_measured": False,
            "independent_lidar_vs_act_validation_approved": False,
            "rights_and_scientific_model_admission_approved": False,
            "model_input_admitted": False,
        }
    except sqlite3.DatabaseError as exc:
        raise LidarIndexError("Unreadable GeoPackage metadata") from exc
    finally:
        if db is not None:
            db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-gpkg", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect(args.original_gpkg)
    except (OSError, LidarIndexError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
