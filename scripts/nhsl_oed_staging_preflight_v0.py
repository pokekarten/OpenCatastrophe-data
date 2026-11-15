# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed NHSL v1.0 settled-area -> Oasis OED staging crosswalk.

This is a one-row, offline diagnostic, NOT an OED location/account file exporter.
No source-data rights, individual building locations, coverage, or insured TIV
may be inferred from the aggregate NHSL source-shaped input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

# Exact source dictionary is public NHSL provider-owned data-documentation code:
# https://github.com/OpenDRR/national-human-settlement/blob/main/docs/_data/nhsl_physical_exposure_attributes.yml
# Git blob SHA fetched 2026-11-04; never claim a remote runtime verification.
NHSL_DICTIONARY_BLOB_SHA = "d54f926c6ee1309f8c8c1ec864820bcc4428ea88"
OED_SPEC_SOURCE = "https://github.com/OasisLMF/ODS_OpenExposureData/blob/main/OpenExposureData/OEDInputFields.csv"
OED_SPEC_BLOB_SHA = "8351e6fbb2efa2f6f55d61bab82853b42f6b2a97"
OED_TARGET_VERSION = "5.0.0"
SOURCE_CANDIDATE = "can.nrcan.nhsl.physical-exposure.2016-2020"
REQUIRED_FIELDS = (
    "Sauid", "E_SauidLat", "E_SauidLon", "Et_BldgNum", "Et_BldgArea",
    "Et_StrValue", "Et_NStrValue", "Et_BldgValue", "Et_ContValue",
    "Et_AssetValue",
)
FINANCIAL_FIELDS = (
    "Et_StrValue", "Et_NStrValue", "Et_BldgValue", "Et_ContValue",
    "Et_AssetValue",
)
BLOCKED_INSURANCE_FIELDS = frozenset((
    "AccNumber", "PortNumber", "PolNumber", "LocPerilsCovered",
    "BuildingTIV", "ContentsTIV", "OtherTIV", "BITIV",
    "LocCurrency", "OEDVersion",
))
MAX_JSON_BYTES = 65_536
MAX_VALUE_CAD = Decimal("1000000000000000")
CENT_TOLERANCE_CAD = Decimal("0.02")


class NHSLStagingError(ValueError):
    """Source-shaped input cannot safely be inspected as aggregate exposure."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise NHSLStagingError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise NHSLStagingError(f"invalid non-finite constant: {value}")


def _decimal(value: object, field: str, *, bound: Decimal = MAX_VALUE_CAD) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise NHSLStagingError(f"{field}: finite numeric value required")
    raw = str(value)
    if len(raw) > 48:
        raise NHSLStagingError(f"{field}: numeric value too long")
    try:
        result = Decimal(raw)
    except InvalidOperation as exc:
        raise NHSLStagingError(f"{field}: invalid number") from exc
    if not result.is_finite() or abs(result) > bound:
        raise NHSLStagingError(f"{field}: out of finite range")
    return result


def examine_row(row: object) -> dict[str, Any]:
    """Check one source-shaped row; return non-admitted evidence, not insurance OED."""
    if not isinstance(row, dict):
        raise NHSLStagingError("row must be a JSON object")
    missing = set(REQUIRED_FIELDS) - set(row)
    if missing:
        raise NHSLStagingError("missing NHSL source fields: " + ", ".join(sorted(missing)))
    forbidden = BLOCKED_INSURANCE_FIELDS & set(row)
    if forbidden:
        raise NHSLStagingError("insurance/OED terms supplied as source fields: " + ", ".join(sorted(forbidden)))
    sauid = row["Sauid"]
    if not isinstance(sauid, str) or not re.fullmatch(r"[a-zA-Z0-9._-]{1,48}", sauid):
        raise NHSLStagingError("Sauid must preserve a bounded source identifier as text")
    lat = _decimal(row["E_SauidLat"], "E_SauidLat", bound=Decimal("90"))
    lon = _decimal(row["E_SauidLon"], "E_SauidLon", bound=Decimal("180"))
    if not Decimal("40") <= lat <= Decimal("85") or not Decimal("-145") <= lon <= Decimal("-50"):
        raise NHSLStagingError("settlement centroid outside conservative Canada bounds")
    buildings = _decimal(row["Et_BldgNum"], "Et_BldgNum")
    sqft = _decimal(row["Et_BldgArea"], "Et_BldgArea")
    if buildings < 0 or sqft < 0:
        raise NHSLStagingError("negative building count or area")
    components = {name: _decimal(row[name], name) for name in FINANCIAL_FIELDS}
    if any(v < 0 for v in components.values()):
        raise NHSLStagingError("negative replacement cost component")
    if buildings == 0 and (sqft > 0 or any(v > 0 for v in components.values())):
        raise NHSLStagingError("positive area/value with zero estimated buildings")
    if buildings > 0 and sqft == 0:
        raise NHSLStagingError("positive buildings but missing finished floor area")
    if abs(components["Et_StrValue"] + components["Et_NStrValue"] - components["Et_BldgValue"]) > CENT_TOLERANCE_CAD:
        raise NHSLStagingError("building value != structural + nonstructural values")
    if abs(components["Et_BldgValue"] + components["Et_ContValue"] - components["Et_AssetValue"]) > CENT_TOLERANCE_CAD:
        raise NHSLStagingError("asset value != building + contents values")
    # These are modelled stock quantities at a settlement-area aggregation level.
    # OED NumberOfBuildings is an integer; aggregate estimated count can be
    # non-integral. Never auto-cast to int or reinterpret as a single roof.
    non_integral_buildings = buildings != buildings.to_integral_value()
    response = {
        "crosswalk": "nhsl-v1.0-settlement-aggregate-to-oed-staging-v0",
        "source_candidate_id": SOURCE_CANDIDATE,
        "source_dictionary_blob_sha": NHSL_DICTIONARY_BLOB_SHA,
        "oed_target_version": OED_TARGET_VERSION,
        "oed_field_reference_blob_sha": OED_SPEC_BLOB_SHA,
        "input_provenance": "source_shaped_one_row_only_unverified_release_bytes",
        "settled_area_source_id": sauid,
        "settled_area_centroid": {
            "latitude": str(lat), "longitude": str(lon),
            "spatial_role": "settled_area_polygon_centroid_not_individual_building_location",
        },
        "aggregated_buildings_estimated": str(buildings),
        "aggregated_building_count_nonintegral": non_integral_buildings,
        "aggregated_finished_area_sqft": str(sqft),
        "monetary_unit": "CAD",
        "monetary_base_year": 2019,
        "replacement_cost_components_cad_2019": {
            "structural": str(components["Et_StrValue"]),
            "nonstructural": str(components["Et_NStrValue"]),
            "buildings_total": str(components["Et_BldgValue"]),
            "contents": str(components["Et_ContValue"]),
            "assets_total": str(components["Et_AssetValue"]),
        },
        "oed_candidate_field_lineage": {
            "Latitude": "E_SauidLat (polygon centroid proxy, not insured site)",
            "Longitude": "E_SauidLon (polygon centroid proxy, not insured site)",
            "BuildingTIV": "Et_BldgValue (modelled replacement-cost proxy ONLY, not insured TIV)",
            "ContentsTIV": "Et_ContValue (modelled replacement-cost proxy ONLY, not insured TIV)",
            "NumberOfBuildings": "Et_BldgNum (aggregate estimate, may be non-integral)",
            "FloorArea": "Et_BldgArea (aggregate square feet, not one location floor area)",
        },
        "unavailable_from_nhsl": [
            "PortNumber", "AccNumber", "LocNumber_as_insured_location",
            "LocPerilsCovered", "policy_and_reinsurance_terms",
            "insured_limits_and_deductibles", "insured_BuildingTIV",
            "insured_ContentsTIV", "OtherTIV", "BITIV",
            "individual_building_coordinates", "OED_occupancy_or_construction_code",
        ],
        "source_bytes_acquired_by_this_program": False,
        "actual_dataset_version_and_license_verified": False,
        "site_level_geocoding_verified": False,
        "insurance_coverage_verified": False,
        "source_rights_reviewed": False,
        "scientific_fitness_reviewed": False,
        "model_input_approved": False,
        "can_export_oed_loc_or_account": False,
        "admission_status": "not_admitted",
    }
    return response


def inspect_file(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
        raise NHSLStagingError("missing or oversized source-shaped JSON file")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_JSON_BYTES:
        raise NHSLStagingError("empty or oversized source-shaped JSON file")
    try:
        row = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object,
                         parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NHSLStagingError("invalid UTF-8 JSON input") from exc
    return examine_row(row)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-json", type=Path, required=True,
                        help="One local source-shaped row in JSON, never source archive")
    args = parser.parse_args(argv)
    try:
        receipt = inspect_file(args.row_json)
    except (NHSLStagingError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
