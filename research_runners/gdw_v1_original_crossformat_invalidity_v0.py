# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact original GDW v1 cross-format GDW_ID quality test, aggregate output only.

Both source ZIPs are independently pinned, externally acquired in an ephemeral
runner and never retained outside the process. Never emit any provider IDs,
point coordinates, GEOS original invalidity reason strings or geometry bytes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_runners import gdw_v1_original_filegdb_quality_v0 as gdb
from research_runners import gdw_v1_shapefile_archive_preflight_v0 as shp_zip
from research_runners import gdw_v1_original_spatial_quality_v0 as shp_geo
from research_runners.gdw_v1_original_filegdb_receipt_v0 import (
    GDW_V1_ORIGINAL_FILEGDB_RECEIPT_V0 as GDB_PIN,
)
from research_runners.gdw_v1_original_shapefile_evidence_v0 import (
    GDW_V1_ORIGINAL_SHAPEFILE_EVIDENCE_V0 as SHP_PIN,
)

PROFILE = "gdw-v1-original-gdb-shp-invalid-id-concordance-v0"


class GDWConcordanceError(ValueError):
    """Cross-format original ID or source topology invariants were violated."""


def _original_shp_sets(path: Path) -> tuple[set[int], set[int], set[int], str]:
    """Original ZIP checksum and all records verified before transient ID reading."""
    try:
        from shapely.geometry import shape
        import shapely
    except ImportError as exc:
        raise GDWConcordanceError("pinned Shapely not installed") from exc
    check = shp_zip.inspect(path,
                            expected_sha256=SHP_PIN["independently_computed_from_original_sha256"])
    barriers: set[int] = set()
    polygons: set[int] = set()
    invalid: set[int] = set()
    with zipfile.ZipFile(path) as z:
        members = shp_zip._members(z)
        reader, idx = shp_geo._open_reader(z, members, "GDW_barriers_v1_0")
        try:
            for row in reader.iterRecords():
                key = shp_geo._check_id(row, idx)
                if key in barriers:
                    raise GDWConcordanceError("duplicate SHP barrier GDW_ID")
                barriers.add(key)
        finally:
            reader.close()
        reader, idx = shp_geo._open_reader(z, members, "GDW_reservoirs_v1_0")
        try:
            for row in reader.iterShapeRecords():
                key = shp_geo._check_id(row.record, idx)
                if key in polygons:
                    raise GDWConcordanceError("duplicate SHP reservoir GDW_ID")
                polygons.add(key)
                try:
                    geom = shape(row.shape.__geo_interface__)
                    if (geom.geom_type not in ("Polygon", "MultiPolygon")
                            or geom.is_empty or not geom.is_valid or geom.area <= 0):
                        invalid.add(key)
                except (TypeError, ValueError, OverflowError,
                        shapely.errors.GEOSException):
                    invalid.add(key)
        finally:
            reader.close()
    if (len(barriers) != 41145 or len(polygons) != 35295
            or len(barriers - polygons) != 5850 or not polygons.issubset(barriers)
            or len(invalid) != 221 or check["dbf_point_only_id_count"] != 5850):
        raise GDWConcordanceError("frozen original shapefile ID/invalidity receipt drift")
    return barriers, polygons, invalid, check["original_sha256"]


def aggregate_concordance(shp_barriers: set[int], shp_polygons: set[int],
                          shp_invalid: set[int], gdb_barriers: set[int],
                          gdb_polygons: set[int], gdb_invalid: set[int]) -> dict:
    """Pure aggregate map: source ID sets never escape the return value."""
    for role, ids, invalid in (("SHP", shp_polygons, shp_invalid),
                               ("GDB", gdb_polygons, gdb_invalid)):
        if not invalid.issubset(ids):
            raise GDWConcordanceError(role + " invalid IDs not contained in native polygons")
    if not shp_polygons.issubset(shp_barriers) or not gdb_polygons.issubset(gdb_barriers):
        raise GDWConcordanceError("unpaired reservoir source ID")
    shared = shp_invalid & gdb_invalid
    gdb_only = gdb_invalid - shp_invalid
    shp_only = shp_invalid - gdb_invalid
    return {
        "shp_barrier_count": len(shp_barriers),
        "gdb_barrier_count": len(gdb_barriers),
        "barrier_id_in_both": len(shp_barriers & gdb_barriers),
        "barrier_id_only_in_shp": len(shp_barriers - gdb_barriers),
        "barrier_id_only_in_gdb": len(gdb_barriers - shp_barriers),
        "shp_polygon_count": len(shp_polygons),
        "gdb_polygon_count": len(gdb_polygons),
        "polygon_id_in_both": len(shp_polygons & gdb_polygons),
        "polygon_id_only_in_shp": len(shp_polygons - gdb_polygons),
        "polygon_id_only_in_gdb": len(gdb_polygons - shp_polygons),
        "shp_invalid_geos_count": len(shp_invalid),
        "gdb_invalid_geos_count": len(gdb_invalid),
        "same_invalid_gdw_id_in_both_formats": len(shared),
        "invalid_gdw_id_only_in_shp": len(shp_only),
        "invalid_gdw_id_only_in_gdb": len(gdb_only),
        "entire_barrier_id_universes_match": shp_barriers == gdb_barriers,
        "entire_polygon_id_universes_match": shp_polygons == gdb_polygons,
        "entire_invalid_gdw_id_sets_match": shp_invalid == gdb_invalid,
        "source_ids_coordinates_geometries_emitted": False,
        "source_geometries_repaired": False,
        "CAT_model_source_admitted": False,
    }


def audit(shp_path: Path, gdb_path: Path) -> dict:
    shp_b, shp_p, shp_bad, shp_sha = _original_shp_sets(shp_path)
    gdb_b: set[int] = set()
    gdb_p: set[int] = set()
    gdb_bad: set[int] = set()
    gdb_check = gdb.audit(
        gdb_path,
        expected_sha256=GDB_PIN["original_sha256_observed"],
        barrier_ids=gdb_b, polygon_ids=gdb_p, invalid_ids=gdb_bad,
    )
    if (gdb_check["geos_invalid_polygons"] != 221
            or gdb_check["geos_invalid_reason_families"] !=
            {"ring_self_intersection": 221}
            or not gdb_check["separately_pinned_sha256_compared"]):
        raise GDWConcordanceError("frozen original FileGDB GEOS quality drift")
    results = aggregate_concordance(shp_b, shp_p, shp_bad, gdb_b, gdb_p, gdb_bad)
    if (results["shp_invalid_geos_count"] != 221
            or results["gdb_invalid_geos_count"] != 221
            or results["shp_polygon_count"] != 35295
            or results["gdb_polygon_count"] != 35295):
        raise GDWConcordanceError("original crossformat source count drift")
    return {
        "schema_version": PROFILE,
        "source_id": "globaldamwatch.gdw.v1.0",
        "original_shp_zip_sha256_reproduced": shp_sha,
        "original_gdb_zip_sha256_reproduced": gdb_check["original_sha256"],
        "frozen_original_sha256_for_both_formats_matched": True,
        "cross_format_original_ids_compared_only_in_process": True,
        **results,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shp-zip", type=Path, required=True)
    p.add_argument("--gdb-zip", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        print(json.dumps(audit(args.shp_zip, args.gdb_zip),
                         sort_keys=True, indent=2, allow_nan=False))
    except (GDWConcordanceError, gdb.GDWFileGDBError, shp_zip.GDWArchiveError,
            shp_geo.GDWSpatialError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
