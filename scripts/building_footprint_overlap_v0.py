#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline diagnostic-only building footprint overlap; no source approval or raw output.

Requires optional reviewed requirements-eu-flood-spatial.txt (shapely + pyproj).
Never downloads provider data, generates per-building joins, or writes a database.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

try:
    from pyproj import CRS, Transformer
    from shapely.geometry import shape
    from shapely.ops import transform
    from shapely.strtree import STRtree
except ImportError:  # optional spatial profile
    CRS = Transformer = shape = transform = STRtree = None


class FootprintError(ValueError):
    """Invalid input or unsafe/unreproducible spatial comparison."""


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FootprintError("GeoJSON has duplicated object keys")
        result[key] = value
    return result


def _crs(text: str):
    if CRS is None:
        raise FootprintError("pyproj and shapely spatial dependencies are not installed")
    try:
        crs = CRS.from_user_input(text)
        if not crs.is_projected and not crs.is_geographic:
            raise ValueError("unsupported CRS")
        if crs.is_compound or crs.is_vertical or crs.is_geocentric:
            raise ValueError("3D/vertical CRS unsupported")
        return crs
    except Exception as exc:
        raise FootprintError("Invalid or unsupported declared CRS") from exc


def _read(path: Path, source_crs: str, *, max_features: int):
    if not path.is_file() or path.stat().st_size > 5_000_000:
        raise FootprintError("Input must be a local GeoJSON file of at most 5 MB")
    try:
        source_bytes = path.read_bytes()
        if len(source_bytes) > 5_000_000:
            raise FootprintError("Input exceeds 5 MB byte budget")
        payload = json.loads(
            source_bytes.decode("utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(FootprintError("Nonfinite GeoJSON number")),
        )
    except (ValueError, OSError, UnicodeError) as exc:
        raise FootprintError("Invalid UTF-8 GeoJSON") from exc
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise FootprintError("Expected GeoJSON FeatureCollection")
    if "crs" in payload:
        raise FootprintError("Legacy embedded CRS unsupported; declare source CRS explicitly")
    features = payload.get("features")
    if not isinstance(features, list) or not features or len(features) > max_features:
        raise FootprintError("Empty or oversized feature collection")
    transformer = Transformer.from_crs(_crs(source_crs), CRS.from_epsg(3035), always_xy=True)
    ids, polygons = [], []
    for row in features:
        if not isinstance(row, dict) or row.get("type") != "Feature":
            raise FootprintError("Expected GeoJSON Feature")
        properties, geometry = row.get("properties"), row.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            raise FootprintError("Each feature needs geometry and properties")
        key = properties.get("building_id")
        if not isinstance(key, str) or not key or key.strip() != key or len(key) > 256:
            raise FootprintError("Missing or invalid building_id")
        if geometry.get("type") not in ("Polygon", "MultiPolygon"):
            raise FootprintError("Only Polygon/MultiPolygon building geometry allowed")
        try:
            polygon = shape(geometry)
            if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
                raise FootprintError("Empty, invalid or zero-area polygon")
            projected = transform(transformer.transform, polygon)
            if not projected.is_valid or projected.is_empty or projected.area <= 0:
                raise FootprintError("Invalid transformed polygon")
            if not all(math.isfinite(x) for x in projected.bounds):
                raise FootprintError("Nonfinite projected coordinates")
        except FootprintError:
            raise
        except Exception as exc:
            raise FootprintError("Unparseable or non-transformable building polygon") from exc
        ids.append(key)
        polygons.append(projected)
    if len(set(ids)) != len(ids):
        raise FootprintError("Duplicate building IDs in a single input")
    return polygons, hashlib.sha256(source_bytes).hexdigest()


def compare(left_path: Path, right_path: Path, *, left_crs: str, right_crs: str,
            left_source: str, right_source: str, min_iou: float = 0.60,
            overlap_warning_fraction: float = 0.20, max_features: int = 1500) -> dict:
    """Strictly count clean overlaps; possible splits/merges are NOT matches."""
    if not isinstance(left_source, str) or not left_source.strip() or not isinstance(right_source, str) or not right_source.strip():
        raise FootprintError("Source names are required")
    if not (0.0 < min_iou <= 1.0 and 0.0 < overlap_warning_fraction <= 1.0):
        raise FootprintError("Overlap and IoU thresholds must be in (0, 1]")
    if not 1 <= max_features <= 10000:
        raise FootprintError("Invalid local feature cap")
    a, left_sha256 = _read(left_path, left_crs, max_features=max_features)
    b, right_sha256 = _read(right_path, right_crs, max_features=max_features)
    index = STRtree(b)
    left_edges: dict[int, list[tuple[int, float]]] = defaultdict(list)
    right_edges: dict[int, list[int]] = defaultdict(list)
    touched_right = set()
    candidate_pairs_checked = 0
    max_candidate_pairs = 20_000  # Bounded GEOS work even for dense overlap.
    for i, g in enumerate(a):
        for j0 in index.query(g):
            candidate_pairs_checked += 1
            if candidate_pairs_checked > max_candidate_pairs:
                raise FootprintError("Bounded spatial candidate-pair budget exceeded")
            j = int(j0)
            other = b[j]
            intersection = g.intersection(other).area
            if intersection <= 0:
                continue
            touched_right.add(j)
            if max(intersection / g.area, intersection / other.area) < overlap_warning_fraction:
                continue
            iou = intersection / (g.area + other.area - intersection)
            left_edges[i].append((j, iou))
            right_edges[j].append(i)
    count = {"high_iou_unique_matches": 0, "ambiguous_split_or_merge_left": 0,
             "single_candidate_below_iou": 0, "left_no_substantial_overlap": 0}
    ious = []
    for i in range(len(a)):
        edges = left_edges.get(i, [])
        if not edges:
            count["left_no_substantial_overlap"] += 1
        elif len(edges) != 1 or len(right_edges[edges[0][0]]) != 1:
            count["ambiguous_split_or_merge_left"] += 1
        elif edges[0][1] < min_iou:
            count["single_candidate_below_iou"] += 1
        else:
            count["high_iou_unique_matches"] += 1
            ious.append(edges[0][1])
    assert sum(count.values()) == len(a)
    return {
        "schema_version": "building-footprint-overlap-diagnostic-v0",
        "left_source": left_source, "right_source": right_source,
        "left_sha256": left_sha256, "right_sha256": right_sha256,
        "left_declared_crs": left_crs, "right_declared_crs": right_crs,
        "comparison_crs": "EPSG:3035", "iou_threshold": min_iou,
        "overlap_warning_fraction": overlap_warning_fraction,
        "counts": {"left_features": len(a), "right_features": len(b),
                   "spatial_candidate_pairs_checked": candidate_pairs_checked,
                   "right_without_any_geometric_intersection": len(b) - len(touched_right),
                   **count},
        "matched_iou_median": round(statistics.median(ious), 6) if ious else None,
        "matched_iou_mean": round(statistics.mean(ious), 6) if ious else None,
        "rights_approved_for_model_input": False,
        "scientific_identity_proven": False,
        "model_input_admitted": False,
        "per_building_matches_exported": False,
        "warning": (
            "Diagnostic-only geometric candidates, not proven building identity or source independence. "
            "No building or customer IDs are exported; splitting and merging are not auto-resolved. "
            "CRS, acquisition vintage, scope, survey lineage and per-source rights need external proof."
        ),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("left", "right"):
        p.add_argument("--" + arg, type=Path, required=True)
        p.add_argument("--" + arg + "-crs", required=True)
        p.add_argument("--" + arg + "-source", required=True)
    p.add_argument("--iou", type=float, default=0.60)
    p.add_argument("--warning-overlap", type=float, default=0.20)
    p.add_argument("--out", type=Path)
    args = p.parse_args(argv)
    try:
        report = compare(args.left, args.right, left_crs=args.left_crs, right_crs=args.right_crs,
                         left_source=args.left_source, right_source=args.right_source,
                         min_iou=args.iou, overlap_warning_fraction=args.warning_overlap)
    except FootprintError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
