#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Research-only, exact-byte-pinned ACT roof vs EUBUCCO building footprint sample.

Original input bytes are local, authorised and ephemeral. No provider network,
per-building output, customer data, source admission or Neon writes.
The as-stored EPSG:2169 XY hypothesis is NOT a certified axis-order decision.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import tempfile

from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect as inspect_act, sample as sample_act,
)
from research_runners.eubucco_lu00_lineage_preflight_v0 import (
    EubuccoPreflightError, inspect as inspect_eubucco,
)
from scripts.building_footprint_overlap_v0 import FootprintError, compare

ACT_SHA = "9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf"
EUBUCCO_SHA = "d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c"
MAX_LOCAL_SIDE = 500


class OverlapPilotError(ValueError):
    """Source receipt, sampling or geometry assumption is unsafe."""


def _export_eubucco(parquet: Path, region, out: Path, *, cap: int) -> dict:
    """Decode source WKB, writing only bounded research-only temporary GeoJSON."""
    try:
        import pyarrow.parquet as pq
        from shapely import wkb
        from shapely.geometry import mapping
    except ImportError as exc:
        raise OverlapPilotError("Missing pinned PyArrow/Shapely research runtime") from exc

    features = []
    ids = set()
    for batch in pq.ParquetFile(parquet).iter_batches(
        batch_size=4096, columns=["id", "geometry", "region_id"]
    ):
        for row in batch.to_pylist():
            if row["region_id"] != "LU000":
                raise OverlapPilotError("Unexpected EUBUCCO NUTS3")
            try:
                polygon = wkb.loads(row["geometry"])
            except (ValueError, TypeError) as exc:
                raise OverlapPilotError("Invalid EUBUCCO WKB") from exc
            if not polygon.intersects(region):
                continue
            if (polygon.geom_type not in ("Polygon", "MultiPolygon")
                    or not polygon.is_valid or polygon.is_empty or polygon.area <= 0):
                raise OverlapPilotError("Invalid selected EUBUCCO footprint")
            building_id = row["id"]
            if not isinstance(building_id, str) or building_id in ids:
                raise OverlapPilotError("Duplicate or nonstring EUBUCCO building identity")
            ids.add(building_id)
            if len(features) > cap:
                raise OverlapPilotError("EUBUCCO window exceeds per-side research cap")
            features.append({
                "type": "Feature",
                "properties": {"building_id": building_id},
                "geometry": mapping(polygon),
            })
    if not features or len(features) > cap:
        raise OverlapPilotError("Empty or oversized EUBUCCO sample")
    out.write_text(json.dumps(
        {"type": "FeatureCollection", "features": features},
        separators=(",", ":"), ensure_ascii=False,
    ) + "\n", encoding="utf-8")
    return {"sample_features": len(features)}


def run_pilot(act_path: Path, eubucco_path: Path, *,
              longitude: float, latitude: float,
              half_width_m: float = 125.0,
              max_features: int = MAX_LOCAL_SIDE,
              act_sha256: str = ACT_SHA,
              eubucco_sha256: str = EUBUCCO_SHA,
              act_layer: str = "ACT2023v2_Buildings3d_Footprints",
              act_id_field: str = "buildingid") -> dict:
    if not all(math.isfinite(x) for x in (longitude, latitude, half_width_m)):
        raise OverlapPilotError("Nonfinite geographic selection")
    if not 5.6 <= longitude <= 6.7 or not 49.2 <= latitude <= 50.4:
        raise OverlapPilotError("Research window outside Luxembourg vicinity")
    if not 20 <= half_width_m <= 350 or not 1 <= max_features <= MAX_LOCAL_SIDE:
        raise OverlapPilotError("Unbounded research window or per-side budget")

    try:
        from pyproj import Transformer
        from shapely.geometry import box
    except ImportError as exc:
        raise OverlapPilotError("Missing pinned PyProj/Shapely research runtime") from exc

    # These are *hypothetical* source axes, not a validated cadastral axis.
    to3035 = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
    to2169 = Transformer.from_crs("EPSG:3035", "EPSG:2169", always_xy=True)
    cx, cy = to3035.transform(longitude, latitude)
    window = box(cx-half_width_m, cy-half_width_m, cx+half_width_m, cy+half_width_m)
    pts = [
        to2169.transform(x, y) for x, y in (
            (cx-half_width_m, cy-half_width_m),
            (cx+half_width_m, cy-half_width_m),
            (cx+half_width_m, cy+half_width_m),
            (cx-half_width_m, cy+half_width_m),
        )
    ]
    source_bbox = (
        min(x for x, _ in pts), min(y for _, y in pts),
        max(x for x, _ in pts), max(y for _, y in pts),
    )
    if not all(math.isfinite(x) for x in (*source_bbox, cx, cy)):
        raise OverlapPilotError("Invalid transformed research window")

    try:
        act_receipt, db = inspect_act(act_path, expected_sha256=act_sha256)
        try:
            layer = next((x for x in act_receipt["layers"] if x["table"] == act_layer), None)
            if layer is None:
                raise OverlapPilotError("Original ACT feature layer not found")
            # This verifies original EUBUCCO hash, all IDs and provenance.
            eb_receipt = inspect_eubucco(eubucco_path, expected_sha256=eubucco_sha256)
            with tempfile.TemporaryDirectory(prefix="lu-exposure-research-") as temp:
                act_temp = Path(temp) / "act-roof.geojson"
                eb_temp = Path(temp) / "eubucco-ground.geojson"
                act_count = sample_act(
                    db, layer, id_field=act_id_field, bbox=source_bbox,
                    limit=max_features, output=act_temp,
                )
                other = _export_eubucco(
                    eubucco_path, window, eb_temp, cap=max_features,
                )
                result = compare(
                    act_temp, eb_temp,
                    left_crs="EPSG:2169", right_crs="EPSG:3035",
                    left_source="lu.act.bd-l-bati3d-2023",
                    right_source="eubucco.buildings.v0.2",
                    min_iou=0.60,
                    overlap_warning_fraction=0.20,
                    max_features=max_features,
                )
        finally:
            db.close()
    except (GeoPackageGateError, EubuccoPreflightError, FootprintError) as exc:
        raise OverlapPilotError("Original source or bounded geometry rejected: " + str(exc)) from exc

    if result["counts"]["left_features"] != act_count:
        raise OverlapPilotError("Source sample count changed during comparison")
    return {
        "schema_version": "lu-act-eubucco-bounded-original-roof-overlap-v0",
        "research_window": {
            "approximate_location": "central Luxembourg city / fixed research pilot",
            "half_width_metres": half_width_m,
            "hypothesis": "ACT as-stored easting/northing XY, not independently ground-controlled",
        },
        "source_receipts": {
            "act_gpkg_sha256": act_receipt["source_gpkg_sha256"],
            "act_entire_source_count": sum(x["feature_count"] for x in act_receipt["layers"]),
            "eubucco_parquet_sha256": eb_receipt["source_bytes_sha256"],
            "eubucco_entire_source_count": eb_receipt["total_buildings"],
        },
        "original_local_sample": {
            "act_roof_features": act_count,
            "eubucco_footprint_features": other["sample_features"],
        },
        "overlap_candidate_diagnostics": {
            "matched_unique_at_iou_0_60": result["counts"]["high_iou_unique_matches"],
            "low_iou_unique": result["counts"]["single_candidate_below_iou"],
            "ambiguous_split_or_merge_roofs": result["counts"]["ambiguous_split_or_merge_left"],
            "no_substantial_overlap_roofs": result["counts"]["left_no_substantial_overlap"],
            "median_candidate_iou": result["matched_iou_median"],
            "mean_candidate_iou": result["matched_iou_mean"],
            "candidate_pairs_checked": result["counts"]["spatial_candidate_pairs_checked"],
        },
        "eubucco_upstream_independence_proven": False,
        "act_coordinate_axis_order_ground_control_verified": False,
        "source_licences_admitted_for_model": False,
        "manual_match_precision_recall_measured": False,
        "insured_building_exposure_imported": False,
        "model_input_admitted": False,
        "per_building_data_exported": False,
        "warning": (
            "Research-only geometry candidate overlay: roof extent differs from "
            "ground footprint, acquisition years differ, boundaries and upstream "
            "cadastre may overlap. No individual building identity or CAT exposure "
            "can be deduced from aggregate IoU; manual adjudication still required."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--act-gpkg", type=Path, required=True)
    parser.add_argument("--eubucco-lu00", type=Path, required=True)
    parser.add_argument("--center-lon", type=float, default=6.1319)
    parser.add_argument("--center-lat", type=float, default=49.6116)
    parser.add_argument("--half-width-m", type=float, default=125)
    parser.add_argument("--cap", type=int, default=MAX_LOCAL_SIDE)
    options = parser.parse_args(argv)
    try:
        report = run_pilot(
            options.act_gpkg, options.eubucco_lu00,
            longitude=options.center_lon, latitude=options.center_lat,
            half_width_m=options.half_width_m, max_features=options.cap,
        )
    except (OverlapPilotError, OSError) as exc:
        print("BLOCKED: " + str(exc))
        return 2
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
