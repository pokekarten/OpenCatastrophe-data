#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only Bavaria dike line -> WRI RIVERINE raster *candidate* cell bridge.

Uses real original WRI Aqueduct Floods v2 historical riverine RP100 TIFF
header/IFD/GeoTIFF tags, independently pinned by bounded original HTTP-range
body SHA256, and the original full Bavaria LfU EPSG:4258 ZIP verified by our
separate full-member Shapefile validator. pyproj is mandatory for the actual
ETRS89->WGS84 datum transformation; no implicit identity-CRS fallback.

No original source binary is committed. Output is AGGREGATES ONLY, not original
points/geometry, protected buildings, matched hazard depth, hydraulic
overtopping/breach probabilities, event catalogues, losses, or model admission.
The original WRI COASTAL model is NOT silently used for inland Bavaria.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zipfile

from research_runners.bavaria_hwsa_full_shapefile_integrity_v0 import (
    EXPECTED_COUNTS, GeometryGateError, inspect_original_zip,
)

PROFILE = "wri-riverine-bavaria-dike-spatial-candidate-v0"
RIVERINE_ORIGINAL = (
    "https://aqueduct.wridata.org/AqueductFloods20/"
    "inunriver_historical_000000000WATCH_1980_rp00100.tif"
)
BAVARIA_ORIGINAL = (
    "https://www.lfu.bayern.de/gdi/dls/daten/hwsa/hwsa_epsg4258_shp.zip"
)
# Original HTTP Range bodies, exact byte lengths, SHA256 independently
# observed from WRI provider on 2026-11-04. NOT whole-object digests.
TIFF_SOURCE_RANGES = {
    "header": (0, 4095, "19fb7bcafa37bd05cb66c5b859de2a89454868b31f4adbe4236788f1820603b0"),
    "ifd": (91989120, 91991167, "b5c2017faece776aa0baf4d3ec204b340dfd08f83913f52903ac3145c306796e"),
    "scale": (92162148, 92162171, "5028a719ed734b672befec6ed0d5c9c9ca5c97660849b79fb91ae874d219bd03"),
    "tie": (92162172, 92162219, "2dd8ddcb9359f78996cff47a4873558e152b82f0521f5e8d78b19e0ec7a1f407"),
    "geokeys": (92162220, 92162283, "b6093cdbd0103bc46a1486c7ca6d97ab5c4dd2ebd18eb38ecf9f1590b4a9e77e"),
    "nodata": (92162142, 92162147, "44855a774102fff976316f1cf98c6c546ee3e34dcfc49bde3ad6d0398ff77b42"),
}
WIDTH, HEIGHT = 43200, 21600
CELLS_PER_DEGREE = 120
CHUNK_WIDTH = 1000
EPS = 1e-8
MAX_CROSSED_CELLS_PER_SEGMENT = 5000
MAX_TOTAL_CELL_FEATURE_RELATIONS = 2_500_000


class SpatialCandidateError(ValueError):
    """Missing evidence, wrong CRS or geometry, or unsafe candidate computation."""


def original_range_bytes(path: Path, key: str) -> bytes:
    if key not in TIFF_SOURCE_RANGES:
        raise SpatialCandidateError("unknown original WRI HTTP Range key")
    start, end, digest = TIFF_SOURCE_RANGES[key]
    length = end - start + 1
    with path.open("rb") as source:
        raw = source.read(length + 1)
    if len(raw) != length or hashlib.sha256(raw).hexdigest() != digest:
        raise SpatialCandidateError("original WRI riverine evidence truncated or source changed")
    return raw


def verify_original_wri_riverine_tiff(ranges: dict[str, bytes]) -> dict:
    if set(ranges) != set(TIFF_SOURCE_RANGES):
        raise SpatialCandidateError("WRI riverine original evidence is incomplete")
    for key, data in ranges.items():
        if type(data) is not bytes:
            raise SpatialCandidateError("original provider response must be bytes")
        start, end, digest = TIFF_SOURCE_RANGES[key]
        if len(data) != end - start + 1 or hashlib.sha256(data).hexdigest() != digest:
            raise SpatialCandidateError("wrong WRI riverine original byte range or SHA256")
    head = ranges["header"]
    if head[:4] != b"II\x2a\x00" or struct.unpack_from("<I", head, 4)[0] != 91989120:
        raise SpatialCandidateError("not the reviewed WRI riverine classic TIFF")
    ifd = ranges["ifd"]
    count = struct.unpack_from("<H", ifd)[0]
    if count != 18:
        raise SpatialCandidateError("WRI original riverine TIFF IFD entry count changed")
    tags = {}
    for i in range(count):
        tag, dtype, n, value = struct.unpack_from("<HHII", ifd, 2 + 12*i)
        if tag in tags:
            raise SpatialCandidateError("duplicate TIFF metadata tag")
        tags[tag] = (dtype, n, value)
    expected = {
        256: (3, 1, WIDTH), 257: (3, 1, HEIGHT),
        258: (3, 1, 32), 259: (3, 1, 5),
        278: (3, 1, 1), 339: (3, 1, 3),
        273: (4, HEIGHT, 92075742), 279: (4, HEIGHT, 91989342),
        33550: (12, 3, 92162148), 33922: (12, 6, 92162172),
        34735: (3, 32, 92162220), 42113: (2, 6, 92162142),
    }
    if any(tags.get(tag) != value for tag, value in expected.items()):
        raise SpatialCandidateError("WRI riverine Float32 GeoTIFF grid profile changed")
    scale = struct.unpack("<3d", ranges["scale"])
    tie = struct.unpack("<6d", ranges["tie"])
    if (not math.isclose(scale[0], 1/120, rel_tol=0, abs_tol=1e-14)
            or not math.isclose(scale[1], 1/120, rel_tol=0, abs_tol=1e-14)
            or scale[2] != 0.0 or tie != (0.0, 0.0, 0.0, -180.0, 90.0, 0.0)):
        raise SpatialCandidateError("WRI riverine grid extent or pixel scale changed")
    keys = struct.unpack("<32H", ranges["geokeys"])
    if keys[:4] != (1, 1, 0, 7):
        raise SpatialCandidateError("unexpected original EPSG GeoKey header")
    geokeys = {}
    for i in range(7):
        key, location, n, value = keys[4+i*4:8+i*4]
        geokeys[key] = (location, n, value)
    if (geokeys.get(1024) != (0, 1, 2)
            or geokeys.get(1025) != (0, 1, 1)
            or geokeys.get(2048) != (0, 1, 4326)
            or ranges["nodata"] != b"-9999\x00"):
        raise SpatialCandidateError("GeoTIFF grid CRS/nodata is not the source profile")
    return {
        "provider": "World Resources Institute",
        "product": "Aqueduct Flood Hazard Maps v2, historical RIVERINE WATCH 1980, RP100",
        "source_url": RIVERINE_ORIGINAL,
        "source_original_range_sha256": {k: x[2] for k, x in TIFF_SOURCE_RANGES.items()},
        "grid_crs": "EPSG:4326",
        "grid_width": WIDTH, "grid_height": HEIGHT,
        "cell_size_degrees": 1/120,
        "top_left_longitude": -180, "top_left_latitude": 90,
        "original_float32_nodata": -9999,
        "whole_TIFF_sha256_verified": False,
        "any_hazard_pixel_depth_sampled": False,
    }


def _axis_cells(value: float, count: int) -> tuple[int, ...]:
    if not math.isfinite(value):
        raise SpatialCandidateError("non-finite transformed grid coordinate")
    rounded = round(value)
    if abs(value - rounded) <= EPS:
        choices = (rounded - 1, rounded)
    else:
        choices = (math.floor(value),)
    result = tuple(sorted({i for i in choices if 0 <= i < count}))
    if not result:
        raise SpatialCandidateError("coordinate is outside WRI global raster extent")
    return result


def global_wri_cell(lon: float, lat: float) -> tuple[int, int]:
    """Interior location: (row, column), WRI PixelIsArea, WGS84 x/y only."""
    if (not math.isfinite(lon) or not math.isfinite(lat)
            or not -180 < lon < 180 or not -90 < lat < 90):
        raise SpatialCandidateError("WRI WGS84 point invalid")
    col = (lon + 180)*CELLS_PER_DEGREE
    row = (90-lat)*CELLS_PER_DEGREE
    return math.floor(row), math.floor(col)


def segment_candidate_cells(
    start: tuple[float, float], end: tuple[float, float]
) -> set[tuple[int, int]]:
    """Conservative raster supercover including grid-line/corner touching.

    Each input point is already explicitly transformed to EPSG:4326 lon/lat.
    At exact cell boundaries both adjacent cells are candidate intersections.
    No nearest-vertex-only shortcut: include every intervening grid crossing.
    """
    x0, y0 = start
    x1, y1 = end
    if any(not math.isfinite(v) for v in (x0, y0, x1, y1)):
        raise SpatialCandidateError("non-finite transformed segment")
    if not all(-180 < x < 180 for x in (x0, x1)) or not all(
            -90 < y < 90 for y in (y0, y1)):
        raise SpatialCandidateError("segment outside reviewed WRI global domain")
    u0, u1 = (x0+180)*CELLS_PER_DEGREE, (x1+180)*CELLS_PER_DEGREE
    v0, v1 = (90-y0)*CELLS_PER_DEGREE, (90-y1)*CELLS_PER_DEGREE
    du, dv = u1-u0, v1-v0
    if abs(du)+abs(dv) > MAX_CROSSED_CELLS_PER_SEGMENT:
        raise SpatialCandidateError("source segment crosses excessive grid cells")
    critical = {0.0, 1.0}
    for a, b in ((u0, u1), (v0, v1)):
        delta = b-a
        if not delta:
            continue
        for mark in range(math.floor(min(a, b))+1, math.ceil(max(a, b))):
            t = (mark-a)/delta
            if 0.0 < t < 1.0:
                critical.add(t)
    times = sorted(critical)
    samples = list(times)
    samples.extend((a+b)/2 for a, b in zip(times, times[1:]))
    cells = set()
    for t in samples:
        u, v = u0+du*t, v0+dv*t
        for row in _axis_cells(v, HEIGHT):
            for col in _axis_cells(u, WIDTH):
                cells.add((row, col))
    if len(cells) > MAX_CROSSED_CELLS_PER_SEGMENT*4:
        raise SpatialCandidateError("unexpectedly many raster candidate cells")
    return cells


def _raw_source_polyline_vertices(shp: bytes, expected: int):
    """Yield one feature as a list of line parts from unmodified source bytes."""
    pos, record = 100, 0
    while pos < len(shp):
        if pos + 8 > len(shp):
            raise SpatialCandidateError("truncated SHP record")
        number, words = struct.unpack_from(">II", shp, pos)
        at, byte_count = pos+8, words*2
        if number != record+1 or at+byte_count > len(shp) or byte_count < 4:
            raise SpatialCandidateError("original source SHP record/index invalid")
        geom = struct.unpack_from("<I", shp, at)[0]
        if geom != 3 or byte_count < 48:
            raise SpatialCandidateError("unexpected source non-polyline/empty geometry")
        n_parts, n_points = struct.unpack_from("<II", shp, at+36)
        if not 0 < n_parts <= n_points <= 200000 or (
                44+4*n_parts+16*n_points != byte_count):
            raise SpatialCandidateError("unreviewed SHP geometry byte layout")
        starts = [struct.unpack_from("<I", shp, at+44+4*k)[0] for k in range(n_parts)]
        starts.append(n_points)
        if starts[0] != 0 or any(a >= b for a, b in zip(starts, starts[1:])):
            raise SpatialCandidateError("invalid polyline part indices")
        point_at = at+44+4*n_parts
        parts = [
            [struct.unpack_from("<2d", shp, point_at+i*16)
             for i in range(first, last)]
            for first, last in zip(starts, starts[1:])
        ]
        yield parts
        pos = at+byte_count
        record += 1
    if pos != len(shp) or record != expected:
        raise SpatialCandidateError("source SHP record count different from verified archive")


def aggregate_original_defence_candidate_cells(
    shp_by_kind: dict[str, bytes],
    transform_lonlat,
) -> dict:
    if set(shp_by_kind) != set(EXPECTED_COUNTS):
        raise SpatialCandidateError("all three original LfU layer payloads required")
    summary = {}
    for kind, shp in sorted(shp_by_kind.items()):
        encountered = 0
        unique_cells = set()
        features_per_tile = defaultdict(int)
        feature_cell_relations = 0
        for parts in _raw_source_polyline_vertices(shp, EXPECTED_COUNTS[kind]):
            encountered += 1
            feature_cells = set()
            for points in parts:
                projected = []
                for x, y in points:
                    if not all(math.isfinite(v) for v in (x, y)):
                        raise SpatialCandidateError("source ETRS89 vertex invalid")
                    lon, lat = transform_lonlat(x, y)
                    if (not 5 < lon < 16 or not 46 < lat < 52):
                        raise SpatialCandidateError("transformed source point outside Bavaria")
                    projected.append((lon, lat))
                if len(projected) == 1:
                    row, col = global_wri_cell(*projected[0])
                    feature_cells.add((row, col))
                for a, b in zip(projected, projected[1:]):
                    feature_cells.update(segment_candidate_cells(a, b))
                if not feature_cells:
                    raise SpatialCandidateError("empty source line part")
            feature_cell_relations += len(feature_cells)
            if feature_cell_relations > MAX_TOTAL_CELL_FEATURE_RELATIONS:
                raise SpatialCandidateError("source-to-cell relation budget exceeded")
            unique_cells.update(feature_cells)
            for tile in {(row//CHUNK_WIDTH, col//CHUNK_WIDTH)
                         for row, col in feature_cells}:
                features_per_tile[tile] += 1
        if encountered != EXPECTED_COUNTS[kind]:
            raise SpatialCandidateError("source feature count changed")
        summary[kind] = {
            "original_source_records": encountered,
            "distinct_wri_riverine_candidate_cells": len(unique_cells),
            "source_record_candidate_cell_relations": feature_cell_relations,
            "candidate_tiles": [
                {"tile_key_y_x": f"{y}.{x}", "source_records_touching_tile": n}
                for (y, x), n in sorted(features_per_tile.items())
            ],
            "no_hazard_depth_or_protection_inferred": True,
        }
    return summary


def inspect_original_spatial_bridge(zip_path: Path, ranges: dict[str, bytes]) -> dict:
    original_riverine = verify_original_wri_riverine_tiff(ranges)
    # Hard gate: the real source ZIP is validated before any geometric use.
    try:
        original_lfu = inspect_original_zip(zip_path, 4258)
        from pyproj import Transformer  # required at runtime, not in synthetic unit tests
    except (GeometryGateError, ImportError) as exc:
        raise SpatialCandidateError("source ZIP or mandatory pyproj unavailable") from exc
    # ETRS89 to WGS84 has a small but real transformation uncertainty.
    # No direct treating EPSG4258 coordinates as exactly EPSG4326.
    converter = Transformer.from_crs("EPSG:4258", "EPSG:4326", always_xy=True)
    if converter.accuracy < 0 or converter.accuracy > 10:
        raise SpatialCandidateError("ETRS89 to WGS84 transform accuracy unverified")
    with zipfile.ZipFile(zip_path) as src:
        layer_bytes = {
            kind: src.read(f"{kind}_epsg4258.shp") for kind in EXPECTED_COUNTS
        }
    candidates = aggregate_original_defence_candidate_cells(
        layer_bytes, converter.transform
    )
    return {
        "profile": PROFILE,
        "lfu_source": BAVARIA_ORIGINAL,
        "lfu_original_zip_sha256": original_lfu["original_zip_sha256"],
        "lfu_crs": "EPSG:4258",
        "wri_riverine_source": original_riverine,
        "wri_raster_crs": "EPSG:4326",
        "wri_origin_and_resolution_source_verified": True,
        "mandatory_coordinate_operation": converter.description,
        "coordinate_operation_reported_accuracy_metres": converter.accuracy,
        "candidate_geometry_aggregation": candidates,
        "source_records_aggregated_once": sum(EXPECTED_COUNTS.values()),
        "original_geometry_or_coordinates_exported": False,
        "wri_riverine_hazard_values_sampled": False,
        "protected_side_of_defence_identified": False,
        "any_building_insurance_exposure_matched": False,
        "defence_effectiveness_or_reliability_modelled": False,
        "riverine_flood_depth_reduced": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lfu-epsg4258-original-zip", type=Path, required=True)
    for key in TIFF_SOURCE_RANGES:
        parser.add_argument("--wri-"+key.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    evidence = {key: getattr(args, "wri_"+key) for key in TIFF_SOURCE_RANGES}
    original_paths = [args.lfu_epsg4258_original_zip] + list(evidence.values())
    if len({p.resolve() for p in original_paths}) != len(original_paths) or (
            args.out.resolve() in {p.resolve() for p in original_paths}):
        parser.error("no duplicate original paths and no overwriting original data")
    try:
        raw_ranges = {key: original_range_bytes(path, key)
                      for key, path in evidence.items()}
        result = inspect_original_spatial_bridge(
            args.lfu_epsg4258_original_zip, raw_ranges
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                            encoding="utf-8")
    except (OSError, GeometryGateError, SpatialCandidateError, ValueError) as exc:
        print("BLOCKED: "+str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
