# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed OED 5.0 export of *persisted* fictional account/policy/TIV rows.

Input is the sole JSON value from oed_synthetic_relational_snapshot_v1.sql
on Neon validation branch; no credentials, database access, real locations or
true insurance sums. The original synthetic smoke fixture is revalidated.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from research_runners.export_synthetic_oed_v0 import (
    ACCOUNT, ACCOUNT_FIELDS, LOCATION_FIELDS, OED_VERSION, POLICY, PORT,
    SYNTHETIC_PERILS, SyntheticOedError, decimal, project,
)

COLUMNS = {
    "building": "BuildingTIV",
    "contents": "ContentsTIV",
    "bi": "BITIV",
    "other": "OtherTIV",
}


def project_relational(snapshot: object) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    locations, _ = project(snapshot)  # exact 12 fixture / source provenance guard
    if not isinstance(snapshot, dict):
        raise SyntheticOedError("relational snapshot must be an object")
    account, policy = snapshot.get("account"), snapshot.get("policy")
    if (not isinstance(account, dict)
        or account != {"account_key": ACCOUNT, "currency": "EUR",
                       "synthetic": True, "source_key": None}):
        raise SyntheticOedError("unexpected/non-synthetic persisted account")
    if (not isinstance(policy, dict)
        or policy != {"policy_key": POLICY, "policy_perils_oed": SYNTHETIC_PERILS,
                      "synthetic": True, "source_key": None}):
        raise SyntheticOedError("unexpected/non-synthetic persisted policy")
    by_id = {unit["external_unit_id"]: unit for unit in snapshot["units"]}
    if len(by_id) != len(locations):
        raise SyntheticOedError("duplicate or missing normalized location IDs")
    for location in locations:
        source = by_id[location["LocNumber"]]
        if source.get("location_perils_oed") != policy["policy_perils_oed"]:
            raise SyntheticOedError("inconsistent persisted peril coverage")
        raw = source.get("tiv_components")
        if not isinstance(raw, dict) or set(raw) != set(COLUMNS):
            raise SyntheticOedError("exactly four persisted TIV components required")
        totals = {}
        for name, column in COLUMNS.items():
            amount = decimal(raw[name], name)
            if amount < 0:
                raise SyntheticOedError("negative TIV")
            totals[name] = amount
            location[column] = str(amount)
        # This is an INVENTED test allocation, not a legal insured-value claim.
        if totals["building"] != decimal(source["insured_value"], "insured_value") or any(
            totals[name] != 0 for name in ("contents", "bi", "other")
        ):
            raise SyntheticOedError("source/persisted component conservation drift")
        location["LocPerilsCovered"] = source["location_perils_oed"]
    if sum(decimal(loc["BuildingTIV"], "BuildingTIV") for loc in locations) != 3150000:
        raise SyntheticOedError("relational total not conserved")
    accounts = [{
        "PortNumber": PORT, "AccNumber": account["account_key"],
        "AccCurrency": account["currency"], "PolNumber": policy["policy_key"],
        "PolPerilsCovered": policy["policy_perils_oed"], "OEDVersion": OED_VERSION,
    }]
    return locations, accounts


def export_relational(snapshot: object, outdir: Path) -> tuple[Path, Path]:
    locations, accounts = project_relational(snapshot)
    if outdir.exists() or not outdir.parent.is_dir():
        raise SyntheticOedError("output directory must be new and parent must exist")
    outdir.mkdir(mode=0o700)
    try:
        for filename, columns, rows in [
            ("location.csv", LOCATION_FIELDS, locations),
            ("account.csv", ACCOUNT_FIELDS, accounts),
        ]:
            with (outdir / filename).open("x", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
    except Exception:
        for file in outdir.iterdir():
            file.unlink()
        outdir.rmdir()
        raise
    return outdir / "location.csv", outdir / "account.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="Single JSON snapshot from read-only Neon SQL")
    parser.add_argument("output_directory", type=Path, help="New directory for disposable OED CSVs")
    args = parser.parse_args()
    try:
        files = export_relational(
            json.loads(args.snapshot.read_text(encoding="utf-8")), args.output_directory
        )
    except (OSError, ValueError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print("SYNTHETIC, NOT MODEL-APPROVED: " + ", ".join(str(p) for p in files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
