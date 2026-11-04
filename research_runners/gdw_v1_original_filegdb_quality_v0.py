# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only original GDW v1.0 FileGDB quality comparison; never publish raw features.

Acquires nothing: a trusted runner supplies an already-downloaded exact original
Figshare ZIP. Use a temporary, access-restricted unpack directory. Only bounded
aggregate geometry validity/ID pairing counts and original-file hashes exit.
An alternate representation is not independent source ground truth.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import logging
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import zipfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_runners.gdw_v1_original_spatial_quality_v0 import (
    _validity_reason_family, _check_id,
)
from research_runners.gdw_v1_original_shapefile_evidence_v0 import (
    GDW_V1_ORIGINAL_SHAPEFILE_EVIDENCE_V0 as SHAPEFILE,
)

GDW_FILE_ID = 47913742
PROVIDER_BYTES = 57_476_758
PROVIDER_MD5 = "410d1ed16312ac613975fd092c193c65"
MAX_UNPACKED_BYTES = 1024 * 1024 * 1024
MAX_SINGLE_MEMBER = 256 * 1024 * 1024
MAX_MEMBERS = 300
BUFFER = 64 * 1024
PROFILE = "gdw-v1-original-filegdb-geos-quality-v0"
EXPECTED_POINTS = 41_145
EXPECTED_POLYGONS = 35_295
EXPECTED_POINT_ONLY = 5_850
_ALLOWED_GEOMETRY_ROLES = {
    "GDW_barriers_v1_0": {"Point"},
    "GDW_reservoirs_v1_0": {"Polygon", "MultiPolygon"},
}


class GDWFileGDBError(ValueError):
    """Unsafe archive, inconsistent source structure, or reader error."""


def original_file_identity(path: Path, *, expected_size=PROVIDER_BYTES,
                           expected_md5=PROVIDER_MD5,
                           expected_sha256: str | None = None) -> dict:
    if (path.is_symlink() or not path.is_file()
            or not 1 <= path.stat().st_size <= PROVIDER_BYTES):
        raise GDWFileGDBError("original GDB ZIP must be a bounded regular file")
    if expected_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise GDWFileGDBError("invalid frozen SHA256 argument")
    sha, md5, total = hashlib.sha256(), hashlib.md5(usedforsecurity=False), 0
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(BUFFER), b""):
            total += len(chunk)
            if total > PROVIDER_BYTES:
                raise GDWFileGDBError("original ZIP exceeded bounded source size")
            sha.update(chunk)
            md5.update(chunk)
    if total != expected_size or md5.hexdigest() != expected_md5:
        raise GDWFileGDBError("Figshare original length or provider MD5 mismatch")
    if expected_sha256 is not None and sha.hexdigest() != expected_sha256:
        raise GDWFileGDBError("separately pinned source SHA256 mismatch")
    return {"original_bytes": total, "original_sha256": sha.hexdigest(),
            "provider_declared_md5_matched": True,
            "separately_pinned_sha256_compared": expected_sha256 is not None}


def safe_members(z: zipfile.ZipFile) -> tuple[list[zipfile.ZipInfo], str]:
    members = z.infolist()
    if not 1 <= len(members) <= MAX_MEMBERS:
        raise GDWFileGDBError("unexpected GDB ZIP member count")
    roots, seen, total = set(), set(), 0
    for info in members:
        name = info.filename
        if (not name or not name.isascii() or len(name) > 260
                or not re.fullmatch(r"[A-Za-z0-9_. /-]+", name)
                or name.startswith("/") or "\\" in name or "//" in name):
            raise GDWFileGDBError("unsafe provider ZIP path")
        parts = PurePosixPath(name.rstrip("/")).parts
        if not parts or any(part in ("", ".", "..") for part in name.rstrip("/").split("/")):
            raise GDWFileGDBError("traversal or ambiguous ZIP path")
        lower = name.casefold()
        if lower in seen:
            raise GDWFileGDBError("duplicate ZIP member name")
        seen.add(lower)
        mode = (info.external_attr >> 16) & 0o170000
        if mode not in (0, stat.S_IFDIR if info.is_dir() else stat.S_IFREG):
            raise GDWFileGDBError("symlink/device in provider ZIP")
        if (info.flag_bits & 1 or info.compress_type not in
                (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
            raise GDWFileGDBError("unsupported compression/encrypted ZIP")
        if info.file_size < 0 or info.file_size > MAX_SINGLE_MEMBER:
            raise GDWFileGDBError("oversized ZIP member")
        total += info.file_size
        if total > MAX_UNPACKED_BYTES:
            raise GDWFileGDBError("unpacked ZIP exceeds fixed budget")
        for idx, part in enumerate(parts):
            if part.lower().endswith(".gdb"):
                roots.add("/".join(parts[:idx + 1]))
    if len(roots) != 1:
        raise GDWFileGDBError("need exactly one original .gdb folder")
    gdb = next(iter(roots))
    if not any(i.filename.lower().startswith(gdb.lower() + "/")
               and not i.is_dir() for i in members):
        raise GDWFileGDBError("GDB directory has no source files")
    # Real source archives may contain their final technical PDF; never
    # require every ZIP member to be inside the .gdb root.
    return members, gdb


def extract_members(z: zipfile.ZipFile, members: list[zipfile.ZipInfo],
                    dest: Path) -> None:
    """Bounded streaming extraction in an independent already-private temp dir."""
    for info in members:
        path = dest.joinpath(*PurePosixPath(info.filename).parts)
        if info.is_dir():
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
            continue
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with z.open(info) as source, path.open("xb") as target:
            remaining = info.file_size
            while remaining:
                chunk = source.read(min(BUFFER, remaining))
                if not chunk:
                    raise GDWFileGDBError("unexpected truncated GDB ZIP member")
                remaining -= len(chunk)
                target.write(chunk)
            # A trailing read forces Python's CRC check; explicit read verifies EOF.
            if source.read(1):
                raise GDWFileGDBError("unexpected ZIP member trailing bytes")


def layer_role(name: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]", "", name.casefold())
    for role in _ALLOWED_GEOMETRY_ROLES:
        if normalized == re.sub(r"[^a-z0-9]", "", role.casefold()):
            return role
    return None


def inspect_original_gdb(gdb: Path) -> dict:
    try:
        import fiona
        from shapely.geometry import shape
        from shapely.validation import explain_validity
        from shapely.errors import GEOSException
    except ImportError as exc:
        raise GDWFileGDBError("pinned Fiona/Shapely GIS reader unavailable") from exc
    logging.getLogger("fiona").setLevel(logging.CRITICAL)
    if "OpenFileGDB" not in fiona.supported_drivers:
        raise GDWFileGDBError("reviewed OpenFileGDB driver unavailable")
    try:
        names = fiona.listlayers(str(gdb))
    except Exception as exc:
        raise GDWFileGDBError("cannot list original FileGDB layers") from exc
    roles = {layer_role(name): name for name in names if layer_role(name)}
    if len(roles) != 2 or len(set(roles.values())) != 2:
        raise GDWFileGDBError("original GDB required layer names missing/ambiguous")
    actual_names = [layer_role(n) for n in names if layer_role(n)]
    if actual_names.count("GDW_barriers_v1_0") != 1 or actual_names.count("GDW_reservoirs_v1_0") != 1:
        raise GDWFileGDBError("duplicate original GDB feature layers")
    points: dict[int, object] = {}
    totals, reasons = Counter(), Counter()
    inside = boundary = outside = invalid = unreadable = 0
    for role in ("GDW_barriers_v1_0", "GDW_reservoirs_v1_0"):
        try:
            with fiona.open(str(gdb), layer=roles[role], driver="OpenFileGDB") as layer:
                field_names = [str(n) for n in layer.schema["properties"]]
                matching = [n for n in field_names if n.casefold() == "gdw_id"]
                if len(matching) != 1:
                    raise GDWFileGDBError("missing/ambiguous GDW_ID in original FileGDB")
                identity = matching[0]
                declared_crs = layer.crs.to_epsg() if hasattr(layer.crs, "to_epsg") else None
                if declared_crs != 4326:
                    raise GDWFileGDBError("source FileGDB CRS is not EPSG 4326")
                for feature in layer:
                    ident = _check_id(feature["properties"], identity) if False else _gdw_id(feature["properties"][identity])
                    if role == "GDW_barriers_v1_0":
                        if ident in points:
                            raise GDWFileGDBError("duplicate barrier GDW_ID")
                        try:
                            g = shape(feature["geometry"])
                            if g.geom_type != "Point" or g.is_empty:
                                raise ValueError("not a point")
                            lon, lat = g.x, g.y
                            if (not math.isfinite(lon) or not math.isfinite(lat)
                                    or not -180 <= lon <= 180 or not -90 <= lat <= 90):
                                raise ValueError("out-of-bounds WGS84 point")
                        except (ValueError, TypeError, GEOSException) as exc:
                            raise GDWFileGDBError("invalid barrier geometry") from exc
                        points[ident] = g
                    else:
                        if ident not in points:
                            raise GDWFileGDBError("GDB reservoir GDW_ID missing from barriers")
                        if ident in totals:
                            raise GDWFileGDBError("duplicate GDB reservoir GDW_ID")
                        totals[ident] = 1  # keys discarded before producing aggregate result
                        try:
                            geom = shape(feature["geometry"])
                            if geom.geom_type not in ("Polygon", "MultiPolygon"):
                                raise ValueError("not a polygon")
                            if geom.is_empty:
                                invalid += 1
                                reasons["empty_polygon"] += 1
                            elif not geom.is_valid:
                                invalid += 1
                                reasons[_validity_reason_family(explain_validity(geom))] += 1
                            elif geom.area <= 0:
                                invalid += 1
                                reasons["nonpositive_polygon_area"] += 1
                            elif geom.contains(points[ident]):
                                inside += 1
                            elif geom.covers(points[ident]):
                                boundary += 1
                            else:
                                outside += 1
                        except (ValueError, TypeError, GEOSException):
                            unreadable += 1
                            reasons["conversion_error"] += 1
        except GDWFileGDBError:
            raise
        except Exception as exc:
            raise GDWFileGDBError("original GDB feature reader failed") from exc
    point_count, polygon_count = len(points), len(totals)
    if (point_count != EXPECTED_POINTS or polygon_count != EXPECTED_POLYGONS
            or point_count - polygon_count != EXPECTED_POINT_ONLY
            or inside + boundary + outside + invalid + unreadable != polygon_count
            or sum(reasons.values()) != invalid + unreadable):
        raise GDWFileGDBError("GDB source counts or paired GDW_ID relations drift")
    return {
        "barrier_points": point_count,
        "reservoir_polygons": polygon_count,
        "point_only_barriers": point_count - polygon_count,
        "geos_valid_polygons": inside + boundary + outside,
        "geos_invalid_polygons": invalid,
        "polygon_reader_errors": unreadable,
        "geos_invalid_reason_families": dict(sorted(reasons.items())),
        "paired_point_inside": inside,
        "paired_point_boundary": boundary,
        "paired_point_outside_valid_polygon": outside,
        "unassessable_invalid_or_error_pairs": invalid + unreadable,
        "original_feature_ids_or_coordinates_exported": False,
        "polygons_repaired": False,
        "model_input_admitted": False,
    }


def _gdw_id(value: object) -> int:
    if type(value) is int:
        ident = value
    elif type(value) is float and math.isfinite(value) and value.is_integer():
        ident = int(value)
    else:
        raise GDWFileGDBError("unexpected non-integer FileGDB GDW_ID")
    if not 1 <= ident < 2**63:
        raise GDWFileGDBError("out-of-range FileGDB GDW_ID")
    return ident


def audit(path: Path, *, expected_size=PROVIDER_BYTES,
          expected_md5=PROVIDER_MD5, expected_sha256=None) -> dict:
    source = original_file_identity(path, expected_size=expected_size,
                                    expected_md5=expected_md5,
                                    expected_sha256=expected_sha256)
    try:
        with zipfile.ZipFile(path) as z:
            members, root = safe_members(z)
            with tempfile.TemporaryDirectory(prefix="gdw-v1-gdb-original-") as folder:
                temp = Path(folder)
                extract_members(z, members, temp)
                quality = inspect_original_gdb(temp.joinpath(*PurePosixPath(root).parts))
    except (OSError, zipfile.BadZipFile, EOFError, RuntimeError) as exc:
        raise GDWFileGDBError("unable to read source GDB ZIP safely") from exc
    return {
        "schema_version": PROFILE,
        "source_id": "globaldamwatch.gdw.v1.0",
        "source_archive": "GDW_v1_0_gdb.zip",
        "figshare_original_file_id": GDW_FILE_ID,
        "original_archive_member_count": len(members),
        **source, **quality,
        "alternate_shapefile_source_sha256": SHAPEFILE["independently_computed_from_original_sha256"],
        "alternate_shapefile_geos_invalid_polygons": 221,
        "cross_format_per_id_geometry_comparison_performed": False,
        "alternate_filegdb_original_bytes_published": False,
    }


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--original-zip", required=True, type=Path)
    args = cli.parse_args(argv)
    try:
        print(json.dumps(audit(args.original_zip), sort_keys=True, indent=2,
                         allow_nan=False))
    except (GDWFileGDBError, ValueError, OSError, zipfile.BadZipFile) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
