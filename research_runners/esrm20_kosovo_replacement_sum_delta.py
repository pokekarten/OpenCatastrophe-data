#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Compare *national* Kosovo residential replacement-cost sums across releases.

This is a standalone, source-bound diagnostic; it does not replace or modify the
existing strict source/runtime comparison action. Reuse that worker's two fixed,
previously receipted ESRM20 CSV inputs and exact bridge/schema checks. Calculate
one new scientific quantity, source TOTAL_REPL_COST_EUR sum minus runtime
OpenQuake 'structural' cost sum, using the existing trap-on-rounding Decimal
context. Emit only the signed *difference*, never either provider cost total,
individual country asset rows or raw provider bytes.

The OpenQuake 'structural' key carries total replacement cost in this runtime
lane; this is not an insured value or a structural-component-only valuation.
Numerical closeness of the two source totals cannot prove the denominator used
to produce the separate *published* ESRM20 Kosovo Residential AALR.
"""

from __future__ import annotations

import json
from decimal import Decimal, Inexact, Rounded, localcontext
from typing import Any

from scripts import compare_esrm20_kosovo_exposure_runtime as compare
from scripts import profile_efehr_kosovo_exposure_value_spatial as source_value
from scripts import profile_efehr_kosovo_exposure as source_profile
from scripts import profile_esrm20_runtime_residential_csv as runtime_profile

SCHEMA_VERSION = "oc-eq1-kosovo-national-replacement-sum-bridge-v1"
SOURCE_FIELD = "TOTAL_REPL_COST_EUR"
RUNTIME_FIELD = "structural"


class ReplacementSumBridgeError(RuntimeError):
    """Exact receipt, asset bridge or Decimal arithmetic cannot be trusted."""


def _signed_delta(
    source_rows: list[dict[str, str]],
    runtime_rows: list[dict[str, str]],
) -> Decimal:
    """Subtract two country sums exactly, without exposing either aggregate."""

    source_keys = tuple(s for s, _ in compare.KEY_FIELD_PAIRS)
    runtime_keys = tuple(r for _, r in compare.KEY_FIELD_PAIRS)
    src = compare._build_unique_bridge(source_rows, fields=source_keys, label="source")
    dst = compare._build_unique_bridge(runtime_rows, fields=runtime_keys, label="runtime")
    if not src or src.keys() != dst.keys():
        raise ReplacementSumBridgeError("source/runtime national asset keysets drifted")
    try:
        with localcontext(source_value._EXACT_DECIMAL_CONTEXT) as context:
            delta = Decimal(0)
            for key, left in src.items():
                right = dst[key]
                a = source_value._parse_decimal(left[SOURCE_FIELD], field=SOURCE_FIELD)
                b = source_value._parse_decimal(right[RUNTIME_FIELD], field=RUNTIME_FIELD)
                delta = context.add(delta, context.subtract(a, b))
    except (KeyError, Inexact, Rounded, source_value.ExposureValueSpatialProfileError) as exc:
        raise ReplacementSumBridgeError("national cost sum cannot be computed exactly") from exc
    return delta


def analyze_verified_bytes(
    source_raw: bytes,
    runtime_raw: bytes,
    *,
    source_expected_byte_count: int = source_profile.EXPECTED_BYTE_COUNT,
    source_expected_sha256: str = source_profile.EXPECTED_SHA256,
    runtime_expected_byte_count: int = runtime_profile.EXPECTED_BYTE_COUNT,
    runtime_expected_sha256: str = runtime_profile.EXPECTED_SHA256,
) -> dict[str, Any]:
    """Reuse established exact-CSV lineage and compute one aggregate residual."""

    args = {
        "source_expected_byte_count": source_expected_byte_count,
        "source_expected_sha256": source_expected_sha256,
        "runtime_expected_byte_count": runtime_expected_byte_count,
        "runtime_expected_sha256": runtime_expected_sha256,
    }
    existing = compare.compare_verified_exposure_bytes(source_raw, runtime_raw, **args)
    identity = next(
        (x for x in existing["numeric_comparisons"]
         if x["source_field"] == SOURCE_FIELD and x["runtime_field"] == RUNTIME_FIELD),
        None,
    )
    if (
        identity is None
        or existing["comparison_key"]["exact_key_set_equal"] is not True
        or identity["record_count"] != existing["record_count"]
        or existing["raw_rows_returned"] is not False
        or existing["external_bytes_persisted"] is not False
        or existing["model_use_authorized"] is not False
        or existing["publication_authorized"] is not False
    ):
        raise ReplacementSumBridgeError("source/runtime bridge authority drifted")

    source_rows = compare._parse_verified_rows(
        source_raw,
        expected_byte_count=source_expected_byte_count,
        expected_sha256=source_expected_sha256,
        expected_header=compare.SOURCE_HEADER,
        label="source exposure",
    )
    runtime_rows = compare._parse_verified_rows(
        runtime_raw,
        expected_byte_count=runtime_expected_byte_count,
        expected_sha256=runtime_expected_sha256,
        expected_header=compare.RUNTIME_HEADER,
        label="runtime exposure",
    )
    delta = _signed_delta(source_rows, runtime_rows)
    delta_abs = abs(delta)
    max_row_difference = Decimal(identity["maximum_absolute_difference"])
    with localcontext(source_value._EXACT_DECIMAL_CONTEXT) as context:
        theoretical_max = context.multiply(
            max_row_difference, Decimal(existing["record_count"])
        )
    if delta_abs > theoretical_max:
        raise ReplacementSumBridgeError("signed aggregate exceeds per-row difference bound")
    if (delta == 0) and identity["non_equal_count"] == 0:
        aggregate_identity = "ALL_ASSET_VALUES_EXACT"
    elif delta == 0:
        aggregate_identity = "NATIONAL_SUM_EXACT_ASSETS_NOT_EXACT"
    else:
        aggregate_identity = "NATIONAL_SUM_NONZERO_RESIDUAL"

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "BOUNDED_SOURCE_RUNTIME_AGGREGATE_DIAGNOSTIC",
        "source_field": SOURCE_FIELD,
        "runtime_field": RUNTIME_FIELD,
        "record_count": existing["record_count"],
        "canonical_receipt_pair_verified": existing["canonical_receipt_pair_verified"],
        "source_identity": existing["source_identity"],
        "runtime_identity": existing["runtime_identity"],
        "key_set_sha256": existing["comparison_key"]["key_set_sha256"],
        "asset_cost_exact_decimal_equal_count": identity["exact_decimal_equal_count"],
        "asset_cost_non_equal_count": identity["non_equal_count"],
        "national_cost_signed_source_minus_runtime_eur": source_value._canonical_decimal(delta),
        "national_cost_exact_sums_equal": delta == 0,
        "national_sum_relation": aggregate_identity,
        "source_or_runtime_national_cost_sum_returned": False,
        "individual_provider_values_returned": False,
        "external_bytes_persisted": False,
        "exact_source_to_runtime_transform_verified": False,
        "published_residential_aalr_denominator_verified": False,
        "published_reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def run() -> dict[str, Any]:
    """Fetch only the canonical pair through the existing strict acquisition."""

    transport = compare._CANONICAL_OPEN_FIXED
    clock = compare._CANONICAL_MONOTONIC
    if compare._open_fixed is not transport or compare.time.monotonic is not clock:
        raise ReplacementSumBridgeError("canonical source transport drifted")
    src = compare._fetch_fixed_payload(
        dataset_id=source_profile.DATASET_ID,
        project_id=source_profile.PROJECT_ID,
        commit_sha=source_profile.COMMIT_SHA,
        repository_path=source_profile.REPOSITORY_PATH,
        maximum=source_profile.EXPECTED_BYTE_COUNT,
        opener=transport,
        monotonic=clock,
    )
    dst = compare._fetch_fixed_payload(
        dataset_id=runtime_profile.DATASET_ID,
        project_id=runtime_profile.PROJECT_ID,
        commit_sha=runtime_profile.COMMIT_SHA,
        repository_path=runtime_profile.REPOSITORY_PATH,
        maximum=runtime_profile.EXPECTED_BYTE_COUNT,
        opener=transport,
        monotonic=clock,
    )
    report = analyze_verified_bytes(src, dst)
    if report["canonical_receipt_pair_verified"] is not True:
        raise ReplacementSumBridgeError("canonical source receipts not verified")
    return report


def main() -> int:
    try:
        report = run()
    except (
        ReplacementSumBridgeError,
        compare.ExposureRuntimeComparisonError,
        OSError,
        ValueError,
    ):
        print(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED",
            "external_bytes_persisted": False,
            "published_residential_aalr_denominator_verified": False,
            "model_use_authorized": False,
        }, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
