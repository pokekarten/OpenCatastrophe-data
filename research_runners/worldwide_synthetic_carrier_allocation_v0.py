# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Research-only deterministic country-to-region allocation of fictional policies.

Input is aggregate metadata only. No insurer asset, location, TIV or hazard inference.
A supplied digest is a declared provenance identifier, not verified source bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from fractions import Fraction
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,99}\Z")
_COUNTRY = re.compile(r"[A-Z]{2}\Z")
_REGION = re.compile(r"[A-Z]{2}-[A-Z0-9][A-Z0-9-]{0,29}\Z")
_DATE = re.compile(r"20[0-9]{2}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\Z")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,6})?\Z")


class InvalidPortfolio(ValueError):
    """The aggregate-only source/assumption contract is not satisfied."""


def _keys(value: Any, required: set[str], optional: set[str] = frozenset()) -> dict:
    if not isinstance(value, dict) or not required.issubset(value) or set(value) - required - optional:
        raise InvalidPortfolio("missing or unexpected aggregate contract keys")
    return value


def _string(value: Any, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise InvalidPortfolio(f"invalid {label}")
    return value


def _date(value: Any, label: str) -> str:
    text = _string(value, _DATE, label)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise InvalidPortfolio(f"invalid {label}") from exc
    return text


def _https(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidPortfolio(f"invalid {label}")
    try:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("not an absolute public HTTPS product URL")
    except ValueError as exc:
        raise InvalidPortfolio(f"invalid {label}") from exc
    return value


def _count(value: Any, label: str) -> int:
    if type(value) is not int or value < 0 or value > 10**12:
        raise InvalidPortfolio(f"invalid {label}")
    return value


def _factor(value: Any) -> Fraction:
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        raise InvalidPortfolio("scenario factors must be nonnegative bounded decimal strings")
    return Fraction(value)


def allocate(document: dict) -> dict:
    """Allocate an observed country policy COUNT to fictional regional cohorts.

    This proves arithmetic only; no actual carrier-region geography is asserted.
    """
    doc = _keys(document, {"carrier", "physical_proxy", "scenarios"})
    carrier = _keys(doc["carrier"], {"carrier_id", "legal_scope", "country_code", "as_of",
                                    "coverage_class", "observed_policy_count", "source_url",
                                    "source_sha256", "source_measure"})
    _string(carrier["carrier_id"], _ID, "carrier ID")
    if carrier["legal_scope"] not in ("solo", "group", "public_programme"):
        raise InvalidPortfolio("explicit legal scope required")
    country = _string(carrier["country_code"], _COUNTRY, "ISO-like country code")
    _date(carrier["as_of"], "carrier observation date")
    _string(carrier["coverage_class"], _ID, "coverage class")
    total = _count(carrier["observed_policy_count"], "observed policy count")
    if carrier["source_measure"] != "carrier_reported_policy_count":
        raise InvalidPortfolio("premiums, exposure and building counts are not policy counts")
    _https(carrier["source_url"], "carrier source URL")
    _string(carrier["source_sha256"], _HEX, "declared source SHA256")

    proxy = _keys(doc["physical_proxy"], {"as_of", "source_url", "source_sha256", "proxy_measure", "regions"})
    _date(proxy["as_of"], "physical-stock vintage")
    if proxy["proxy_measure"] != "non_insurer_physical_building_count":
        raise InvalidPortfolio("regional proxy must be independent physical building counts")
    _https(proxy["source_url"], "physical source URL")
    _string(proxy["source_sha256"], _HEX, "declared physical source SHA256")
    regions = proxy["regions"]
    if not isinstance(regions, list) or not 1 <= len(regions) <= 10000:
        raise InvalidPortfolio("require a bounded nonempty physical-region roster")
    stock: dict[str, int] = {}
    for row in regions:
        _keys(row, {"region_id", "building_count"})
        region = _string(row["region_id"], _REGION, "region ID")
        if not region.startswith(country + "-") or region in stock:
            raise InvalidPortfolio("foreign or duplicate region ID")
        stock[region] = _count(row["building_count"], "physical building count")
    if sum(stock.values()) == 0:
        raise InvalidPortfolio("empty regional physical denominator")

    scenarios = doc["scenarios"]
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 20:
        raise InvalidPortfolio("require one to twenty distinct synthetic scenarios")
    results = []
    seen: set[str] = set()
    for item in scenarios:
        _keys(item, {"scenario_id", "description", "regional_factors"})
        scenario_id = _string(item["scenario_id"], _ID, "scenario ID")
        if scenario_id in seen:
            raise InvalidPortfolio("duplicate scenario ID")
        seen.add(scenario_id)
        if not isinstance(item["description"], str) or not item["description"].strip():
            raise InvalidPortfolio("describe invented selection/penetration assumptions")
        factors = item["regional_factors"]
        if not isinstance(factors, dict) or set(factors) != set(stock):
            raise InvalidPortfolio("factors must explicitly cover exactly the physical roster")
        weights = {r: Fraction(stock[r]) * _factor(factors[r]) for r in stock}
        denominator = sum(weights.values())
        if denominator <= 0:
            raise InvalidPortfolio("scenario has no positive eligible physical weight")
        base = {r: (total * w) // denominator for r, w in weights.items()}
        remainders = {r: (total * w) / denominator - base[r] for r, w in weights.items()}
        extra = total - sum(base.values())
        for region in sorted(stock, key=lambda r: (-remainders[r], r))[:extra]:
            base[region] += 1
        if sum(base.values()) != total:
            raise AssertionError("internal Hamilton conservation failure")
        results.append({"scenario_id": scenario_id,
                        "status": "FICTIONAL_REGION_ALLOCATION_NOT_INSURER_GEOGRAPHY",
                        "allocation": [{"region_id": r, "synthetic_policy_count": base[r]}
                                       for r in sorted(stock)],
                        "total_synthetic_policies": sum(base.values()),
                        "conservation_pass": True})
    semantic_input = {"carrier": carrier,
                      "physical_proxy": {**proxy, "regions": sorted(regions, key=lambda r: r["region_id"])},
                      "scenarios": scenarios}
    input_digest = hashlib.sha256(json.dumps(semantic_input, sort_keys=True, ensure_ascii=False,
                                             separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"aggregate_input_sha256": input_digest,
            "carrier_id": carrier["carrier_id"], "country_code": country,
            "coverage_class": carrier["coverage_class"], "legal_scope": carrier["legal_scope"],
            "carrier_as_of": carrier["as_of"], "physical_as_of": proxy["as_of"],
            "declared_source_sha256": carrier["source_sha256"],
            "declared_physical_sha256": proxy["source_sha256"],
            "source_bytes_verified": False, "source_rights_reviewed": False,
            "observed_company_region_geography": False,
            "insured_tiv_known": False, "model_ready": False,
            "scenario_sensitivity_available": len(results) >= 2,
            "scenarios": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aggregate_json", type=Path, help="locally prepared aggregate-only input JSON")
    args = parser.parse_args()
    try:
        value = json.loads(args.aggregate_json.read_text(encoding="utf-8"))
        result = allocate(value)
    except (OSError, json.JSONDecodeError, InvalidPortfolio) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
