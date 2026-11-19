#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed CHIRPS3-GEFS daily forecast issue-vintage candidate checker.

This checks a *synthetic or external research claim* for internal consistency.
It neither fetches an original issue nor proves that WFP retained an issue.
No network, file writes, actual forecast backtests or source admission.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import re

SOURCE_ID = "wfp.hdc.chirps3-gefs-daily-forecast.v3"
PRODUCT_VERSION = "v3.0"
MAX_BYTES = 16384
SHA_RE = re.compile(r"[a-f0-9]{64}\Z")
FIELDS = {
    "source_id", "product_version", "issue_date", "valid_date",
    "lead_days", "asset_sha256", "research_role",
}
ALLOWED_ROLE = "prospective_forecast_context_only"


class Blocked(ValueError):
    """Block speculative forecast as-of, skill, observation or insurance claims."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise Blocked("duplicate JSON key")
        seen[key] = value
    return seen


def _reject_constant(_: str) -> None:
    raise Blocked("non-finite JSON value")


def _date(value: object, name: str) -> date:
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise Blocked(name + " must be an exact ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Blocked(name + " is not a calendar date") from exc


def inspect_claim(raw: bytes) -> dict[str, object]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise Blocked("empty or oversized research claim")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Blocked("invalid strict JSON") from exc
    if type(value) is not dict or set(value) != FIELDS:
        raise Blocked("unexpected research claim fields")
    if value["source_id"] != SOURCE_ID or value["product_version"] != PRODUCT_VERSION:
        raise Blocked("wrong forecast product or version")
    if value["research_role"] != ALLOWED_ROLE:
        raise Blocked("observed event, financial claim or historical backtest not authorized")
    issued = _date(value["issue_date"], "issue_date")
    valid = _date(value["valid_date"], "valid_date")
    lead = value["lead_days"]
    if type(lead) is not int or not 0 <= lead <= 15:
        raise Blocked("GEFS daily forecast lead must be an integer from 0 to 15")
    if issued < date(2001, 1, 1) or valid != issued + timedelta(days=lead):
        raise Blocked("issue/valid date/lead mismatch or unverified historical coverage")
    digest = value["asset_sha256"]
    if type(digest) is not str or not SHA_RE.fullmatch(digest):
        raise Blocked("asset SHA-256 must have 64 lower-case hex digits")
    # SHA equality and date arithmetic alone are not provider provenance.
    # Never silently promote metadata to an immutable issue archive.
    return {
        "profile": "wfp-chirps3-gefs-daily-issue-claim-v0",
        "source_id": SOURCE_ID,
        "product_version": PRODUCT_VERSION,
        "issue_date": issued.isoformat(),
        "valid_date": valid.isoformat(),
        "lead_days": lead,
        "asset_sha256_claimed": digest,
        "issue_valid_lead_consistent": True,
        "data_role": "forecast_context_only",
        "original_issue_bytes_verified": False,
        "historical_issue_archive_verified": False,
        "independent_rainfall_observation": False,
        "as_of_backtesting_authorized": False,
        "insured_loss_model_input_admitted": False,
        "all_external_rights_reviewed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-json", type=Path, required=True,
                        help="Offline local research claim JSON, not an original source file")
    args = parser.parse_args(argv)
    try:
        with args.claim_json.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        result = inspect_claim(raw)
    except (Blocked, OSError) as exc:
        print("BLOCKED: " + str(exc))
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
