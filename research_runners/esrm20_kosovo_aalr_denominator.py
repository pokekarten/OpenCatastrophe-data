#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded Kosovo Residential AALR denominator compatibility diagnostic.

The diagnostic reads only two already-schema-proven numeric cells from the exact
ESRM20 v1.0 country-risk object and combines them with the exact aggregate
TOTAL_REPL_COST_EUR from the frozen Kosovo residential exposure object.

Provider rows are not returned. The output reports only derived compatibility
evidence. No numerical loss agreement, publication authority, or model use is
established by this diagnostic.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any

from scripts import acquire_efehr_esrm20_country_risk_receipt as country
from scripts import profile_efehr_kosovo_exposure_value_spatial as exposure
from scripts import profile_esrm20_country_risk_schema as schema

COUNTRY_EXPECTED_BYTE_COUNT = 4225
COUNTRY_EXPECTED_SHA256 = (
    "95584a1de1fce1f65e29ea0f8beb5ff87b9489c9e9cca71949791427482312fb"
)
COUNTRY_EXPECTED_COMMIT = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
COUNTRY_EXPECTED_PATH = "Risk/European_Risk_Country.csv"

NAME_HEADER = "Name"
KOSOVO_LITERAL = "Kosovo"
AAL_HEADER = "AAL Residential (economic, M EUR)"
AALR_HEADER = "AALR Residential (economic, per mille)"

_CALC_CONTEXT = Context(prec=80, Emin=-999_999, Emax=999_999)


class DenominatorDiagnosticError(RuntimeError):
    """Raised when the bounded denominator experiment cannot be trusted."""


def _parse_positive_decimal(value: str, *, field: str) -> Decimal:
    if type(value) is not str or value == "" or value != value.strip():
        raise DenominatorDiagnosticError(f"{field} is empty or padded")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise DenominatorDiagnosticError(f"{field} is not decimal") from exc
    if not number.is_finite() or number <= 0:
        raise DenominatorDiagnosticError(f"{field} must be finite and positive")
    if len(number.as_tuple().digits) > 64 or abs(number.adjusted()) > 50:
        raise DenominatorDiagnosticError(f"{field} exceeds bounded decimal policy")
    return number


def _decimal_places(value: Decimal) -> int:
    return max(0, -value.as_tuple().exponent)


def _half_display_unit(value: Decimal) -> Decimal:
    places = _decimal_places(value)
    return Decimal(5).scaleb(-(places + 1))


def _canonical(value: Decimal, *, places: int = 18) -> str:
    if not value.is_finite():
        raise DenominatorDiagnosticError("derived decimal is non-finite")
    with localcontext(_CALC_CONTEXT):
        quantum = Decimal(1).scaleb(-places)
        text = format(value.quantize(quantum), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _extract_kosovo_residential_literals(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> tuple[Decimal, Decimal]:
    profile = schema.profile_country_risk_schema_bytes(
        raw,
        expected_byte_count=expected_byte_count,
        expected_sha256=expected_sha256,
    )
    if profile["kosovo_row_status"] != "unique":
        raise DenominatorDiagnosticError("country-risk Kosovo row is not unique")
    if not profile["residential_aal_schema_candidate"]:
        raise DenominatorDiagnosticError("Residential AAL field is not schema-proven")
    if not profile["residential_aalr_schema_candidate"]:
        raise DenominatorDiagnosticError("Residential AALR field is not schema-proven")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DenominatorDiagnosticError("country-risk bytes are not UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=",", strict=True)
    if reader.fieldnames is None:
        raise DenominatorDiagnosticError("country-risk CSV has no header")
    required = {NAME_HEADER, AAL_HEADER, AALR_HEADER}
    if not required.issubset(set(reader.fieldnames)):
        raise DenominatorDiagnosticError("country-risk required fields drifted")

    matches: list[dict[str, str | None]] = []
    try:
        for row in reader:
            if row.get(NAME_HEADER) == KOSOVO_LITERAL:
                matches.append(row)
    except csv.Error as exc:
        raise DenominatorDiagnosticError("country-risk CSV parse failed") from exc
    if len(matches) != 1:
        raise DenominatorDiagnosticError("country-risk Kosovo row cardinality drifted")

    row = matches[0]
    aal = _parse_positive_decimal(row.get(AAL_HEADER) or "", field=AAL_HEADER)
    aalr = _parse_positive_decimal(row.get(AALR_HEADER) or "", field=AALR_HEADER)
    return aal, aalr


def build_result(
    *,
    aal_m_eur: Decimal,
    aalr_per_mille: Decimal,
    residential_replacement_cost_eur: Decimal,
) -> dict[str, Any]:
    if residential_replacement_cost_eur <= 0:
        raise DenominatorDiagnosticError("residential replacement-cost sum must be positive")

    with localcontext(_CALC_CONTEXT) as context:
        billion = Decimal(1_000_000_000)
        implied_denominator = context.divide(
            context.multiply(aal_m_eur, billion),
            aalr_per_mille,
        )
        relative_difference = context.divide(
            context.subtract(implied_denominator, residential_replacement_cost_eur),
            residential_replacement_cost_eur,
        )
        relative_difference_ppm = context.multiply(
            relative_difference, Decimal(1_000_000)
        )

        aal_half = _half_display_unit(aal_m_eur)
        aalr_half = _half_display_unit(aalr_per_mille)
        aal_low = max(Decimal(0), context.subtract(aal_m_eur, aal_half))
        aal_high = context.add(aal_m_eur, aal_half)
        aalr_low = max(Decimal(0), context.subtract(aalr_per_mille, aalr_half))
        aalr_high = context.add(aalr_per_mille, aalr_half)

        predicted_aalr_low = context.divide(
            context.multiply(aal_low, billion),
            residential_replacement_cost_eur,
        )
        predicted_aalr_high = context.divide(
            context.multiply(aal_high, billion),
            residential_replacement_cost_eur,
        )
        nearest_display_rounding_compatible = not (
            predicted_aalr_high < aalr_low or predicted_aalr_low > aalr_high
        )

    conclusion = (
        "RESIDENTIAL_DENOMINATOR_NUMERICALLY_COMPATIBLE_UNDER_DISPLAY_ROUNDING_HYPOTHESIS"
        if nearest_display_rounding_compatible
        else "RESIDENTIAL_DENOMINATOR_NUMERICALLY_INCOMPATIBLE_UNDER_DISPLAY_ROUNDING_HYPOTHESIS"
    )

    return {
        "schema_version": "oc-esrm20-kosovo-aalr-denominator-diagnostic-v1",
        "status": "SCIENTIFIC_DIAGNOSTIC_ONLY",
        "published_numeric_values_interpreted": True,
        "published_numeric_values_returned": False,
        "residential_exposure_aggregate_interpreted": True,
        "residential_exposure_aggregate_returned": False,
        "aal_literal_decimal_places": _decimal_places(aal_m_eur),
        "aalr_literal_decimal_places": _decimal_places(aalr_per_mille),
        "implied_denominator_relative_difference_ppm": _canonical(
            relative_difference_ppm
        ),
        "nearest_decimal_display_rounding_hypothesis": {
            "assumption": (
                "Each published literal represents nearest rounding to half of its "
                "least-significant displayed decimal unit."
            ),
            "compatible_with_residential_replacement_cost": (
                nearest_display_rounding_compatible
            ),
            "provider_rounding_rule_verified": False,
        },
        "denominator_semantics_verified": False,
        "threshold_compatibility_verified": False,
        "annualization_semantics_verified": False,
        "reference_loss_agreement_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "conclusion": conclusion,
    }


def run() -> dict[str, Any]:
    receipt, raw = country.acquire_country_risk_receipt_with_payload()
    if (
        receipt["commit_sha"] != COUNTRY_EXPECTED_COMMIT
        or receipt["repository_path"] != COUNTRY_EXPECTED_PATH
        or receipt["byte_count"] != COUNTRY_EXPECTED_BYTE_COUNT
        or receipt["sha256"] != COUNTRY_EXPECTED_SHA256
    ):
        raise DenominatorDiagnosticError("country-risk receipt drifted from trusted #778 identity")
    if (
        len(raw) != COUNTRY_EXPECTED_BYTE_COUNT
        or hashlib.sha256(raw).hexdigest() != COUNTRY_EXPECTED_SHA256
    ):
        raise DenominatorDiagnosticError("country-risk payload is not receipt-bound")

    aal, aalr = _extract_kosovo_residential_literals(
        raw,
        expected_byte_count=COUNTRY_EXPECTED_BYTE_COUNT,
        expected_sha256=COUNTRY_EXPECTED_SHA256,
    )
    raw = b""

    exposure_profile = exposure.acquire_and_profile_kosovo_exposure_value_spatial()
    summary = exposure_profile["summary"]
    try:
        total_text = summary["replacement_cost_component_diagnostic"][
            "total_replacement_cost_eur_sum"
        ]
    except (KeyError, TypeError) as exc:
        raise DenominatorDiagnosticError(
            "exposure replacement-cost aggregate is absent"
        ) from exc
    residential_total = _parse_positive_decimal(
        total_text,
        field="Kosovo residential TOTAL_REPL_COST_EUR sum",
    )

    result = build_result(
        aal_m_eur=aal,
        aalr_per_mille=aalr,
        residential_replacement_cost_eur=residential_total,
    )
    result["country_risk_identity"] = {
        "commit_sha": COUNTRY_EXPECTED_COMMIT,
        "repository_path": COUNTRY_EXPECTED_PATH,
        "byte_count": COUNTRY_EXPECTED_BYTE_COUNT,
        "sha256": COUNTRY_EXPECTED_SHA256,
    }
    result["residential_exposure_identity"] = {
        "commit_sha": exposure.COMMIT_SHA,
        "repository_path": exposure.REPOSITORY_PATH,
        "byte_count": exposure.EXPECTED_BYTE_COUNT,
        "sha256": exposure.EXPECTED_SHA256,
    }
    return result


def main() -> int:
    try:
        result = run()
    except (
        DenominatorDiagnosticError,
        country.Esrm20CountryRiskReceiptError,
        exposure.ExposureValueSpatialProfileError,
        schema.CountryRiskSchemaProfileError,
    ) as exc:
        print(
            json.dumps(
                {
                    "schema_version": "oc-esrm20-kosovo-aalr-denominator-diagnostic-v1",
                    "status": "BLOCKED",
                    "error": str(exc),
                    "external_bytes_persisted": False,
                    "reference_loss_agreement_verified": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
