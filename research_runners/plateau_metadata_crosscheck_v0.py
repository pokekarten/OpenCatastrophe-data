# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, offline cross-check of two independently supplied PLATEAU catalogues.

REST and GraphQL views are NOT independent observations of physical buildings.
No HTTP request, original ZIP read, model admission, licence decision, or asset join.
The source preflight validates each metadata response before comparison.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__:
    from .plateau_citygml_catalogue_preflight_v0 import (
        CataloguePreflightError,
        GRAPHQL_MAX_INPUT_BYTES,
        MAX_INPUT_BYTES,
        TARGET_CITY_CODE,
        TARGET_YEAR,
        _reject_nonfinite,
        _strict_pairs,
        preflight_bytes,
        preflight_graphql_bytes,
        read_local_metadata,
    )
else:
    from plateau_citygml_catalogue_preflight_v0 import (
        CataloguePreflightError,
        GRAPHQL_MAX_INPUT_BYTES,
        MAX_INPUT_BYTES,
        TARGET_CITY_CODE,
        TARGET_YEAR,
        _reject_nonfinite,
        _strict_pairs,
        preflight_bytes,
        preflight_graphql_bytes,
        read_local_metadata,
    )


def _strict_json(raw: bytes) -> dict:
    # Both preflight functions have already bounded and checked these bytes;
    # repeat strict decoding to compare the validated records without echoing
    # any provider URL or native dataset identifier.
    payload = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_strict_pairs,
        parse_constant=_reject_nonfinite,
    )
    assert isinstance(payload, dict)
    return payload


def crosscheck_bytes(rest_raw: bytes, graphql_raw: bytes) -> dict[str, object]:
    """Return a non-admission metadata receipt only if common fields agree.

    The two API projections can stem from a shared upstream catalogue. Agreement
    is neither independent corroboration nor evidence that an asset exists.
    """
    rest = preflight_bytes(rest_raw)
    graphql = preflight_graphql_bytes(graphql_raw)

    rest_rows = _strict_json(rest_raw)["citygml"]
    candidates = [
        row for row in rest_rows
        if isinstance(row, dict) and row.get("city_code") == TARGET_CITY_CODE
        and row.get("year") == TARGET_YEAR
    ]
    # preflight_bytes already enforces uniqueness; keep the contract explicit.
    if len(candidates) != 1:
        raise CataloguePreflightError("cross-check target REST record is ambiguous")
    rest_row = candidates[0]
    graphql_row = _strict_json(graphql_raw)["data"]["citygmlDatasets"][0]

    if rest["registration_year"] != graphql["registration_year"]:
        raise CataloguePreflightError("REST and GraphQL registration years disagree")
    if set(rest_row["feature_types"]) != set(graphql_row["featureTypes"]):
        raise CataloguePreflightError("REST and GraphQL feature types disagree")
    if rest_row["url"] != graphql_row["url"]:
        raise CataloguePreflightError("REST and GraphQL original CMS URL metadata disagree")
    if not (rest["fixed_year_composite_url_present"] and graphql["fixed_year_composite_url_present"]):
        raise CataloguePreflightError("both views must expose an explicit fixed-year composite URL")
    if rest_row["composite_url"] != graphql_row["compositeUrl"]:
        raise CataloguePreflightError("REST and GraphQL fixed-year composite URLs disagree")

    return {
        "source_id": "jp.mlit.plateau.citygml.3d-city-models",
        "target_city_code": TARGET_CITY_CODE,
        "target_fiscal_year": TARGET_YEAR,
        "registration_year": rest["registration_year"],
        "metadata_crosscheck": "common_fields_structurally_consistent",
        "fields_compared": [
            "municipality_code",
            "fiscal_year",
            "registration_year",
            "building_feature_type_set",
            "original_cms_url_exact_match",
            "fixed_fiscal_year_composite_url_exact_match",
        ],
        "rest_metadata_sha256": rest["input_sha256"],
        "graphql_metadata_sha256": graphql["input_sha256"],
        "rest_metadata_byte_count": rest["input_byte_count"],
        "graphql_metadata_byte_count": graphql["input_byte_count"],
        "rest_cms_size_metadata_known": rest["cms_original_size_metadata_known"],
        "graphql_cms_size_not_selected": True,
        "gspatial_archive_metadata_not_comparable_to_cms": True,
        "same_upstream_possible": True,
        "independent_building_verification": False,
        "provider_original_bytes_verified": False,
        "licence_review_completed": False,
        "model_input_approved": False,
        "provider_network_access": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rest-input", required=True, type=Path)
    parser.add_argument("--graphql-input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        rest = read_local_metadata(args.rest_input, MAX_INPUT_BYTES)
        graphql = read_local_metadata(args.graphql_input, GRAPHQL_MAX_INPUT_BYTES)
        result = crosscheck_bytes(rest, graphql)
    except CataloguePreflightError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
