#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, source-byte-pinned structure audit of HANZE 2024 Polygon shapefile.

Checks the actual SHP polygon records against SHX offsets, the source ZIP and
the published .prj text; returns *aggregate-only* evidence, never coordinate
arrays, original feature IDs, region labels or polygon bytes.

This is NOT a polygon topology/OGC validity audit, flood inundation mapping,
hydrological validation, asset allocation or commercial geography admission.
"""
from __future__ import annotations

from collections import Counter
import io
import math
import re
import struct
import zipfile

if __package__:
    from .hanze_regions2024_geometry_zip_audit_v0 import (
        inspect_hanze_region_geometry_zip, RegionArchiveError,
    )
else:
    from hanze_regions2024_geometry_zip_audit_v0 import (
        inspect_hanze_region_geometry_zip, RegionArchiveError,
    )

MAX_TOTAL_POINTS = 2_500_000
MAX_RECORD_POINTS = 400_000
MAX_RECORD_PARTS = 20_000
MAX_PRJ_BYTES = 65_536
SHAPE_POLYGON = 5


def _wkt_metadata(value: bytes) -> dict:
    if not 0 < len(value) <= MAX_PRJ_BYTES:
        raise RegionArchiveError("original projection text is empty or oversized")
    try:
        text = value.decode("utf-8-sig").strip()
    except UnicodeError as exc:
        raise RegionArchiveError("PRJ projection is not UTF-8/ASCII text") from exc
    if "\x00" in text or not re.match(r"^(?:GEOGCS|PROJCS|GEOCCS|GEOGCRS|PROJCRS)\s*[\[(]", text, re.I):
        raise RegionArchiveError("unexpected original WKT projection syntax")
    # Structural evidence only: WKT authority and units are not a guarantee
    # that coordinates are correctly georeferenced on earth.
    epsg = re.findall(r'(?:AUTHORITY|ID)\s*[\[(]\s*"EPSG"\s*,\s*"?([0-9]{3,6})"?\s*[\])]', text, re.I)
    units = re.findall(r'(?:UNIT|LENGTHUNIT|ANGLEUNIT)\s*[\[(]\s*"([^"]{1,80})"', text, re.I)
    if not units:
        raise RegionArchiveError("PRJ WKT has no explicit coordinate units")
    return {
        "prj_source_bytes": len(value),
        "wkt_header_family": re.match(r"[A-Za-z]+", text).group(0).upper(),
        "wkt_authority_epsg_codes_reported": sorted(set(epsg)),
        "wkt_contains_unit_declaration": bool(units),
        "prj_wkt_parsed_by_authoritative_crs_library": False,
        "coordinate_units_physical_interpretation_verified": False,
    }


def inspect_polygon_records(archive_bytes: bytes, *, expected_sha256: str) -> dict:
    """Parse full source SHP and SHX in memory, fail on structural tampering."""
    prior = inspect_hanze_region_geometry_zip(archive_bytes, expected_sha256=expected_sha256)
    data = prior["shapefile_component_groups"]
    if len(data) != 1 or data[0]["shape_type_code"] != SHAPE_POLYGON:
        raise RegionArchiveError("expected one source Polygon (type 5) shapefile")
    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as zf:
        files = {name.rsplit(".", 1)[-1].lower(): name for name in zf.namelist()}
        if not {"shp", "shx", "prj", "dbf"} <= files.keys():
            raise RegionArchiveError("missing original polygon source files")
        shp = zf.read(files["shp"])
        shx = zf.read(files["shx"])
        projection = _wkt_metadata(zf.read(files["prj"]))
    if len(shx) != 100 + data[0]["shape_index_record_count"] * 8:
        raise RegionArchiveError("SHX record count changes from pinned source ZIP")
    if len(shp) < 100 or len(shp) > 100_000_000:
        raise RegionArchiveError("original polygon SHP size exceeds bounded reader")
    n = data[0]["shape_index_record_count"]
    pos = 100
    stats = Counter()
    for i in range(n):
        idx_offset, idx_words = struct.unpack_from(">II", shx, 100 + 8 * i)
        if idx_offset * 2 != pos or idx_words == 0 or idx_words > MAX_RECORD_POINTS * 12:
            raise RegionArchiveError("original SHX record offset/length inconsistent")
        if pos + 8 > len(shp):
            raise RegionArchiveError("truncated original polygon record header")
        rec_number, rec_words = struct.unpack_from(">II", shp, pos)
        if rec_number != i+1 or rec_words != idx_words:
            raise RegionArchiveError("SHP record numbering/length does not match SHX")
        start = pos + 8
        end = start + rec_words * 2
        if end > len(shp) or end < start + 4:
            raise RegionArchiveError("polygon record size exceeds original SHP")
        kind = struct.unpack_from("<I", shp, start)[0]
        stats["feature_records"] += 1
        if kind == 0:
            if end - start != 4:
                raise RegionArchiveError("malformed null-shape record")
            stats["null_shape_records"] += 1
            pos = end
            continue
        if kind != SHAPE_POLYGON or end-start < 44:
            raise RegionArchiveError("not a canonical Polygon (type 5) record")
        xmin,ymin,xmax,ymax,nparts,npoints = struct.unpack_from("<4dII", shp, start+4)
        if (not all(math.isfinite(v) for v in (xmin,ymin,xmax,ymax))
            or xmin > xmax or ymin > ymax
            or not 1 <= nparts <= MAX_RECORD_PARTS
            or not 4 <= npoints <= MAX_RECORD_POINTS
            or end-start != 44 + 4*nparts + 16*npoints):
            raise RegionArchiveError("polygon record bounds, parts or point structure invalid")
        if sum((stats["polygon_vertices"],npoints)) > MAX_TOTAL_POINTS:
            raise RegionArchiveError("total polygon vertex count exceeds bounded parser")
        parts = struct.unpack_from("<"+"I"*nparts, shp, start+44)
        if parts[0] != 0 or any(parts[j] >= parts[j+1] for j in range(len(parts)-1)):
            raise RegionArchiveError("nonascending polygon ring part indices")
        if parts[-1] >= npoints:
            raise RegionArchiveError("polygon part index exceeds point count")
        point_start = start+44+4*nparts
        violations = 0
        for point in range(npoints):
            x,y = struct.unpack_from("<dd",shp,point_start + 16*point)
            if not math.isfinite(x) or not math.isfinite(y):
                raise RegionArchiveError("nonfinite polygon vertex coordinate")
            tolx = 1e-8 * max(1.0,abs(xmin),abs(xmax),abs(x))
            toly = 1e-8 * max(1.0,abs(ymin),abs(ymax),abs(y))
            if x < xmin-tolx or x > xmax+tolx or y < ymin-toly or y > ymax+toly:
                violations += 1
        if violations:
            raise RegionArchiveError("polygon vertex outside declared record bounding box")
        for part_i, first in enumerate(parts):
            last_exclusive = parts[part_i+1] if part_i+1 < nparts else npoints
            if last_exclusive-first < 4:
                raise RegionArchiveError("polygon ring has fewer than four points")
            first_xy = struct.unpack_from("<dd",shp,point_start + first*16)
            last_xy = struct.unpack_from("<dd",shp,point_start + (last_exclusive-1)*16)
            if first_xy == last_xy:
                stats["closed_rings"] += 1
            else:
                stats["open_rings"] += 1
        stats["polygon_feature_records"] += 1
        stats["polygon_rings"] += nparts
        stats["polygon_vertices"] += npoints
        pos = end
    if pos != len(shp):
        raise RegionArchiveError("unconsumed original polygon records")
    if stats["feature_records"] != data[0]["dbf"]["declared_record_count"]:
        raise RegionArchiveError("polygon feature count differs from attributes")
    return {
        "evidence_stage": "HANZE_ORIGINAL_SHAPEFILE_RECORD_STRUCTURE_ONLY",
        "original_zip_sha256_verified": expected_sha256 == prior["observed_sha256"],
        "projection_declaration": projection,
        "shp_shx_record_count_exactly_reconciled": True,
        "polygon_records": stats["polygon_feature_records"],
        "null_shape_records": stats["null_shape_records"],
        "polygon_rings": stats["polygon_rings"],
        "polygon_vertices": stats["polygon_vertices"],
        "exactly_closed_ring_count": stats["closed_rings"],
        "open_ring_count": stats["open_rings"],
        "all_declared_bounds_contain_finite_vertices": True,
        "all_polygon_part_offsets_structurally_valid": True,
        "original_polygon_coordinates_or_wkt_exported": False,
        "polygon_topology_or_self_intersections_verified": False,
        "historical_hazard_footprint_observed": False,
        "underlying_geometry_rights_reviewed_for_commercial_use": False,
        "model_source_admitted": False,
    }
