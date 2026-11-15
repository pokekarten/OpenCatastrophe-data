#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-byte-pinned, read-only Luxembourg ACT2023v2 vs GeoBase2026 ID probe.

Reports aggregate identifier *string equality*, not proven stable building
identities, independent building observations, model input, or temporal change.
No individual source IDs, geometry or crosswalk are exported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ACT_SHA = "9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf"
GEOBASE_SHA = "ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676"
ACT_LAYER = "ACT2023v2_Buildings3d_Footprints"
GEOBASE_LAYER = "Buildings_BU_Building"
ACT_COL = "buildingid"
GEOBASE_COL = "BU_BuildingID"
ACT_COUNT = 238189
GEOBASE_COUNT = 230353
MAX_BYTES = 500 * 1024 * 1024


class ActIdentityError(ValueError):
    """Unsafe, mutated or incomparable original source identifier population."""


def _digest(file: Path, expected: str) -> None:
    if (not file.is_file() or file.is_symlink() or not 0 < file.stat().st_size <= MAX_BYTES):
        raise ActIdentityError("missing, linked or oversized original GeoPackage")
    h = hashlib.sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != expected:
        raise ActIdentityError("original GeoPackage SHA-256 mismatch")


def _collect(db: sqlite3.Connection, *, table: str, name: str, rows: int) -> dict:
    names = {x[1] for x in db.execute(f'PRAGMA table_info("{table}")')}
    if name not in names:
        raise ActIdentityError("expected original identifier column is missing")
    metadata = db.execute(
        "SELECT c.srs_id, g.geometry_type_name "
        "FROM gpkg_contents c JOIN gpkg_geometry_columns g "
        "ON c.table_name=g.table_name WHERE c.table_name=?", (table,)
    ).fetchone()
    if not metadata or metadata[0] != 2169 or metadata[1].upper() != "MULTIPOLYGON":
        raise ActIdentityError("unexpected source declared geometry or EPSG")
    actual_rows = db.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
    if actual_rows != rows:
        raise ActIdentityError("source population has drifted")
    found = set()
    missing, duplicates, integer_type, text_type = 0, 0, 0, 0
    for (value,) in db.execute(f'SELECT "{name}" FROM "{table}"'):
        if value is None or (isinstance(value, str) and not value.strip()):
            missing += 1
            continue
        if isinstance(value, int):
            integer_type += 1
            key = str(value)
        elif isinstance(value, str):
            text_type += 1
            key = value
        else:
            raise ActIdentityError("unexpected original ID field type")
        if len(key) > 256 or key != key.strip() or any(ord(c) < 32 for c in key):
            raise ActIdentityError("noncanonical original ID values")
        if key in found:
            duplicates += 1
        found.add(key)
    if actual_rows != len(found) + duplicates + missing:
        raise ActIdentityError("identifier conservation failure")
    return {
        "_ids": found,
        "feature_rows": actual_rows,
        "distinct_nonblank_identifiers": len(found),
        "missing_or_blank_identifiers": missing,
        "duplicate_nonblank_rows": duplicates,
        "stored_integer_id_rows": integer_type,
        "stored_text_id_rows": text_type,
    }


def inspect(act: Path, geobase: Path, *,
            act_sha: str = ACT_SHA, geobase_sha: str = GEOBASE_SHA) -> dict:
    if act_sha != ACT_SHA or geobase_sha != GEOBASE_SHA:
        raise ActIdentityError("wrong independently previously observed version pin")
    _digest(act, ACT_SHA)
    _digest(geobase, GEOBASE_SHA)
    outputs = []
    try:
        for source, table, name, rows in (
            (act, ACT_LAYER, ACT_COL, ACT_COUNT),
            (geobase, GEOBASE_LAYER, GEOBASE_COL, GEOBASE_COUNT),
        ):
            with sqlite3.connect(source.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
                db.execute("PRAGMA query_only=ON")
                app = db.execute("PRAGMA application_id").fetchone()[0]
                if app not in (0x47504B47, 0x47503130, 0x47503131):
                    raise ActIdentityError("source is not a GeoPackage")
                outputs.append(_collect(db, table=table, name=name, rows=rows))
    except sqlite3.DatabaseError as exc:
        raise ActIdentityError("invalid source SQLite metadata") from exc

    left, right = outputs
    common = len(left["_ids"] & right["_ids"])
    only_left = len(left["_ids"]) - common
    only_right = len(right["_ids"]) - common
    if common + only_left != len(left["_ids"]) or common + only_right != len(right["_ids"]):
        raise ActIdentityError("inconsistent source population cross-tab")
    for obj in outputs:
        del obj["_ids"]
    return {
        "profile": "lu-act2023-geobase2026-exact-text-id-overlap-v0",
        "source_original_gpkg_sha256": {
            "act2023v2": ACT_SHA, "geobase20261001": GEOBASE_SHA,
        },
        "act2023v2": left, "geobase20261001": right,
        "exact_normalized_string_id_intersection": common,
        "act2023_only_distinct_ids": only_left,
        "geobase2026_only_distinct_ids": only_right,
        "id_namespace_equivalence_proven": False,
        "matched_records_are_same_physical_buildings_proven": False,
        "building_stock_change_inferred": False,
        "new_or_demolished_buildings_inferred": False,
        "independent_validation_proven": False,
        "per_building_ids_or_crosswalk_exported": False,
        "original_data_or_geometry_persisted": False,
        "model_input_admitted": False,
        "warning": (
            "Matching text is only a candidate common namespace, not geometry/"
            "vintage/physical identity. ACT roof extents and GeoBase polygons "
            "may differ; nonmatching IDs do not imply additions or demolitions."
        ),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--act-gpkg", type=Path, required=True)
    p.add_argument("--geobase-gpkg", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        report = inspect(a.act_gpkg, a.geobase_gpkg)
    except (ActIdentityError, OSError, sqlite3.DatabaseError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
