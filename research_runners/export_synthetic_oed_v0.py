# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Export ONLY the independently invented 12-location Neon smoke fixture to OED 5.0.

This is a CSV/round-trip plumbing proof, not an ODS_Tools certification, an
insured exposure, a commercial dataset, or a model lookup/financial run.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

OED_VERSION = "5.0.0"
PORT = "oc-synthetic-exposure-smoke-v0"
ACCOUNT = "SYNTH-ACC-01"
POLICY = "SYNTH-POL-01"
# Explicit hypothetical coverage choices.  WW2 excludes storm surge; OO1 is
# the flood group without storm surge.  These CANNOT be inferred from the DB's
# generic ['windstorm', 'flood'] perimeter or actual contract wording.
SYNTHETIC_PERILS = "WW2;OO1"
LOCATION_FIELDS = (
    "PortNumber", "AccNumber", "LocNumber", "CountryCode", "Latitude",
    "Longitude", "LocPerilsCovered", "BuildingTIV", "OtherTIV",
    "ContentsTIV", "BITIV", "LocCurrency", "NumberOfBuildings", "OEDVersion",
)
ACCOUNT_FIELDS = (
    "PortNumber", "AccNumber", "AccCurrency", "PolNumber",
    "PolPerilsCovered", "OEDVersion",
)


class SyntheticOedError(ValueError):
    """Unsafe input or unsupported projection."""


def decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise SyntheticOedError(f"{field}: numeric value required")
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise SyntheticOedError(f"{field}: invalid decimal") from exc
    if not n.is_finite():
        raise SyntheticOedError(f"{field}: non-finite decimal")
    return n


def project(snapshot: object) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    if not isinstance(snapshot, dict):
        raise SyntheticOedError("snapshot must be a JSON object")
    if snapshot.get("portfolio_key") != PORT or snapshot.get("portfolio_type") != "synthetic":
        raise SyntheticOedError("not the independent synthetic smoke portfolio")
    if snapshot.get("organization_id") is not None or snapshot.get("version_label") != "v0":
        raise SyntheticOedError("real insurer linkage or unexpected version")
    if snapshot.get("generation_method") != "deterministic_independent_synthetic_sql_v0":
        raise SyntheticOedError("unexpected generation method")
    assumptions = snapshot.get("assumptions")
    if not isinstance(assumptions, dict) or assumptions.get("synthetic") is not True or assumptions.get("real_insurer") is not False or assumptions.get("real_buildings") is not False or assumptions.get("model_input_approved") is not False or assumptions.get("external_source_rows_used") != 0:
        raise SyntheticOedError("missing mandatory fail-closed synthetic provenance")
    units = snapshot.get("units")
    if not isinstance(units, list) or len(units) != 12:
        raise SyntheticOedError("only the exact 12-location fixture is supported")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    total = Decimal(0)
    for unit in units:
        if not isinstance(unit, dict):
            raise SyntheticOedError("unit must be an object")
        loc = unit.get("external_unit_id")
        if not isinstance(loc, str) or not re.fullmatch(r"SYNTH-(?:0[1-9]|1[0-2])", loc) or loc in seen:
            raise SyntheticOedError("invalid or duplicate synthetic location ID")
        seen.add(loc)
        n = int(loc.rsplit("-", 1)[1])
        if (unit.get("source_key") is not None
            or unit.get("assumption_status") != "synthetic"
            or unit.get("unit_type") != "asset"
            or unit.get("country_code") != "DE"
            or unit.get("insured_value_currency") != "EUR"
            or unit.get("value_basis") != "invented_smoke_test_value_not_insured_observation"):
            raise SyntheticOedError(f"{loc}: input is not the approved invented fixture")
        value = decimal(unit.get("insured_value"), "insured_value")
        if value != 100000 + 25000 * n:
            raise SyntheticOedError(f"{loc}: source value differs from canonical synthetic recipe")
        if decimal(unit.get("building_count"), "building_count") != 1:
            raise SyntheticOedError(f"{loc}: expected one invented building")
        latitude = decimal(unit.get("latitude"), "latitude")
        longitude = decimal(unit.get("longitude"), "longitude")
        if abs(latitude - (Decimal("50.0") + ((n - 1) // 4) * Decimal("0.1"))) > Decimal("0.00000001") or abs(longitude - (Decimal("9.9") + (n % 4) * Decimal("0.1"))) > Decimal("0.00000001"):
            raise SyntheticOedError(f"{loc}: coordinates differ from invented grid")
        total += value
        rows.append({
            "PortNumber": PORT, "AccNumber": ACCOUNT, "LocNumber": loc,
            "CountryCode": "DE", "Latitude": str(latitude), "Longitude": str(longitude),
            "LocPerilsCovered": SYNTHETIC_PERILS,
            # 100% building allocation is an EXTRA hypothetical choice, not
            # a valuation/coverage claim from Neon or an insurance contract.
            "BuildingTIV": str(value), "OtherTIV": "0", "ContentsTIV": "0",
            "BITIV": "0", "LocCurrency": "EUR", "NumberOfBuildings": "1",
            "OEDVersion": OED_VERSION,
        })
    if total != 3150000 or seen != {f"SYNTH-{n:02}" for n in range(1, 13)}:
        raise SyntheticOedError("fixture identity/value conservation failed")
    rows.sort(key=lambda r: r["LocNumber"])
    accounts = [{
        "PortNumber": PORT, "AccNumber": ACCOUNT, "AccCurrency": "EUR",
        "PolNumber": POLICY, "PolPerilsCovered": SYNTHETIC_PERILS,
        "OEDVersion": OED_VERSION,
    }]
    return rows, accounts


def export(snapshot: object, outdir: Path) -> tuple[Path, Path]:
    locations, accounts = project(snapshot)  # validate BEFORE creating files
    if outdir.exists():
        raise SyntheticOedError("output directory must not already exist")
    if not outdir.parent.is_dir():
        raise SyntheticOedError("output parent does not exist")
    outdir.mkdir(mode=0o700)
    try:
        for name, fields, rows in (
            ("location.csv", LOCATION_FIELDS, locations),
            ("account.csv", ACCOUNT_FIELDS, accounts),
        ):
            with (outdir / name).open("x", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
    except Exception:
        for f in outdir.iterdir():
            f.unlink()
        outdir.rmdir()
        raise
    return outdir / "location.csv", outdir / "account.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="JSON output from synthetic_oed_snapshot_v0.sql")
    parser.add_argument("output_directory", type=Path, help="fresh directory for 2 synthetic CSVs")
    args = parser.parse_args()
    try:
        result = export(json.loads(args.snapshot.read_text(encoding="utf-8")), args.output_directory)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(f"SYNTHETIC ONLY; NOT MODEL-APPROVED: {result[0]} | {result[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
