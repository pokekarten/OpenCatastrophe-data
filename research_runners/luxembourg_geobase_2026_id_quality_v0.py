#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pinned original Luxembourg GeoBase 2026 building identifier quality diagnostics.

Offline read-only original ZIP/GPKG verification. No building rows, IDs,
addresses, polygon bytes, source-label values or insurance records are emitted.
No rights admission or database writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import sys
import zipfile

from research_runners.luxembourg_geobase_buildings_20261001_v0 import (
    GeoBaseError, inspect as original_inspect, _metadata, _safe,
)

EXPECTED_ZIP_SHA256 = "6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3"
EXPECTED_GPKG_SHA256 = "ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676"
EXPECTED_LAYER = "Buildings_BU_Building"
EXPECTED_FEATURE_COUNT = 230353
REQUIRED_COLUMNS = {"id", "geom", "BU_BuildingID", "Source"}
MAX_GPKG_BYTES = 150 * 1024 * 1024


def profile(connection: sqlite3.Connection, *, expected_rows: int = EXPECTED_FEATURE_COUNT) -> dict:
    """Return aggregate cardinality/coverage from *only* fixed known columns."""
    tables = {x[0] for x in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if EXPECTED_LAYER not in tables:
        raise GeoBaseError("Original GeoBase feature layer missing")
    columns = {x[1] for x in connection.execute(
        'PRAGMA table_info("Buildings_BU_Building")')}
    if not REQUIRED_COLUMNS.issubset(columns):
        raise GeoBaseError("Original GeoBase ID/source schema drifted")
    try:
        row = connection.execute(
            'SELECT count(*), count(DISTINCT id), '
            'sum(CASE WHEN geom IS NULL THEN 1 ELSE 0 END), '
            'sum(CASE WHEN BU_BuildingID IS NULL OR TRIM(CAST(BU_BuildingID AS TEXT))="" '
            'THEN 1 ELSE 0 END), '
            'count(DISTINCT NULLIF(TRIM(CAST(BU_BuildingID AS TEXT)),"")), '
            'sum(CASE WHEN Source IS NULL OR TRIM(CAST(Source AS TEXT))="" '
            'THEN 1 ELSE 0 END), '
            'count(DISTINCT NULLIF(TRIM(CAST(Source AS TEXT)),"")) '
            'FROM "Buildings_BU_Building"'
        ).fetchone()
    except sqlite3.DatabaseError as exc:
        raise GeoBaseError("Aggregate original SQL could not be executed") from exc
    if not row or row[0] != expected_rows:
        raise GeoBaseError("Original building feature count drifted")
    total, fid_unique, geometry_missing, id_missing, id_unique, source_missing, source_distinct = row
    if any(not isinstance(x, int) or x < 0 or x > total for x in (
        fid_unique, geometry_missing, id_missing, id_unique, source_missing
    )) or source_distinct is None or source_distinct < 0:
        raise GeoBaseError("Original aggregate values invalid")
    if id_unique > total - id_missing or source_distinct > total - source_missing:
        raise GeoBaseError("Original distinct key counts inconsistent")
    return {
        "source_object_rows": total,
        "sqlite_primary_id_unique": fid_unique,
        "geometry_null_rows": geometry_missing,
        "building_id_blank_rows": id_missing,
        "building_id_nonblank_rows": total - id_missing,
        "building_id_distinct_nonblank": id_unique,
        "building_id_duplicate_excess_rows": total - id_missing - id_unique,
        "source_label_blank_rows": source_missing,
        "source_label_nonblank_rows": total - source_missing,
        "source_label_distinct_nonblank": source_distinct,
    }


def audit(source_zip: Path) -> dict:
    """Inspect one immutable source ZIP pinned to earlier independent receipt."""
    path = Path(source_zip)
    if path.is_symlink() or not path.is_file():
        raise GeoBaseError("Input ZIP must be a regular local original")
    digest = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != EXPECTED_ZIP_SHA256:
        raise GeoBaseError("Previously observed original ZIP SHA-256 mismatch")

    # Existing source validator checks official MD5, all ZIP entries, their
    # safety and CRC, GPKG application ID, original layer metadata and EPSG.
    source_receipt = original_inspect(path)
    if len(source_receipt["original_gpkg_files"]) != 1:
        raise GeoBaseError("Expected one original GeoPackage")
    original_gp = source_receipt["original_gpkg_files"][0]
    if original_gp["gpkg_sha256"] != EXPECTED_GPKG_SHA256:
        raise GeoBaseError("Previously observed GeoPackage SHA-256 mismatch")
    actual_layers = original_gp["gpkg_layer_metadata"]
    if len(actual_layers) != 1 or actual_layers[0]["layer"] != EXPECTED_LAYER:
        raise GeoBaseError("Original Buildings-only theme schema drifted")
    if not REQUIRED_COLUMNS.issubset(set(actual_layers[0]["field_names_only"])):
        raise GeoBaseError("Source ID fields absent")
    if actual_layers[0]["feature_rows"] != EXPECTED_FEATURE_COUNT:
        raise GeoBaseError("Original building count changed")

    with tempfile.TemporaryDirectory(prefix="oc-geobase-quality-") as temp:
        destination = Path(temp) / "verified.gpkg"
        with zipfile.ZipFile(path) as archive:
            members = [m for m in archive.infolist() if m.filename.lower().endswith(".gpkg")
                       and not m.is_dir()]
            if len(members) != 1:
                raise GeoBaseError("Expected one source GeoPackage member")
            member = members[0]
            _safe(member)
            if member.file_size > MAX_GPKG_BYTES:
                raise GeoBaseError("Source GeoPackage exceeds extraction budget")
            verify = hashlib.sha256()
            written = 0
            with archive.open(member) as data, destination.open("xb") as out:
                while block := data.read(1024 * 1024):
                    written += len(block)
                    if written > MAX_GPKG_BYTES or written > member.file_size:
                        raise GeoBaseError("Source GeoPackage exceeded declared size")
                    verify.update(block)
                    out.write(block)
            if written != member.file_size or verify.hexdigest() != EXPECTED_GPKG_SHA256:
                raise GeoBaseError("Decompressed original GeoPackage identity mismatch")
        db = sqlite3.connect(destination.resolve().as_uri()+"?mode=ro&immutable=1", uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            # Compare native GPKG schema one last time before fixed SQL.
            second = _metadata(destination)
            if second["gpkg_layer_metadata"] != actual_layers:
                raise GeoBaseError("Original GeoPackage metadata changed")
            counts = profile(db)
        finally:
            db.close()
    return {
        "schema_version": "lu-geobase-buildings-20261001-id-source-quality-v0",
        "resource_id": source_receipt["resource_id"],
        "original_zip_sha256": EXPECTED_ZIP_SHA256,
        "original_gpkg_sha256": EXPECTED_GPKG_SHA256,
        "source_observation_date": "2026-10-01",
        "epsg_declared_unverified_axis_order": 2169,
        "counts": counts,
        "building_id_namespace_matches_act2023_verified": False,
        "construction_date_from_source_proven": False,
        "rights_and_scientific_admission_approved": False,
        "per_building_data_exported": False,
        "source_bytes_persisted_by_script": False,
        "model_input_admitted": False,
        "warning": "ID existence/uniqueness, not proof of stable cross-vintage identity, "
                   "historical building existence, geometry equivalence, independent data, "
                   "insured value or permitted commercial CAT source use.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(args.source_zip)
    except (OSError, sqlite3.DatabaseError, zipfile.BadZipFile, GeoBaseError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
