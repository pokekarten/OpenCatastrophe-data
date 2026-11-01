# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One-shot EMSN028 FileGDB priority-layer semantic research receipt.

Download pinned public ZIP in ephemeral scratch; inspect bounded metadata
of aoi, Flooded_area and Estimated_Max_Flood_Extent, then delete source
bytes. No stored source polygons, building values or CAT admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request
import zipfile

from scripts.cems_emns028_ephemeral_zip_inventory_v0 import EXPECTED_SIZE, MAX_ARCHIVE_BYTES
from scripts.cems_emns028_zip_head_receipt_v0 import (
    SOURCE_URL, OfficialRedirectOnly, assert_expected_destination,
)
from research_runners.cems_emns028_filegdb_layer_inventory_v0 import (
    PINNED_ARCHIVE_SHA256, extract_gdb_only,
)

PRIORITY_LAYERS = ("aoi", "Flooded_area", "Estimated_Max_Flood_Extent")
ALLOW_FIELDS = ("act_id", "src_date", "ext_date", "src_name",
    "src_info", "intrp", "evnt", "evnt_type", "type", "name", "nam",
    "map_type", "acc", "fcsubtype", "cpyrt_note")
GAUGE_LON_LAT = (2.547772811, 48.536875139)  # Control point, not an asset


def source_property_summary(properties: dict) -> dict:
    result = {}
    for name in ALLOW_FIELDS:
        if name not in properties or properties[name] is None:
            continue
        value = properties[name]
        if not isinstance(value, (str, int, float, bool)):
            continue
        val = str(value).strip()
        result[name] = val if len(val) <= 85 else "[LONG_VALUE_REDACTED]"
    return result


def inspect_priority_layers(gdb: Path) -> dict:
    import fiona
    from fiona.transform import transform
    from shapely.geometry import Point, shape
    from shapely.validation import explain_validity
    from shapely import get_num_coordinates
    from research_runners.cems_emns028_topology_repair_challenge_v0 import compare_repair_methods

    east, north = transform("EPSG:4326", "EPSG:32631",
                            [GAUGE_LON_LAT[0]], [GAUGE_LON_LAT[1]])
    gauge = Point(float(east[0]), float(north[0]))
    available = set(fiona.listlayers(str(gdb)))
    if any(name not in available for name in PRIORITY_LAYERS):
        raise ValueError("required original FileGDB layer missing")
    summary = {}
    for name in PRIORITY_LAYERS:
        with fiona.open(str(gdb), layer=name, mode="r") as collection:
            count = len(collection)
            epsg = collection.crs.to_epsg() if collection.crs else None
            if epsg != 32631 or count < 1:
                raise ValueError("unexpected layer CRS or zero count")
            samples = []
            for i, feature in enumerate(collection):
                if i >= (2 if name == "Estimated_Max_Flood_Extent" else 1):
                    break
                geo = feature.get("geometry")
                if geo is None:
                    raise ValueError("source feature lacks geometry")
                polygon = shape(geo)
                if polygon.geom_type not in ("Polygon", "MultiPolygon"):
                    raise ValueError("unexpected non-polygon source geometry")
                valid = bool(polygon.is_valid)
                try:
                    at_gauge = bool(polygon.intersects(gauge)) if valid else None
                except Exception:
                    at_gauge = None
                samples.append({
                    "sample_index_not_source_id": i,
                    "source_attributes": source_property_summary(dict(feature["properties"])),
                    "geometry_type": polygon.geom_type,
                    "geometry_valid": valid,
                    "geometry_validation_reason": explain_validity(polygon)[:160],
                    "geometry_vertex_coordinate_count": int(get_num_coordinates(polygon)),
                    "overlay_rejected_until_manual_topology_review": not valid,
                    "geometry_area_square_metres": round(float(polygon.area), 2)
                    if valid else None,
                    "geometry_intersects_ponthierry_gauge_control": at_gauge,
                    "gauge_intersection_is_not_insured_loss": True,
                })
                if name == "Flooded_area" and not valid:
                    samples[-1]["repair_method_sensitivity_research"] = (
                        compare_repair_methods(polygon)
                    )
            summary[name] = {
                "feature_count_total_layer": count,
                "source_crs_epsg": epsg,
                "samples": samples,
                "all_features_sampled": count <= len(samples),
                "source_geometry_stored_in_public_repo": False,
            }
    return {
        "gauge_control_easting_northing_epsg32631":
            [round(gauge.x, 2), round(gauge.y, 2)],
        "semantic_layer_receipts": summary,
        "observed_aoi04_flood_layer_scientifically_validated": False,
        "observed_extent_versus_maximum_automatically_conflated": False,
        "historical_2016_building_stock_validated": False,
        "source_rights_independently_approved": False,
        "insured_exposure_or_loss_model_admitted": False,
    }


def live() -> dict:
    opener = urllib.request.build_opener(OfficialRedirectOnly())
    with tempfile.TemporaryDirectory(prefix="cems-2016-semantic-") as t:
        base = Path(t)
        zippath = base / "original.zip"
        request = urllib.request.Request(
            SOURCE_URL, method="GET",
            headers={"User-Agent": "OpenCatastrophe-Original-Layer-Research/0.1"})
        digest = hashlib.sha256()
        total = 0
        with opener.open(request, timeout=90) as response:
            assert_expected_destination(response.geturl())
            if response.status != 200:
                raise ValueError("unexpected upstream HTTP status")
            length = response.headers.get("Content-Length")
            if length and (not length.isdecimal() or int(length) != EXPECTED_SIZE):
                raise ValueError("upstream ZIP length drift")
            with zippath.open("wb") as sink:
                while True:
                    part = response.read(min(1024*1024, MAX_ARCHIVE_BYTES+1-total))
                    if not part:
                        break
                    total += len(part)
                    if total > MAX_ARCHIVE_BYTES:
                        raise ValueError("ZIP download exceeds upper bound")
                    digest.update(part)
                    sink.write(part)
        if total != EXPECTED_SIZE or digest.hexdigest() != PINNED_ARCHIVE_SHA256:
            raise ValueError("original source hash/size drift")
        with zipfile.ZipFile(zippath) as zf:
            gdb = extract_gdb_only(zf, base / "temporary-gdb")
        evidence = inspect_priority_layers(gdb)
        return {
            "receipt_kind": "CEMS_EMSN028_ORIGINAL_PRIORITY_LAYERS_V0",
            "original_archive_sha256_verified": True,
            "original_archive_sha256": PINNED_ARCHIVE_SHA256,
            "source_archive_url": SOURCE_URL,
            "source_original_bytes": total,
            "original_archive_and_layers_ephemeral_only": True,
            **evidence,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        parser.error("explicit --live required")
    try:
        result = live()
    except Exception as exc:
        result = {
            "receipt_kind": "CEMS_EMSN028_ORIGINAL_PRIORITY_LAYERS_V0",
            "successful": False,
            "error_type": type(exc).__name__,
            "original_geometry_stored": False,
            "insured_exposure_or_loss_model_admitted": False,
        }
        print(json.dumps(result, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
