#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline bridge of a *synthetic* Census parish point receipt to OpenCat region labels.

No downloaded geography, imported private model, model run, insured exposure,
source-identity admission or right to use historical actual property records.
This checks receipt structure only; caller supplied metadata is not original proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

PROFILE = "OC_CENSUS_2026_LA_SYNTHETIC_POINT_CROSSWALK_V0"
BRIDGE_PROFILE = "OC_CENSUS_2026_LA_TO_OPENCAT_SYNTHETIC_REGION_SHAPE_V0"
NAMESPACE = "US_CENSUS_TIGER_2026"
ORIGINAL_SHA = "b527c9ba7aeb8f17ef118f026eae5e5a938aa1d00b873bc32342d0dce59321c0"
ASSIGNMENT_SHA = "1f54b0a387831fc7a20ba801632284142be685f03b0823ab6d72df60d8e4b57f"
SAMPLE_GEOIDS = ("22051", "22071", "22087")
MAX_BYTES = 16384
RECEIPT_FIELDS = {
    "profile", "original_source_sha256", "source_namespace", "boundary_year",
    "country_iso2", "country_iso3", "synthetic_parent_regions",
    "original_validated_parish_polygon_count", "source_derived_synthetic_point_count",
    "synthetic_points_with_exactly_one_polygon_interior",
    "points_from_polygon_representative_point_not_real_assets",
    "synthetic_region_assignment_sha256", "sample_region_assignments",
    "original_source_geometry_persisted", "original_point_coordinates_emitted",
    "actual_asset_geolocation_demonstrated", "insured_TIV_or_policy_terms_verified",
    "native_OpenCat_region_loss_model_executed", "rights_and_scientific_admission_granted",
}
ASSIGNMENT_FIELDS = {"asset_id", "country_code", "subdivisions"}


class Blocked(ValueError):
    """Reject any claim not pinned to exact fake, geometry-derived reference sites."""


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for k, v in pairs:
        if k in out:
            raise Blocked("duplicate original receipt JSON key")
        out[k] = v
    return out


def _nonfinite(_: str) -> None:
    raise Blocked("non-finite JSON value")


def verify_receipt(original: bytes) -> dict[str, object]:
    if type(original) is not bytes or not 0 < len(original) <= MAX_BYTES:
        raise Blocked("empty or oversized synthetic source receipt")
    try:
        x = json.loads(original.decode("utf-8"), object_pairs_hook=_unique,
                       parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Blocked("invalid strict receipt JSON") from exc
    if type(x) is not dict or set(x) != RECEIPT_FIELDS:
        raise Blocked("unexpected original receipt fields")
    expected = {
        "profile": PROFILE, "original_source_sha256": ORIGINAL_SHA,
        "source_namespace": NAMESPACE, "boundary_year": 2026,
        "country_iso2": "US", "country_iso3": "USA",
        "synthetic_parent_regions": ["US", "US-LA"],
        "original_validated_parish_polygon_count": 64,
        "source_derived_synthetic_point_count": 64,
        "synthetic_points_with_exactly_one_polygon_interior": 64,
        "points_from_polygon_representative_point_not_real_assets": True,
        "synthetic_region_assignment_sha256": ASSIGNMENT_SHA,
        "original_source_geometry_persisted": False,
        "original_point_coordinates_emitted": False,
        "actual_asset_geolocation_demonstrated": False,
        "insured_TIV_or_policy_terms_verified": False,
        "native_OpenCat_region_loss_model_executed": False,
        "rights_and_scientific_admission_granted": False,
    }
    for key, val in expected.items():
        if type(x[key]) is not type(val) or x[key] != val:
            raise Blocked("unverified synthetic crosswalk receipt: " + key)
    rows = x["sample_region_assignments"]
    if type(rows) is not list or len(rows) != len(SAMPLE_GEOIDS):
        raise Blocked("expected only three fixed synthetic sample region labels")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not dict or set(row) != ASSIGNMENT_FIELDS:
            raise Blocked("unexpected RegionAssignment fields")
        asset_id = row["asset_id"]
        if type(asset_id) is not str or not re.fullmatch(r"synthetic_sample_22[0-9]{3}", asset_id):
            raise Blocked("not a synthetic parish-derived asset ID")
        geoid = asset_id.rsplit("_", 1)[-1]
        if geoid not in SAMPLE_GEOIDS or geoid in seen:
            raise Blocked("not a fixed distinct official parish example")
        seen.add(geoid)
        if (type(row["country_code"]) is not str or row["country_code"] != "US"
                or type(row["subdivisions"]) is not list
                or row["subdivisions"] != ["US-LA", "US-LA-" + geoid]):
            raise Blocked("OpenCat country/subdivision nesting mismatch")
    if seen != set(SAMPLE_GEOIDS):
        raise Blocked("missing synthetic source parish samples")
    output = [
        {"asset_id": "synthetic_sample_" + geoid,
         "country_code": "US",
         "subdivisions": ["US-LA", "US-LA-" + geoid]}
        for geoid in SAMPLE_GEOIDS
    ]
    return {
        "profile": BRIDGE_PROFILE,
        "private_target_contract": "OpenCat PR16 RegionAssignment(asset_id,country_code,tuple(subdivisions))",
        "private_target_code_identity_checked_by_this_script": False,
        "source_receipt_original_bytes_independently_authenticated": False,
        "sample_synthetic_region_labels": output,
        "sample_count": len(output),
        "full_64_synthetic_assignments_available_from_this_receipt": False,
        "model_loss_bearing_asset_roster_matched": False,
        "region_rollup_executed": False,
        "actual_property_geolocation_verified": False,
        "source_license_and_scientific_admission_verified": False,
        "insured_loss_or_real_model_run_proven": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-crosswalk-receipt", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        with args.synthetic_crosswalk_receipt.open("rb") as f:
            raw = f.read(MAX_BYTES + 1)
        result = verify_receipt(raw)
    except (Blocked, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
