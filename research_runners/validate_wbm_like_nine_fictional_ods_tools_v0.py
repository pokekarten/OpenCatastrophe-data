# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Check nine *fictional* OED 5.0 CSVs with pinned official ods-tools==5.0.8.

Never makes CAT model keys, GUL/IL/FML or annual loss curves. No live insurer
contract, site data, database access, company mapping or reinsurance is used.
"""
from __future__ import annotations

import csv
import json
import tempfile
from decimal import Decimal
from pathlib import Path

from . import wbm_like_nine_fictional_oed_v0 as synth


def main() -> int:
    from ods_tools import __version__ as version
    from ods_tools.oed import OedExposure, OdsException

    if version != "5.0.8":
        raise RuntimeError("pinned ods-tools 5.0.8 required")
    with tempfile.TemporaryDirectory(prefix="nine_fictional_commercial_oed_") as d:
        out = Path(d)
        location, account, manifest = synth.export(out / "fictional9")
        OedExposure(location=str(location), account=str(account), check_oed=True)
        with location.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        with account.open(encoding="utf-8", newline="") as f:
            acc = list(csv.DictReader(f))
        meta = json.loads(manifest.read_text(encoding="utf-8"))
        synth.validate(rows, acc, meta)
        if (len(rows) != 9 or len(acc) != 1 or
                sum(Decimal(r["BuildingTIV"]) for r in rows)
                != synth.TOTAL_FAKE_BUILDING_EUR):
            raise RuntimeError("fictional nine-site arithmetic drift")
        # Challenge the official library, not only our own projection:
        # CountryCode is mandatory in the OED location file.
        without_country = out / "negative_country_missing.csv"
        with without_country.open("w", encoding="utf-8", newline="") as f:
            fields = [c for c in rows[0] if c != "CountryCode"]
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore",
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        try:
            OedExposure(location=str(without_country), account=str(account),
                        check_oed=True)
        except OdsException:
            pass
        else:
            raise RuntimeError("official ODS library accepted missing CountryCode")

    print("PASS: official ods-tools 5.0.8 accepted nine FICTIONAL OED 5.0 "
          "commercial-grid sites; one invented policy/account; invented "
          "EUR108m test TIV; invalid CountryCode rejected; "
          "NO source insurer property exposure / GUL/IL/RI curves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
