# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed synthetic CAT-XL loss ledger handoff; NOT NextGen execution or ORD.

This bridge is intentionally narrower than the original tower calculation.
It keeps insurer/physical-event/contractual-occurrence claims unasserted.
No network, database, external data, or third-party libraries are used.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from typing import Any


class HandoffError(ValueError):
    """An unauthorised or inconsistent fictional handoff."""


def _shape(value: Any, keys: set[str], context: str) -> None:
    if type(value) is not dict or set(value) != keys:
        raise HandoffError(f"{context}: unexpected or missing keys")


def _money(value: Any, context: str) -> int:
    if type(value) is not int or not 0 <= value <= 10**15:
        raise HandoffError(f"{context}: expected bounded nonnegative integer")
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def build_handoff(positions: dict[str, int], events: list[dict[str, Any]],
                  treaty: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    """Wrap an already computed fictional tower result, with independent checks.

    The SHA binds claimed *test-fixture bytes*, not external evidence or rights.
    No conclusion about loss model, event IDs, contractual occurrences or FX.
    """
    # Import is delayed to keep this module usable as a standalone read validator.
    from research_runners.synthetic_catxl_tower_v0 import calculate_toy_tower

    # Recompute the calculation instead of trusting a caller-supplied result.
    recalculated = calculate_toy_tower(positions, events, treaty)
    if result != recalculated:
        raise HandoffError("result differs from original synthetic tower replay")
    payload = {
        "profile": "OC-SYNTHETIC-CATXL-LEDGER-0.1",
        "admission": "RESEARCH_SYNTHETIC_ONLY_NOT_ADMITTED",
        "nextgen_execution_authorized": False,
        "ord_compatibility_attested": False,
        "currency": "EUR",
        "loss_unit": "whole_EUR",
        "premium_unit": "EUR_cent",
        "event_identity_semantics": "fictional_label_only_not_physical_or_contractual_occurrence",
        "input_fixture_sha256": _sha256({"positions": positions, "events": events, "treaty": treaty}),
        "gross_insured_loss_eur": result["gross_eur"],
        "ceded_loss_eur": result["ceded_eur"],
        "net_insured_loss_eur": result["net_insured_loss_eur"],
        "reinstatement_premium_cents": result["reinstatement_premium_cents"],
        "base_premium_cents": result["base_premium_cents"],
        "event_rows": [
            {
                "label": e["event_id"], "date": e["date"], "peril": e["peril"],
                "physical_event_id": None, "contractual_occurrence_id": None,
                "gross_insured_loss_eur": e["gross_eur"],
                "ceded_loss_eur": e["ceded_eur"],
                "net_insured_loss_eur": e["net_insured_loss_eur"],
                "reinstatement_premium_cents": e["reinstatement_premium_cents"],
                "layer_rows": [
                    {"layer_id": row["layer_id"], "ceded_loss_eur": row["ceded_eur"],
                     "reinstatement_premium_cents": row["incremental_reinstatement_premium_cents"]}
                    for row in e["layers"]
                ],
            } for e in result["events"]
        ],
        "layer_totals": [
            {"layer_id": row["layer_id"], "ceded_loss_eur": row["ceded_eur"],
             "reinstatement_premium_cents": row["reinstatement_premium_cents"]}
            for row in result["layers"]
        ],
    }
    receipt = {"payload": payload, "payload_sha256": _sha256(payload)}
    validate_handoff(receipt)
    return receipt


def validate_handoff(receipt: Any) -> None:
    """Check identity/monetary invariants, never authorize production handoff.

    SHA alone is not authentication: independent physical-event, source, peril,
    contract, hours and currency admission still needs a dedicated NextGen gate.
    """
    _shape(receipt, {"payload", "payload_sha256"}, "receipt")
    payload = receipt["payload"]
    _shape(payload, {
        "profile", "admission", "nextgen_execution_authorized",
        "ord_compatibility_attested", "currency", "loss_unit", "premium_unit",
        "event_identity_semantics", "input_fixture_sha256",
        "gross_insured_loss_eur", "ceded_loss_eur", "net_insured_loss_eur",
        "reinstatement_premium_cents", "base_premium_cents", "event_rows", "layer_totals",
    }, "payload")
    expected = {
        "profile": "OC-SYNTHETIC-CATXL-LEDGER-0.1",
        "admission": "RESEARCH_SYNTHETIC_ONLY_NOT_ADMITTED",
        "nextgen_execution_authorized": False,
        "ord_compatibility_attested": False,
        "currency": "EUR", "loss_unit": "whole_EUR", "premium_unit": "EUR_cent",
        "event_identity_semantics": "fictional_label_only_not_physical_or_contractual_occurrence",
    }
    for key, value in expected.items():
        if type(payload[key]) is not type(value) or payload[key] != value:
            raise HandoffError(f"incorrect immutable boundary field: {key}")
    if (type(payload["input_fixture_sha256"]) is not str or
        re.fullmatch(r"[0-9a-f]{64}", payload["input_fixture_sha256"]) is None):
        raise HandoffError("missing canonical synthetic fixture content hash")
    if type(receipt["payload_sha256"]) is not str or receipt["payload_sha256"] != _sha256(payload):
        raise HandoffError("payload changed or digest invalid")
    money_fields = ("gross_insured_loss_eur", "ceded_loss_eur",
                    "net_insured_loss_eur", "reinstatement_premium_cents", "base_premium_cents")
    for key in money_fields:
        _money(payload[key], key)
    if payload["gross_insured_loss_eur"] != payload["ceded_loss_eur"] + payload["net_insured_loss_eur"]:
        raise HandoffError("annual gross/ceded/net imbalance")
    rows, layers = payload["event_rows"], payload["layer_totals"]
    if type(rows) is not list or not 1 <= len(rows) <= 366:
        raise HandoffError("event rows missing or excessive")
    if type(layers) is not list or not 1 <= len(layers) <= 8:
        raise HandoffError("layer rows missing or excessive")
    layer_ids: list[str] = []
    for layer in layers:
        _shape(layer, {"layer_id", "ceded_loss_eur", "reinstatement_premium_cents"}, "layer total")
        if type(layer["layer_id"]) is not str or not re.fullmatch(r"FICTIONAL-[A-Za-z0-9-]{1,40}",layer["layer_id"]):
            raise HandoffError("invalid synthetic layer label")
        for key in ("ceded_loss_eur", "reinstatement_premium_cents"):
            _money(layer[key], key)
        layer_ids.append(layer["layer_id"])
    if len(set(layer_ids)) != len(layer_ids):
        raise HandoffError("duplicate layers")
    seen: set[str] = set()
    last_day: dt.date | None = None
    totals = {k: 0 for k in money_fields}
    layer_ceded = {k: 0 for k in layer_ids}
    layer_ri = {k: 0 for k in layer_ids}
    for event in rows:
        _shape(event, {"label", "date", "peril", "physical_event_id", "contractual_occurrence_id",
                       "gross_insured_loss_eur", "ceded_loss_eur", "net_insured_loss_eur",
                       "reinstatement_premium_cents", "layer_rows"}, "event")
        label = event["label"]
        if type(label) is not str or not re.fullmatch(r"FICTIONAL-[A-Za-z0-9-]{1,40}", label) or label in seen:
            raise HandoffError("duplicate or non-fictional event")
        seen.add(label)
        if event["physical_event_id"] is not None or event["contractual_occurrence_id"] is not None:
            raise HandoffError("cannot infer physical/contractual occurrence ID")
        if event["peril"] not in ("flood", "windstorm") or type(event["peril"]) is not str:
            raise HandoffError("unsupported fictional peril")
        if type(event["date"]) is not str or len(event["date"]) != 10:
            raise HandoffError("malformed event date")
        try:
            day = dt.date.fromisoformat(event["date"])
        except ValueError as exc:
            raise HandoffError("invalid event date") from exc
        if day.isoformat() != event["date"] or day.year != 2026 or (last_day is not None and day <= last_day):
            raise HandoffError("noncanonical/unordered fictional event date")
        last_day = day
        for key in money_fields[:-1]:
            _money(event[key], key)
            totals[key] += event[key]
        if event["gross_insured_loss_eur"] != event["ceded_loss_eur"] + event["net_insured_loss_eur"]:
            raise HandoffError("event gross/ceded/net mismatch")
        event_layers = event["layer_rows"]
        if type(event_layers) is not list or [x.get("layer_id") if type(x) is dict else None for x in event_layers] != layer_ids:
            raise HandoffError("missing/reordered/extra layer per event")
        summed_ceded = summed_ri = 0
        for item in event_layers:
            _shape(item, {"layer_id", "ceded_loss_eur", "reinstatement_premium_cents"}, "event layer")
            _money(item["ceded_loss_eur"], "event-layer ceded")
            _money(item["reinstatement_premium_cents"], "event-layer premium")
            layer_ceded[item["layer_id"]] += item["ceded_loss_eur"]
            layer_ri[item["layer_id"]] += item["reinstatement_premium_cents"]
            summed_ceded += item["ceded_loss_eur"]
            summed_ri += item["reinstatement_premium_cents"]
        if summed_ceded != event["ceded_loss_eur"] or summed_ri != event["reinstatement_premium_cents"]:
            raise HandoffError("event layer allocation does not reconcile")
    for key in money_fields[:-1]:
        if totals[key] != payload[key]:
            raise HandoffError(f"event/year reconciliation fails: {key}")
    for item in layers:
        name = item["layer_id"]
        if layer_ceded[name] != item["ceded_loss_eur"] or layer_ri[name] != item["reinstatement_premium_cents"]:
            raise HandoffError("layer annual totals do not reconcile")
    if sum(x["ceded_loss_eur"] for x in layers) != payload["ceded_loss_eur"] or sum(x["reinstatement_premium_cents"] for x in layers) != payload["reinstatement_premium_cents"]:
        raise HandoffError("layer/year totals do not reconcile")
