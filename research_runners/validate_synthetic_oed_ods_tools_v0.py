# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Official ODS Tools check for the wholly invented OED 5.0 smoke exposure.

Run with pinned ods-tools==5.0.8.  This script never accesses Neon, a provider,
or private/real exposure.  No files survive the temporary directory.
"""
from __future__ import annotations

import csv
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from research_runners.export_synthetic_oed_v0 import export  # noqa: E402
from test_export_synthetic_oed_v0 import fixture  # noqa: E402


def main() -> int:
    from ods_tools import __version__ as tools_version
    from ods_tools.oed import OedExposure, OdsException

    if tools_version != "5.0.8":
        raise RuntimeError(f"ODS Tools 5.0.8 required; found {tools_version}")

    with tempfile.TemporaryDirectory(prefix="synthetic_oed_v5_") as root:
        location, account = export(fixture(), Path(root) / "oed")
        # Constructor validation deliberately uses the library API: in some
        # versions the CLI check catches and logs OdsException.
        OedExposure(location=str(location), account=str(account), check_oed=True)

        # Negative challenge: CountryCode is required. Verify the API raises;
        # some CLI versions only log errors but return success.
        missing_country = Path(root) / "invalid_location.csv"
        with location.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            source_rows = list(reader)
            source_fields = list(reader.fieldnames or ())
        fields = [field for field in source_fields if field != "CountryCode"]
        with missing_country.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore",
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(source_rows)
        try:
            OedExposure(location=str(missing_country), account=str(account),
                        check_oed=True)
        except OdsException:
            pass
        else:
            raise RuntimeError("ODS Tools accepted a missing CountryCode")

        with location.open(newline="", encoding="utf-8") as file:
            locations = list(csv.DictReader(file))
        with account.open(newline="", encoding="utf-8") as file:
            accounts = list(csv.DictReader(file))
        assert len(locations) == 12 and len(accounts) == 1
        assert accounts[0]["AccNumber"] == "SYNTH-ACC-01"
        assert all(row["AccNumber"] == accounts[0]["AccNumber"] for row in locations)
        tiv = sum(
            Decimal(row["BuildingTIV"]) + Decimal(row["OtherTIV"]) +
            Decimal(row["ContentsTIV"]) + Decimal(row["BITIV"])
            for row in locations
        )
        assert tiv == Decimal("3150000")
        assert all(row["OEDVersion"] == "5.0.0" for row in locations)
    print("PASS: pinned ods-tools 5.0.8 validated 12 invented OED 5.0 locations and one invented account; invalid schema rejected; EUR 3,150,000 conserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
