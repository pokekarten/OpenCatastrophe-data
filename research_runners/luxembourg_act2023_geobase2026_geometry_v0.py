#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original ACT2023 roof versus ACT GeoBase2026 building polygon overlay.

Research-only geometric diagnostics. The same-source-family datasets do not
establish independent truth or stable IDs. Never export individual matches.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import tempfile
import sys

from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect as inspect_gpkg, sample,
)
from scripts.building_footprint_overlap_v0 import FootprintError, compare

ACT_GPKG_SHA = "9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf"
GEOBASE_GPKG_SHA = "ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676"
ACT_LAYER = "ACT2023v2_Buildings3d_Footprints"
GEOBASE_LAYER = "Buildings_BU_Building"
ACT_COUNT = 238189
GEOBASE_COUNT = 230353
MAX_FEATURES = 400


class SameFamilyOverlapError(ValueError):
    pass


def research(act: Path, geobase: Path, *, lon: float = 6.1319,
             lat: float = 49.6116, halfwidth: float = 125,
             max_features: int = MAX_FEATURES,
             act_sha: str = ACT_GPKG_SHA,
             geobase_sha: str = GEOBASE_GPKG_SHA,
             act_layer: str = ACT_LAYER,
             geobase_layer: str = GEOBASE_LAYER,
             act_id: str = "buildingid",
             geobase_id: str = "BU_BuildingID") -> dict:
    if not (math.isfinite(lon) and math.isfinite(lat)
            and math.isfinite(halfwidth) and 5.6 <= lon <= 6.7
            and 49.2 <= lat <= 50.4 and 20 <= halfwidth <= 250
            and 1 <= max_features <= MAX_FEATURES):
        raise SameFamilyOverlapError("outside fixed Luxembourg research bounds")
    if not (act_sha == ACT_GPKG_SHA and geobase_sha == GEOBASE_GPKG_SHA):
        raise SameFamilyOverlapError("original source hashes must match pinned releases")
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise SameFamilyOverlapError("pinned spatial runtime missing") from exc
    to_equal_area = Transformer.from_crs(4326, 3035, always_xy=True)
    to_native = Transformer.from_crs(3035, 2169, always_xy=True)
    cx, cy = to_equal_area.transform(lon, lat)
    corners = [
        to_native.transform(x, y) for x, y in (
            (cx-halfwidth,cy-halfwidth), (cx+halfwidth,cy-halfwidth),
            (cx+halfwidth,cy+halfwidth), (cx-halfwidth,cy+halfwidth)
        )
    ]
    bbox = (min(p[0] for p in corners), min(p[1] for p in corners),
            max(p[0] for p in corners), max(p[1] for p in corners))
    if not all(math.isfinite(v) for v in bbox):
        raise SameFamilyOverlapError("invalid native research envelope")

    results = []
    try:
        with tempfile.TemporaryDirectory(prefix="act-samefamily-research-") as td:
            originals = (
                (act, act_sha, act_layer, act_id, ACT_COUNT, "act.geojson"),
                (geobase, geobase_sha, geobase_layer, geobase_id, GEOBASE_COUNT,
                 "geobase.geojson"),
            )
            for path, sha, table, name, expected, filename in originals:
                receipt, db = inspect_gpkg(path, expected_sha256=sha)
                try:
                    layer = next((l for l in receipt["layers"] if l["table"] == table), None)
                    if layer is None:
                        raise SameFamilyOverlapError("original feature-layer mismatch")
                    # When comparing release versions the complete source population
                    # must agree with the independently prior-observed receipt.
                    # Synthetic tests can override expected full counts below.
                    if layer["feature_count"] != expected:
                        raise SameFamilyOverlapError("original feature population drift")
                    output = Path(td) / filename
                    count = sample(db, layer, id_field=name, bbox=bbox,
                                   limit=max_features, output=output)
                    results.append((output, count))
                finally:
                    db.close()
            r = compare(results[0][0], results[1][0],
                        left_crs="EPSG:2169", right_crs="EPSG:2169",
                        left_source="act2023v2-roof-research",
                        right_source="act2026-geobase-building-research",
                        min_iou=0.60, overlap_warning_fraction=0.20,
                        max_features=max_features)
    except (GeoPackageGateError, FootprintError, OSError) as exc:
        raise SameFamilyOverlapError("source/sample comparison blocked: " + str(exc)) from exc

    return {
        "profile": "lu-act2023-geobase2026-bounded-geometry-v0",
        "original_sha256": {"act2023": act_sha, "geobase2026": geobase_sha},
        "roi_type": "fixed 2D EPSG:3035 research window",
        "roi_halfwidth_metres": halfwidth,
        "source_counts": {"act_roof_polygons": results[0][1],
                          "geobase_building_polygons": results[1][1]},
        "iou_0_60_unique_candidates": r["counts"]["high_iou_unique_matches"],
        "ambiguous_roof_polygons": r["counts"]["ambiguous_split_or_merge_left"],
        "weak_unique_roof_polygons": r["counts"]["single_candidate_below_iou"],
        "no_substantial_overlap_roofs": r["counts"]["left_no_substantial_overlap"],
        "median_unique_candidate_iou": r["matched_iou_median"],
        "spatial_candidate_pairs_checked": r["counts"]["spatial_candidate_pairs_checked"],
        "identical_id_namespace_proven": False,
        "independent_ground_truth_proven": False,
        "source_geometry_equivalent_proven": False,
        "native_axis_ground_control_verified": False,
        "insured_exposure_or_building_stock_change_inferred": False,
        "original_id_pairs_or_geometry_exported": False,
        "CAT_model_input_admitted": False,
        "warning": (
            "Exploratory aggregate geometry overlap between two releases from ACT, "
            "not a validated physical-building crosswalk or new/demolished stock. "
            "Rooftop and GeoBase object definitions differ; native CRS order is "
            "plausible but not independently ground controlled."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--act-gpkg", type=Path, required=True)
    parser.add_argument("--geobase-gpkg", type=Path, required=True)
    a = parser.parse_args(argv)
    try:
        report = research(a.act_gpkg, a.geobase_gpkg)
    except (SameFamilyOverlapError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
