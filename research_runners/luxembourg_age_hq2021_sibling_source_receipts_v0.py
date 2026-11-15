# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact published original AGE HQ10 / HQext sibling archive source receipts.

Uses the same fail-closed ZIP/CRC/DBF/SHP structural gate as tested HQ100,
but freezes each sibling's *own* provider ZIP URL and SHA-1. No feature
coordinates, depth observations or source ID/locations are exported.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    inspect, HQ100OriginalError,
)

SOURCES = {
    "hq10": {
        "resource_id": "af0df0ea-f4a0-475c-9dc1-d52a391125d9",
        "url": ("https://download.data.public.lu/resources/"
                "flood-hazard-maps-10-year-flood/20220613-155024/hwgk2021-hq10.zip"),
        "sha1": "08c75a51c0d2f42b9f95530494320ec085203d89",
        "catalogue": "https://data.public.lu/en/datasets/flood-hazard-maps-10-year-flood/",
    },
    "hqext": {
        "resource_id": "4bdd0d13-e783-4d7b-99d6-c4274de404c8",
        "url": ("https://download.data.public.lu/resources/"
                "flood-hazard-maps-extreme/20220613-154504/hwgk2021-hqext.zip"),
        "sha1": "a32da12e9c41275466c07d51fff72a8c518eaf26",
        "catalogue": "https://data.public.lu/en/datasets/flood-hazard-maps-extreme/",
    },
}


def summarize(scenario: str, preflight: dict) -> dict:
    """Label observed structure according to the verified sibling's catalogue."""
    if scenario not in SOURCES or not isinstance(preflight, dict):
        raise HQ100OriginalError("Unknown original AGE source scenario")
    if preflight.get("original_zip_sha1_matches_publisher") is not True or (
            preflight.get("shp_records_match_dbf_records") is not True):
        raise HQ100OriginalError("Original sibling archive not verified")
    members = preflight.get("format_header_inventory_only")
    if not isinstance(members, list):
        raise HQ100OriginalError("Missing original sibling archive structural inventory")
    dbfs = [x for x in members if x.get("format") == ".dbf"]
    shps = [x for x in members if x.get("format") == ".shp"]
    if len(dbfs) != 1 or len(shps) != 1:
        raise HQ100OriginalError("Expected one independently observed SHP/DBF pair")
    dbf, shp = dbfs[0], shps[0]
    if (shp.get("shp_shape_type_code") != 5
            or not isinstance(shp.get("shp_total_polygon_ring_parts"), int)
            or not isinstance(shp.get("shp_total_coordinate_pairs_skipped_without_decoding"), int)
            or dbf.get("dbf_declared_records") != shp.get("shp_polygon_record_count")):
        raise HQ100OriginalError("Original sibling format or record count mismatch")
    fields = [x["name"] for x in dbf["dbf_field_schema"]]
    if not fields or any(not isinstance(x, str) for x in fields):
        raise HQ100OriginalError("Invalid original DBF field names")
    catalog = SOURCES[scenario]
    return {
        "profile": "lu-age-2021-flood-scenario-sibling-original-format-v0",
        "scenario": scenario,
        "official_dataset_url": catalog["catalogue"],
        "official_zip_url": catalog["url"],
        "official_resource_id": catalog["resource_id"],
        "publisher_sha1_match": True,
        "observed_sha256": preflight["original_zip_sha256_observed"],
        "original_zip_bytes": preflight["original_zip_bytes"],
        "archive_member_count": preflight["archive_member_count"],
        "source_shp_type_code": shp["shp_shape_type_code"],
        "source_polygon_records": shp["shp_polygon_record_count"],
        "source_dbf_records": dbf["dbf_declared_records"],
        "original_source_ring_parts": shp["shp_total_polygon_ring_parts"],
        "source_coordinates_skipped_without_reading": (
            shp["shp_total_coordinate_pairs_skipped_without_decoding"]),
        "original_dbf_field_names_only": fields,
        "numeric_depth_semantics_verified": False,
        "shp_full_topology_or_axis_verified": False,
        "source_flood_area_versus_other_scenarios_ordering_verified": False,
        "original_source_coordinates_or_depth_values_exported": False,
        "CAT_model_input_admitted": False,
        "source_provider_bytes_saved_to_git_or_neon": False,
    }


def audit(path: Path, *, scenario: str) -> dict:
    if scenario not in SOURCES:
        raise HQ100OriginalError("Unsupported source scenario")
    validated = inspect(path, expected_sha1=SOURCES[scenario]["sha1"])
    return summarize(scenario, validated)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=tuple(SOURCES), required=True)
    parser.add_argument("--source-zip", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.source_zip, scenario=args.scenario),
                         indent=2, sort_keys=True, allow_nan=False))
    except (OSError, HQ100OriginalError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
