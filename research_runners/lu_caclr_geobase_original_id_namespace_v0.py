#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""ACT BD-Adresses CACLR IDs versus GeoBase building IDs: original-only evidence.

Strict exact-original SHA checks; read-only ephemeral identifiers; aggregate
literal-text overlap only. A shared text string is NOT verified building identity.
No addresses, source identifiers, geometry or crosswalk are emitted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import zipfile

from research_runners.lu_bd_adresses_original_csv_quality_v0 import (
    EXPECTED_SHA256 as ADDRESS_SHA,
    EXPECTED_SIZE as ADDRESS_BYTES,
    HEADER as ADDRESS_HEADER,
    verify_original_stream,
)
from research_runners.luxembourg_geobase_2026_id_quality_v0 import (
    EXPECTED_ZIP_SHA256 as GEOBASE_ZIP_SHA,
    EXPECTED_GPKG_SHA256 as GEOBASE_GPKG_SHA,
    EXPECTED_FEATURE_COUNT as GEOBASE_ROWS,
    EXPECTED_LAYER as GEOBASE_LAYER,
    MAX_GPKG_BYTES,
    audit as audit_geobase,
)
from research_runners.luxembourg_geobase_buildings_20261001_v0 import _safe

ADDRESS_ROWS = 179768
MAX_ADDRESS_ROWS = 250000
MAX_BUILDING_ROWS = 300000
MAX_ID_LEN = 256


class NamespaceEvidenceError(ValueError):
    """Original ID proof cannot be performed safely with this input."""


def _id_counters(values, *, budget: int, role: str) -> tuple[Counter[str], dict]:
    """Collect exact original text counts; never return values to output."""
    if not isinstance(budget, int) or budget < 1:
        raise NamespaceEvidenceError("invalid source row budget")
    counts: Counter[str] = Counter()
    rows = blank = space_padded = 0
    for value in values:
        rows += 1
        if rows > budget:
            raise NamespaceEvidenceError(f"{role}: identifier row budget exceeded")
        if value is None:
            blank += 1
            continue
        if isinstance(value, int) and type(value) is not bool:
            value = str(value)
        if not isinstance(value, str) or len(value) > MAX_ID_LEN:
            raise NamespaceEvidenceError(f"{role}: unexpected identifier type or size")
        if any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise NamespaceEvidenceError(f"{role}: control character in identifier")
        if not value.strip():
            blank += 1
            continue
        if value != value.strip():
            space_padded += 1
        counts[value] += 1
    return counts, {
        "rows": rows,
        "missing_or_blank": blank,
        "nonblank_rows": rows - blank,
        "distinct_nonblank": len(counts),
        "duplicate_excess_rows": sum(n - 1 for n in counts.values()),
        "max_rows_for_one_exact_id": max(counts.values(), default=0),
        "rows_with_surrounding_whitespace": space_padded,
    }


def aggregate_ids(
    caclr: list[str], geoportail: list[str], buildings: list[str],
) -> dict:
    """Small pure core used in synthetic tests, never exports any identifier."""
    if len(caclr) != len(geoportail):
        raise NamespaceEvidenceError("address source ID population mismatch")
    ac, asummary = _id_counters(caclr, budget=MAX_ADDRESS_ROWS, role="CACLR")
    pc, psummary = _id_counters(geoportail, budget=MAX_ADDRESS_ROWS, role="Geoportail")
    bc, bsummary = _id_counters(buildings, budget=MAX_BUILDING_ROWS, role="GeoBase")
    if not caclr or not buildings:
        raise NamespaceEvidenceError("original source ID population is empty")
    common_caclr = ac.keys() & bc.keys()
    common_geoportail = pc.keys() & bc.keys()
    return {
        "address_caclr_building_id": asummary,
        "address_geoportail_id": psummary,
        "geobase_building_id": bsummary,
        "exact_text_overlap": {
            "caclr_to_geobase_distinct_shared_strings": len(common_caclr),
            "caclr_address_rows_with_shared_string": sum(ac[k] for k in common_caclr),
            "geobase_rows_with_caclr_shared_string": sum(bc[k] for k in common_caclr),
            "geoportail_to_geobase_distinct_shared_strings": len(common_geoportail),
            "geoportail_address_rows_with_shared_string": sum(pc[k] for k in common_geoportail),
        },
        "id_namespace_equivalence_proven": False,
        "common_string_proves_same_physical_building": False,
        "independent_source_validation_proven": False,
        "raw_ids_or_join_pairs_exported": False,
        "insurer_asset_or_tiv_proven": False,
        "rights_review_approved": False,
        "scientific_model_input_admitted": False,
    }


def _original_address_ids(source: Path) -> tuple[list[str], list[str]]:
    caclr: list[str] = []
    geoportail: list[str] = []
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, delimiter=";", strict=True)
        if tuple(next(reader)) != ADDRESS_HEADER:
            raise NamespaceEvidenceError("pinned original address CSV schema drift")
        for row in reader:
            if len(row) != len(ADDRESS_HEADER):
                raise NamespaceEvidenceError("original address CSV width mismatch")
            caclr.append(row[5])
            geoportail.append(row[10])
            if len(caclr) > MAX_ADDRESS_ROWS:
                raise NamespaceEvidenceError("original address row budget exceeded")
    if len(caclr) != ADDRESS_ROWS:
        raise NamespaceEvidenceError("original national address population drift")
    return caclr, geoportail


def _original_geobase_ids(zip_file: Path, work: Path) -> list[str]:
    # The existing original validator first checks full ZIP SHA, publisher MD5,
    # ZIP safety/CRC, original GeoPackage digest, EPSG and source layer.
    receipt = audit_geobase(zip_file)
    if (receipt["original_zip_sha256"] != GEOBASE_ZIP_SHA
            or receipt["original_gpkg_sha256"] != GEOBASE_GPKG_SHA
            or receipt["counts"]["source_object_rows"] != GEOBASE_ROWS):
        raise NamespaceEvidenceError("original GeoBase source receipt drift")
    with zipfile.ZipFile(zip_file) as archive:
        members = [m for m in archive.infolist()
                   if m.filename.lower().endswith(".gpkg") and not m.is_dir()]
        if len(members) != 1:
            raise NamespaceEvidenceError("expected exactly one original GeoPackage")
        member = members[0]
        _safe(member)
        if not 0 < member.file_size <= MAX_GPKG_BYTES:
            raise NamespaceEvidenceError("original GeoPackage expanded size exceeds budget")
        target = work / "original.gpkg"
        h = hashlib.sha256()
        count = 0
        with archive.open(member) as original, target.open("xb") as output:
            while chunk := original.read(1024 * 1024):
                count += len(chunk)
                if count > member.file_size or count > MAX_GPKG_BYTES:
                    raise NamespaceEvidenceError("original GeoPackage size drift")
                h.update(chunk)
                output.write(chunk)
        if count != member.file_size or h.hexdigest() != GEOBASE_GPKG_SHA:
            raise NamespaceEvidenceError("original GeoPackage SHA-256 mismatch")
    with sqlite3.connect(target.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        if db.execute("PRAGMA application_id").fetchone()[0] not in (
            0x47504B47, 0x47503130, 0x47503131,
        ):
            raise NamespaceEvidenceError("original file not GeoPackage")
        meta = db.execute(
            "SELECT c.srs_id,g.geometry_type_name FROM gpkg_contents c "
            "JOIN gpkg_geometry_columns g ON c.table_name=g.table_name "
            "WHERE c.table_name=?", (GEOBASE_LAYER,)
        ).fetchone()
        if meta is None or meta[0] != 2169 or str(meta[1]).upper() != "MULTIPOLYGON":
            raise NamespaceEvidenceError("original building layer metadata drift")
        n = db.execute('SELECT COUNT(*) FROM "Buildings_BU_Building"').fetchone()[0]
        if n != GEOBASE_ROWS:
            raise NamespaceEvidenceError("original building population drift")
        values = [row[0] for row in db.execute(
            'SELECT "BU_BuildingID" FROM "Buildings_BU_Building"'
        )]
    if len(values) != GEOBASE_ROWS:
        raise NamespaceEvidenceError("original building identifier count drift")
    return values


def inspect(address_csv: Path, geobase_zip: Path) -> dict:
    if any(p.is_symlink() or not p.is_file() for p in (address_csv, geobase_zip)):
        raise NamespaceEvidenceError("original local files must be regular and not symlinks")
    if address_csv.stat().st_size != ADDRESS_BYTES:
        raise NamespaceEvidenceError("original address byte size drift")
    with address_csv.open("rb") as src:
        rec = verify_original_stream(src)
    if (rec["original_sha256_computed"] != ADDRESS_SHA
            or rec["row_count"] != ADDRESS_ROWS):
        raise NamespaceEvidenceError("original address hash/row receipt drift")
    addresses, geoportal = _original_address_ids(address_csv)
    with tempfile.TemporaryDirectory(prefix="lu-caclr-geobase-id-evidence-") as tmp:
        buildings = _original_geobase_ids(geobase_zip, Path(tmp))
        report = aggregate_ids(addresses, geoportal, buildings)
    if (report["address_caclr_building_id"]["rows"] != ADDRESS_ROWS
            or report["geobase_building_id"]["rows"] != GEOBASE_ROWS):
        raise NamespaceEvidenceError("source population conservation failed")
    return {
        "profile": "lu-caclr-to-geobase-original-id-string-overlap-v0",
        "address_original_sha256": ADDRESS_SHA,
        "geobase_original_zip_sha256": GEOBASE_ZIP_SHA,
        "geobase_original_gpkg_sha256": GEOBASE_GPKG_SHA,
        "source_releases": {"addresses": "2026-11-02", "buildings": "2026-10-01"},
        **report,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--address-csv", required=True, type=Path)
    p.add_argument("--geobase-zip", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        outcome = inspect(args.address_csv, args.geobase_zip)
    except (OSError, ValueError, csv.Error, sqlite3.DatabaseError,
            zipfile.BadZipFile, EOFError):
        print("BLOCKED: original CACLR/GeoBase identifier evidence is not admissible",
              file=sys.stderr)
        return 2
    print(json.dumps(outcome, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
