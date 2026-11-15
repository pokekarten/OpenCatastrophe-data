#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original GeoPackage schema/CRS receipt and optional bounded polygon export.

Stage 2 AFTER independently verified ACT ZIP preflight (PR #911).
Only accepts an already extracted local .gpkg and a predeclared exact SHA-256.
Does not download data, import to Neon, validate commercial rights, certify
building identity, or admit any provider asset as an insurance model input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import struct
import sys

MAX_GPKG_BYTES = 2 * 1024**3
MAX_EXPORT = 1500
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
ENVELOPES = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


class GeoPackageGateError(ValueError):
    """Stop: input geometry, identity or provenance is not verified."""


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def identifier(value: str) -> str:
    if not isinstance(value, str) or not IDENT_RE.fullmatch(value):
        raise GeoPackageGateError("Invalid SQL identifier")
    return '"' + value + '"'


def decode_gpkg_wkb(blob: bytes, expected_srs: int) -> bytes:
    """Decode GeoPackage binary header; never guess its coordinate order."""
    if not isinstance(blob, bytes) or len(blob) < 13 or blob[:2] != b"GP" or blob[2] != 0:
        raise GeoPackageGateError("Invalid GeoPackage geometry header")
    flags = blob[3]
    if flags & 0xF0:
        raise GeoPackageGateError("Reserved/empty geometry flags rejected")
    envelope_kind = (flags >> 1) & 7
    if envelope_kind not in ENVELOPES:
        raise GeoPackageGateError("Unsupported geometry envelope code")
    endian = "<" if flags & 1 else ">"
    srid = struct.unpack(endian + "i", blob[4:8])[0]
    if srid != expected_srs:
        raise GeoPackageGateError("Geometry blob SRID differs from declared layer CRS")
    offset = 8 + ENVELOPES[envelope_kind]
    if len(blob) < offset + 5:
        raise GeoPackageGateError("Truncated geometry binary")
    return blob[offset:]


def inspect(path: Path, *, expected_sha256: str) -> tuple[dict, sqlite3.Connection]:
    if not isinstance(expected_sha256, str) or not SHA_RE.fullmatch(expected_sha256):
        raise GeoPackageGateError("Expected predeclared SHA-256 is mandatory")
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".gpkg":
        raise GeoPackageGateError("Require an existing non-symlink local .gpkg")
    size = path.stat().st_size
    if not 0 < size <= MAX_GPKG_BYTES:
        raise GeoPackageGateError("Local GeoPackage exceeds bounded size")
    digest = file_hash(path)
    if digest != expected_sha256:
        raise GeoPackageGateError("GeoPackage hash does not match original ZIP receipt")
    with path.open("rb") as stream:
        if stream.read(16) != b"SQLite format 3\x00":
            raise GeoPackageGateError("Not a SQLite GeoPackage")
    db = None
    try:
        db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
        db.execute("PRAGMA query_only=ON")
        if db.execute("PRAGMA application_id").fetchone()[0] not in (
            0x47504B47, 0x47503130, 0x47503131,
        ):
            raise GeoPackageGateError("Invalid GeoPackage application ID")
        rows = db.execute(
            "SELECT c.table_name, g.column_name, g.geometry_type_name, g.srs_id "
            "FROM gpkg_contents c JOIN gpkg_geometry_columns g "
            "ON c.table_name=g.table_name WHERE c.data_type='features' "
            "ORDER BY c.table_name"
        ).fetchall()
        if not rows:
            raise GeoPackageGateError("GeoPackage has no feature layers")
        layers = []
        for name, geom, geometry_type, srs in rows:
            table, geom_column = identifier(name), identifier(geom)
            if geometry_type.upper() not in ("POLYGON", "MULTIPOLYGON", "GEOMETRY"):
                raise GeoPackageGateError("Unexpected non-polygon geometry layer")
            crs_row = db.execute(
                "SELECT organization, organization_coordsys_id "
                "FROM gpkg_spatial_ref_sys WHERE srs_id=?", (srs,),
            ).fetchone()
            if not crs_row or crs_row[0].upper() != "EPSG" or crs_row[1] != srs:
                raise GeoPackageGateError("Layer CRS is not a verified EPSG identifier")
            cols = db.execute("PRAGMA table_info(" + table + ")").fetchall()
            if geom not in [col[1] for col in cols]:
                raise GeoPackageGateError("Missing registered geometry field")
            n = db.execute("SELECT count(*) FROM " + table).fetchone()[0]
            rtree = "rtree_" + name + "_" + geom
            indexed = bool(db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (rtree,),
            ).fetchone())
            layers.append({
                "table": name, "geometry_column": geom,
                "geometry_type": geometry_type, "srs_id": srs,
                "feature_count": n, "has_rtree": indexed,
                "fields": [
                    {"name": col[1], "type": col[2], "is_primary_key": bool(col[5])}
                    for col in cols
                ],
            })
        report = {
            "schema_version": "lu-official-gpkg-schema-receipt-v0",
            "source_gpkg_sha256": digest, "source_gpkg_bytes": size,
            "layers": layers,
            "source_identity_verified": False,
            "source_rights_approved": False,
            "raw_database_imported": False,
            "model_input_admitted": False,
            "coordinate_axis_order_verified": False,
            "note": (
                "Provider ACT2023v2 reports EPSG:2169 / LUREF LTM, "
                "X=Northing Y=Easting; verify actual stored X/Y order from "
                "known ground-control landmarks before reprojection. "
                "These 2D polygons are *roof extents*, not surveyed wall footprints."
            ),
        }
        return report, db
    except (sqlite3.Error, OSError) as exc:
        if db:
            db.close()
        raise GeoPackageGateError("Unreadable GeoPackage SQLite schema") from exc
    except Exception:
        if db:
            db.close()
        raise


def sample(db: sqlite3.Connection, layer: dict, *, id_field: str,
           bbox: tuple[float, float, float, float], limit: int, output: Path) -> int:
    if not 1 <= limit <= MAX_EXPORT:
        raise GeoPackageGateError("Bounded export limit must be 1..1500")
    if (len(bbox) != 4 or not all(isinstance(x, (int, float))
            and math.isfinite(x) and abs(x) < 1e9 for x in bbox)):
        raise GeoPackageGateError("Invalid or nonfinite native-coordinate bbox")
    xmin, ymin, xmax, ymax = bbox
    if xmin >= xmax or ymin >= ymax:
        raise GeoPackageGateError("Invalid native-coordinate bbox bounds")
    if layer["srs_id"] != 2169:
        raise GeoPackageGateError("ACT2023v2 sample must be EPSG:2169")
    if not layer["has_rtree"]:
        raise GeoPackageGateError("No spatial RTree: bounded extraction denied")
    id_sql = identifier(id_field)
    if id_field not in [col["name"] for col in layer["fields"]]:
        raise GeoPackageGateError("Explicit original building ID column missing")
    if id_field.casefold() in ("address", "owner", "street", "postcode", "name"):
        raise GeoPackageGateError("Cannot use address/owner as a building identity")
    table, geom = identifier(layer["table"]), identifier(layer["geometry_column"])
    rtree = identifier("rtree_" + layer["table"] + "_" + layer["geometry_column"])
    if output.exists() or output.is_symlink():
        raise GeoPackageGateError("Never overwrite an existing output")
    try:
        from shapely import wkb
        from shapely.geometry import box, mapping
    except ImportError as exc:
        raise GeoPackageGateError("Shapely is required for optional spatial export") from exc
    query = (
        f"SELECT b.{id_sql}, b.{geom} FROM {table} b "
        f"JOIN {rtree} r ON b.ROWID = r.id "
        "WHERE r.maxx>=? AND r.minx<=? AND r.maxy>=? AND r.miny<=? "
        f"ORDER BY b.{id_sql} LIMIT ?"
    )
    rows = db.execute(query, (xmin, xmax, ymin, ymax, limit + 1)).fetchall()
    if len(rows) > limit:
        raise GeoPackageGateError("Window contains too many candidates; reduce bbox")
    window = box(xmin, ymin, xmax, ymax)
    features, seen = [], set()
    for source_id, blob in rows:
        if not isinstance(source_id, (str, int)):
            raise GeoPackageGateError("Missing/non-scalar source building ID")
        sid = str(source_id)
        if not sid or len(sid) > 256 or sid in seen:
            raise GeoPackageGateError("Blank, duplicate or oversized source building ID")
        seen.add(sid)
        raw_wkb = decode_gpkg_wkb(blob, 2169)
        try:
            polygon = wkb.loads(raw_wkb)
        except (ValueError, TypeError) as exc:
            raise GeoPackageGateError("Invalid WKB geometry") from exc
        if (polygon.is_empty or not polygon.is_valid or polygon.area <= 0
                or polygon.geom_type not in ("Polygon", "MultiPolygon")):
            raise GeoPackageGateError("Invalid/non-polygon source geometry")
        if polygon.intersects(window):
            features.append({
                "type": "Feature", "properties": {"building_id": sid},
                "geometry": mapping(polygon),
            })
    if not features:
        raise GeoPackageGateError("No building polygons intersect the window")
    output.write_text(json.dumps(
        {"type": "FeatureCollection", "features": features},
        ensure_ascii=False, separators=(",", ":"),
    ) + "\n", encoding="utf-8")
    return len(features)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpkg", type=Path, required=True)
    parser.add_argument("--expected-gpkg-sha256", required=True)
    parser.add_argument("--layer")
    parser.add_argument("--id-column")
    parser.add_argument("--native-epsg2169-bbox", nargs=4, type=float)
    parser.add_argument("--output-local", type=Path)
    parser.add_argument("--permit-local-research-export", action="store_true")
    parser.add_argument("--limit", type=int, default=250)
    args = parser.parse_args(argv)
    try:
        receipt, db = inspect(args.gpkg, expected_sha256=args.expected_gpkg_sha256)
        try:
            if args.output_local is not None:
                if not (args.permit_local_research_export and args.layer and args.id_column
                        and args.native_epsg2169_bbox):
                    raise GeoPackageGateError("Local sample needs explicit source, bbox, and opt-in")
                matches = [x for x in receipt["layers"] if x["table"] == args.layer]
                if len(matches) != 1:
                    raise GeoPackageGateError("Requested feature layer does not exist")
                receipt["local_sample_features"] = sample(
                    db, matches[0], id_field=args.id_column,
                    bbox=tuple(args.native_epsg2169_bbox),
                    limit=args.limit, output=args.output_local,
                )
            print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))
        finally:
            db.close()
        return 0
    except GeoPackageGateError as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
