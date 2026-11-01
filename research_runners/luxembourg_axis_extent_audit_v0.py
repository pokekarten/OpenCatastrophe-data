#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only Luxembourg 2D GPKG aggregate bbox / coordinate-order challenge.

Only checks a SHA-pinned original ACT2023v2 ZIP, metadata and area-of-use
plausibility. The GeoPackage is temporary and original building rows are never
read, emitted or imported. This is NOT control-point coordinate-order proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import tempfile
import zipfile

from scripts.luxembourg_gpkg_zip_preflight_v0 import preflight, OriginalPreflightError

SOURCE_ZIP_SHA256 = "a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a"
SOURCE_GPKG_SHA256 = "9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf"
GPKG_APP_ID = 0x47504B47
# EPSG:2169 area-of-use bbox. Liberal 0.12° buffer is only a screening rule.
EPSG_LU_WGS84 = (5.73, 49.44, 6.53, 50.19)
BUFFER_DEG = 0.12


class AxisAuditError(ValueError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def geographic_screen(extent: tuple[float, float, float, float]) -> dict:
    """Compare *aggregate* projected envelope hypotheses; no building identities."""
    if (len(extent) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) for v in extent)):
        raise AxisAuditError("Nonfinite or absent aggregate extent")
    xmin, ymin, xmax, ymax = extent
    if not (xmin < xmax and ymin < ymax and all(0 <= v <= 500000 for v in extent)):
        raise AxisAuditError("Unexpected EPSG:2169 projected envelope")
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise AxisAuditError("Pinned optional PyProj spatial runtime required") from exc
    transformer = Transformer.from_crs(2169, 4326, always_xy=True)
    east_west = (EPSG_LU_WGS84[0] - BUFFER_DEG, EPSG_LU_WGS84[2] + BUFFER_DEG)
    south_north = (EPSG_LU_WGS84[1] - BUFFER_DEG, EPSG_LU_WGS84[3] + BUFFER_DEG)
    cases = {}
    for order in ("as_stored_xy", "swapped_xy"):
        coordinates = []
        for x in (xmin, xmax):
            for y in (ymin, ymax):
                lon, lat = transformer.transform(*(x, y) if order == "as_stored_xy" else (y, x))
                if not math.isfinite(lon) or not math.isfinite(lat):
                    raise AxisAuditError("Nonfinite reprojected coordinates")
                coordinates.append((lon, lat))
        lonmin = min(v[0] for v in coordinates)
        lonmax = max(v[0] for v in coordinates)
        latmin = min(v[1] for v in coordinates)
        latmax = max(v[1] for v in coordinates)
        # A bounding rectangle can include unoccupied land, so failure is a
        # diagnostic and must never trigger auto-coordinate swapping.
        plausible = (east_west[0] <= lonmin <= lonmax <= east_west[1] and
                     south_north[0] <= latmin <= latmax <= south_north[1])
        cases[order] = {
            "bbox_wgs84_rounded_4dp": [round(lonmin, 4), round(latmin, 4), round(lonmax, 4), round(latmax, 4)],
            "fits_buffered_epsg_area_of_use": plausible
        }
    a = cases["as_stored_xy"]["fits_buffered_epsg_area_of_use"]
    b = cases["swapped_xy"]["fits_buffered_epsg_area_of_use"]
    finding = ("native_only_plausible" if a and not b else
               "swapped_only_plausible" if b and not a else
               "ambiguous_both_plausible" if a and b else "neither_plausible")
    return {
        "screen_finding": finding, "hypotheses": cases,
        "coordinate_order_verified": False,
        "geometry_topology_verified": False,
        "building_match_authorised": False,
    }


def audit_gpkg(gpkg: Path, *, expected_gpkg_sha256: str) -> dict:
    if not gpkg.is_file() or gpkg.is_symlink() or _sha256(gpkg) != expected_gpkg_sha256:
        raise AxisAuditError("GeoPackage hash/file identity mismatch")
    db = sqlite3.connect(gpkg.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        if db.execute("PRAGMA application_id").fetchone()[0] != GPKG_APP_ID:
            raise AxisAuditError("Unexpected GeoPackage application ID")
        rows = db.execute(
            "SELECT c.min_x,c.min_y,c.max_x,c.max_y,c.srs_id,g.srs_id,g.geometry_type_name "
            "FROM gpkg_contents c JOIN gpkg_geometry_columns g ON c.table_name=g.table_name "
            "WHERE c.data_type='features'"
        ).fetchall()
        if len(rows) != 1:
            raise AxisAuditError("Expected exactly one original feature layer")
        xmin, ymin, xmax, ymax, srs_c, srs_g, geom = rows[0]
        if srs_c != 2169 or srs_g != 2169 or geom.upper() not in ("POLYGON", "MULTIPOLYGON"):
            raise AxisAuditError("Wrong source CRS or polygon type")
        result = geographic_screen((xmin, ymin, xmax, ymax))
        result.update({
            "profile": "luxembourg-act2023v2-aggregate-axis-screen-v0",
            "gpkg_sha256": expected_gpkg_sha256,
            "original_gpkg_extent_epsg2169_rounded_1m": [round(v) for v in (xmin, ymin, xmax, ymax)],
            "epsg_area_of_use_wgs84": list(EPSG_LU_WGS84),
            "non_admission_research_only": True,
            "raw_feature_rows_read": 0,
            "source_records_exported": False,
            "source_rights_and_science_approved": False,
        })
        return result
    except sqlite3.DatabaseError as exc:
        raise AxisAuditError("Invalid original GeoPackage metadata") from exc
    finally:
        db.close()


def audit_zip(original_zip: Path, *, zip_sha256: str = SOURCE_ZIP_SHA256,
              gpkg_sha256: str = SOURCE_GPKG_SHA256) -> dict:
    try:
        receipt = preflight(original_zip, expected_sha256=zip_sha256)
    except (OSError, OriginalPreflightError) as exc:
        raise AxisAuditError("Original source ZIP preflight failed") from exc
    if receipt["original_gpkg_sha256"] != gpkg_sha256:
        raise AxisAuditError("Original source GPKG SHA differs from independent receipt")
    with tempfile.TemporaryDirectory(prefix="oc-lu-axis-") as directory:
        local = Path(directory) / "original.gpkg"
        with zipfile.ZipFile(original_zip, "r") as archive:
            members = [i for i in archive.infolist() if i.filename.lower().endswith(".gpkg")]
            if len(members) != 1:
                raise AxisAuditError("Original member count changed")
            with archive.open(members[0]) as src, local.open("wb") as dest:
                for block in iter(lambda: src.read(1024 * 1024), b""):
                    dest.write(block)
        result = audit_gpkg(local, expected_gpkg_sha256=gpkg_sha256)
    result["zip_sha256"] = zip_sha256
    result["provider_resource_id"] = receipt["provider_resource_id"]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(audit_zip(args.source_zip), indent=2, sort_keys=True, allow_nan=False))
    except (AxisAuditError, OSError, zipfile.BadZipFile, ValueError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
