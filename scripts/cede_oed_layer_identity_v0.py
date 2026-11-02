# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, synthetic-only CEDE v10 -> OED v3 layer identity comparison.

The upstream Oasis account example maps LayerID to BOTH PolNumber and LayerNumber.
This checks candidate CSVs; it does NOT run ODS Tools, validate full OED, or admit data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__:
    from .cede_oed_output_reconcile_v0 import ReconcileError, _csv_rows, reconcile, MAX_FILE_BYTES
    from .cede_oed_synthetic_preflight_v0 import inspect, PreflightError, _no_duplicate_keys, _reject_constant
else:
    from cede_oed_output_reconcile_v0 import ReconcileError, _csv_rows, reconcile, MAX_FILE_BYTES
    from cede_oed_synthetic_preflight_v0 import inspect, PreflightError, _no_duplicate_keys, _reject_constant

LAYER_ROOT = {"source_version", "target_version", "synthetic_only", "layers"}
LAYER_KEYS = {"ExposureSetName", "ContractID", "LayerID", "Currency"}
OED_LAYER_KEYS = {"PortNumber", "AccNumber", "PolNumber", "LayerNumber", "AccCurrency"}
MAX_LAYERS = 10000


def reconcile_layers(exposure: object, layer_document: object,
                     locations: list[dict[str, str]], accounts: list[dict[str, str]]) -> dict[str, object]:
    inspected = inspect(exposure)
    if type(layer_document) is not dict or set(layer_document) != LAYER_ROOT:
        raise ReconcileError("unexpected synthetic layer document fields")
    if layer_document["source_version"] != "10.0.0" or layer_document["target_version"] != "3.0.2":
        raise ReconcileError("unsupported CEDE/OED layer mapping versions")
    if layer_document["synthetic_only"] is not True:
        raise ReconcileError("only independently invented synthetic layer data are allowed")
    layers = layer_document["layers"]
    if type(layers) is not list or not 0 < len(layers) <= MAX_LAYERS:
        raise ReconcileError("synthetic layers must be a nonempty bounded array")
    source_currencies: dict[tuple[str, str], set[str]] = {}
    for loc in exposure["rows"]:
        account = loc["ExposureSetName"], loc["ContractID"]
        source_currencies.setdefault(account, set()).add(loc["Currency"])
    if any(len(currencies) != 1 for currencies in source_currencies.values()):
        raise ReconcileError("synthetic account has mixed location currencies")
    expected: dict[tuple[str, str, str], str] = {}
    covered: set[tuple[str, str]] = set()
    for index, layer in enumerate(layers, 1):
        if type(layer) is not dict or set(layer) != LAYER_KEYS:
            raise ReconcileError(f"synthetic layer {index} missing or unexpected fields")
        if any(type(layer[f]) is not str or not layer[f] or layer[f] != layer[f].strip()
               for f in LAYER_KEYS):
            raise ReconcileError(f"synthetic layer {index} has invalid identity/currency")
        account = layer["ExposureSetName"], layer["ContractID"]
        key = (*account, layer["LayerID"])
        if account not in source_currencies:
            raise ReconcileError(f"synthetic layer {index} references unknown source account")
        if layer["Currency"] not in source_currencies[account]:
            raise ReconcileError(f"synthetic layer {index} currency differs from locations")
        if key in expected:
            raise ReconcileError(f"duplicate source synthetic layer {index}")
        expected[key] = layer["Currency"]
        covered.add(account)
    if covered != set(source_currencies):
        raise ReconcileError("synthetic source account missing any layer")
    # Existing legacy source-to-location reconciler checks counts and exact TIV,
    # but its account assumption is one row per account; use a fictional account
    # projection only for the location check, then verify true layer rows below.
    canonical_account_rows = [
        {"PortNumber": p, "AccNumber": a} for p, a in sorted(source_currencies)
    ]
    checked_locations = reconcile(exposure, locations, canonical_account_rows)
    if len(accounts) != len(expected):
        raise ReconcileError("OED layer row cardinality does not match source")
    seen: set[tuple[str, str, str]] = set()
    for index, row in enumerate(accounts, 1):
        if type(row) is not dict or not OED_LAYER_KEYS.issubset(row):
            raise ReconcileError(f"OED layer row {index} missing required columns")
        key = row["PortNumber"], row["AccNumber"], row["PolNumber"]
        if any(type(k) is not str or not k or k != k.strip() for k in key):
            raise ReconcileError(f"OED layer row {index} invalid identity")
        if key in seen or key not in expected:
            raise ReconcileError(f"OED layer row {index} duplicate or unmatched")
        seen.add(key)
        if row["LayerNumber"] != key[2] or row["AccCurrency"] != expected[key]:
            raise ReconcileError(f"OED layer row {index} changed layer identity or currency")
    return {
        "profile": "cede-oed-synthetic-layer-reconciliation-v0",
        "source_version": "10.0.0", "target_version": "3.0.2",
        "source_location_count": inspected["row_count"],
        "oed_location_count": checked_locations["oed_location_count"],
        "source_account_count": len(source_currencies),
        "source_layer_count": len(expected), "oed_layer_count": len(seen),
        "synthetic_totals_by_currency": checked_locations["synthetic_totals_by_currency"],
        "layer_identity_consistent": True,
        "executed_ods_tools": False, "oed_schema_validated": False,
        "peril_and_financial_terms_validated": False, "cede_13_compatible": False,
        "model_input_admitted": False, "rights_approved": False,
    }


def run(exposure_path: Path, layers_path: Path, location_path: Path, account_path: Path) -> dict[str, object]:
    paths = (exposure_path, layers_path, location_path, account_path)
    if len({p.resolve() for p in paths}) != 4:
        raise ReconcileError("all source/output paths must be distinct")
    if any(not p.is_file() or p.stat().st_size > MAX_FILE_BYTES for p in (exposure_path, layers_path)):
        raise ReconcileError("synthetic JSON input missing or exceeds byte limit")
    exposure = json.loads(exposure_path.read_text(encoding="utf-8"),
                          object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    layers = json.loads(layers_path.read_text(encoding="utf-8"),
                        object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    inspect(exposure)
    if type(layers) is not dict or type(layers.get("layers")) is not list or len(layers["layers"]) > MAX_LAYERS:
        raise ReconcileError("invalid synthetic layer array")
    loc_rows = _csv_rows(location_path, {"PortNumber", "AccNumber", "LocNumber", "CountryCode", "LocCurrency", "BuildingTIV", "ContentsTIV", "Latitude", "Longitude"}, len(exposure["rows"]))
    acc_rows = _csv_rows(account_path, OED_LAYER_KEYS, len(layers["layers"]))
    return reconcile_layers(exposure, layers, loc_rows, acc_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-exposure", type=Path, required=True)
    parser.add_argument("--synthetic-layers", type=Path, required=True)
    parser.add_argument("--oed-location", type=Path, required=True)
    parser.add_argument("--oed-account", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.synthetic_exposure, args.synthetic_layers, args.oed_location, args.oed_account)
    except (PreflightError, ReconcileError, OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
