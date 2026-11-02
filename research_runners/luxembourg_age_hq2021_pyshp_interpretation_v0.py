# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent PyShp 2.3.1 multipart interpretation of original AGE flood SHPs.

Does not assume GEOS isolated-ring orientation counts describe a complete
floodplain. Checks how another published, pinned Shapefile reader groups
source polygon exteriors and holes under its own GeoJSON conversion rules.

All source SHA-1, SHA-256 and ZIP CRCs validated before access. The converter
may assign an ambiguous or invalid ring incorrectly; its interpretation is
*not* a hydraulic mask. No original geometry, ring, source ID or point saved.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import zipfile

from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    HQ100OriginalError, inspect, _safe_member,
)
from research_runners.luxembourg_age_hq100_2021_ring_coordinate_quality_v0 import (
    EXPECTED_SHA256 as HQ100_SHA,
)
from research_runners.luxembourg_age_hq2021_sibling_source_receipts_v0 import (
    audit as sibling_receipt,
)
from research_runners.luxembourg_age_hq2021_sibling_full_geometry_quality_v0 import (
    EXPECTED_SHA256 as SIBLING_SHA,
)

MAX_SHP_BYTES = 32 * 1024 * 1024
MAX_SIDECAR_BYTES = 2 * 1024 * 1024
MAX_RECORD_POINTS = 2_000_000
MAX_RINGS = 20_000


class OriginalInterpreterError(ValueError):
    """Do not expose raw source geometry in invalid reader exceptions."""


def _one_member(z: zipfile.ZipFile, suffix: str, max_bytes: int) -> bytes:
    members = [m for m in z.infolist() if not m.is_dir()
               and m.filename.lower().endswith(suffix)]
    if len(members) != 1:
        raise OriginalInterpreterError("Not exactly one source shapefile sidecar")
    member = members[0]
    _safe_member(member)
    if not 1 <= member.file_size <= max_bytes:
        raise OriginalInterpreterError("Source exceeds original Shapefile reader byte budget")
    with z.open(member) as stream:
        data = stream.read(max_bytes + 1)
    if len(data) != member.file_size:
        raise OriginalInterpreterError("Original Shapefile sidecar size changed")
    return data


def interpret_bytes(*, shp: bytes, shx: bytes, dbf: bytes,
                    expected_rings: int, expected_points: int) -> dict:
    if (not isinstance(expected_rings, int) or not 1 <= expected_rings <= MAX_RINGS
            or not isinstance(expected_points, int)
            or not 4 * expected_rings <= expected_points <= MAX_RECORD_POINTS):
        raise OriginalInterpreterError("Unbounded original ring/point population")
    if (not 100 <= len(shp) <= MAX_SHP_BYTES or not 100 <= len(shx) <= MAX_SIDECAR_BYTES
            or not 33 <= len(dbf) <= MAX_SIDECAR_BYTES):
        raise OriginalInterpreterError("Unbounded original source file")
    import shapefile

    if shapefile.__version__ != "2.3.1":
        raise OriginalInterpreterError("Non-pinned shapefile parser version")
    old_verbose = shapefile.VERBOSE
    shapefile.VERBOSE = False
    try:
        # pyshp conversion may warn about malformed part winding, but printing
        # the warning could expose source content; suppress it, not failures.
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            reader = shapefile.Reader(shp=io.BytesIO(shp), shx=io.BytesIO(shx),
                                      dbf=io.BytesIO(dbf))
            if len(reader) != 1:
                raise OriginalInterpreterError("Expected exactly one original source record")
            record = reader.shape(0)
            if (record.shapeType != 5 or len(record.parts) != expected_rings
                    or len(record.points) != expected_points):
                raise OriginalInterpreterError("Independent source parser lost shape/ring points")
            geo = record.__geo_interface__
    except OriginalInterpreterError:
        raise
    except (Exception) as exc:
        # pyshp errors may contain source coordinates: never include their text.
        raise OriginalInterpreterError("Independent source Shapefile parser blocked") from None
    finally:
        shapefile.VERBOSE = old_verbose
    if not isinstance(geo, dict):
        raise OriginalInterpreterError("Non-GeoJSON converted source")
    if geo.get("type") == "Polygon":
        groups = [geo.get("coordinates")]
    elif geo.get("type") == "MultiPolygon":
        groups = geo.get("coordinates")
    else:
        raise OriginalInterpreterError("PyShp did not produce polygonal data")
    if not isinstance(groups, (list, tuple)) or not 1 <= len(groups) <= MAX_RINGS:
        raise OriginalInterpreterError("Nonconforming original polygon grouping")
    holes = 0
    assembled_rings = assembled_points = 0
    for poly in groups:
        if not isinstance(poly, (list, tuple)) or not 1 <= len(poly) <= MAX_RINGS:
            raise OriginalInterpreterError("Polygon group absent or too many rings")
        holes += len(poly) - 1
        for ring in poly:
            if not isinstance(ring, (list, tuple)) or len(ring) < 4:
                raise OriginalInterpreterError("Converted source ring incomplete")
            assembled_rings += 1
            assembled_points += len(ring)
    if assembled_rings != expected_rings or assembled_points != expected_points:
        raise OriginalInterpreterError("Independent polygon conversion changed original population")
    return {
        "parser": "pyshp",
        "pinned_pyshp_version": shapefile.__version__,
        "original_source_shape_type": 5,
        "original_source_record_count": 1,
        "original_source_ring_count_conserved": True,
        "original_source_coordinate_count_conserved": True,
        "pyshp_geo_interface_geometry_type": geo["type"],
        "pyshp_interpreted_polygon_group_count": len(groups),
        "pyshp_interpreted_hole_ring_count": holes,
        "pyshp_interpreted_exterior_ring_count": len(groups),
        "source_outline_hole_semantics_independently_verified": False,
        "pyshp_conversion_is_hydraulic_model_ground_truth": False,
        "full_source_ogc_geometry_validity_verified": False,
        "original_individual_ring_locations_or_coordinates_exported": False,
        "flood_building_spatial_join_authorized": False,
        "numeric_hazard_depth_verified": False,
        "CAT_model_input_admitted": False,
    }


def audit(original_zip: Path, scenario: str) -> dict:
    if scenario == "hq100":
        source = inspect(original_zip)
        expected_sha = HQ100_SHA
        shp = next(i for i in source["format_header_inventory_only"]
                   if i["format"] == ".shp")
        expected_rings = shp["shp_total_polygon_ring_parts"]
        expected_points = shp["shp_total_coordinate_pairs_skipped_without_decoding"]
        observed_sha = source["original_zip_sha256_observed"]
    elif scenario in SIBLING_SHA:
        source = sibling_receipt(original_zip, scenario=scenario)
        expected_sha = SIBLING_SHA[scenario]
        expected_rings = source["original_source_ring_parts"]
        expected_points = source["source_coordinates_skipped_without_reading"]
        observed_sha = source["observed_sha256"]
    else:
        raise OriginalInterpreterError("Unknown official AGE source scenario")
    if observed_sha != expected_sha:
        raise OriginalInterpreterError("Original source SHA256 changed since first source witness")
    with zipfile.ZipFile(original_zip) as z:
        readings = interpret_bytes(
            shp=_one_member(z, ".shp", MAX_SHP_BYTES),
            shx=_one_member(z, ".shx", MAX_SIDECAR_BYTES),
            dbf=_one_member(z, ".dbf", MAX_SIDECAR_BYTES),
            expected_rings=expected_rings,
            expected_points=expected_points,
        )
    return {
        "profile": "lu-age-hq2021-independent-pyshp-geometry-interpretation-v0",
        "scenario": scenario,
        "original_source_sha256_verified": expected_sha,
        **readings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("hq10", "hq100", "hqext"), required=True)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.source_zip, args.scenario), indent=2,
                         sort_keys=True, allow_nan=False))
    except (OriginalInterpreterError, HQ100OriginalError, ValueError,
            OSError, zipfile.BadZipFile):
        parser.exit(2, "BLOCKED: Original source reader rejected or could not interpret this archive\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
