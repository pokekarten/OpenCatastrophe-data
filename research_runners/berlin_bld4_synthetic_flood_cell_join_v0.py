#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, offline BLD4 building-polygon x SYNTHETIC metre-depth cell QA.

This only proves a geospatial calculation contract. The grid is synthetic,
NOT a provider hazard, event, return-period map, hazard calibration or CAT
model input. Never export per-building IDs, WKB, location or modeled losses.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import quote

from research_runners.berlin_alkis_gebaeude_five_feature_join_v0 import (
    BBOX, CAT4_APP_ID as BUILDING_APP_ID, CAT4_SCHEMA, CAT4_SCHEMA_VERSION,
)

MAX_GRID_BYTES = 131_072
MAX_GRID_CELLS = 1_024
MAX_BLD4_BYTES = 2_000_000
GRID_PROFILE = "synthetic-berlin-flood-depth-cells-v0"
REPORT_PROFILE = "berlin-building-synthetic-flood-support-v0"
HASH = re.compile(r"[0-9a-f]{64}\Z")


class GridJoinError(ValueError):
    """Unsafe file, unsupported hazard semantics or unreviewed spatial join."""


def _object(pairs):
    data = {}
    for k, v in pairs:
        if k in data:
            raise GridJoinError("duplicate hazard-grid JSON field")
        data[k] = v
    return data


def _num(x, label, *, low, high):
    if type(x) not in (int, float):
        raise GridJoinError(f"{label} must be a finite numeric value")
    try:
        v = float(x)
    except (ValueError, OverflowError) as exc:
        raise GridJoinError(f"{label} must be finite") from exc
    if not math.isfinite(v) or not low <= v <= high:
        raise GridJoinError(f"{label} outside reviewed range")
    return v


def read_synthetic_grid(path: Path):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_GRID_BYTES:
        raise GridJoinError("synthetic grid file missing or outside byte limit")
    raw = path.read_bytes()
    if not 0 < len(raw) <= MAX_GRID_BYTES:
        raise GridJoinError("synthetic grid byte limit exceeded")
    try:
        g = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                       parse_constant=lambda x: (_ for _ in ()).throw(GridJoinError("nonfinite grid constant")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GridJoinError("invalid synthetic grid JSON") from exc
    fields = {"profile", "source_class", "crs", "peril", "unit", "top_left_x_m",
              "top_left_y_m", "cell_size_m", "width", "height", "cells"}
    if type(g) is not dict or set(g) != fields:
        raise GridJoinError("unreviewed synthetic grid schema")
    if (g["profile"] != GRID_PROFILE or g["source_class"] != "synthetic_test_only"
            or g["crs"] != "EPSG:25833" or g["peril"] != "flood_water_depth"
            or g["unit"] != "m"):
        raise GridJoinError("real, unverified, non-metre or foreign CRS hazard not accepted")
    for key in ("width", "height"):
        if type(g[key]) is not int or not 1 <= g[key] <= MAX_GRID_CELLS:
            raise GridJoinError("invalid synthetic grid dimensions")
    if g["width"] * g["height"] > MAX_GRID_CELLS:
        raise GridJoinError("synthetic pixel budget exceeded")
    x0 = _num(g["top_left_x_m"], "top_left_x_m", low=300_000, high=500_000)
    y0 = _num(g["top_left_y_m"], "top_left_y_m", low=5_700_000, high=5_950_000)
    size = _num(g["cell_size_m"], "cell_size_m", low=0.5, high=200)
    cells = g["cells"]
    if (type(cells) is not list or len(cells) != g["height"]
            or any(type(row) is not list or len(row) != g["width"] for row in cells)):
        raise GridJoinError("synthetic cell matrix dimensions do not match grid")
    clean = []
    for row in cells:
        clean.append([None if value is None else _num(value, "depth_m", low=0, high=30)
                      for value in row])
    return {"x0": x0, "y0": y0, "size": size, "width": g["width"],
            "height": g["height"], "cells": clean,
            "grid_sha256": hashlib.sha256(raw).hexdigest()}


def read_bld4_footprints(path: Path):
    from shapely import wkb
    from shapely.geometry import box

    if (path.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= MAX_BLD4_BYTES):
        raise GridJoinError("bounded BLD4 source database missing or oversized")
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as db:
            db.execute("PRAGMA query_only=ON")
            if (db.execute("PRAGMA application_id").fetchone()[0] != BUILDING_APP_ID
                    or db.execute("PRAGMA user_version").fetchone()[0] != CAT4_SCHEMA_VERSION):
                raise GridJoinError("not independently staged BLD4 building database")
            prov = db.execute("SELECT schema_id, source_response_sha256, source_rights, "
                              "building_vintage, boundary_vintage, model_admitted "
                              "FROM provenance").fetchall()
            if (len(prov) != 1 or prov[0][0] != CAT4_SCHEMA
                    or not isinstance(prov[0][1], str) or not HASH.fullmatch(prov[0][1])
                    or prov[0][2] != "dl-de-zero-2.0"
                    or prov[0][3] != "current_mutable_unknown_feature_date"
                    or prov[0][4] != 2021 or prov[0][5] != 0):
                raise GridJoinError("BLD4 source provenance or non-admission gate failed")
            rows = db.execute("SELECT ordinal, projected_epsg25833_geometry_wkb, "
                              "footprint_area_m2, nuts1_region FROM building_sample "
                              "ORDER BY ordinal LIMIT 6").fetchall()
    except sqlite3.Error as exc:
        raise GridJoinError("unreadable or invalid BLD4 schema") from exc
    if not 1 <= len(rows) <= 5:
        raise GridJoinError("unreviewed BLD4 building count")
    footprints = []
    area_box = box(*BBOX)
    for idx, blob, stored_area, nuts in rows:
        if type(idx) is not int or type(blob) is not bytes or len(blob) > 100_000 or nuts != "DE3":
            raise GridJoinError("invalid BLD4 building row identity or region")
        try:
            geom = wkb.loads(blob)
        except Exception as exc:
            raise GridJoinError("invalid BLD4 building polygon WKB") from exc
        if (geom.geom_type not in {"Polygon", "MultiPolygon"} or not geom.is_valid
                or geom.is_empty or not 0 < geom.area < 1_000_000 or not geom.intersects(area_box)
                or type(stored_area) is not float
                or not math.isclose(stored_area, geom.area, rel_tol=1e-10, abs_tol=1e-6)):
            raise GridJoinError("invalid BLD4 building metric geometry or area")
        if any(geom.intersection(existing).area > 1e-6 for existing in footprints):
            raise GridJoinError("overlapping source buildings could double-count affected area")
        footprints.append(geom)
    return footprints, prov[0][1]


def audit_support(footprints, grid: dict, *, building_source_sha256: str):
    from shapely.geometry import box

    if not footprints or len(footprints) > 5:
        raise GridJoinError("bounded sample requires 1–5 building polygons")
    x0, y0, size = grid["x0"], grid["y0"], grid["size"]
    bounds = box(x0, y0 - grid["height"]*size,
                 x0 + grid["width"]*size, y0)
    total_area = valid = wet = dry = nodata = outside = 0.0
    fully_valid = any_wet = no_valid = 0
    for footprint in footprints:
        total_area += footprint.area
        cover = footprint.intersection(bounds)
        inside_area = cover.area
        outside_area = max(0.0, footprint.area - inside_area)
        outside += outside_area
        current_valid = current_wet = 0.0
        for row in range(grid["height"]):
            top = y0 - row*size
            for col in range(grid["width"]):
                left = x0 + col*size
                overlap = cover.intersection(box(left, top-size, left+size, top)).area
                if overlap <= 0:
                    continue
                depth = grid["cells"][row][col]
                if depth is None:
                    nodata += overlap
                elif depth == 0:
                    dry += overlap
                    current_valid += overlap
                else:
                    wet += overlap
                    current_valid += overlap
                    current_wet += overlap
        valid += current_valid
        if math.isclose(current_valid, footprint.area, rel_tol=1e-9, abs_tol=1e-6):
            fully_valid += 1
        if current_wet > 1e-8:
            any_wet += 1
        if current_valid <= 1e-8:
            no_valid += 1
    if not math.isclose(total_area, wet+dry+nodata+outside, rel_tol=1e-8, abs_tol=1e-5):
        raise GridJoinError("hazard-support area does not conserve building footprint area")
    return {
        "profile": REPORT_PROFILE,
        "building_source_response_sha256": building_source_sha256,
        "synthetic_grid_sha256": grid["grid_sha256"],
        "building_polygons_checked": len(footprints),
        "grid_cells_checked": grid["width"]*grid["height"],
        "building_area_m2": round(total_area, 6),
        "wet_supported_area_m2": round(wet, 6),
        "dry_supported_area_m2": round(dry, 6),
        "nodata_area_m2": round(nodata, 6),
        "outside_grid_area_m2": round(outside, 6),
        "building_count_with_complete_valid_hazard_support": fully_valid,
        "building_count_with_any_positive_synthetic_depth": any_wet,
        "building_count_without_any_valid_hazard_support": no_valid,
        "area_coverage_is_exact_polygon_cell_intersection": True,
        "area_metrics_not_building_count_or_insured_share": True,
        "grid_is_synthetic_not_real_hazard": True,
        "hazard_event_frequency_or_timing_verified": False,
        "building_hazard_temporal_alignment_verified": False,
        "real_provider_hazard_values_used": False,
        "real_building_hazard_link_admitted": False,
        "vulnerability_or_insured_losses_calculated": False,
        "individual_building_footprints_or_ids_exported": False,
    }


def run(buildings: Path, hazard: Path):
    footprints, source_sha = read_bld4_footprints(buildings)
    grid = read_synthetic_grid(hazard)
    return audit_support(footprints, grid, building_source_sha256=source_sha)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--buildings", type=Path, required=True,
                        help="bounded local BLD4 staging *.cat.sqlite")
    parser.add_argument("--synthetic-grid", type=Path, required=True,
                        help="synthetic-only EPSG25833 flood cell JSON")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args.buildings, args.synthetic_grid), sort_keys=True))
    except (GridJoinError, OSError, ImportError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
