#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed scientific screen of a bounded NSI 2026 GeoJSON sample.

Only consumes caller-supplied bytes after a separate authorised acquisition.
No HTTP, discovery, credentials, original-row logging, admission or publication.
Official field semantics: USACE NSI 2026 public technical documentation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SOURCE_ID = "usace.nsi.base.2026"
MAX_BYTES = 1_048_576
MAX_FEATURES = 256


class NSI2026SampleBlocked(ValueError):
    """Malformed, ambiguous or unsafe source-bound local sample."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise NSI2026SampleBlocked("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_nonfinite(_: str) -> None:
    raise NSI2026SampleBlocked("non-finite JSON numeric value")


def _number(value: Any, name: str, *, minimum: float | None = None) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise NSI2026SampleBlocked(f"invalid {name} number")
    if minimum is not None and value < minimum:
        raise NSI2026SampleBlocked(f"negative {name} value")
    return float(value)


def inspect_nsi_2026_geojson(original: bytes) -> dict[str, Any]:
    """Return aggregate-only screen; never assert data rights or CAT admission."""
    if type(original) is not bytes or not (0 < len(original) <= MAX_BYTES):
        raise NSI2026SampleBlocked("input bytes exceed fixed size bound")
    try:
        doc = json.loads(
            original.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NSI2026SampleBlocked("not strict UTF-8 GeoJSON") from exc
    if type(doc) is not dict or doc.get("type") != "FeatureCollection" or "error" in doc:
        raise NSI2026SampleBlocked("not a GeoJSON FeatureCollection")
    features = doc.get("features")
    if type(features) is not list or not 1 <= len(features) <= MAX_FEATURES:
        raise NSI2026SampleBlocked("invalid bounded feature count")
    seen_ids: set[int] = set()
    footprint_ids: set[str] = set()
    shared_footprints = 0
    missing_fullrep = 0
    missing_depreciated = 0
    counterintuitive_valuation_pairs = 0
    for feature in features:
        if type(feature) is not dict or feature.get("type") != "Feature":
            raise NSI2026SampleBlocked("invalid GeoJSON Feature")
        geometry = feature.get("geometry")
        props = feature.get("properties")
        if type(geometry) is not dict or geometry.get("type") != "Point" or type(props) is not dict:
            raise NSI2026SampleBlocked("NSI Base structure must have a point and properties")
        coords = geometry.get("coordinates")
        if type(coords) is not list or len(coords) != 2:
            raise NSI2026SampleBlocked("point must have exactly two WGS84 coordinates")
        lon, lat = _number(coords[0], "longitude"), _number(coords[1], "latitude")
        x, y = _number(props.get("x"), "x"), _number(props.get("y"), "y")
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise NSI2026SampleBlocked("point outside WGS84 coordinate bounds")
        if abs(lon - x) > 0.000001 or abs(lat - y) > 0.000001:
            raise NSI2026SampleBlocked("GeoJSON coordinates do not match NSI x/y")
        fd_id = props.get("fd_id")
        if type(fd_id) is not int or fd_id < 0 or fd_id in seen_ids:
            raise NSI2026SampleBlocked("missing, repeated or invalid NSI fd_id")
        seen_ids.add(fd_id)
        footprint = props.get("ftprntid")
        if footprint is not None:
            if type(footprint) is not str or len(footprint) > 256:
                raise NSI2026SampleBlocked("invalid footprint identifier")
            if footprint in footprint_ids:
                shared_footprints += 1  # Stacked structures are not duplicate fd_ids.
            footprint_ids.add(footprint)
        fullrep = props.get("fullrep")
        depreciated = props.get("val_struct")
        if fullrep is None:
            missing_fullrep += 1  # Missing is never zero-imputed.
        else:
            fullrep = _number(fullrep, "fullrep", minimum=0)
        if depreciated is None:
            missing_depreciated += 1
        else:
            depreciated = _number(depreciated, "val_struct", minimum=0)
        if fullrep is not None and depreciated is not None and depreciated > fullrep:
            counterintuitive_valuation_pairs += 1  # Flag, do not modify publisher data.
    return {
        "schema": "usace-nsi-2026-bounded-geojson-scientific-screen-v0",
        "source_id": SOURCE_ID,
        "sample_byte_count": len(original),
        "input_byte_sha256": hashlib.sha256(original).hexdigest(),
        "feature_count": len(features),
        "unique_fd_id_count": len(seen_ids),
        "shared_footprint_extra_records": shared_footprints,
        "missing_fullrep_count": missing_fullrep,
        "missing_val_struct_count": missing_depreciated,
        "val_struct_exceeds_fullrep_count": counterintuitive_valuation_pairs,
        "field_price_level": "2025-08 (USACE NSI 2026 Base)",
        "coordinate_reference": "WGS84 longitude/latitude",
        "valuation_caution": "fullrep and val_struct are distinct estimates, not insured TIV",
        "provider_bytes_persisted": False,
        "provider_network_request_performed": False,
        "legal_or_model_admission_verified": False,
        "source_native_original_receipt_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geojson", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.geojson.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        result = inspect_nsi_2026_geojson(raw)
    except (OSError, NSI2026SampleBlocked):
        parser.exit(2, "BLOCKED: NSI 2026 sample size/identity/science preflight\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
