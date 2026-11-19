# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded CEDE-v10/OED-v3 legacy mapping preflight on synthetic values only.

This deliberately does NOT invoke ODS Tools, emit OED files, inspect CEDE backup
bytes, or establish CEDE 13.0 compatibility or admission rights.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

SOURCE_VERSION = "10.0.0"
TARGET_VERSION = "3.0.2"
# Public Oasis ODS Tools example mapping *blob* SHAs observed 2026-11-02.
LOCATION_MAPPING_SHA = "b5433d6bc7f5ecd926fba4899dc12245d9b1e64a"
ACCOUNT_MAPPING_SHA = "81a0f2e0aab4d140e8dd403f16ebd12d42d804c8"
ROOT_KEYS = {"source_format", "source_version", "target_format", "target_version", "synthetic_only", "rows"}
ROW_KEYS = {"ExposureSetName", "ContractID", "LocationID", "CountryISO", "Currency",
            "BuildingValue", "ContentsValue", "Latitude", "Longitude"}
NUMBER = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")
SIGNED_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
ISO2 = re.compile(r"^[A-Z]{2}$")
ISO3 = re.compile(r"^[A-Z]{3}$")
MAX_ROWS = 10000


class PreflightError(ValueError):
    """A synthetic-only profile is unsupported or unsafe to inspect."""


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PreflightError("duplicate JSON key is not allowed")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PreflightError("non-finite JSON number is not allowed")


def _money(value: object, field: str, index: int) -> Decimal:
    if type(value) is not str or not NUMBER.fullmatch(value):
        raise PreflightError(f"row {index}: {field} must be a nonnegative decimal string with <=2 decimal places")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise PreflightError(f"row {index}: invalid {field}") from exc
    if not result.is_finite():
        raise PreflightError(f"row {index}: invalid {field}")
    return result


def _coordinate(value: object, field: str, index: int, limit: int) -> Decimal | None:
    if value == "":
        return None
    if type(value) is not str or not SIGNED_DECIMAL.fullmatch(value):
        raise PreflightError(f"row {index}: malformed {field}")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise PreflightError(f"row {index}: malformed {field}") from exc
    if not result.is_finite() or abs(result) > limit:
        raise PreflightError(f"row {index}: {field} out of range")
    return result


def inspect(payload: object) -> dict[str, object]:
    if type(payload) is not dict or set(payload) != ROOT_KEYS:
        raise PreflightError("unexpected or missing document fields")
    if payload["source_format"] != "CEDE" or payload["target_format"] != "OED":
        raise PreflightError("only legacy CEDE to OED preflight is supported")
    if payload["source_version"] != SOURCE_VERSION or payload["target_version"] != TARGET_VERSION:
        raise PreflightError("unsupported CEDE/OED mapping version; CEDE 13.0 is NOT validated")
    if payload["synthetic_only"] is not True:
        raise PreflightError("real, licensed or unidentified exposure is forbidden in synthetic preflight")
    rows = payload["rows"]
    if type(rows) is not list or not 0 < len(rows) <= MAX_ROWS:
        raise PreflightError("synthetic rows must be a nonempty bounded array")
    seen = set()
    portfolios = set()
    accounts = set()
    totals: dict[str, dict[str, Decimal]] = {}
    missing_coordinates = 0
    for n, row in enumerate(rows, start=1):
        if type(row) is not dict or set(row) != ROW_KEYS:
            raise PreflightError(f"row {n}: unexpected or missing fields; unreviewed CEDE 13 fields are blocked")
        for field in ("ExposureSetName", "ContractID", "LocationID"):
            if type(row[field]) is not str or not row[field].strip() or row[field] != row[field].strip():
                raise PreflightError(f"row {n}: missing or noncanonical {field}")
        identity = (row["ExposureSetName"], row["ContractID"], row["LocationID"])
        if identity in seen:
            raise PreflightError(f"row {n}: duplicate synthetic location identity")
        seen.add(identity)
        portfolios.add(row["ExposureSetName"])
        accounts.add((row["ExposureSetName"], row["ContractID"]))
        if type(row["CountryISO"]) is not str or not ISO2.fullmatch(row["CountryISO"]):
            raise PreflightError(f"row {n}: invalid CountryISO format")
        currency = row["Currency"]
        if type(currency) is not str or not ISO3.fullmatch(currency):
            raise PreflightError(f"row {n}: invalid Currency format")
        building = _money(row["BuildingValue"], "BuildingValue", n)
        contents = _money(row["ContentsValue"], "ContentsValue", n)
        lat = _coordinate(row["Latitude"], "Latitude", n, 90)
        lon = _coordinate(row["Longitude"], "Longitude", n, 180)
        if (lat is None) != (lon is None):
            raise PreflightError(f"row {n}: partial geographic coordinates are blocked")
        if lat is None:
            missing_coordinates += 1
        bucket = totals.setdefault(currency, {"BuildingTIV": Decimal(0), "ContentsTIV": Decimal(0)})
        bucket["BuildingTIV"] += building
        bucket["ContentsTIV"] += contents
    return {
        "profile": "cede-oed-synthetic-preflight-v0",
        "observed_upstream_mapping": {"source_version": SOURCE_VERSION, "target_version": TARGET_VERSION,
                                      "location_mapping_blob_sha": LOCATION_MAPPING_SHA,
                                      "account_mapping_blob_sha": ACCOUNT_MAPPING_SHA},
        "row_count": len(rows), "exposure_set_count": len(portfolios),
        "account_count": len(accounts), "rows_without_coordinates": missing_coordinates,
        "mapped_field_examples": {"LocationID": "LocNumber", "ContractID": "AccNumber",
                                  "BuildingValue": "BuildingTIV", "ContentsValue": "ContentsTIV",
                                  "CountryISO": "CountryCode", "Currency": "LocCurrency"},
        "synthetic_totals_by_currency": {
            c: {k: format(v, ".2f") for k, v in sorted(bucket.items())}
            for c, bucket in sorted(totals.items())
        },
        "executed_ods_tools": False,
        "generated_oed_files": False,
        "cede_13_compatible": False,
        "rights_approved": False,
        "model_input_admitted": False,
    }


def run(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    return inspect(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-input", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.synthetic_input)
    except (OSError, UnicodeError, json.JSONDecodeError, PreflightError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
