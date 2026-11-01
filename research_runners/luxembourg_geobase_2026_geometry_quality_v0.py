# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Full original ACT 2026 GeoBase building-geometry quality research audit.

Read-only source with independently frozen original ZIP/GPKG hashes.
All feature geometries are inspected ONLY in temporary local storage.
Only country-wide aggregate counts and area distributions are printed.
Neither observed building geometry nor addresses/IDs nor insurance values
are saved in Git/Neon; no CAT-model admission is implied.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import struct
import tempfile
import zipfile

from shapely import wkb
from shapely.errors import GEOSException
from shapely.validation import explain_validity

from research_runners.luxembourg_geobase_2026_id_quality_v0 import (
    audit as id_audit, EXPECTED_ZIP_SHA256, EXPECTED_GPKG_SHA256,
    EXPECTED_FEATURE_COUNT, EXPECTED_LAYER, MAX_GPKG_BYTES,
)
from research_runners.luxembourg_geobase_buildings_20261001_v0 import (
    GeoBaseError, _safe,
)

MAX_GEOMETRY_BYTES = 2 * 1024 * 1024
MAX_FEATURE_ROWS = 250000
ENVELOPE_DOUBLES = {0: 0, 1: 4, 2: 6, 3: 6, 4: 8}
TOPOLOGY_LABELS = frozenset({
    "Ring Self-intersection", "Self-intersection", "Hole lies outside shell",
    "Nested shells", "Nested holes", "Disconnected interior",
    "Too few points in geometry component", "Invalid Coordinate",
    "Repeated Point",
})


def _topology_class(geometry) -> str:
    # GEOS may include original coordinates in brackets: NEVER leak them.
    explanation = explain_validity(geometry).split("[", 1)[0].strip()
    return explanation if explanation in TOPOLOGY_LABELS else "other_invalid_topology"



def _decode_gpkg(blob: object):
    """Decode GeoPackage 1.2 geometry without assuming axis orientation."""
    if not isinstance(blob, bytes):
        raise GeoBaseError("Geometry missing or is not a binary GeoPackage value")
    if len(blob) < 13 or len(blob) > MAX_GEOMETRY_BYTES or blob[:2] != b"GP" or blob[2] != 0:
        raise GeoBaseError("Invalid GeoPackage geometry header or size")
    flags = blob[3]
    if flags & 0xE0:
        raise GeoBaseError("Unsupported GeoPackage geometry flags")
    envelope = (flags >> 1) & 7
    if envelope not in ENVELOPE_DOUBLES:
        raise GeoBaseError("Unknown GeoPackage envelope encoding")
    prefix = "<" if flags & 1 else ">"
    if struct.unpack_from(prefix + "i", blob, 4)[0] != 2169:
        raise GeoBaseError("Geometry SRS differs from the exact EPSG:2169 source")
    offset = 8 + 8 * ENVELOPE_DOUBLES[envelope]
    if len(blob) < offset + 5:
        raise GeoBaseError("Truncated GeoPackage WKB")
    try:
        geom = wkb.loads(blob[offset:])
    except (GEOSException, ValueError, TypeError) as exc:
        raise GeoBaseError("Malformed GeoPackage WKB") from exc
    if geom.geom_type not in ("Polygon", "MultiPolygon"):
        raise GeoBaseError("Non-polygon GeoBase source object")
    return geom


def profile(connection: sqlite3.Connection, *, expected_rows: int = EXPECTED_FEATURE_COUNT) -> dict:
    """Read the full exact layer and publish *only aggregates*, never IDs/geometry."""
    if not (0 < expected_rows <= MAX_FEATURE_ROWS):
        raise GeoBaseError("Unbounded or invalid source-object count")
    tables = {r[0] for r in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if EXPECTED_LAYER not in tables:
        raise GeoBaseError("Unexpected source layer")
    fields = {r[1] for r in connection.execute(
        'PRAGMA table_info("Buildings_BU_Building")')}
    if not {"id", "geom", "BU_BuildingID", "Source"}.issubset(fields):
        raise GeoBaseError("Unexpected original layer columns")
    try:
        n = connection.execute('SELECT count(*) FROM "Buildings_BU_Building"').fetchone()[0]
    except sqlite3.DatabaseError as exc:
        raise GeoBaseError("Cannot read original source population") from exc
    if n != expected_rows:
        raise GeoBaseError("Original building population changed")

    measured = []
    invalid_topology = 0
    topology_classes: Counter[str] = Counter()
    empty = 0
    nonpositive_area = 0
    malformed = 0
    inspected = 0
    # no source IDs, source labels or geometries enter output or audit logs
    for (blob,) in connection.execute('SELECT geom FROM "Buildings_BU_Building" ORDER BY id'):
        inspected += 1
        try:
            polygon = _decode_gpkg(blob)
        except GeoBaseError:
            malformed += 1
            continue
        if polygon.is_empty:
            empty += 1
            continue
        if not polygon.is_valid:
            invalid_topology += 1
            topology_classes[_topology_class(polygon)] += 1
            continue
        area = polygon.area  # square metres in the declared projected source CRS
        if not math.isfinite(area) or area <= 0:
            nonpositive_area += 1
            continue
        measured.append(area)

    if inspected != n:
        raise GeoBaseError("Source population changed during read-only geometry scan")
    counted = len(measured) + invalid_topology + empty + nonpositive_area + malformed
    if counted != n:
        raise GeoBaseError("Geometry quality counts do not conserve source rows")
    measured.sort()
    med = round(measured[(len(measured) - 1) // 2], 2) if measured else None
    q95 = round(measured[math.ceil(len(measured) * 0.95) - 1], 2) if measured else None
    return {
        "original_objects": n,
        "polygon_valid_positive_area": len(measured),
        "invalid_topology": invalid_topology,
        "invalid_topology_classes_aggregate": dict(sorted(topology_classes.items())),
        "empty_geometry": empty,
        "nonpositive_or_nonfinite_area": nonpositive_area,
        "malformed_gpkg_geometry": malformed,
        "valid_polygon_median_projected_m2": med,
        "valid_polygon_p95_projected_m2": q95,
        "valid_polygon_area_sum_projected_m2": round(math.fsum(measured), 2),
        "source_rows_conserved": counted == n,
        "all_source_geometries_parseable": malformed == 0,
        "all_source_polygon_topologies_valid": invalid_topology == 0,
        "ground_control_axis_order_verified": False,
        "physical_building_identity_verified": False,
        "individual_building_records_exported": False,
        "building_geometry_model_input_approved": False,
        "insured_property_or_tiv_inferred": False,
    }


def audit(source_zip: Path) -> dict:
    """Require existing immutable receipt and inspect only a temporary verified GPKG."""
    path = Path(source_zip)
    # Existing full source gate verifies exact original SHA, catalogue MD5,
    # complete ZIP member integrity, GPKG schema, and source-ID totals.
    receipt = id_audit(path)
    if receipt["original_zip_sha256"] != EXPECTED_ZIP_SHA256 or receipt[
        "original_gpkg_sha256"
    ] != EXPECTED_GPKG_SHA256:
        raise GeoBaseError("Pinned original receipt mismatch")
    with tempfile.TemporaryDirectory(prefix="oc-geobase-geometry-") as temp:
        target = Path(temp) / "original.gpkg"
        with zipfile.ZipFile(path) as archive:
            members = [m for m in archive.infolist()
                       if m.filename.lower().endswith(".gpkg") and not m.is_dir()]
            if len(members) != 1:
                raise GeoBaseError("Original GeoPackage member count differs")
            member = members[0]
            _safe(member)
            if member.file_size > MAX_GPKG_BYTES:
                raise GeoBaseError("Oversize original GeoPackage")
            h = hashlib.sha256()
            count = 0
            with archive.open(member) as source, target.open("xb") as output:
                while block := source.read(1024 * 1024):
                    count += len(block)
                    if count > MAX_GPKG_BYTES or count > member.file_size:
                        raise GeoBaseError("Unbounded GeoPackage extraction")
                    h.update(block)
                    output.write(block)
            if count != member.file_size or h.hexdigest() != EXPECTED_GPKG_SHA256:
                raise GeoBaseError("Original GeoPackage content changed")
        db = sqlite3.connect(target.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            stats = profile(db)
        finally:
            db.close()
    return {
        "schema_version": "lu-act-geobase-20261001-full-original-geometry-quality-v0",
        "publisher_catalogue": "https://data.public.lu/en/datasets/bd-l-geobase/",
        "source_release": "2026-10-01",
        "original_zip_sha256": EXPECTED_ZIP_SHA256,
        "original_gpkg_sha256": EXPECTED_GPKG_SHA256,
        "source_layer": EXPECTED_LAYER,
        "source_epsg_declared_not_field_validated": 2169,
        "geometry_quality": stats,
        "original_feature_bytes_or_ids_persisted": False,
        "source_specific_commercial_and_scientific_admission_approved": False,
        "real_insurer_exposure_ingested": False,
        "warning": "Research-only original geometry validation, not one footprint per building, "
                   "an independently surveyed object, real insured risk or CAT model input.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(audit(args.source_zip), indent=2, sort_keys=True, allow_nan=False))
    except (OSError, sqlite3.DatabaseError, zipfile.BadZipFile, GeoBaseError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
