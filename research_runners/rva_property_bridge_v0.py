# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Cross-repo R+V solo property-premium receipt -> explicitly fictional regional TIV.

Reads a separately verified official SFCR receipt; never infers sites/TIV from premiums.
No external network or database access. Output is NOT model/OED-ready.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from hashlib import sha256
import json
import tomllib
from pathlib import Path
import re


class RvaBridgeError(ValueError):
    pass


_PROFILE_ID = "RVA_DE_2025"
_SOURCE_SCHEMA = "RVA_PUBLIC_SOLO_SFCR_PROFILE_V0"
_SOURCE_PROPERTY_GWP_M = Decimal("2223.182")  # official issuer source, not exposure data
_SOURCE_TOTAL_GWP_M = Decimal("5992.306")
_REGION = re.compile(r"DE_[A-Z][A-Z0-9_]{1,39}\Z")
_PERILS = {"windstorm", "hail", "flood", "earthquake"}


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def _integer(value: object, label: str, bound: int) -> int:
    if type(value) is not str or not re.fullmatch(r"[1-9][0-9]{0,15}", value):
        raise RvaBridgeError(f"{label}: positive integer decimal string required")
    number = int(value)
    if number > bound:
        raise RvaBridgeError(f"{label}: scenario limit exceeded")
    return number


def _weight(value: object) -> Decimal:
    if type(value) is not str or not re.fullmatch(r"(?:0|1|0\.[0-9]{1,12}|1\.0{1,12})", value):
        raise RvaBridgeError("weights must be decimal strings between 0 and 1")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise RvaBridgeError("invalid decimal weight") from exc
    if result < 0 or result > 1:
        raise RvaBridgeError("weight outside [0,1]")
    return result


def _split(total: int, weights: dict[str, Decimal]) -> dict[str, int]:
    ordered = sorted(weights)
    ideal = {k: weights[k] * Decimal(total) for k in ordered}
    result = {k: int(ideal[k].to_integral_value(rounding=ROUND_FLOOR)) for k in ordered}
    remaining = total - sum(result.values())
    if not 0 <= remaining < len(ordered):
        raise RvaBridgeError("non-conserving allocation")
    for k in sorted(ordered, key=lambda x: (-(ideal[x] - result[x]), x))[:remaining]:
        result[k] += 1
    return result


def _source_profile(document: dict) -> dict:
    if (type(document) is not dict or document.get("schema_version") != _SOURCE_SCHEMA
            or document.get("calibration_status") != "NOT_CALIBRATED"
            or type(document.get("profiles")) is not list):
        raise RvaBridgeError("unexpected solo SFCR source schema/status")
    profiles = [p for p in document["profiles"] if p.get("profile_id") == _PROFILE_ID]
    if len(profiles) != 1:
        raise RvaBridgeError("expected exactly one RVA_DE_2025 solo profile")
    p = profiles[0]
    if (p.get("entity") != "R+V Allgemeine Versicherung AG"
            or p.get("entity_kind") != "solo_direct_insurer"
            or type(p.get("report_year")) is not int or p["report_year"] != 2025
            or p.get("currency") != "EUR"
            or p.get("lob_measure") != "gross_written_premium_eur_million"
            or p.get("basis", {}).get("denominator_measure") != "gross_written_premium"
            or not p.get("source", {}).get("url", "").startswith("https://www.ruv.de/")
            or type(p.get("lob_rows")) is not list):
        raise RvaBridgeError("R+V source entity, year, currency or accounting scope changed")
    try:
        total = Decimal(p["basis"]["denominator_eur_million"])
        values = {r["code"]: Decimal(r["value"]) for r in p["lob_rows"]}
    except (KeyError, ValueError, InvalidOperation, TypeError) as exc:
        raise RvaBridgeError("invalid source premium rows") from exc
    if (len(values) != len(p["lob_rows"]) or total != _SOURCE_TOTAL_GWP_M
            or values.get("fire_and_other_property") != _SOURCE_PROPERTY_GWP_M
            or abs(sum(values.values()) - total) > Decimal("0.001")):
        raise RvaBridgeError("source SFCR 2025 accounting receipt not reconciled")
    return p


def bridge(source: dict, scenario: dict) -> dict:
    _source_profile(source)
    fields = {"schema_version", "scenario_status", "target_profile_id", "as_of",
              "assumed_tiv_eur", "assumed_site_count", "model_perils", "regions"}
    if type(scenario) is not dict or set(scenario) != fields:
        raise RvaBridgeError("scenario has missing or extra fields")
    if (scenario["schema_version"] != "0.1.0"
            or scenario["scenario_status"] != "entirely_fictional_insurer_hypothesis"
            or scenario["target_profile_id"] != _PROFILE_ID
            or scenario["as_of"] != "2025-12-31"):
        raise RvaBridgeError("unsupported profile or scenario authority")
    tiv = _integer(scenario["assumed_tiv_eur"], "assumed_tiv_eur", 10**15)
    sites = _integer(scenario["assumed_site_count"], "assumed_site_count", 10**8)
    perils = scenario["model_perils"]
    if type(perils) is not list or not perils or len(perils) != len(set(perils)) or not set(perils) <= _PERILS:
        raise RvaBridgeError("unsupported peril selection")
    rows = scenario["regions"]
    if type(rows) is not list or not 2 <= len(rows) <= 50:
        raise RvaBridgeError("require 2..50 fictional DE region hypotheses")
    site_weights, tiv_weights = {}, {}
    for r in rows:
        if type(r) is not dict or set(r) != {"region_id", "site_weight", "tiv_weight"}:
            raise RvaBridgeError("bad fictional region row")
        code = r["region_id"]
        if type(code) is not str or not _REGION.fullmatch(code) or code in site_weights:
            raise RvaBridgeError("duplicate or non-DE fictional region")
        site_weights[code] = _weight(r["site_weight"])
        tiv_weights[code] = _weight(r["tiv_weight"])
    if sum(site_weights.values()) != 1 or sum(tiv_weights.values()) != 1:
        raise RvaBridgeError("both independent regional weights must sum exactly to 1")
    sites_by_region = _split(sites, site_weights)
    tiv_by_region = _split(tiv, tiv_weights)
    out = [{"fictional_region": k, "assumed_site_count": sites_by_region[k],
            "assumed_tiv_eur": tiv_by_region[k]} for k in sorted(site_weights)]
    if sum(x["assumed_site_count"] for x in out) != sites or sum(x["assumed_tiv_eur"] for x in out) != tiv:
        raise RvaBridgeError("synthetic amount conservation failed")
    return {"status": "SCENARIO_ONLY_NOT_OASIS_ADMISSIBLE", "source_profile_id": _PROFILE_ID,
            "reported_fire_other_property_gwp_eur": str(_SOURCE_PROPERTY_GWP_M * 1_000_000),
            "reported_total_solo_gwp_eur": str(_SOURCE_TOTAL_GWP_M * 1_000_000),
            "public_sfcr_input_sha256": _digest(source), "scenario_sha256": _digest(scenario),
            "assumed_total_tiv_eur": str(tiv), "assumed_total_sites": sites,
            "perils_hypothetical": sorted(perils), "fictional_region_rows": out,
            "company_site_geography_observed": False, "company_tiv_observed": False,
            "property_premium_is_natcat_premium": False,
            "gwp_to_tiv_conversion_used": False,
            "site_coordinates_present": False, "hazard_calibrated": False,
            "vulnerability_calibrated": False, "risk_transfer_contract_observed": False,
            "oed_location_ready": False, "oasis_production_run_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public_sfcr_receipt", type=Path, help="public R+V solo 2025 SFCR TOML receipt")
    parser.add_argument("fictional_scenario", type=Path, help="synthetic parameter scenario TOML")
    args = parser.parse_args()
    try:
        for file in (args.public_sfcr_receipt, args.fictional_scenario):
            if file.stat().st_size > 2_000_000:
                raise RvaBridgeError("file size exceeds 2 MB")
        result = bridge(tomllib.loads(args.public_sfcr_receipt.read_text(encoding="utf-8")),
                        tomllib.loads(args.fictional_scenario.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, RvaBridgeError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
