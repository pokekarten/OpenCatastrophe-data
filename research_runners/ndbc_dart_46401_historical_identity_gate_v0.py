#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One exact documented NDBC-owned 2004 DART station source, offline only.

This is a frozen *historical* source identity and format preflight, not an
HTTP client, current-operational claim, provider-origin attestation, source
rights decision, tsunami science validation or CAT model admission.

Authority: https://www.ndbc.noaa.gov/dart_data_access.shtml
Station history: https://www.ndbc.noaa.gov/station_history.php?station=46401
Station page: https://www.ndbc.noaa.gov/station_page.php?station=46401
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from research_runners.ndbc_dart_original_preflight_v0 import (
    DARTPreflightError,
    preflight,
)

STATION = "46401"
START = "2004-01-18"
END = "2004-01-22"
ORIGINAL_DOCUMENTED_URL = (
    "https://www.ndbc.noaa.gov/dart_data.php"
    "?station=46401&start=2004-01-18&end=2004-01-22"
)
STATION_HISTORY_URL = "https://www.ndbc.noaa.gov/station_history.php?station=46401"
DART_API_DOCUMENTATION_URL = "https://www.ndbc.noaa.gov/dart_data_access.shtml"
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def inspect_local_canary(
    path: Path, *, supplied_original_sha256: str | None = None
) -> dict[str, object]:
    """Reject any changed request identity; check only previously supplied bytes.

    A caller-supplied checksum can establish byte-consistency with the caller's
    receipt. It cannot itself authenticate the source, provider HTTP operation,
    ownership, service terms, or licensing of the actual copied bytes.
    """
    if supplied_original_sha256 is not None and not SHA256_RE.fullmatch(
        supplied_original_sha256
    ):
        raise DARTPreflightError("expected original checksum must be canonical SHA-256")
    evidence = preflight(path, station=STATION, start=START, end=END)
    if (
        evidence["source_id"] != "noaa.ndbc.dart"
        or evidence["station"] != STATION
        or evidence["requested_start_utc_date"] != START
        or evidence["requested_end_utc_date"] != END
        or evidence["response_format_checked"] is not True
        or evidence["original_provider_provenance_verified"] is not False
        or evidence["model_input_admitted"] is not False
    ):
        raise DARTPreflightError("fixed historical canary preflight identity drift")
    digest_matches = supplied_original_sha256 is not None and (
        evidence["input_sha256"] == supplied_original_sha256
    )
    if supplied_original_sha256 is not None and not digest_matches:
        raise DARTPreflightError("local bytes differ from caller-supplied SHA-256")
    return {
        **evidence,
        "profile": "noaa-ndbc-dart-historical-46401-20040118-22-offline-v0",
        "source_product_scope": "NDBC DART water-column-height historical five-day sample",
        "fixed_documented_request_method": "GET",
        "fixed_documented_request_url": ORIGINAL_DOCUMENTED_URL,
        "frozen_request_identity_sha256": hashlib.sha256(
            ("GET " + ORIGINAL_DOCUMENTED_URL).encode("ascii")
        ).hexdigest(),
        "official_historical_station_page": STATION_HISTORY_URL,
        "official_query_documentation": DART_API_DOCUMENTATION_URL,
        "station_owner_documented_by_ndbc": "National Data Buoy Center",
        "historical_station_record_includes_2004": True,
        "station_disestablished_in_2006": True,
        "station_operational_in_2026": False,
        "external_digest_supplied_and_matched": digest_matches,
        "external_digest_proves_provider_origin": False,
        "original_provider_provenance_verified": False,
        "original_http_response_retrieved_in_this_run": False,
        "original_dart_sample_downloaded": False,
        "service_automation_rights_verified": False,
        "commercial_cat_use_rights_verified": False,
        "station_deployment_period_and_instrument_qc_verified": False,
        "tsunami_event_identity_verified": False,
        "source_admitted": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, required=True,
        help="separately authorized local file, never a URL; no network access",
    )
    parser.add_argument(
        "--expected-original-sha256",
        help="optional independently recorded checksum (not provenance proof)",
    )
    args = parser.parse_args(argv)
    try:
        result = inspect_local_canary(
            args.file, supplied_original_sha256=args.expected_original_sha256
        )
    except (DARTPreflightError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
