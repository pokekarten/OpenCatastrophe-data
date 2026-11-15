# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original fictional multi-layer CAT-XL arithmetic, not a CAT model.

No insurer, real claim, real location, provider bytes, hazard, vulnerability,
database operation or external source is used. All losses are invented.
Loss and cession amounts are whole EUR; premium amounts are integer cents.
Gross-occurrence layers must be ordered and non-overlapping.
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any


class ToyTowerInputError(ValueError):
    """Reject ambiguous, non-fictional or malformed test inputs."""


def _shape(data: Any, fields: set[str], label: str) -> None:
    if type(data) is not dict or set(data) != fields:
        raise ToyTowerInputError(f"{label}: exact fields required: {sorted(fields)}")


def _int(value: Any, label: str, minimum: int = 0, maximum: int = 10**12) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ToyTowerInputError(f"{label}: bounded integer required")
    return value


def _date(value: Any, label: str) -> dt.date:
    if type(value) is not str or len(value) != 10:
        raise ToyTowerInputError(f"{label}: canonical ISO date required")
    try:
        result = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ToyTowerInputError(f"{label}: invalid date") from exc
    if result.isoformat() != value:
        raise ToyTowerInputError(f"{label}: noncanonical date")
    return result


def _earned_ri_cents(recovered_eur: int, layer: dict[str, Any]) -> int:
    """Half-up rounded *cumulative* premium on reinstated limit used.

    Toy definition, not contractual premium on activation, not time-pro-rated.
    Differencing consecutive cumulative charges prevents rounding drift.
    """
    limit = layer["limit_eur"]
    used = min(max(recovered_eur - limit, 0), limit * layer["reinstatements"])
    n = used * layer["base_premium_cents"] * layer["reinstatement_rate_bps"]
    d = limit * 10000
    return (2 * n + d) // (2 * d)


def calculate_toy_tower(positions: dict[str, int], events: list[dict[str, Any]],
                        contract: dict[str, Any]) -> dict[str, Any]:
    """Demonstrate fictional per-event gross -> non-overlap cessions -> net."""
    _shape(contract, {"synthetic_only", "currency", "year", "as_of_date",
                      "basis", "reinstatement_premium_convention", "layers"}, "contract")
    if contract["synthetic_only"] is not True:
        raise ToyTowerInputError("only invented contracts supported")
    if contract["currency"] != "EUR" or contract["basis"] != "independent_gross_occurrence":
        raise ToyTowerInputError("unsupported currency or overlapping inuring basis")
    if contract["reinstatement_premium_convention"] != "toy_consumed_reinstated_limit_pro_rata_no_time":
        raise ToyTowerInputError("undefined or different reinstatement pricing")
    _int(contract["year"], "year", 2026, 2026)
    as_of = _date(contract["as_of_date"], "as-of date")
    if as_of.year != 2026:
        raise ToyTowerInputError("snapshot must be in synthetic cover year")
    if type(positions) is not dict or not 1 <= len(positions) <= 100:
        raise ToyTowerInputError("invalid fictional position collection")
    for unit, amount in positions.items():
        if type(unit) is not str or not unit.startswith("SYNTH-") or len(unit) > 24:
            raise ToyTowerInputError("non-fictional unit identity")
        _int(amount, "synthetic unit insured value", 1)

    layers = contract["layers"]
    if type(layers) is not list or not 1 <= len(layers) <= 8:
        raise ToyTowerInputError("one to eight fictional layers expected")
    last_end = 0
    seen_layers: set[str] = set()
    for layer in layers:
        _shape(layer, {"layer_id", "attachment_eur", "limit_eur", "reinstatements",
                       "base_premium_cents", "reinstatement_rate_bps", "covered_perils"}, "layer")
        name = layer["layer_id"]
        if type(name) is not str or not name.startswith("FICTIONAL-") or not 1 <= len(name) <= 48:
            raise ToyTowerInputError("invalid fictional layer identity")
        if name in seen_layers:
            raise ToyTowerInputError("duplicate fictional layer")
        seen_layers.add(name)
        att = _int(layer["attachment_eur"], "attachment")
        limit = _int(layer["limit_eur"], "occurrence limit", 1)
        _int(layer["reinstatements"], "reinstatements", 0, 3)
        _int(layer["base_premium_cents"], "toy base premium")
        _int(layer["reinstatement_rate_bps"], "toy RI rate bps", 0, 20000)
        if att < last_end:
            raise ToyTowerInputError("layer bands must not overlap on original gross basis")
        last_end = att + limit
        perils = layer["covered_perils"]
        if (type(perils) is not list or not perils
            or any(type(p) is not str or p not in ("flood", "windstorm") for p in perils)
            or perils != sorted(set(perils))):
            raise ToyTowerInputError("layer peril coverage must be sorted distinct known values")

    if type(events) is not list or not 1 <= len(events) <= 366:
        raise ToyTowerInputError("invalid fictional event list")
    recovered = {layer["layer_id"]: 0 for layer in layers}
    earned_ri = {layer["layer_id"]: 0 for layer in layers}
    event_ids: set[str] = set()
    prev_date = as_of
    output_events: list[dict[str, Any]] = []
    total_gross = total_ceded = total_ri_premium = 0
    for event in events:
        _shape(event, {"event_id", "date", "peril", "losses_eur"}, "event")
        eid = event["event_id"]
        if type(eid) is not str or not eid.startswith("FICTIONAL-") or not 1 <= len(eid) <= 48:
            raise ToyTowerInputError("only fictional events allowed")
        if eid in event_ids:
            raise ToyTowerInputError("duplicate event")
        event_ids.add(eid)
        date = _date(event["date"], "event date")
        if date.year != 2026 or date <= prev_date:
            raise ToyTowerInputError("events must be after snapshot and strictly date-ordered")
        prev_date = date
        peril = event["peril"]
        if type(peril) is not str or peril not in ("flood", "windstorm"):
            raise ToyTowerInputError("unknown or unsupported peril")
        losses = event["losses_eur"]
        if type(losses) is not dict or not losses:
            raise ToyTowerInputError("missing asset-event losses")
        gross = 0
        for unit, amount in losses.items():
            if unit not in positions:
                raise ToyTowerInputError("event references unknown synthetic exposure")
            _int(amount, "asset-event loss")
            if amount > positions[unit]:
                raise ToyTowerInputError("event loss exceeds that synthetic unit's value")
            gross += amount

        ceded_event = premium_event = 0
        cessions = []
        for layer in layers:
            name = layer["layer_id"]
            cap = layer["limit_eur"] * (1 + layer["reinstatements"])
            remaining = cap - recovered[name]
            provisional = (min(max(gross - layer["attachment_eur"], 0), layer["limit_eur"])
                           if peril in layer["covered_perils"] else 0)
            ceded = min(provisional, remaining)
            before_ri = earned_ri[name]
            recovered[name] += ceded
            after_ri = _earned_ri_cents(recovered[name], layer)
            increment = after_ri - before_ri
            if increment < 0:
                raise AssertionError("RI earned-premium charge must not decrease")
            earned_ri[name] = after_ri
            ceded_event += ceded
            premium_event += increment
            cessions.append({
                "layer_id": name, "covered": peril in layer["covered_perils"],
                "pre_aggregate_recovery_eur": provisional, "ceded_eur": ceded,
                "aggregate_remaining_before_eur": remaining,
                "aggregate_remaining_after_eur": cap - recovered[name],
                "incremental_reinstatement_premium_cents": increment,
                "cumulative_reinstatement_premium_cents": after_ri,
            })
        if not 0 <= ceded_event <= gross:
            raise AssertionError("non-overlap CAT-XL gross basis violated")
        total_gross += gross
        total_ceded += ceded_event
        total_ri_premium += premium_event
        output_events.append({
            "event_id": eid, "date": event["date"], "peril": peril,
            "gross_eur": gross, "ceded_eur": ceded_event,
            "net_insured_loss_eur": gross - ceded_event,
            "reinstatement_premium_cents": premium_event, "layers": cessions,
        })

    summary = [
        {"layer_id": layer["layer_id"],
         "ceded_eur": recovered[layer["layer_id"]],
         "reinstatement_premium_cents": earned_ri[layer["layer_id"]],
         "annual_base_premium_cents": layer["base_premium_cents"]}
        for layer in layers
    ]
    if (sum(x["ceded_eur"] for x in summary) != total_ceded
        or sum(x["reinstatement_premium_cents"] for x in summary) != total_ri_premium):
        raise AssertionError("layer and event totals must reconcile")
    net = total_gross - total_ceded
    base_premium_cents = sum(layer["base_premium_cents"] for layer in layers)
    return {
        "classification": "ORIGINAL_SYNTHETIC_TOWER_ARITHMETIC_ONLY",
        "model_input_approved": False, "real_insurer_or_treaty": False,
        "real_hazard_or_vulnerability": False, "currency": "EUR", "year": 2026,
        "gross_eur": total_gross, "ceded_eur": total_ceded,
        "net_insured_loss_eur": net,
        "reinstatement_premium_cents": total_ri_premium,
        "base_premium_cents": base_premium_cents,
        "net_plus_reinstatement_premium_cents": net * 100 + total_ri_premium,
        "net_plus_all_toy_premiums_cents": net * 100 + total_ri_premium + base_premium_cents,
        "events": output_events, "layers": summary,
    }


def fictional_example() -> tuple[dict[str, int], list[dict[str, Any]], dict[str, Any]]:
    """Independent, invented amounts matching the 12-position smoke-test arithmetic."""
    positions = {f"SYNTH-{i:02d}": 100_000 + 25_000 * i for i in range(1, 13)}
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
    layers = [
        {"layer_id": "FICTIONAL-L1", "attachment_eur": 200000, "limit_eur": 200000,
         "reinstatements": 1, "base_premium_cents": 2500000,
         "reinstatement_rate_bps": 10000, "covered_perils": ["flood", "windstorm"]},
        {"layer_id": "FICTIONAL-L2", "attachment_eur": 400000, "limit_eur": 300000,
         "reinstatements": 1, "base_premium_cents": 3000000,
         "reinstatement_rate_bps": 5000, "covered_perils": ["windstorm"]},
        {"layer_id": "FICTIONAL-L3", "attachment_eur": 700000, "limit_eur": 500000,
         "reinstatements": 0, "base_premium_cents": 4000000,
         "reinstatement_rate_bps": 0, "covered_perils": ["flood", "windstorm"]},
    ]
    contract = {
        "synthetic_only": True, "currency": "EUR", "year": 2026,
        "as_of_date": "2026-11-01", "basis": "independent_gross_occurrence",
        "reinstatement_premium_convention": "toy_consumed_reinstated_limit_pro_rata_no_time",
        "layers": layers,
    }
    return positions, events, contract


def main() -> int:
    positions, events, contract = fictional_example()
    print(json.dumps(calculate_toy_tower(positions, events, contract), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
