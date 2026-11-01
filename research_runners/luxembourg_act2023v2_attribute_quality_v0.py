#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-asset, aggregate-only ACT2023v2 GeoPackage attribute quality profile.

Reads an independently SHA-pinned, already-extracted official GeoPackage.
Does NOT export feature IDs/values/geometries, infer exposure or admit CAT input.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect, identifier,
)

EXPECTED_LAYER = "ACT2023v2_Buildings3d_Footprints"
EXPECTED_COLUMNS = {
    "id", "geom", "buildingid", "gml_id", "commune", "lau2",
    "modelmodificationdate", "area", "zmin",
}
EXPECTED_ROWS = 238189
EXPECTED_GPKG_SHA256 = "9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf"


def profile(db: sqlite3.Connection, layer: dict) -> dict:
    """Aggregate only; all SQL identifiers come from a validated source schema."""
    fields = {x["name"] for x in layer["fields"]}
    if not EXPECTED_COLUMNS.issubset(fields):
        raise GeoPackageGateError("Original ACT attribute columns have drifted")
    table = identifier(layer["table"])
    geom = identifier(layer["geometry_column"])
    if layer["srs_id"] != 2169 or layer["geometry_type"].upper() != "MULTIPOLYGON":
        raise GeoPackageGateError("ACT declared geometry/CRS has drifted")
    names = ("id", "buildingid", "gml_id", "commune", "lau2")
    q = [f"COUNT(*)", f"SUM(CASE WHEN {geom} IS NULL THEN 1 ELSE 0 END)"]
    for col in names:
        c = identifier(col)
        q.extend([
            f"COUNT(DISTINCT NULLIF(TRIM(CAST({c} AS TEXT)), ''))",
            f"SUM(CASE WHEN {c} IS NULL OR TRIM(CAST({c} AS TEXT))='' THEN 1 ELSE 0 END)",
        ])
    for col in ("area", "zmin"):
        c = identifier(col)
        q.extend([
            f"SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END)",
            f"SUM(CASE WHEN {c} IS NOT NULL AND typeof({c}) NOT IN ('integer','real') THEN 1 ELSE 0 END)",
            f"SUM(CASE WHEN typeof({c}) IN ('integer','real') AND {c}<=0 THEN 1 ELSE 0 END)",
        ])
    d = identifier("modelmodificationdate")
    q.append(f"SUM(CASE WHEN {d} IS NULL OR TRIM(CAST({d} AS TEXT))='' THEN 1 ELSE 0 END)")
    result = db.execute(f"SELECT {', '.join(q)} FROM {table}").fetchone()
    if not result or int(result[0]) != layer["feature_count"]:
        raise GeoPackageGateError("Aggregate row count differs from metadata receipt")
    it = iter(result)
    n = int(next(it))
    null_geom = int(next(it))
    identifiers = {}
    for name in names:
        distinct, missing = int(next(it)), int(next(it))
        identifiers[name] = {
            "distinct_nonblank": distinct, "missing_or_blank": missing,
            "duplicate_nonblank_rows": n - missing - distinct,
        }
        if not 0 <= distinct <= n or not 0 <= missing <= n or distinct + missing > n:
            raise GeoPackageGateError("Inconsistent identifier counts")
    quantitative = {}
    for name in ("area", "zmin"):
        missing, invalid_type, nonpositive = (int(next(it)), int(next(it)), int(next(it)))
        quantitative[name] = {
            "null": missing, "nonnull_not_numeric_sqlite": invalid_type,
            "nonpositive_numeric": nonpositive,
        }
    missing_modification_date = int(next(it))
    rtree_count = None
    if layer["has_rtree"]:
        rtree_name = identifier("rtree_" + layer["table"] + "_" + layer["geometry_column"])
        rtree_count = db.execute(f"SELECT COUNT(*) FROM {rtree_name}").fetchone()[0]
        if not isinstance(rtree_count, int) or not 0 <= rtree_count <= n:
            raise GeoPackageGateError("Impossible RTree row count")
    return {
        "profile": "act2023v2-gpkg-attribute-quality-v0",
        "feature_row_count": n,
        "null_geometry_count": null_geom,
        "original_id_diagnostics": identifiers,
        "numeric_field_diagnostics": quantitative,
        "missing_modification_date_count": missing_modification_date,
        "rtree_entries": rtree_count,
        "rtree_missing_entries_vs_features": n - rtree_count if rtree_count is not None else None,
        "geometry_topology_checked": False,
        "coordinate_axis_order_verified": False,
        "roofs_are_ground_footprints_proven": False,
        "building_identity_approved": False,
        "source_rights_and_model_admission_approved": False,
        "raw_records_exported": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpkg", type=Path, required=True)
    parser.add_argument("--expected-gpkg-sha256", default=EXPECTED_GPKG_SHA256)
    args = parser.parse_args(argv)
    try:
        if args.expected_gpkg_sha256 != EXPECTED_GPKG_SHA256:
            raise GeoPackageGateError("Original ACT GeoPackage digest must match pinned version")
        receipt, db = inspect(args.gpkg, expected_sha256=EXPECTED_GPKG_SHA256)
        try:
            if len(receipt["layers"]) != 1 or receipt["layers"][0]["table"] != EXPECTED_LAYER:
                raise GeoPackageGateError("Original feature table identity drift")
            if receipt["layers"][0]["feature_count"] != EXPECTED_ROWS:
                raise GeoPackageGateError("Original pinned feature population drift")
            report = profile(db, receipt["layers"][0])
        finally:
            db.close()
    except (OSError, sqlite3.Error, GeoPackageGateError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    report["source_gpkg_sha256"] = EXPECTED_GPKG_SHA256
    report["provider_product"] = "Luxembourg ACT2023v2 roof-derived 2D footprints"
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
