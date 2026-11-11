# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, research-only QA of EA *observed* 3.3%-AEP OGC feature labels.

Accept exactly one saved FeatureCollection response (limit=1) from the
present-day defended river/sea layer. Do not fetch it, store feature geometry,
join buildings, infer dry depth from unavailable, or calculate loss/AEP/OEP.
The fixed vocabulary was observed from bounded original provider queries on
2026-11-11; this is not an approval of source assets for production use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MAX_BYTES = 65_536
COLLECTION = "Rivers_1in30_Sea_1in30_defended_depths"
FEATURE_PREFIX = COLLECTION + "."
BANDS_MM: dict[str, tuple[int | None, int | None]] = {
    "<150mm": (None, 150),
    "150-300mm": (150, 300),
    "300-600mm": (300, 600),
    "600-900mm": (600, 900),
    "900-1200mm": (900, 1200),
    "1200-2300mm": (1200, 2300),
    ">2300mm": (2300, None),
}
MISSING_BAND = "unavailable"
SOURCES = frozenset(("river", "sea", "rivers and sea", "unavailable"))
PROPERTY_KEYS = frozenset(("depth_band", "flood_source", "shape_length", "shape_area"))


class FeatureLabelBlocked(ValueError):
    """Unknown vocabulary or unsafe/unbounded original response."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FeatureLabelBlocked("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise FeatureLabelBlocked("non-finite JSON value")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise FeatureLabelBlocked("overflowed JSON number")
    return parsed


def inspect_original_label_response(raw: bytes) -> dict[str, object]:
    """Report bounded categorical facts, without outputting feature geometry."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise FeatureLabelBlocked("empty or unbounded original response")
    try:
        doc = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_nonfinite,
            parse_float=_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FeatureLabelBlocked("malformed UTF-8 feature JSON") from exc
    if type(doc) is not dict or doc.get("type") != "FeatureCollection":
        raise FeatureLabelBlocked("expected one OGC FeatureCollection")
    feats = doc.get("features")
    if (
        type(feats) is not list or len(feats) != 1
        or type(doc.get("numberReturned")) is not int
        or doc["numberReturned"] != 1
        or type(doc.get("numberMatched")) is not int
        or doc["numberMatched"] < 1
    ):
        raise FeatureLabelBlocked("must contain exactly one returned feature")
    feature = feats[0]
    if (
        type(feature) is not dict or feature.get("type") != "Feature"
        or type(feature.get("id")) is not str
        or not feature["id"].startswith(FEATURE_PREFIX)
    ):
        raise FeatureLabelBlocked("wrong depth collection feature identity")
    props = feature.get("properties")
    if type(props) is not dict or frozenset(props) != PROPERTY_KEYS:
        raise FeatureLabelBlocked("unexpected provider attribute inventory")
    band, source = props["depth_band"], props["flood_source"]
    if type(band) is not str or band not in (*BANDS_MM, MISSING_BAND):
        raise FeatureLabelBlocked("unverified raw depth_band lexical value")
    if type(source) is not str or source not in SOURCES:
        raise FeatureLabelBlocked("unverified raw flood_source lexical value")
    if any(type(props[k]) not in (int, float, type(None)) for k in ("shape_length", "shape_area")):
        raise FeatureLabelBlocked("malformed area/length numeric metadata")
    geometry = feature.get("geometry")
    if type(geometry) is not dict or geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise FeatureLabelBlocked("unsupported original depth geometry type")
    # Presence and type do not validate the CRS or polygon; coordinates must
    # never enter this report. Field units, area and exact boundary inclusivity
    # are not established by this lexical preflight.
    is_missing = band == MISSING_BAND
    low, high = (None, None) if is_missing else BANDS_MM[band]
    return {
        "contract": "EA-DEFENDED-3P3-ORIGINAL-LABEL-QA-v0",
        "collection": COLLECTION,
        "source_body_bytes": len(raw),
        "source_body_sha256": hashlib.sha256(raw).hexdigest(),
        "source_authenticity_proven_by_this_parser": False,
        "depth_band": band,
        "flood_source": source,
        "depth_band_missing": is_missing,
        "flood_source_missing": source == "unavailable",
        "nominal_lower_boundary_mm": low,
        "nominal_upper_boundary_mm": high,
        "lower_boundary_inclusive_verified": False,
        "upper_boundary_inclusive_verified": False,
        "unbounded_endpoint_is_not_zero_depth": True,
        "unknown_or_missing_coverage_is_not_dry": True,
        "depth_band_class_vocabulary_observed_on_provider": True,
        "raw_feature_source_and_release_authenticity_verified": False,
        "geometry_coordinates_reported": False,
        "geometry_topology_verified": False,
        "geometry_crs_verified": False,
        "shape_area_and_length_units_verified": False,
        "physical_depth_at_individual_building_verified": False,
        "representative_depth_mm": None,
        "estimated_damage_ratio": None,
        "commercial_asset_rights_approved": False,
        "model_data_admitted": False,
        "provider_requests_performed": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as f:
            raw = f.read(MAX_BYTES + 1)
        result = inspect_original_label_response(raw)
    except (OSError, FeatureLabelBlocked) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
