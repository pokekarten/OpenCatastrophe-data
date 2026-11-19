# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Cross-check synthetic CEDE v10 input against candidate OED v3 CSV outputs.

This tool never invokes ODS Tools and does not establish OED schema validity,
CEDE v13 compatibility, model admissibility or data rights.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import json
from pathlib import Path

if __package__:
    from .cede_oed_synthetic_preflight_v0 import PreflightError, inspect, _no_duplicate_keys, _reject_constant
else:
    from cede_oed_synthetic_preflight_v0 import PreflightError, inspect, _no_duplicate_keys, _reject_constant

MAX_FILE_BYTES = 2_000_000
LOC_COLS = {"PortNumber", "AccNumber", "LocNumber", "CountryCode", "LocCurrency", "BuildingTIV", "ContentsTIV"}
ACC_COLS = {"PortNumber", "AccNumber"}
CROSSWALK = {
    "PortNumber": "ExposureSetName", "AccNumber": "ContractID",
    "LocNumber": "LocationID", "CountryCode": "CountryISO",
    "LocCurrency": "Currency", "BuildingTIV": "BuildingValue",
    "ContentsTIV": "ContentsValue",
}


class ReconcileError(ValueError):
    """Candidate synthetic output is incomplete, ambiguous, or inconsistent."""


def _csv_rows(path: Path, required: set[str], limit: int) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise ReconcileError("OED candidate CSV is absent or exceeds synthetic-only byte limit")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, restkey="__extra_columns__")
            fields = reader.fieldnames
            if not fields or any(not field for field in fields) or len(fields) != len(set(fields)):
                raise ReconcileError("CSV header missing, blank or duplicate")
            if not required.issubset(set(fields)):
                raise ReconcileError("CSV missing required OED field")
            rows = []
            for n, row in enumerate(reader, 1):
                if n > limit:
                    raise ReconcileError("CSV exceeds synthetic row limit")
                if None in row.values() or "__extra_columns__" in row:
                    raise ReconcileError("CSV row is truncated or over-wide")
                if any(type(v) is not str for v in row.values()):
                    raise ReconcileError("CSV cell is not a string")
                rows.append(row)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ReconcileError("CSV cannot be read cleanly") from exc
    return rows


def reconcile(payload: dict, location_rows: list[dict[str, str]],
              account_rows: list[dict[str, str]]) -> dict[str, object]:
    preflight = inspect(payload)
    source_by_id = {
        (r["ExposureSetName"], r["ContractID"], r["LocationID"]): r
        for r in payload["rows"]
    }
    expected_acc = {(r["ExposureSetName"], r["ContractID"]) for r in payload["rows"]}
    seen_loc: set[tuple[str, str, str]] = set()
    totals: dict[str, dict[str, Decimal]] = {}
    if len(location_rows) != len(source_by_id):
        raise ReconcileError("OED location cardinality does not match synthetic source")
    for number, row in enumerate(location_rows, 1):
        if not LOC_COLS.issubset(row):
            raise ReconcileError("OED location columns missing")
        key = (row["PortNumber"], row["AccNumber"], row["LocNumber"])
        if any(not x or x != x.strip() for x in key):
            raise ReconcileError(f"OED location row {number} has invalid identity")
        if key in seen_loc or key not in source_by_id:
            raise ReconcileError(f"OED location row {number} duplicate or unmatched")
        seen_loc.add(key)
        original = source_by_id[key]
        for oed, cede in CROSSWALK.items():
            if oed not in {"BuildingTIV", "ContentsTIV"} and row[oed] != original[cede]:
                raise ReconcileError(f"OED location row {number} changed {oed}")
        currency = row["LocCurrency"]
        bucket = totals.setdefault(currency, {"BuildingTIV": Decimal(0), "ContentsTIV": Decimal(0)})
        for target, source in (("BuildingTIV", "BuildingValue"), ("ContentsTIV", "ContentsValue")):
            value = row[target]
            try:
                val = Decimal(value)
            except (ArithmeticError, ValueError) as exc:
                raise ReconcileError(f"OED location row {number} invalid {target}") from exc
            if not val.is_finite() or val < 0 or val.as_tuple().exponent < -2:
                raise ReconcileError(f"OED location row {number} invalid {target}")
            if val != Decimal(original[source]):
                raise ReconcileError(f"OED location row {number} changed {target}")
            bucket[target] += val
        for field in ("Latitude", "Longitude"):
            if field in row and row[field] != original[field]:
                raise ReconcileError(f"OED location row {number} changed {field}")
    acc_seen: set[tuple[str, str]] = set()
    if len(account_rows) != len(expected_acc):
        raise ReconcileError("OED account cardinality does not match synthetic source")
    for number, row in enumerate(account_rows, 1):
        if not ACC_COLS.issubset(row):
            raise ReconcileError("OED account columns missing")
        key = (row["PortNumber"], row["AccNumber"])
        if any(not x or x != x.strip() for x in key) or key in acc_seen or key not in expected_acc:
            raise ReconcileError(f"OED account row {number} duplicate or unmatched")
        acc_seen.add(key)
    reported = {c: {field: format(total, ".2f") for field, total in sorted(group.items())}
                for c, group in sorted(totals.items())}
    if reported != preflight["synthetic_totals_by_currency"]:
        raise ReconcileError("Synthetic currency totals do not reconcile")
    return {"profile": "cede-oed-synthetic-output-reconciliation-v0",
            "source_version": "10.0.0", "target_version": "3.0.2",
            "source_location_count": len(source_by_id), "oed_location_count": len(seen_loc),
            "oed_account_count": len(acc_seen), "synthetic_totals_by_currency": reported,
            "direct_mapping_consistent": True,
            "executed_ods_tools": False, "oed_schema_validated": False,
            "cede_13_compatible": False, "model_input_admitted": False,
            "rights_approved": False}


def run(source: Path, location: Path, account: Path) -> dict[str, object]:
    if not source.is_file() or source.stat().st_size > MAX_FILE_BYTES:
        raise ReconcileError("synthetic input missing or exceeds byte limit")
    payload = json.loads(source.read_text(encoding="utf-8"),
                         object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    inspect(payload)
    if source.resolve() in (location.resolve(), account.resolve()) or location.resolve() == account.resolve():
        raise ReconcileError("input and output paths must be distinct")
    loc = _csv_rows(location, LOC_COLS, len(payload["rows"]))
    acc = _csv_rows(account, ACC_COLS, len({(r["ExposureSetName"], r["ContractID"]) for r in payload["rows"]}))
    return reconcile(payload, loc, acc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-input", type=Path, required=True)
    parser.add_argument("--oed-location", type=Path, required=True)
    parser.add_argument("--oed-account", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.synthetic_input, args.oed_location, args.oed_account)
    except (PreflightError, ReconcileError, OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
