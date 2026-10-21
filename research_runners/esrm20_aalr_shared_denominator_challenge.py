#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded, source-bound falsification of a *shared* ESRM20 AALR denominator.

Under the predeclared hypothetical nearest-displayed-decimal rounding model,
if Commercial, Industrial, Residential and Total AALRs all use the same
all-occupancy replacement-cost denominator, and the four underlying annual
losses have additive scope, the three occupancy AALRs must sum to Total AALR.

Test this necessary condition across exactly the 44 frozen ESRM20 v1.0
country rows, but emit only counts of compatible/incompatible rows; neither
source rows nor numerical risk estimates are published or retained.

Failure of the shared-denominator hypothesis does NOT establish what the
occupancy-specific denominator actually is, provider rounding, threshold
semantics, or numerical reference agreement. It must not authorize model use.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from decimal import Decimal, Context, InvalidOperation, localcontext
from typing import Any

from research_runners import esrm20_country_viewer_provenance as viewer
from scripts import acquire_efehr_esrm20_country_risk_receipt as country
from scripts import profile_esrm20_country_risk_schema as schema

SCHEMA_VERSION = "oc-esrm20-aalr-shared-denominator-challenge-v1"
EXPECTED_ROWS = 44
EXPECTED_COLUMNS = 18
ALLOWED_DECIMAL = re.compile(r"^(?:0|[0-9]+)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$")
CALC_CONTEXT = Context(prec=80, Emin=-999999, Emax=999999)

AAL_COLUMNS = (
    "AAL Commercial (economic, M EUR)",
    "AAL Industrial (economic, M EUR)",
    "AAL Residential (economic, M EUR)",
    "AAL Total (economic, M EUR)",
)
# Preserve the actual provider's misspelled *Commerical* column label.
AALR_COLUMNS = (
    "AALR Commerical (economic, per mille)",
    "AALR Industrial (economic, per mille)",
    "AALR Residential (economic, per mille)",
    "AALR Total (economic, per mille)",
)
REQUIRED_COLUMNS = ("Name",) + AAL_COLUMNS + AALR_COLUMNS


class SharedDenominatorChallengeError(RuntimeError):
    """Fail-closed invalid source or unsupported numeric representation."""


def _interval(literal: str) -> tuple[Decimal, Decimal]:
    if (
        type(literal) is not str
        or len(literal) > 80
        or ALLOWED_DECIMAL.fullmatch(literal) is None
    ):
        raise SharedDenominatorChallengeError("risk metric decimal syntax drifted")
    try:
        value = Decimal(literal)
    except InvalidOperation as exc:
        raise SharedDenominatorChallengeError("risk metric decimal invalid") from exc
    if (
        not value.is_finite()
        or value < 0
        or abs(value.adjusted()) > 50
        or len(value.as_tuple().digits) > 64
    ):
        raise SharedDenominatorChallengeError("risk metric outside bounded policy")
    # Decimal's original exponent (not the number of digits after a decimal
    # point) preserves the actual displayed unit even for 1E+3.
    half_unit = Decimal(5).scaleb(value.as_tuple().exponent - 1)
    with localcontext(CALC_CONTEXT):
        return max(Decimal(0), value - half_unit), value + half_unit


def _intervals_overlap(
    parts: tuple[tuple[Decimal, Decimal], ...],
    total: tuple[Decimal, Decimal],
) -> bool:
    with localcontext(CALC_CONTEXT):
        lower = sum((part[0] for part in parts), Decimal(0))
        upper = sum((part[1] for part in parts), Decimal(0))
    return lower <= total[1] and total[0] <= upper


def analyze_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Only bounded aggregate hypothesis checks; no provider rows in output."""

    if type(rows) is not list or len(rows) != EXPECTED_ROWS:
        raise SharedDenominatorChallengeError("country row count drifted")
    known_names: set[str] = set()
    aal_additive = 0
    aal_nonadditive = 0
    ratio_sum_incompatible_when_aal_additive = 0
    ratio_sum_compatible_when_aal_additive = 0
    for row in rows:
        if type(row) is not dict or any(k not in row for k in REQUIRED_COLUMNS):
            raise SharedDenominatorChallengeError("country risk fields drifted")
        name = row["Name"]
        if type(name) is not str or not name or name in known_names:
            raise SharedDenominatorChallengeError("country identity is missing or duplicated")
        known_names.add(name)
        aal = tuple(_interval(row[column]) for column in AAL_COLUMNS)
        ratios = tuple(_interval(row[column]) for column in AALR_COLUMNS)
        if _intervals_overlap(aal[:3], aal[3]):
            aal_additive += 1
            if _intervals_overlap(ratios[:3], ratios[3]):
                ratio_sum_compatible_when_aal_additive += 1
            else:
                ratio_sum_incompatible_when_aal_additive += 1
        else:
            aal_nonadditive += 1

    rejected = ratio_sum_incompatible_when_aal_additive > 0
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "BOUNDED_SCIENTIFIC_HYPOTHESIS_TEST",
        "rows_analyzed": len(rows),
        "absolute_aal_additive_under_display_rounding": aal_additive,
        "absolute_aal_not_additive_under_display_rounding": aal_nonadditive,
        "shared_denominator_sum_incompatible_under_display_rounding": (
            ratio_sum_incompatible_when_aal_additive
        ),
        "shared_denominator_sum_compatible_under_display_rounding": (
            ratio_sum_compatible_when_aal_additive
        ),
        "predeclared_hypothesis": (
            "If four occupancy-level/total AALRs share an identical denominator "
            "and AAL scopes add, then occupancy AALRs must sum to Total AALR."
        ),
        "rounding_assumption": (
            "Nearest rounding to half of each literal's least significant "
            "displayed decimal unit; provider rule not established."
        ),
        "shared_all_occupancy_denominator_hypothesis_rejected": rejected,
        "occupancy_specific_denominator_verified": False,
        "provider_rounding_rule_verified": False,
        "provider_numeric_values_interpreted": True,
        "provider_numeric_values_returned": False,
        "provider_rows_returned": False,
        "external_bytes_persisted": False,
        "threshold_compatibility_verified": False,
        "annualization_semantics_verified": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "conclusion": (
            "SHARED_DENOMINATOR_NECESSARY_CONDITION_FALSIFIED_UNDER_ROUNDING"
            if rejected else "SHARED_DENOMINATOR_NECESSARY_CONDITION_NOT_FALSIFIED"
        ),
    }


def analyze_frozen_bytes(
    payload: bytes, receipt: dict[str, Any]
) -> dict[str, Any]:
    """Require trusted v1.0 source identity and schema *before* reading figures."""

    if type(payload) is not bytes or type(receipt) is not dict:
        raise SharedDenominatorChallengeError("source receipt shape drifted")
    expected_sha = viewer.FROZEN_V10_SHA256
    if (
        len(payload) != viewer.FROZEN_V10_BYTE_COUNT
        or hashlib.sha256(payload).hexdigest() != expected_sha
        or receipt.get("project_id") != country.PROJECT_ID
        or receipt.get("commit_sha") != viewer.FROZEN_V10_COMMIT
        or receipt.get("repository_path") != viewer.COUNTRY_RISK_PATH
        or receipt.get("byte_count") != viewer.FROZEN_V10_BYTE_COUNT
        or receipt.get("sha256") != expected_sha
        or receipt.get("external_bytes_persisted") is not False
    ):
        raise SharedDenominatorChallengeError("frozen source identity not proven")

    profile = schema.profile_country_risk_schema_bytes(
        payload,
        expected_byte_count=viewer.FROZEN_V10_BYTE_COUNT,
        expected_sha256=expected_sha,
    )
    if (
        profile["row_count"] != EXPECTED_ROWS
        or profile["column_count"] != EXPECTED_COLUMNS
        or profile["kosovo_row_status"] != "unique"
    ):
        raise SharedDenominatorChallengeError("frozen country table schema drifted")

    try:
        reader = csv.DictReader(
            io.StringIO(payload.decode("utf-8"), newline=""),
            delimiter=",",
            strict=True,
        )
        if (
            reader.fieldnames is None
            or len(reader.fieldnames) != EXPECTED_COLUMNS
            or len(set(reader.fieldnames)) != EXPECTED_COLUMNS
            or not set(REQUIRED_COLUMNS).issubset(set(reader.fieldnames))
        ):
            raise SharedDenominatorChallengeError("exact risk column set drifted")
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise SharedDenominatorChallengeError("frozen CSV encoding/structure drifted") from exc
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise SharedDenominatorChallengeError("frozen CSV row width drifted")
    result = analyze_rows(rows)
    # Carry the trusted immutable source identity in the durable aggregate
    # evidence; synthetic analyze_rows() calls never claim this provenance.
    result["trusted_source_receipt_bound"] = True
    result["source_identity"] = {
        "project_id": country.PROJECT_ID,
        "commit_sha": viewer.FROZEN_V10_COMMIT,
        "repository_path": viewer.COUNTRY_RISK_PATH,
        "byte_count": viewer.FROZEN_V10_BYTE_COUNT,
        "sha256": expected_sha,
        "git_blob_sha1": viewer.FROZEN_V10_BLOB_SHA1,
    }
    return result


def run() -> dict[str, Any]:
    receipt, payload = country.acquire_country_risk_receipt_with_payload()
    return analyze_frozen_bytes(payload, receipt)


def main() -> int:
    try:
        result = run()
    except (
        SharedDenominatorChallengeError,
        country.Esrm20CountryRiskReceiptError,
        schema.CountryRiskSchemaProfileError,
    ):
        print(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED",
            "provider_rows_returned": False,
            "external_bytes_persisted": False,
            "reference_loss_agreement_verified": False,
            "model_use_authorized": False,
        }, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
