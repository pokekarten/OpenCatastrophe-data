#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline EMSR165 2016 flood research scope and product QA; no API calls.

Input is untrusted metadata, NOT authenticated original CEMS bytes.
This never approves acquisition, source rights or CAT model use.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re

ACTIVATION = "EMSR165"
PARIS_AUSTERLITZ_LON_LAT = (2.365510635, 48.844689620)


class ReviewBlocked(ValueError):
    """Invalid or unreviewed input; no inference permitted."""


def _no_duplicates(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ReviewBlocked("duplicate JSON key")
        obj[k] = v
    return obj


def _reject_nonfinite(_value):
    raise ReviewBlocked("non-finite JSON numbers are forbidden")


def load_metadata(path: Path):
    if not path.is_file() or path.stat().st_size > 32768:
        raise ReviewBlocked("input must be one bounded local metadata file")
    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=_no_duplicates,
                          parse_constant=_reject_nonfinite)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewBlocked("invalid strict UTF-8 JSON") from exc


def _utc(value, label):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value
    ):
        raise ReviewBlocked(f"{label} must be complete UTC ISO 8601 with Z")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ReviewBlocked(f"invalid {label} date/time") from exc


def _bounded_number(value, minimum, maximum, label):
    if type(value) not in (int, float):
        raise ReviewBlocked(f"invalid numeric {label}")
    # Compare bounds before isfinite: huge JSON integers may overflow
    # float conversion performed internally by math.isfinite.
    if not minimum <= value <= maximum:
        raise ReviewBlocked(f"{label} outside accepted coordinate bounds")
    if type(value) is float and not math.isfinite(value):
        raise ReviewBlocked(f"nonfinite numeric {label}")
    return value


def _bbox_contains_station(box):
    if not isinstance(box, list) or len(box) != 4:
        raise ReviewBlocked("AOI bbox requires [west,south,east,north]")
    west = _bounded_number(box[0], -180, 180, "west")
    south = _bounded_number(box[1], -90, 90, "south")
    east = _bounded_number(box[2], -180, 180, "east")
    north = _bounded_number(box[3], -90, 90, "north")
    if not west < east or not south < north:
        raise ReviewBlocked("bbox reversed, empty, or antimeridian ambiguity")
    lon, lat = PARIS_AUSTERLITZ_LON_LAT
    return west <= lon <= east and south <= lat <= north


def preflight(candidate):
    if not isinstance(candidate, dict) or set(candidate) != {"activation", "selected_product"}:
        raise ReviewBlocked("exactly activation and selected_product required")
    summary = candidate["activation"]
    if not isinstance(summary, dict):
        raise ReviewBlocked("activation summary must be an object")
    if not {"code", "category", "countries", "n_aois", "n_products",
            "activationTime", "lastUpdate"} <= set(summary):
        raise ReviewBlocked("activation summary lacks required public fields")
    if summary["code"] != ACTIVATION or not isinstance(summary["category"], dict):
        raise ReviewBlocked("wrong activation identity or category structure")
    if summary["category"].get("slug") != "flood":
        raise ReviewBlocked("not the historical flood activation")
    countries = summary["countries"]
    if not isinstance(countries, list) or not any(
        isinstance(x, dict) and x.get("short_name") == "France" for x in countries
    ):
        raise ReviewBlocked("French AOI identity not established")
    # Frozen 2026-11-04 public snapshot, not independent event/day counts.
    if type(summary["n_aois"]) is not int or summary["n_aois"] != 8:
        raise ReviewBlocked("AOI count differs from reviewed snapshot")
    if type(summary["n_products"]) is not int or summary["n_products"] != 21:
        raise ReviewBlocked("product count differs from reviewed snapshot")
    activated = _utc(summary["activationTime"], "activationTime")
    updated = _utc(summary["lastUpdate"], "lastUpdate")
    if activated.isoformat() != "2016-06-01T18:45:00+00:00":
        raise ReviewBlocked("activation time differs from reviewed identity")
    if updated < activated:
        raise ReviewBlocked("lastUpdate precedes activation")

    result = {
        "profile": "cems-emsr165-2016-flood-validation-scope-v0",
        "activation_code": ACTIVATION,
        "activation_metadata_shape_valid": True,
        "provider_product_url_or_bytes_acquired": False,
        "api_execution_authorized_by_repository": False,
        "reported_aois": 8, "reported_products": 21,
        "event_kind": "2016_FLOOD_CEMS_RAPID_MAPPING",
        "aoi_bbox_covers_paris_station": None,
        "image_utc_date_equals_paris_daily_peak_date": None,
        "product_type_suitable_for_extent_comparison": False,
        "product_metadata_shape_valid": False,
        "asset_original_bytes_authenticated": False,
        "source_rights_and_third_party_cleared": False,
        "independent_observed_flood_truth_established": False,
        "model_input_admitted": False,
        "insured_loss_inference_allowed": False,
        "blockers": ["exact_AOI_geometry_missing", "product_version_imagery_missing",
                     "provider_original_bytes_unverified", "API_terms_and_asset_rights_unreviewed"],
    }
    product = candidate["selected_product"]
    if product is None:
        return result
    if not isinstance(product, dict) or set(product) != {
        "activation_code", "aoi_id", "aoi_bbox_wgs84", "product_type",
        "image_acquired_utc", "product_delivered_utc", "product_version",
        "original_vector_sha256", "original_vector_bytes"
    }:
        raise ReviewBlocked("unreviewed/missing selected-product fields")
    if product["activation_code"] != ACTIVATION:
        raise ReviewBlocked("cross-activation product contamination")
    if not isinstance(product["aoi_id"], str) or not re.fullmatch(
        r"[A-Za-z0-9_-]{1,32}", product["aoi_id"]
    ):
        raise ReviewBlocked("invalid AOI identifier")
    product_type = product["product_type"]
    if not isinstance(product_type, str) or product_type not in {"DEL", "GRA", "REF"}:
        raise ReviewBlocked("unknown product class: preserve source semantics")
    inside_paris = _bbox_contains_station(product["aoi_bbox_wgs84"])
    imagery_time = _utc(product["image_acquired_utc"], "image_acquired_utc")
    delivery_time = _utc(product["product_delivered_utc"], "product_delivered_utc")
    if delivery_time < imagery_time:
        raise ReviewBlocked("product delivered before satellite acquisition")
    if type(product["product_version"]) is not int or not 1 <= product["product_version"] <= 100:
        raise ReviewBlocked("invalid product version")
    sha = product["original_vector_sha256"]
    size = product["original_vector_bytes"]
    if sha is not None and (not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{64}", sha)):
        raise ReviewBlocked("invalid reported original SHA-256 format")
    if size is not None and (type(size) is not int or not 0 < size <= 5_000_000_000):
        raise ReviewBlocked("invalid original byte count")
    if (sha is None) != (size is None):
        raise ReviewBlocked("partial original-file receipt")
    # Calendar equality is not an hour-level event match or physical flood extent.
    on_utc_peak_day = imagery_time.date().isoformat() == "2016-06-03"
    result["aoi_bbox_covers_paris_station"] = inside_paris
    result["image_utc_date_equals_paris_daily_peak_date"] = on_utc_peak_day
    result["product_type_suitable_for_extent_comparison"] = product_type == "DEL"
    result["product_metadata_shape_valid"] = True
    result["reported_original_sha256_format_valid"] = sha is not None
    result["blockers"] = ["AOI_geometry_only_bbox_not_original_proof",
                          "imagery_time_unverified_against_original_provider_and_local_day",
                          "reported_SHA_format_not_original_byte_authentication",
                          "API_terms_and_asset_rights_unreviewed"]
    if not inside_paris:
        result["blockers"].append("candidate_AOI_does_not_contain_paris_station")
    if product_type != "DEL":
        result["blockers"].append("not_an_extent_delineation_product")
    if not on_utc_peak_day:
        result["blockers"].append("not_imaged_on_paris_peak_calendar_day")
    if sha is None:
        result["blockers"].append("no_original_vector_receipt_even_reported")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-json", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = preflight(load_metadata(args.metadata_json))
    except ReviewBlocked as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
