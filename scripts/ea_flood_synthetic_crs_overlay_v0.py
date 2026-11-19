# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, synthetic-only EA 3.3% defended label/geometry intersection audit.

All input polygons are SYNTHETIC EPSG:4326 GeoJSON; the source's OGC GeoJSON
can declare EPSG:4326 although its backing collection stores EPSG:27700.
This is not a real feature/building join or a hazard/loss admission pathway.
Never emit geometry, coordinates, feature IDs, building IDs or insured losses.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from scripts.ea_flood_original_feature_label_qa_v0 import BANDS_MM, MISSING_BAND, SOURCES

MAX_BYTES = 65_536
MAX_FEATURES = 8
MAX_BUILDINGS = 8
MAX_VERTICES = 512
PROFILE = "ea-3p3-defended-synthetic-crs-overlay-v0"
# Source *collection* metadata (2026-11-10), CRS84 longitude,latitude envelope.
SOURCE_BBOX_CRS84 = (-6.9869611877272115, 49.881385801260535,
                      2.0755019347798958, 55.810777963189906)


class OverlayBlocked(ValueError):
    """Unsupported source, CRS, topology, missingness or overlay semantics."""


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in pairs:
        if k in result:
            raise OverlayBlocked("duplicate JSON key")
        result[k] = v
    return result


def _bad_constant(v: str) -> None:
    raise OverlayBlocked("non-finite JSON constant")


def _finite_float(v: str) -> float:
    out = float(v)
    if not math.isfinite(out):
        raise OverlayBlocked("overflowed JSON number")
    return out


def _geometry(obj: Any, transformer: Any, shape: Any, transform: Any) -> Any:
    if type(obj) is not dict or obj.get("type") not in ("Polygon", "MultiPolygon"):
        raise OverlayBlocked("only synthetic Polygon/MultiPolygon are supported")
    if set(obj) != {"type", "coordinates"}:
        raise OverlayBlocked("unexpected GeoJSON geometry members")
    pairs = 0

    def visit(coords: Any, depth: int) -> None:
        nonlocal pairs
        if depth == 0:
            if type(coords) is not list or len(coords) != 2:
                raise OverlayBlocked("non-finite or malformed coordinate")
            for v in coords:
                if type(v) not in (int, float):
                    raise OverlayBlocked("non-finite or malformed coordinate")
                try:
                    valid = math.isfinite(v)
                except (ValueError, OverflowError) as exc:
                    raise OverlayBlocked("invalid or huge coordinate") from exc
                if not valid:
                    raise OverlayBlocked("non-finite or malformed coordinate")
            x, y = coords
            if not (SOURCE_BBOX_CRS84[0] <= x <= SOURCE_BBOX_CRS84[2]
                    and SOURCE_BBOX_CRS84[1] <= y <= SOURCE_BBOX_CRS84[3]):
                raise OverlayBlocked("source lon/lat outside England EA envelope or axes swapped")
            pairs += 1
            if pairs > MAX_VERTICES:
                raise OverlayBlocked("unbounded geometry vertices")
        else:
            if type(coords) is not list or not coords:
                raise OverlayBlocked("malformed polygon nesting")
            for item in coords:
                visit(item, depth - 1)

    visit(obj.get("coordinates"), 3 if obj["type"] == "MultiPolygon" else 2)
    try:
        geom = shape(obj)
        if geom.is_empty or not geom.is_valid or geom.area <= 0:
            raise OverlayBlocked("invalid/singular synthetic polygon topology")
        projected = transform(transformer.transform, geom)
        if projected.is_empty or not projected.is_valid or not math.isfinite(projected.area) or projected.area <= 0:
            raise OverlayBlocked("invalid projected polygon topology/area")
        minx, miny, maxx, maxy = projected.bounds
        if not (0 <= minx < maxx <= 800_000 and 0 <= miny < maxy <= 1_500_000):
            raise OverlayBlocked("projected metre coordinates outside BNG review envelope")
        return projected
    except OverlayBlocked:
        raise
    except (ValueError, TypeError, OverflowError) as exc:
        raise OverlayBlocked("synthetic polygon projection failed") from exc


def audit_synthetic_overlay(raw: bytes) -> dict[str, object]:
    """Return only non-identifying *synthetic* aggregate support area in m²."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise OverlayBlocked("empty or oversized input")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                         parse_constant=_bad_constant, parse_float=_finite_float)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OverlayBlocked("malformed UTF-8 JSON") from exc
    if type(doc) is not dict or set(doc) != {
        "profile", "source_class", "scenario", "source_crs", "area_crs",
        "synthetic_hazards", "synthetic_buildings",
    }:
        raise OverlayBlocked("unexpected synthetic spatial audit schema")
    if (doc["profile"] != PROFILE or doc["source_class"] != "synthetic_test_only"
            or doc["scenario"] != "ea_defended_river_sea_3p3_present"
            or doc["source_crs"] != "EPSG:4326" or doc["area_crs"] != "EPSG:27700"):
        raise OverlayBlocked("real hazard, different scenario or incorrect CRS is not permitted")
    hazards, buildings = doc["synthetic_hazards"], doc["synthetic_buildings"]
    if (type(hazards) is not list or not 1 <= len(hazards) <= MAX_FEATURES or
            type(buildings) is not list or not 1 <= len(buildings) <= MAX_BUILDINGS):
        raise OverlayBlocked("bounded nonempty synthetic hazards and buildings required")
    # These optional spatial packages are used ONLY on explicit synthetic inputs.
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform

    converter = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    hpolys = []
    for item in hazards:
        if type(item) is not dict or set(item) != {"depth_band", "flood_source", "geometry"}:
            raise OverlayBlocked("unexpected synthetic hazard fields")
        band, source = item["depth_band"], item["flood_source"]
        if (type(band) is not str or band not in (*BANDS_MM, MISSING_BAND)
                or type(source) is not str or source not in SOURCES):
            raise OverlayBlocked("unreviewed raw depth or source vocabulary")
        hpolys.append((_geometry(item["geometry"], converter, shape, transform), band, source))
    bpolys = []
    for item in buildings:
        if type(item) is not dict or set(item) != {"geometry"}:
            raise OverlayBlocked("synthetic buildings may not carry IDs, portfolios or private attributes")
        bpolys.append(_geometry(item["geometry"], converter, shape, transform))

    # Polygon overlaps would double-count depth classes or building footprint area.
    # Boundaries touching are OK: a line carries zero surface area.
    for polygons in ([p[0] for p in hpolys], bpolys):
        for i, p in enumerate(polygons):
            for q in polygons[i + 1:]:
                if p.intersection(q).area > 1e-6:
                    raise OverlayBlocked("overlapping hazard classes/buildings double-count area")

    total = 0.0
    known = 0.0
    unknown_depth = 0.0
    source_unknown = 0.0
    unsupported = 0.0
    for building in bpolys:
        area = building.area
        total += area
        touched = 0.0
        for hazard, band, source in hpolys:
            overlap = building.intersection(hazard).area
            if overlap < 0 or not math.isfinite(overlap):
                raise OverlayBlocked("invalid polygon intersection")
            touched += overlap
            if band == MISSING_BAND:
                unknown_depth += overlap
            else:
                known += overlap
            if source == MISSING_BAND:
                source_unknown += overlap
        gap = area - touched
        if gap < -max(1e-5, area * 1e-8):
            raise OverlayBlocked("polygon support overlaps / negative missing area")
        unsupported += max(0.0, gap)
    if not math.isclose(total, known + unknown_depth + unsupported, abs_tol=max(1e-4, total * 1e-8)):
        raise OverlayBlocked("source area partition does not conserve synthetic building area")

    return {
        "profile": PROFILE,
        "synthetic_building_count": len(bpolys),
        "synthetic_hazard_polygon_count": len(hpolys),
        "total_synthetic_footprint_area_m2": round(total, 4),
        "known_depth_band_support_area_m2": round(known, 4),
        "depth_unavailable_support_area_m2": round(unknown_depth, 4),
        "outside_hazard_support_area_m2": round(unsupported, 4),
        "flood_source_unavailable_area_m2_nonadditive": round(source_unknown, 4),
        "source_missingness_is_a_separate_nonadditive_axis": True,
        "area_partition_conserved_in_projected_epsg27700": True,
        "geographic_source_is_exclusively_synthetic": True,
        "actual_ea_polygons_or_buildings_used": False,
        "outside_source_support_is_not_proven_dry": True,
        "depth_unavailable_is_not_zero": True,
        "crs_transformation_is_always_xy": True,
        "depth_values_are_categories_not_measured_metres": True,
        "building_depth_or_loss_calculated": False,
        "commercial_source_rights_approved": False,
        "model_data_admitted": False,
        "identifiers_or_coordinates_reported": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-input", type=Path, required=True)
    args = parser.parse_args()
    try:
        path = args.synthetic_input
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise OverlayBlocked("synthetic source file unavailable or not bounded")
        with path.open("rb") as f:
            raw = f.read(MAX_BYTES + 1)
        result = audit_synthetic_overlay(raw)
    except (OSError, OverlayBlocked, ImportError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
