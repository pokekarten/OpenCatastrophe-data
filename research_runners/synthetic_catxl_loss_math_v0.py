# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic *fictional* CAT-XL arithmetic; not a CAT model or a real treaty.

This module intentionally does not read provider files or connect to Neon.
The 12 locations/values and all losses are invented. Contract timing,
reinstatement price and allocation are toy assumptions explicitly isolated
from any actual treaty or real insurer.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
from typing import Any


class SyntheticLossInputError(ValueError):
    """Fail closed on invalid/unscoped fake CAT-XL loss input."""


def _exact_keys(obj: Any, fields: set[str], label: str) -> None:
    if not isinstance(obj, dict) or set(obj) != fields:
        raise SyntheticLossInputError(f"{label}: expected exact fields {sorted(fields)}")


def _integer(value: Any, label: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < int(positive) or value > 10**12:
        raise SyntheticLossInputError(f"{label}: invalid bounded integer EUR value")
    return value


def _date(value: Any, label: str) -> dt.date:
    if not isinstance(value, str) or len(value) != 10:
        raise SyntheticLossInputError(f"{label}: expected ISO YYYY-MM-DD")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SyntheticLossInputError(f"{label}: invalid ISO date") from exc
    if parsed.isoformat() != value:
        raise SyntheticLossInputError(f"{label}: noncanonical date")
    return parsed


def allocate(positions: dict[str, int], events: list[dict[str, Any]], treaty: dict[str, Any]) -> dict[str, Any]:
    """Calculate toy insured-gross -> ceded -> net for a *single* fictional CAT-XL.

    Simplification: free automatic annual aggregate capacity of
    (1 + reinstatements) * occurrence limit; each event is capped by its
    occurrence limit, with no paid reinstatement premium, no reinstatement
    timing or cross-treaty sequencing. The output is NOT an insurance quote,
    capital model, real payout, economic loss, or actual treaty result.
    """
    _exact_keys(treaty, {
        "currency", "year", "attachment_eur", "occurrence_limit_eur",
        "reinstatements", "covered_perils", "reinstatement_pricing",
        "portfolio_as_of", "synthetic_only",
    }, "fictional treaty")
    if treaty["synthetic_only"] is not True:
        raise SyntheticLossInputError("only independently synthetic contracts are allowed")
    if treaty["currency"] != "EUR" or treaty["reinstatement_pricing"] != "assumed_free_for_math_only":
        raise SyntheticLossInputError("unsupported currency or undefined toy reinstatement convention")
    year = _integer(treaty["year"], "year", positive=True)
    if year != 2026:
        raise SyntheticLossInputError("toy fixture is fixed to calendar year 2026")
    as_of = _date(treaty["portfolio_as_of"], "portfolio_as_of")
    if as_of.year != year:
        raise SyntheticLossInputError("as-of date and cover year disagree")
    attachment = _integer(treaty["attachment_eur"], "attachment_eur")
    limit = _integer(treaty["occurrence_limit_eur"], "occurrence_limit_eur", positive=True)
    reinstatements = _integer(treaty["reinstatements"], "reinstatements")
    if reinstatements > 3:
        raise SyntheticLossInputError("reinstatements > 3 not supported in toy arithmetic")
    perils = treaty["covered_perils"]
    if type(perils) is not list or perils != ["flood", "windstorm"]:
        raise SyntheticLossInputError("toy covered_perils must be ['flood','windstorm']")
    if type(positions) is not dict or not positions or len(positions) > 100:
        raise SyntheticLossInputError("invalid synthetic positions")
    for name, amount in positions.items():
        if type(name) is not str or not name.startswith("SYNTH-") or len(name) > 24:
            raise SyntheticLossInputError("only synthetic exposure unit identifiers permitted")
        _integer(amount, f"position {name}", positive=True)
    if type(events) is not list or not events or len(events) > 366:
        raise SyntheticLossInputError("invalid event list")

    capacity = (reinstatements + 1) * limit
    previous: dt.date | None = None
    seen_ids: set[str] = set()
    results: list[dict[str, Any]] = []
    total_gross = 0
    total_ceded = 0
    for i, event in enumerate(events):
        _exact_keys(event, {"event_id", "date", "peril", "losses_eur"}, f"event {i}")
        event_id = event["event_id"]
        if type(event_id) is not str or not event_id.startswith("FICTIONAL-") or len(event_id) > 40:
            raise SyntheticLossInputError("event identifier must clearly identify fictional data")
        if event_id in seen_ids:
            raise SyntheticLossInputError("duplicate synthetic event identifier")
        seen_ids.add(event_id)
        date = _date(event["date"], "event date")
        if date.year != year or date <= as_of or (previous is not None and date <= previous):
            raise SyntheticLossInputError("dates must be after exposure vintage and strictly chronological")
        previous = date
        if event["peril"] not in perils:
            raise SyntheticLossInputError("uncovered/unsupported peril in this toy example")
        losses = event["losses_eur"]
        if type(losses) is not dict or not losses:
            raise SyntheticLossInputError("missing per-unit fictional event losses")
        gross = 0
        for name, value in losses.items():
            if name not in positions:
                raise SyntheticLossInputError("loss references unknown synthetic exposure unit")
            _integer(value, f"event loss {name}")
            if value > positions[name]:
                raise SyntheticLossInputError("per-event loss exceeds synthetic insured value")
            gross += value
        provisional = min(max(gross - attachment, 0), limit)
        remaining_before = capacity - total_ceded
        ceded = min(provisional, remaining_before)
        net = gross - ceded
        if not (0 <= ceded <= provisional <= limit and gross == ceded + net):
            raise AssertionError("fictional gross/ceded/net conservation violated")
        total_gross += gross
        total_ceded += ceded
        results.append({
            "event_id": event_id, "date": event["date"], "peril": event["peril"],
            "gross_eur": gross, "pre_aggregate_ceded_eur": provisional,
            "ceded_eur": ceded, "net_eur": net,
            "aggregate_capacity_before_eur": remaining_before,
            "aggregate_capacity_after_eur": capacity - total_ceded,
        })

    return {
        "classification": "INDEPENDENTLY_SYNTHETIC_ARITHMETIC_ONLY",
        "model_input_approved": False,
        "actual_insurer_or_treaty": False,
        "reinstatement_premium_modelled": False,
        "currency": "EUR", "year": year, "event_count": len(results),
        "aggregate_capacity_eur": capacity,
        "gross_eur": total_gross, "ceded_eur": total_ceded,
        "net_eur": total_gross - total_ceded,
        "aggregate_capacity_remaining_eur": capacity - total_ceded,
        "events": results,
    }


def example() -> tuple[dict[str, int], list[dict[str, Any]], dict[str, Any]]:
    """Exactly 12 independent invented positions; same arithmetic as SQL smoke fixture."""
    positions = {f"SYNTH-{i:02d}": 100_000 + 25_000*i for i in range(1, 13)}
    events = [
        {"event_id": "FICTIONAL-WIND-001", "date": "2026-11-02", "peril": "windstorm",
         "losses_eur": {"SYNTH-01": 100_000}},
        {"event_id": "FICTIONAL-FLOOD-002", "date": "2026-11-08", "peril": "flood",
         "losses_eur": {"SYNTH-05": 200_000, "SYNTH-06": 200_000}},
        {"event_id": "FICTIONAL-WIND-003", "date": "2026-11-15", "peril": "windstorm",
         "losses_eur": {f"SYNTH-{i:02d}": 150_000 for i in range(3, 9)}},
        {"event_id": "FICTIONAL-WIND-004", "date": "2026-11-22", "peril": "windstorm",
         "losses_eur": {f"SYNTH-{i:02d}": 150_000 for i in range(9, 13)}},
    ]
    treaty = {
        "currency": "EUR", "year": 2026, "portfolio_as_of": "2026-11-01",
        "attachment_eur": 200_000, "occurrence_limit_eur": 500_000,
        "reinstatements": 1, "covered_perils": ["flood", "windstorm"],
        "reinstatement_pricing": "assumed_free_for_math_only", "synthetic_only": True,
    }
    return positions, events, treaty


def main() -> int:
    # Only built-in fully synthetic fixture, no file/network/DB inputs.
    positions, events, treaty = example()
    print(json.dumps(allocate(positions, events, treaty), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
