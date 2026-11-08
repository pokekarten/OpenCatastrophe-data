# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed synthetic AALA counterfactual semantics guard.

This module DOES NOT read FEMA workbooks, BCAT geometry, insurance claims,
insured portfolios, treaty terms, or external datasets. It checks a small
independently synthetic example of one building-code-only counterfactual
comparison. It must not be used to calibrate vulnerability or generate ELTs.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "FEMA_BCS_SYNTHETIC_AALA_V0"
EXPOSURE_CLASS = "independently_synthetic_no_fema_bytes"
BASIS = "same_hazard_exposure_and_money_year_code_only_difference"
PERILS = frozenset(("flood", "hurricane_wind", "earthquake"))
ROOT_KEYS = frozenset(("schema_version", "evidence_class", "cases"))
CASE_KEYS = frozenset((
    "case_id", "synthetic_region", "peril", "construction_year",
    "currency_year", "comparison_basis", "source_identity",
    "pre_icode_aal_usd_cents", "with_icode_aal_usd_cents",
))
IDENTIFIER = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,63}$")


class SyntheticAALAError(ValueError):
    """Inputs cannot establish a safe synthetic counterfactual."""


def _bounded_int(value: object, field: str, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise SyntheticAALAError(f"{field}: exact bounded integer required")
    return value


def _identifier(value: object, field: str) -> str:
    if type(value) is not str or not IDENTIFIER.fullmatch(value):
        raise SyntheticAALAError(f"{field}: expected synthetic uppercase identifier")
    return value


def check_synthetic_aala(payload: object) -> dict:
    """Return no-loss-model synthetic AALA comparisons (not summed across regions).

    FEMA BCS describes AALA = modelled pre-code AAL - modelled code AAL.
    It does not establish a change to an individual insured event-loss curve.
    """
    if type(payload) is not dict or set(payload) != ROOT_KEYS:
        raise SyntheticAALAError("expected only schema_version, evidence_class and cases")
    if payload["schema_version"] != SCHEMA:
        raise SyntheticAALAError("unsupported schema_version")
    if payload["evidence_class"] != "synthetic_contract_test_only":
        raise SyntheticAALAError("no external data or production model execution")
    cases = payload["cases"]
    if type(cases) is not list or not 1 <= len(cases) <= 1000:
        raise SyntheticAALAError("cases must contain 1 to 1000 synthetic entries")

    seen_ids: set[str] = set()
    seen_semantics: set[tuple] = set()
    output: list[dict] = []
    for case in cases:
        if type(case) is not dict or set(case) != CASE_KEYS:
            raise SyntheticAALAError("case fields do not match the v0 contract")
        case_id = _identifier(case["case_id"], "case_id")
        region = _identifier(case["synthetic_region"], "synthetic_region")
        if not region.startswith("SYNTH-"):
            raise SyntheticAALAError("region must be explicitly synthetic")
        if case_id in seen_ids:
            raise SyntheticAALAError("duplicate case_id")
        seen_ids.add(case_id)
        peril = case["peril"]
        if type(peril) is not str or peril not in PERILS:
            raise SyntheticAALAError("unsupported code-study peril")
        # FEMA BCS 2020 modeled the 2000-2016 construction cohort;
        # do not silently include 2017/2018 incomplete source years.
        year = _bounded_int(case["construction_year"], "construction_year", 2000, 2016)
        currency_year = _bounded_int(case["currency_year"], "currency_year", 1900, 2100)
        if case["comparison_basis"] != BASIS or case["source_identity"] != EXPOSURE_CLASS:
            raise SyntheticAALAError("baseline/code scenarios need matched synthetic basis and source")
        pre = _bounded_int(case["pre_icode_aal_usd_cents"],
                           "pre_icode_aal_usd_cents", 0, 10**15)
        built = _bounded_int(case["with_icode_aal_usd_cents"],
                             "with_icode_aal_usd_cents", 0, 10**15)
        key = (region, peril, year, currency_year)
        if key in seen_semantics:
            raise SyntheticAALAError("duplicate region/peril/cohort/year counterfactual")
        seen_semantics.add(key)
        aala = pre - built  # signed: never silently floor adverse effects at zero
        ratio = Fraction(built, pre) if pre else None
        output.append({
            "case_id": case_id,
            "synthetic_region": region,
            "peril": peril,
            "construction_year": year,
            "currency_year": currency_year,
            "aala_usd_cents_signed": aala,
            "with_code_to_pre_code_aal_ratio": (
                f"{ratio.numerator}/{ratio.denominator}" if ratio is not None else None
            ),
            "scenario_difference_only": True,
            "observed_claims": False,
        })
    output.sort(key=lambda item: item["case_id"])
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "evidence_class": "SYNTHETIC_CODE_AALA_DIFFERENCE_ONLY",
        "input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "cases": output,
        "aggregate_aala": None,
        "independent_empirical_validation": False,
        "fema_workbook_or_bcat_data_read": False,
        "insured_or_event_loss_generated": False,
        "elt_ylt_aep_oep_generated": False,
    }


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SyntheticAALAError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise SyntheticAALAError(f"non-finite JSON number: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path, help="independently synthetic input JSON only")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"),
                             object_pairs_hook=_reject_duplicate_json_keys,
                             parse_constant=_reject_nonfinite)
        print(json.dumps(check_synthetic_aala(payload), indent=2, sort_keys=True))
    except (OSError, UnicodeError, json.JSONDecodeError, SyntheticAALAError, ValueError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
