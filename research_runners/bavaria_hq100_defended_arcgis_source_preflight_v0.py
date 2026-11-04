#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original Bayern UmweltAtlas defended HQ100 polygon *source-access* gate.

The official ArcGIS REST MapServer layers are queried externally and the
bounded original JSON response bodies are supplied outside the repository.
This module never fetches provider assets or writes original vector geometry.
It checks actual polygon layer / native EPSG metadata, counted provider
features, a reprojected WGS84 sample in two key layers, protected source-date
provenance, and original provider-side spatial *count* queries on a previously
verified WRI riverine 100-year row-5000 bbox.

It does NOT clip polygons, join buildings or original WRI positive-depth
pixels, infer legal safety thresholds, breach/failure probabilities, or
calculate insurance losses. Strict fail-closed no CAT source admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import sys

PROFILE = "bavaria-umweltatlas-hq100-defended-polygons-source-gate-v0"
BASE_URL = (
    "https://umweltatlas.bayern.de/arcgis/rest/services/"
    "wasser/naturgefahren_ftz/MapServer"
)
LAYER_IDS = {
    10: "hwgg_hq100",         # area behind a defence, not proof of no flooding
    14: "wt_hwgg_hq100",      # protected-side failure-case depth classes
    8: "hwgf_hq100",          # ordinary official HQ100 flood hazard polygon
}
CORE_FIELDS = ("sl_gew_nam", "geb_hq", "erm_datum",
               "link_link", "webgisid", "geom", "linkalias_link")
ROW5000_ENVELOPE = (9.0333333333, 48.325, 13.65, 48.3333333333)
EXPECTED_RESPONSE_FILES = {
    **{f"metadata_{id}": f"layer-{id}-metadata.json" for id in LAYER_IDS},
    **{f"count_{id}": f"layer-{id}-count.json" for id in LAYER_IDS},
    **{f"row_count_{id}": f"layer-{id}-row5000-spatial-count.json" for id in LAYER_IDS},
    "sample_10": "layer-10-sample-geojson.json",
    "sample_14": "layer-14-sample-geojson.json",
    "attributes_10": "layer-10-attributes-without-geometry.json",
}
MAX_RESPONSE = 100_000
MAX_ORIGINAL_GEOJSON_POLYGON_COORDINATES = 20_000
PROVIDER_DECLARED_LICENSE_UNDER_REVIEW = True


class DefendedArcgisGateError(ValueError):
    """Source JSON, spatial field, projection or evidence integrity problem."""


def read_original_json(path: Path) -> tuple[dict, str]:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_RESPONSE:
        raise DefendedArcgisGateError("source response missing/oversized")
    data = path.read_bytes()
    try:
        obj = json.loads(data)
    except (ValueError, UnicodeError) as err:
        raise DefendedArcgisGateError("source JSON invalid") from err
    if not isinstance(obj, dict) or "error" in obj:
        raise DefendedArcgisGateError("original provider returned error or wrong JSON type")
    return obj, hashlib.sha256(data).hexdigest()


def verify_layer_metadata(value: dict, layer_id: int) -> dict:
    if layer_id not in LAYER_IDS:
        raise DefendedArcgisGateError("unreviewed ArcGIS layer ID")
    if (value.get("name") != LAYER_IDS[layer_id]
            or value.get("type") != "Feature Layer"
            or value.get("geometryType") != "esriGeometryPolygon"):
        raise DefendedArcgisGateError("source name / polygon feature type changed")
    extent = value.get("extent") or {}
    sr = extent.get("spatialReference") or {}
    if (sr.get("wkid") != 25832
            or not all(math.isfinite(extent.get(k, float("nan")))
                       for k in ("xmin", "ymin", "xmax", "ymax"))
            or not 100_000 < extent["xmin"] < extent["xmax"] < 1_000_000
            or not 4_000_000 < extent["ymin"] < extent["ymax"] < 6_000_000):
        raise DefendedArcgisGateError("native original layer must be EPSG:25832 Bavaria")
    fields = {f.get("name") for f in value.get("fields", [])
              if isinstance(f, dict)}
    if not set(CORE_FIELDS).issubset(fields):
        raise DefendedArcgisGateError("Bavaria flood polygon source schema changed")
    if layer_id == 14 and "sl_wtiefe" not in fields:
        raise DefendedArcgisGateError("protected depth category attribute missing")
    advanced = value.get("advancedQueryCapabilities") or {}
    if (not advanced.get("supportsPagination")
            or value.get("maxRecordCount", 0) < 1):
        raise DefendedArcgisGateError("source service no longer supports page-safe reads")
    return {
        "source_url": f"{BASE_URL}/{layer_id}",
        "native_geometry_type": "esriGeometryPolygon",
        "native_crs": "EPSG:25832",
        "output_reprojection_must_be_requested": True,
        "supports_original_feature_pagination": True,
        "layer_identity": value["name"],
        "source_has_protected_depth_class": layer_id == 14,
    }


def validate_provider_count(value: dict) -> int:
    count = value.get("count")
    if type(count) is not int or not 0 < count <= 500_000:
        raise DefendedArcgisGateError("original provider count invalid")
    return count


def validate_row_envelope_count(value: dict, global_count: int) -> int:
    count = value.get("count")
    if type(count) is not int or not 0 <= count <= global_count:
        raise DefendedArcgisGateError("invalid server-side spatial predicate count")
    return count


def _multipolygon_points(coordinates) -> int:
    if not isinstance(coordinates, list) or not coordinates:
        raise DefendedArcgisGateError("source MultiPolygon rings missing")
    seen = 0
    for polygon in coordinates:
        if not isinstance(polygon, list) or not polygon:
            raise DefendedArcgisGateError("invalid polygon part")
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4:
                raise DefendedArcgisGateError("ring shorter than four WGS84 vertices")
            first = ring[0]
            last = ring[-1]
            if first != last:
                raise DefendedArcgisGateError("source GeoJSON polygon ring not closed")
            for point in ring:
                if not isinstance(point, list) or len(point) < 2:
                    raise DefendedArcgisGateError("not a source WGS84 XY pair")
                lon, lat = point[:2]
                if (type(lon) not in (int, float) or type(lat) not in (int, float)
                        or not math.isfinite(lon) or not math.isfinite(lat)
                        or not 5 < lon < 16 or not 46 < lat < 52):
                    raise DefendedArcgisGateError("GeoJSON WGS84 projection/axis order invalid")
                seen += 1
                if seen > MAX_ORIGINAL_GEOJSON_POLYGON_COORDINATES:
                    raise DefendedArcgisGateError("original polygon exceeds bounded sample")
    return seen


def verify_one_reprojected_provider_polygon(value: dict, layer_id: int) -> dict:
    if layer_id not in (10, 14):
        raise DefendedArcgisGateError("only two review-approved polygon sample layers")
    if value.get("type") != "FeatureCollection":
        raise DefendedArcgisGateError("provider returned no GeoJSON FeatureCollection")
    features = value.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise DefendedArcgisGateError("sample cannot prove exactly one source polygon")
    f = features[0]
    geometry = (f or {}).get("geometry") or {}
    props = (f or {}).get("properties") or {}
    if geometry.get("type") != "MultiPolygon":
        raise DefendedArcgisGateError("unexpected original source GeoJSON geometry")
    points = _multipolygon_points(geometry.get("coordinates"))
    if (not isinstance(props.get("sl_gew_nam"), str)
            or props.get("geb_hq") != "HQ 100"
            or not isinstance(props.get("erm_datum"), str)):
        raise DefendedArcgisGateError("original sample polygon attribution/period invalid")
    if layer_id == 14 and (
            not isinstance(props.get("sl_wtiefe"), str) or
            not props["sl_wtiefe"]):
        raise DefendedArcgisGateError("original depth-class missing")
    return {
        "reprojected_sample_crs": "EPSG:4326",
        "returned_geometry": "GeoJSON MultiPolygon",
        "sample_polygon_coordinate_pairs_verified": points,
        "original_source_date_of_sample": props["erm_datum"],
        "source_water_depth_class_is_categorical": layer_id == 14,
        "sample_geometry_not_exported": True,
        "sample_source_feature_id_not_exported": True,
    }


def summarise_no_geometry_protected_attributes(value: dict, expected_count: int) -> dict:
    fs = value.get("features")
    if (not isinstance(fs, list) or len(fs) != expected_count
            or value.get("exceededTransferLimit") is True):
        raise DefendedArcgisGateError("incomplete provider source property population")
    ids = set()
    dates = Counter()
    scenarios = Counter()
    missing_date = 0
    for feature in fs:
        props = feature.get("attributes") if isinstance(feature, dict) else None
        if not isinstance(props, dict):
            raise DefendedArcgisGateError("provider no-geometry attribute row changed")
        identifier = props.get("webgisid")
        if type(identifier) is not int or identifier in ids:
            raise DefendedArcgisGateError("duplicate/missing source object ID")
        ids.add(identifier)
        period = props.get("geb_hq") or ""
        if period not in ("HQ 100", ""):
            raise DefendedArcgisGateError("non HQ100 event class mixed into protected source")
        scenarios[period or "missing"] += 1
        observed = props.get("erm_datum") or ""
        if observed:
            try:
                instant = datetime.strptime(observed, "%d.%m.%Y")
            except ValueError as exc:
                raise DefendedArcgisGateError("unreviewed source polygon determination date") from exc
            dates[str(instant.year)] += 1
        else:
            missing_date += 1
    return {
        "all_protected_polygon_attributes_verified": True,
        "source_feature_count": expected_count,
        "date_year_distribution": dict(sorted(dates.items())),
        "missing_determination_dates": missing_date,
        "source_period_classes": dict(sorted(scenarios.items())),
        "underlying_current_asset_condition_not_proven": True,
    }


def audit_original_service_responses(source: dict[str, dict]) -> dict:
    if set(source) != set(EXPECTED_RESPONSE_FILES):
        raise DefendedArcgisGateError("expected complete provider response contract")
    verified = {}
    counts = {}
    row_counts = {}
    for layer_id in LAYER_IDS:
        verified[layer_id] = verify_layer_metadata(source[f"metadata_{layer_id}"], layer_id)
        counts[layer_id] = validate_provider_count(source[f"count_{layer_id}"])
        row_counts[layer_id] = validate_row_envelope_count(
            source[f"row_count_{layer_id}"], counts[layer_id]
        )
    original_date_summary = summarise_no_geometry_protected_attributes(
        source["attributes_10"], counts[10]
    )
    samples = {
        layer_id: verify_one_reprojected_provider_polygon(
            source[f"sample_{layer_id}"], layer_id
        )
        for layer_id in (10, 14)
    }
    return {
        "profile": PROFILE,
        "provider": "Bayerisches Landesamt fuer Umwelt via UmweltAtlas Bayern",
        "source_base": BASE_URL,
        "original_server_layer_metadata": verified,
        "source_provider_all_features_count": counts,
        "original_server_row5000_bbox": list(ROW5000_ENVELOPE),
        "row5000_envelope_intersection_feature_counts": row_counts,
        "source_attributes_10_no_geometry": original_date_summary,
        "real_reprojected_polygon_samples": samples,
        "official_riverine_wri_depth_pixels_spatially_joined": False,
        "verified_defence_polyline_to_protected_polygon_link": False,
        "source_service_access_proved_not_licensed_republication": True,
        "rights_review_complete": False,
        "data_absence_means_no_risk": False,
        "defended_site_flood_depth_calculated": False,
        "defence_failure_probability_calibrated": False,
        "insurer_exposure_TIV_or_policy_attached": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    files = {name: args.responses_dir / filename
             for name, filename in EXPECTED_RESPONSE_FILES.items()}
    if args.out.resolve() in {p.resolve() for p in files.values()}:
        parser.error("never overwrite original source response file")
    try:
        source = {}
        hashes = {}
        for key, file in files.items():
            source[key], hashes[key] = read_original_json(file)
        report = audit_original_service_responses(source)
        report["original_provider_response_sha256"] = hashes
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n",
                            encoding="utf-8")
    except (OSError, DefendedArcgisGateError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
