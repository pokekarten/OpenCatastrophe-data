# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fiction-only conditional underwriter comparison; no Aon data or annual EP."""

from __future__ import annotations

import hashlib
import json


class SyntheticAccumulationError(ValueError):
    """An invalid or unsupported fictional comparison cannot become an estimate."""


_RISK_FIELDS = frozenset({
    "location_id", "policy_id", "zone", "currency", "tiv_cents",
    "deductible_cents", "limit_cents",
})
_HAZARD_FIELDS = frozenset({"event_id", "version", "damage_bps_by_zone"})


def _id(value: object, label: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise SyntheticAccumulationError(f"{label}: nonempty canonical text required")
    return value


def _cents(value: object, label: str) -> int:
    if type(value) is not int or value < 0 or value > 10**15:
        raise SyntheticAccumulationError(f"{label}: bounded integer euro cents required")
    return value


def _risk(value: object) -> dict:
    if type(value) is not dict or set(value) != _RISK_FIELDS:
        raise SyntheticAccumulationError("unsupported risk fields (including annualization)")
    risk = dict(value)
    for field in ("location_id", "policy_id", "zone"):
        _id(risk[field], field)
    if risk["currency"] != "EUR" or type(risk["currency"]) is not str:
        raise SyntheticAccumulationError("currency must be EUR for every risk")
    for field in ("tiv_cents", "deductible_cents", "limit_cents"):
        _cents(risk[field], field)
    return risk


def _hazard(value: object) -> dict:
    if type(value) is not dict or set(value) != _HAZARD_FIELDS:
        raise SyntheticAccumulationError("one declared conditional event is required")
    h = dict(value)
    _id(h["event_id"], "event_id")
    _id(h["version"], "version")
    zones = h["damage_bps_by_zone"]
    if type(zones) is not dict or not zones:
        raise SyntheticAccumulationError("explicit footprint support is required")
    for zone, bps in zones.items():
        _id(zone, "hazard zone")
        if type(bps) is not int or not 0 <= bps <= 10000:
            raise SyntheticAccumulationError("damage severity must be integer basis points")
    return h


def _verify_unique(risks: list[dict]) -> None:
    for key in ("location_id", "policy_id"):
        identities = [risk[key] for risk in risks]
        if len(identities) != len(set(identities)):
            raise SyntheticAccumulationError(f"duplicate {key}")


def _totals(risks: list[dict], hazard: dict) -> dict:
    """One supported event; half-up cent rounding, then per-risk limits."""
    by_zone: dict[str, dict[str, int]] = {}
    for risk in risks:
        zone = risk["zone"]
        if zone not in hazard["damage_bps_by_zone"]:
            raise SyntheticAccumulationError("missing footprint is unknown, not zero loss")
        bps = hazard["damage_bps_by_zone"][zone]
        # Exact integer arithmetic: never float; half-up to one euro cent.
        gross = (risk["tiv_cents"] * bps + 5000) // 10000
        insured = min(max(gross - risk["deductible_cents"], 0), risk["limit_cents"])
        slot = by_zone.setdefault(zone, {"tiv_cents": 0, "gross_cents": 0, "insured_cents": 0, "risks": 0})
        slot["risks"] += 1
        slot["tiv_cents"] += risk["tiv_cents"]
        slot["gross_cents"] += gross
        slot["insured_cents"] += insured
    return {
        "tiv_cents": sum(v["tiv_cents"] for v in by_zone.values()),
        "gross_cents": sum(v["gross_cents"] for v in by_zone.values()),
        "insured_cents": sum(v["insured_cents"] for v in by_zone.values()),
        "by_zone": dict(sorted(by_zone.items())),
    }


def compare(baseline: object, proposal_a: object, proposal_b: object, hazard: object) -> dict:
    """Same fictional value/terms: one proposed risk in each of two zones."""
    if type(baseline) is not list or not baseline:
        raise SyntheticAccumulationError("nonempty fictional baseline required")
    prior = [_risk(r) for r in baseline]
    a, b = _risk(proposal_a), _risk(proposal_b)
    h = _hazard(hazard)
    if a["zone"] == b["zone"]:
        raise SyntheticAccumulationError("proposals must compare different concentration zones")
    if any(a[k] != b[k] for k in ("tiv_cents", "deductible_cents", "limit_cents", "currency")):
        raise SyntheticAccumulationError("proposal values and terms must match")
    # The proposals are counterfactual alternatives, never simultaneous risks.
    _verify_unique(prior + [a])
    _verify_unique(prior + [b])
    # Fail before producing partial numerical outputs if *any* zone is missing.
    for risk in prior + [a, b]:
        if risk["zone"] not in h["damage_bps_by_zone"]:
            raise SyntheticAccumulationError("missing footprint is unknown, not zero loss")
    base = _totals(prior, h)
    result = {}
    for key, risk in (("A", a), ("B", b)):
        post = _totals(prior + [risk], h)
        result[key] = {
            "added_zone": risk["zone"],
            "post": post,
            "delta": {field: post[field] - base[field]
                      for field in ("tiv_cents", "gross_cents", "insured_cents")},
        }
    payload = {"baseline": prior, "proposal_a": a, "proposal_b": b, "hazard": h}
    receipt = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "profile": "synthetic-underwriter-conditional-accumulation-v0",
        "risk_metric_kind": "conditional_scenario",
        "annual_ep_admitted": False,
        "actual_insurer_data_used": False,
        "aon_data_or_score_used": False,
        "currency": "EUR",
        "physical_event_id": h["event_id"],
        "hazard_version": h["version"],
        "fictional_fixture_sha256": receipt,
        "source_original_bytes_verified": False,
        "baseline": base,
        "proposals": result,
    }


def example() -> dict:
    hazard = {"event_id": "FICTIONAL_STORM_1", "version": "toy-hazard-v1",
              "damage_bps_by_zone": {"HIGH": 3000, "LOW": 500}}
    common = {"currency": "EUR", "deductible_cents": 25000, "limit_cents": 5000000}
    baseline = [
        {**common, "location_id": "BASE-H", "policy_id": "BH", "zone": "HIGH", "tiv_cents": 10000000},
        {**common, "location_id": "BASE-L", "policy_id": "BL", "zone": "LOW", "tiv_cents": 10000000},
    ]
    proposal_a = {**common, "location_id": "PROPOSED-H", "policy_id": "PH", "zone": "HIGH", "tiv_cents": 5000000}
    proposal_b = {**common, "location_id": "PROPOSED-L", "policy_id": "PL", "zone": "LOW", "tiv_cents": 5000000}
    return compare(baseline, proposal_a, proposal_b, hazard)


if __name__ == "__main__":
    print(json.dumps(example(), sort_keys=True, indent=2))
