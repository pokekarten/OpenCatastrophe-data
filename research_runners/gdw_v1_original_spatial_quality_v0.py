# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, aggregated GDW v1 source geometry and GDW_ID spatial-relation audit.

Requires pyshp 2.3.1 and Shapely 2.1.2 in the isolated review runner.
Never downloads, exports original IDs/coordinates, repairs geometry, derives
inundation or approves CAT model input. Original full-archive SHA is pinned.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import zipfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_runners import gdw_v1_shapefile_archive_preflight_v0 as pre
from research_runners.gdw_v1_original_shapefile_evidence_v0 import (
    GDW_V1_ORIGINAL_SHAPEFILE_EVIDENCE_V0 as EVIDENCE,
)

PROFILE = "oc-gdw-v1-original-shapefile-spatial-quality-v0"
PINNED_SHA256 = EVIDENCE["independently_computed_from_original_sha256"]


class GDWSpatialError(ValueError):
    """Original source, feature record or geospatial reader mismatch."""


def _check_id(record, field_index: int) -> int:
    value = record[field_index]
    if type(value) is int:
        ident = value
    elif type(value) is float and math.isfinite(value) and value.is_integer():
        ident = int(value)
    else:
        raise GDWSpatialError("non-integer GDW_ID in original source reader")
    if not 0 < ident <= (2**63 - 1):
        raise GDWSpatialError("invalid GDW_ID range")
    return ident


def _open_reader(z: zipfile.ZipFile, members: dict, stem: str):
    try:
        import shapefile
    except ImportError as exc:
        raise GDWSpatialError("pinned pyshp review dependency unavailable") from exc
    parts = {}
    for ext in (".shp", ".shx", ".dbf"):
        info = pre._find(members, stem, ext)
        parts[ext[1:]] = io.BytesIO(z.read(info))
    # Numeric IDs are independent of locale; latin1 is lossless for non-ID
    # single-byte source attribute data. No source attribute strings are emitted.
    reader = shapefile.Reader(shp=parts["shp"], shx=parts["shx"], dbf=parts["dbf"],
                              encoding="latin1")
    fields = [f[0].upper() for f in reader.fields[1:]]
    if fields.count("GDW_ID") != 1:
        reader.close()
        raise GDWSpatialError("GDW_ID column missing or ambiguous")
    return reader, fields.index("GDW_ID")


def audit(path: Path, *, expected_sha256: str = PINNED_SHA256,
          original_bytes: int = pre.PROVIDER_BYTES,
          publisher_md5: str = pre.PROVIDER_MD5,
          expected_counts: dict | None = None) -> dict:
    """Read one local original archive; non-default bounds only for synthetic tests."""
    try:
        from shapely.geometry import Point, shape
        import shapely
    except ImportError as exc:
        raise GDWSpatialError("pinned Shapely/GEOS review dependency unavailable") from exc
    if expected_counts is None:
        expected_counts = pre.EXPECTED_COUNTS
    receipt = pre.inspect(path, expected_sha256=expected_sha256,
                          original_size=original_bytes, publisher_md5=publisher_md5,
                          counts=expected_counts)
    points: dict[int, object] = {}
    count, invalid, conversion_error = 0, 0, 0
    inside, boundary, outside = 0, 0, 0
    with zipfile.ZipFile(path) as z:
        members = pre._members(z)
        bars, bars_index = _open_reader(z, members, "GDW_barriers_v1_0")
        try:
            for row in bars.iterShapeRecords():
                ident = _check_id(row.record, bars_index)
                if ident in points or len(row.shape.points) != 1:
                    raise GDWSpatialError("duplicate ID or non-point barrier feature")
                lon, lat = row.shape.points[0]
                if not (-180 <= lon <= 180 and -90 <= lat <= 90
                        and math.isfinite(lon) and math.isfinite(lat)):
                    raise GDWSpatialError("out-of-domain barrier coordinate")
                points[ident] = Point(lon, lat)
        finally:
            bars.close()
        if len(points) != expected_counts["GDW_barriers_v1_0"][1]:
            raise GDWSpatialError("original point reader count drift")
        regions, regions_index = _open_reader(z, members, "GDW_reservoirs_v1_0")
        paired = set()
        try:
            for row in regions.iterShapeRecords():
                ident = _check_id(row.record, regions_index)
                if ident not in points or ident in paired:
                    raise GDWSpatialError("GDW_ID pairing mismatch in spatial reader")
                paired.add(ident)
                count += 1
                try:
                    geom = shape(row.shape.__geo_interface__)
                    if geom.geom_type not in ("Polygon", "MultiPolygon"):
                        raise ValueError("unsupported reservoir geometry type")
                    if geom.is_empty or geom.area <= 0 or not geom.is_valid:
                        invalid += 1
                        continue
                    point = points[ident]
                    if geom.contains(point):
                        inside += 1
                    elif geom.covers(point):
                        boundary += 1
                    else:
                        outside += 1
                except (ValueError, TypeError, OverflowError, shapely.errors.GEOSException):
                    conversion_error += 1
        finally:
            regions.close()
    if count != expected_counts["GDW_reservoirs_v1_0"][1]:
        raise GDWSpatialError("original polygon reader count drift")
    if inside + boundary + outside + invalid + conversion_error != count:
        raise GDWSpatialError("original spatial disposition count mismatch")
    if len(points) - len(paired) != receipt["dbf_point_only_id_count"]:
        raise GDWSpatialError("original spatial point-only count drift")
    return {
        "schema_version": PROFILE,
        "source_id": "globaldamwatch.gdw.v1.0",
        "original_archive_sha256": receipt["original_sha256"],
        "original_archive_bytes": receipt["original_bytes"],
        "original_archive_sha256_matched_frozen": receipt["caller_supplied_sha256_matches"],
        "source_original_structure_verified": True,
        "geometry_engine": "Shapely/GEOS",
        "spatial_reader": "pyshp",
        "barrier_points": len(points),
        "reservoir_polygons": count,
        "paired_gdw_ids": len(paired),
        "expected_point_only_barriers": len(points) - len(paired),
        "valid_reservoir_polygons": inside + boundary + outside,
        "invalid_reservoir_polygons": invalid,
        "unparseable_or_error_reservoir_polygons": conversion_error,
        "paired_barrier_within_polygon_interior": inside,
        "paired_barrier_on_polygon_boundary": boundary,
        "paired_barrier_outside_valid_polygon": outside,
        "unassessable_pair_invalid_or_unparseable_polygon": invalid + conversion_error,
        "all_original_geometries_topologically_valid": invalid + conversion_error == 0,
        "all_assessable_id_pairs_geometrically_covered": outside == 0,
        "source_coordinates_ids_attributes_exported": False,
        "polygon_repairs_or_snapping_performed": False,
        "hydraulic_inundation_or_dam_failure_risk_proven": False,
        "CAT_model_source_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(audit(args.original_zip), indent=2, sort_keys=True, allow_nan=False))
    except (GDWSpatialError, pre.GDWArchiveError, OSError, zipfile.BadZipFile,
            ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
