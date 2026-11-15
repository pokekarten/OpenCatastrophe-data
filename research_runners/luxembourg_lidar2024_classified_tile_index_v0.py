#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""ACT LiDAR2024 classified COPC-LAZ official tile-index source receipt.

Read only one exact 3.4MB official GeoPackage index. Select two fixed
100m public research polygons, identify source tile/package metadata, and
print bounded aggregate diagnostics. NO LAZ points, buildings, addresses,
original geometry or insurer exposure are downloaded or exported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys

from research_runners.luxembourg_gpkg_schema_window_v0 import decode_gpkg_wkb

OFFICIAL_SOURCE = (
    "https://download.data.public.lu/resources/"
    "lidar-2024-releve-3d-du-territoire-luxembourgeois/"
    "20250117-095958/lidar2024-ta.gpkg"
)
PUBLISHED_SHA1 = "3269aecb189271e7c3f86127c0e96f4e213557c9"
MAX_BYTES = 6 * 1024 * 1024
MAX_TILES = 25000
MAX_PER_SITE = 25
SITES = {
    "luxembourg-city": (6.1319, 49.6116),
    "berdorf-village": (6.348821, 49.820946),
}
IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")


class LidarIndexGateError(ValueError):
    """Official tile reference or source geometry failed a research safeguard."""


def _hash(path: Path, kind: str) -> str:
    h = hashlib.new(kind)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _id(value: str) -> str:
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise LidarIndexGateError("Unsupported source SQL identifier")
    return '"' + value + '"'


def _study_polygon(site: str):
    """Same predeclared 100m equal-area square as GeoBase/LiDAR site control."""
    from pyproj import Transformer
    from shapely.geometry import Polygon

    if site not in SITES:
        raise LidarIndexGateError("Research site is not preapproved")
    longitude, latitude = SITES[site]
    x, y = Transformer.from_crs(4326, 3035, always_xy=True).transform(
        longitude, latitude
    )
    transform = Transformer.from_crs(3035, 2169, always_xy=True)
    corners = [
        transform.transform(x + dx, y + dy)
        for dx, dy in ((-50, -50), (50, -50), (50, 50), (-50, 50))
    ]
    roi = Polygon(corners)
    if not roi.is_valid or not 9700 <= roi.area <= 10300:
        raise LidarIndexGateError("Fixed 100m source CRS window is invalid")
    return roi


def _one_published_tile_layer(db: sqlite3.Connection):
    try:
        rows = db.execute(
            "SELECT c.table_name, g.column_name, g.geometry_type_name, g.srs_id "
            "FROM gpkg_contents c JOIN gpkg_geometry_columns g "
            "ON c.table_name=g.table_name WHERE c.data_type='features' "
            "ORDER BY c.table_name"
        ).fetchall()
    except sqlite3.Error as exc:
        raise LidarIndexGateError("Cannot inspect original GeoPackage schema") from exc
    if len(rows) != 1:
        raise LidarIndexGateError(
            "Expected exactly one official polygon index layer; inspect upstream schema"
        )
    table, geom, typ, srs = rows[0]
    _id(table)
    _id(geom)
    if not isinstance(typ, str) or typ.upper() not in ("POLYGON", "MULTIPOLYGON", "GEOMETRY"):
        raise LidarIndexGateError("Tile index must declare area geometries")
    if srs != 2169:
        raise LidarIndexGateError("Original tile index EPSG:2169 required")
    crs = db.execute(
        "SELECT organization, organization_coordsys_id "
        "FROM gpkg_spatial_ref_sys WHERE srs_id=?", (srs,)
    ).fetchone()
    if not crs or crs[0].upper() != "EPSG" or crs[1] != 2169:
        raise LidarIndexGateError("Original EPSG:2169 spatial reference missing")
    cols = db.execute("PRAGMA table_info(" + _id(table) + ")").fetchall()
    fieldnames = [c[1] for c in cols]
    if geom not in fieldnames:
        raise LidarIndexGateError("Missing original tile geometry column")
    count = db.execute("SELECT COUNT(*) FROM " + _id(table)).fetchone()[0]
    if not 1 <= count <= MAX_TILES:
        raise LidarIndexGateError("Original tile directory has unreasonable row count")
    return {
        "layer": table,
        "geometry_field": geom,
        "declared_geometry_type": typ,
        "source_srid": srs,
        "source_records": count,
        "source_column_names": fieldnames,
    }


def inspect(path: Path, *, published_sha1: str = PUBLISHED_SHA1) -> dict:
    if not isinstance(published_sha1, str) or not re.fullmatch("[0-9a-f]{40}", published_sha1):
        raise LidarIndexGateError("Official published SHA1 required before source use")
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".gpkg":
        raise LidarIndexGateError("Input must be the original local non-symlink .gpkg")
    if not 1000 <= path.stat().st_size <= MAX_BYTES:
        raise LidarIndexGateError("Index source is missing/oversized")
    sha1 = _hash(path, "sha1")
    if sha1 != published_sha1:
        raise LidarIndexGateError("Original file does not match published ACT SHA1")
    with path.open("rb") as reader:
        if reader.read(16) != b"SQLite format 3\x00":
            raise LidarIndexGateError("Original index does not contain SQLite header")
    from shapely import wkb

    try:
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
            db.execute("PRAGMA query_only=ON")
            if db.execute("PRAGMA application_id").fetchone()[0] not in (
                0x47504B47, 0x47503130, 0x47503131
            ):
                raise LidarIndexGateError("Invalid original GeoPackage application ID")
            schema = _one_published_tile_layer(db)
            table, geom = _id(schema["layer"]), _id(schema["geometry_field"])
            columns = [name for name in schema["source_column_names"] if name != schema["geometry_field"]]
            # Only coarse public tile names/group reference fields can ever be shown.
            # No arbitrary source columns or individual address values are emitted.
            candidate_cols = [
                name for name in columns
                if re.search(r"(tile|kachel|laz|copc|file|fichier|zip|group|groupe|dossier|download|url|link|nom|name)", name, re.I)
                and IDENT.fullmatch(name)
            ][:8]
            columns_sql = ",".join(_id(c) for c in candidate_cols)
            sql = (
                "SELECT " + _id(schema["geometry_field"]) +
                ("," + columns_sql if columns_sql else "") +
                " FROM " + table
            )
            studies = {name: _study_polygon(name) for name in SITES}
            matched = {name: [] for name in studies}
            records_scanned = 0
            # Bounded by verified official size and the maximum 25k table entries.
            for row in db.execute(sql):
                records_scanned += 1
                if records_scanned > MAX_TILES:
                    raise LidarIndexGateError("Unexpected unbounded original tile table")
                try:
                    polygon = wkb.loads(decode_gpkg_wkb(row[0], 2169))
                except Exception as exc:
                    raise LidarIndexGateError("Malformed original tile polygon WKB") from exc
                if (polygon.is_empty or not polygon.is_valid or polygon.area <= 0
                        or polygon.geom_type not in ("Polygon", "MultiPolygon")):
                    raise LidarIndexGateError("Malformed original tile footprint")
                for name, roi in studies.items():
                    if polygon.intersects(roi) and polygon.intersection(roi).area > 0:
                        if len(matched[name]) >= MAX_PER_SITE:
                            raise LidarIndexGateError("Too many tiles at fixed site")
                        fields = {}
                        for key, value in zip(candidate_cols, row[1:]):
                            # Reject unexpected types and avoid personal/signed URL material.
                            if isinstance(value, (int, str)):
                                val = str(value)
                                if 0 < len(val) < 260 and not any(x in val.lower() for x in (
                                    "token=", "key=", "signature=", "@"
                                )):
                                    fields[key] = val
                        matched[name].append(fields)
            if records_scanned != schema["source_records"]:
                raise LidarIndexGateError("Original index row count differs from schema")
            if any(not tiles for tiles in matched.values()):
                raise LidarIndexGateError("Missing official classified tile intersection")
    except sqlite3.Error as exc:
        raise LidarIndexGateError("Corrupted/unreadable original GeoPackage index") from exc

    return {
        "schema_version": "lu-classified-lidar2024-copc-tile-index-receipt-v0",
        "official_dataset": "ACT BD-L-Lidar2024 classified COPC pointcloud tiles",
        "original_resource_url": OFFICIAL_SOURCE,
        "original_published_sha1_verified": True,
        "source_sha1": sha1,
        "source_sha256": _hash(path, "sha256"),
        "source_file_bytes": path.stat().st_size,
        "tile_index_schema": schema,
        "tile_reference_columns": candidate_cols,
        "fixed_study_tile_intersections": {
            name: {"tile_count": len(v), "public_tile_reference_fields": v}
            for name, v in matched.items()
        },
        "source_class_codes_from_publisher": {
            "ground": 2, "high_vegetation": 5, "buildings": 6
        },
        "point_records_or_laz_archives_downloaded": False,
        "building_vs_vegetation_classified_points_observed": False,
        "class_6_validated_against_manual_roof_truth": False,
        "historical_source_and_geo_geometry_independence_proven": False,
        "licence_and_scientific_admission_approved": False,
        "per_building_data_exported": False,
        "model_input_admitted": False,
        "note": (
            "Class 5 vegetation and class 6 building points are part of the official "
            "COPC LAZ source catalogue, NOT distinguished in the existing combined MNS raster. "
            "This index is only for an exact, bounded point-classification experiment. "
            "Publisher licence CC0 does not prove classification accuracy or source independence."
        )
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-gpkg", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect(args.index_gpkg)
    except (LidarIndexGateError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
