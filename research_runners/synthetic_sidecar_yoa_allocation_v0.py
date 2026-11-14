#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic loss-ordering challenge for an audited sidecar YOA percentage.

No real Lloyd's loss, insurer portfolio, treaty operation or source admission.
The externally supplied recovery is *fictional*: this is not an XL engine.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN
import json
from pathlib import Path
import re
import sys

MONEY = re.compile(r"(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,4})?\Z")
EVENT = re.compile(r"SYNTH_[A-Z0-9_]{1,64}\Z")
UNIT = re.compile(r"[A-Z]{3}\Z")
CENTI = Decimal("0.0001")
# Audited 2025 accounts of Syndicate 6117; 2026 is a *proposed* next YoA.
SHARES = {
    2023: (Decimal("0.1168"), "historical_yoa"),
    2024: (Decimal("0.1328"), "historical_yoa"),
    2025: (Decimal("0.1527"), "historical_yoa"),
    2026: (Decimal("0.0418"), "proposed_future_yoa"),
}
SOURCE = "https://assets.lloyds.com/media-651c0e64-c1d0-4f97-90f7-883c69fe2ef2/d0c78619-c395-42fd-97b2-49a13bc87990/6117_Accounts_2025Q4_20260219_131838.html"


class SidecarAllocationBlocked(ValueError):
    """Insufficient ordering, YOA or synthetic input evidence."""


def _amount(value: object, field: str) -> Decimal:
    if type(value) is not str or not MONEY.fullmatch(value):
        raise SidecarAllocationBlocked(field + ": canonical decimal-string money required")
    return Decimal(value)


def allocate(scenario: dict) -> dict:
    """Fictional host GUL -> external recovery -> 6117 share -> *unallocated* remainder.

    This split cannot resolve host retained risk or additional SPA 6136 shares.
    The money columns are synthetic even though the YOA rate is publicly reported.
    """
    required = {"schema_version", "scenario_kind", "unit", "year_of_account",
                "financial_year", "external_reinsurance_order", "source_basis",
                "events"}
    if type(scenario) is not dict or set(scenario) != required:
        raise SidecarAllocationBlocked("exact synthetic scenario keys required")
    if scenario["schema_version"] != "0.1.0" or scenario["scenario_kind"] != "fully_synthetic_test_only":
        raise SidecarAllocationBlocked("only wholly fictional scenarios are supported")
    if scenario["source_basis"] != "lloyds_6117_2025_audited_accounts_yoa_disclosure":
        raise SidecarAllocationBlocked("published YOA source basis required")
    if scenario["external_reinsurance_order"] != "host_external_reinsurance_before_sidecar":
        raise SidecarAllocationBlocked("sidecar is net of host's prior external reinsurance")
    if type(scenario["unit"]) is not str or not UNIT.fullmatch(scenario["unit"]):
        raise SidecarAllocationBlocked("single uppercase ISO-like money unit required")
    year = scenario["year_of_account"]
    if type(year) is not int or year not in SHARES:
        raise SidecarAllocationBlocked("unsupported source year of account")
    if scenario["financial_year"] != 2025 or type(scenario["financial_year"]) is not int:
        raise SidecarAllocationBlocked("2025 audited financial-report vintage must be distinct from YoA")
    share, status = SHARES[year]
    if status == "proposed_future_yoa":
        raise SidecarAllocationBlocked("2026 YoA 4.18% is proposed, not an observed final risk share")
    rows = scenario["events"]
    if type(rows) is not list or not 1 <= len(rows) <= 128:
        raise SidecarAllocationBlocked("expected 1..128 fictional loss rows")
    seen: set[str] = set()
    output = []
    totals = [Decimal(0), Decimal(0), Decimal(0), Decimal(0)]
    for item in rows:
        if type(item) is not dict or set(item) != {"event_id", "host_gross_loss", "host_external_reinsurance_recovery"}:
            raise SidecarAllocationBlocked("bad event fields")
        event_id = item["event_id"]
        if type(event_id) is not str or not EVENT.fullmatch(event_id) or event_id in seen:
            raise SidecarAllocationBlocked("event must have a unique SYNTH_ identifier")
        seen.add(event_id)
        gross = _amount(item["host_gross_loss"], "host_gross_loss")
        recovery = _amount(item["host_external_reinsurance_recovery"], "host_external_reinsurance_recovery")
        if recovery > gross:
            raise SidecarAllocationBlocked("external recovery cannot exceed host gross loss")
        net = gross - recovery
        sidecar = (net * share).quantize(CENTI, rounding=ROUND_HALF_EVEN)
        other = net - sidecar
        if gross != recovery + sidecar + other:
            raise SidecarAllocationBlocked("loss conservation failed")
        for i, amount in enumerate((gross, recovery, sidecar, other)):
            totals[i] += amount
        output.append({"event_id": event_id, "host_gross_loss": str(gross),
                       "host_external_reinsurance_recovery": str(recovery),
                       "sidecar_6117_fictional_loss": str(sidecar),
                       "other_post_external_allocation_unresolved": str(other)})
    if totals[0] != sum(totals[1:]):
        raise SidecarAllocationBlocked("aggregate loss conservation failed")
    return {"schema_version": "0.1.0", "audit": "sidecar-yoa-net-of-host-ri-order-v0",
            "reported_rate_source": SOURCE,
            "source_statement_status": status,
            "financial_report_year": 2025, "year_of_account": year,
            "sidecar_fraction": str(share), "currency": scenario["unit"],
            "events": output,
            "gross_total": str(totals[0]), "host_external_reinsurance_recovery_total": str(totals[1]),
            "sidecar_6117_loss_total": str(totals[2]),
            "other_post_external_allocation_unresolved_total": str(totals[3]),
            "host_ultimate_retention_established": False,
            "other_sidecars_resolved": False,
            "actual_underwriting_losses_established": False,
            "cat_policy_treaty_or_model_admission_granted": False}


def _strict_object(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise SidecarAllocationBlocked("duplicate JSON key")
        out[k] = v
    return out


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print("usage: python -m research_runners.synthetic_sidecar_yoa_allocation_v0 SCENARIO.json", file=sys.stderr)
        return 2
    try:
        path = Path(argv[0])
        if not path.is_file() or path.stat().st_size > 300_000:
            raise SidecarAllocationBlocked("missing or oversized scenario")
        item = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object,
                          parse_constant=lambda _x: (_ for _ in ()).throw(SidecarAllocationBlocked("nonfinite JSON number")))
        result = allocate(item)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
