#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Build an isolated CAT-only SQLite spatial staging index from pinned DEU ADM1.

Opt-in only, off-repository path, no source fetch and no connection to any
production database. RTree gives candidate bboxes; exact point-in-polygon is
evaluated separately with Shapely to avoid incorrect bbox-only assignments.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import Any

from research_runners.geoboundaries_deu_adm1_original_geojson_v0 import (
    BOUNDARY_ID, BoundaryGeometryError, DATA_YEAR, EXPECTED_FEATURES,
    MAX_SOURCE_BYTES, SOURCE_GIT_COMMIT, SOURCE_LFS_OID_SHA256,
    SOURCE_LFS_SIZE, SOURCE_URL, inspect_geojson_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
CAT_APP_ID = 0x43415431  # 'CAT1', physically separate from existing catalog DBs
CAT_SCHEMA_VERSION = 1
SCHEMA_NAME = "deu_adm1_geoBoundaries_2021_cat_stage_v0"
COLLECTION_LICENSE = "CC BY 4.0 (geoBoundaries, attribution required)"
ORIGINAL_LICENSE = "Data license Germany - Attribution - Version 2.0"
ORIGINAL_LICENSE_SOURCE = "https://www.govdata.de/dl-de/by-2-0"


class SpatialStageError(ValueError):
    """Unsafe output, source mismatch, schema drift or ambiguous join."""


def _check_destination(path: Path) -> Path:
    if not path.is_absolute() or not path.name.endswith(".cat.sqlite"):
        raise SpatialStageError("output must be an absolute new *.cat.sqlite CAT file")
    target = path.resolve(strict=False)
    if target.is_relative_to(ROOT):
        raise SpatialStageError("no original or derived geography inside Git checkout")
    if target.exists():
        raise SpatialStageError("refusing to overwrite any pre-existing database")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise SpatialStageError("CAT staging parent directory must already exist")
    return target


def _create_schema(conn: sqlite3.Connection, source_digest: str) -> None:
    conn.execute(f"PRAGMA application_id = {CAT_APP_ID}")
    conn.execute(f"PRAGMA user_version = {CAT_SCHEMA_VERSION}")
    conn.executescript("""
        CREATE TABLE source_provenance (
            singleton INTEGER PRIMARY KEY CHECK(singleton=1),
            schema_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            boundary_id TEXT NOT NULL,
            country_iso3 TEXT NOT NULL CHECK(country_iso3='DEU'),
            level TEXT NOT NULL CHECK(level='ADM1'),
            represented_year INTEGER NOT NULL,
            pinned_upstream_commit TEXT NOT NULL,
            original_source_sha256 TEXT NOT NULL,
            original_source_length INTEGER NOT NULL,
            original_asset_url TEXT NOT NULL,
            collection_license TEXT NOT NULL,
            original_license TEXT NOT NULL,
            original_license_source TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status='isolated_research_staging_not_model_admitted')
        );
        CREATE TABLE admin1_polygon (
            id INTEGER PRIMARY KEY,
            shape_id TEXT NOT NULL UNIQUE,
            shape_name TEXT NOT NULL UNIQUE,
            shape_iso TEXT,
            geometry_wkb BLOB NOT NULL,
            min_lon REAL NOT NULL,
            min_lat REAL NOT NULL,
            max_lon REAL NOT NULL,
            max_lat REAL NOT NULL
        );
        CREATE VIRTUAL TABLE admin1_bbox USING rtree(
            id, min_lon, max_lon, min_lat, max_lat
        );
    """)
    conn.execute("""
        INSERT INTO source_provenance
        VALUES (1, ?, 'geoboundaries.gbopen', ?, 'DEU', 'ADM1', ?, ?, ?, ?, ?, ?, ?, ?,
                'isolated_research_staging_not_model_admitted')
    """, (SCHEMA_NAME, BOUNDARY_ID, DATA_YEAR, SOURCE_GIT_COMMIT,
          source_digest, SOURCE_LFS_SIZE, SOURCE_URL, COLLECTION_LICENSE,
          ORIGINAL_LICENSE, ORIGINAL_LICENSE_SOURCE))


def build_staging_from_bytes(
    raw: bytes, *, expected_sha256: str, expected_size: int, output_path: Path,
) -> dict[str, Any]:
    """In CI, fixtures pass their own digests; CLI always pins original LFS SHA."""
    report = inspect_geojson_bytes(
        raw, expected_sha256=expected_sha256, expected_size=expected_size,
    )
    dest = _check_destination(output_path)
    try:
        from shapely.geometry import shape
    except ImportError as exc:
        raise SpatialStageError("Shapely reviewed dependency is required") from exc

    # SHA verified before this second parse; only 16 bounded original features.
    features = json.loads(raw.decode("utf-8"))["features"]
    fd, tmp_name = tempfile.mkstemp(prefix=".cat-adm1-", suffix=".sqlite", dir=dest.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(tmp_name)) as conn:
            _create_schema(conn, expected_sha256)
            with conn:
                for id_, feature in enumerate(features, 1):
                    p = feature["properties"]
                    geo = shape(feature["geometry"])
                    x0, y0, x1, y1 = (float(n) for n in geo.bounds)
                    shape_iso = p.get("shapeISO")
                    if shape_iso is not None and type(shape_iso) is not str:
                        raise SpatialStageError("unexpected provider shapeISO")
                    conn.execute("""
                        INSERT INTO admin1_polygon (
                            id, shape_id, shape_name, shape_iso, geometry_wkb,
                            min_lon, min_lat, max_lon, max_lat
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (id_, p["shapeID"], p["shapeName"], shape_iso, geo.wkb,
                          x0, y0, x1, y1))
                    conn.execute("""
                        INSERT INTO admin1_bbox VALUES (?, ?, ?, ?, ?)
                    """, (id_, x0, x1, y0, y1))
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise SpatialStageError("SQLite integrity_check did not pass")
            if conn.execute("SELECT count(*) FROM admin1_bbox").fetchone()[0] != EXPECTED_FEATURES:
                raise SpatialStageError("incomplete spatial RTree index")
        # A hard link refuses to replace an existing file even under a race.
        os.link(tmp_name, dest)
    except (OSError, sqlite3.Error, ValueError) as exc:
        raise SpatialStageError("CAT SQLite staging construction failed") from exc
    finally:
        Path(tmp_name).unlink(missing_ok=True)

    return {
        "schema": SCHEMA_NAME,
        "db_application_id": CAT_APP_ID,
        "model_input_admitted": False,
        "country": "DEU",
        "level": "ADM1",
        "represented_year": DATA_YEAR,
        "source_sha256": expected_sha256,
        "indexed_polygons": EXPECTED_FEATURES,
        "rtree_bbox_candidates_need_exact_polygon_test": True,
        "provider_bytes_committed_to_repository": False,
        "separate_cat_staging_file_created": True,
        "verified_geometry_coordinates": report["total_polygon_coordinates"],
    }


def open_cat_index(db: Path) -> sqlite3.Connection:
    if not db.is_file():
        raise SpatialStageError("CAT staging database missing")
    # read-only URI disables accidental writes, also from query users.
    from urllib.parse import quote
    uri = "file:" + quote(str(db.resolve()), safe="/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    if (
        conn.execute("PRAGMA application_id").fetchone()[0] != CAT_APP_ID
        or conn.execute("PRAGMA user_version").fetchone()[0] != CAT_SCHEMA_VERSION
    ):
        conn.close()
        raise SpatialStageError("not the reviewed CAT geography staging schema")
    return conn


def lookup_admin1(conn: sqlite3.Connection, longitude: float, latitude: float) -> dict | None:
    """Exact WGS84 point join. Shared boundaries are ambiguous, not guessed."""
    from shapely.geometry import Point
    from shapely.wkb import loads

    if (
        type(longitude) not in (float, int)
        or type(latitude) not in (float, int)
        or not math.isfinite(longitude) or not math.isfinite(latitude)
        or not -180 <= longitude <= 180 or not -90 <= latitude <= 90
    ):
        raise SpatialStageError("invalid WGS84 longitude/latitude")
    point = Point(longitude, latitude)
    candidates = conn.execute("""
        SELECT p.shape_id, p.shape_name, p.shape_iso, p.geometry_wkb
        FROM admin1_bbox r JOIN admin1_polygon p ON p.id=r.id
        WHERE r.min_lon<=? AND r.max_lon>=?
          AND r.min_lat<=? AND r.max_lat>=?
    """, (longitude, longitude, latitude, latitude)).fetchall()
    matched = [
        (sid, name, iso)
        for sid, name, iso, wkb in candidates
        if loads(wkb).covers(point)
    ]
    if len(matched) > 1:
        raise SpatialStageError("boundary/overlap point matches several ADM1 polygons")
    if len(matched) == 0:
        return None
    sid, name, iso = matched[0]
    return {
        "shape_id": sid,
        "shape_name": name,
        "shape_iso_original": iso,
        "source_year": DATA_YEAR,
        "source_boundary_id": BOUNDARY_ID,
        "official_nuts_crosswalk_verified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-geojson", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="absolute path outside repo ending in *.cat.sqlite")
    args = parser.parse_args(argv)
    try:
        inp = args.original_geojson
        if not inp.is_file() or inp.is_symlink() or inp.stat().st_size != SOURCE_LFS_SIZE:
            raise SpatialStageError("original source file must match fixed Git-LFS size")
        with inp.open("rb") as f:
            raw = f.read(MAX_SOURCE_BYTES + 1)
        out = build_staging_from_bytes(
            raw, expected_sha256=SOURCE_LFS_OID_SHA256,
            expected_size=SOURCE_LFS_SIZE, output_path=args.output,
        )
        print(json.dumps(out, sort_keys=True, indent=2))
    except (BoundaryGeometryError, SpatialStageError, OSError, sqlite3.Error) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
