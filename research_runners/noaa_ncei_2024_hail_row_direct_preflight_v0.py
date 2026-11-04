#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Opt-in NOAA NCEI 2024 original compressed CSV report-identity preflight.

This verifies an exact original government yearly *file identity* and one
candidate Storm Events ID through a read-only, fixed HTTPS GET. Does not
download/commit third-party data into Git, CI artifacts, a production DB or
an actuarial model. It does NOT equate NCEI rows with independent storms.
Only a minimal sanitized public event identity and source checksum are printed.

The 2024 filename is the NCEI published fixed *release*, NOT a mutable
'latest' URL. If NCEI republishes a new version it requires a new review.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any, Iterable

PROVIDER_HOST = "www.ncei.noaa.gov"
RELEASE_FILE = "StormEvents_details-ftp_v1.0_d2024_c20260728.csv.gz"
PROVIDER_URL = (
    "https://" + PROVIDER_HOST + "/pub/data/swdi/stormevents/csvfiles/"
    + RELEASE_FILE
)
EXPECTED_COMPRESSED_BYTES = 12_693_243
# SHA-256 independently computed on original NOAA HTTPS source, GitHub Actions
# original direct run #41829444110, 2026-11-04. Any release byte drift blocks.
EXPECTED_ORIGINAL_SHA256 = "2070b83eccab041b36360ab73645b9a249c3eefc5b92b5b3fc0cbba4d9fcc09c"
MAX_COMPRESSED_BYTES = 13_500_000
MAX_EXPANDED_BYTES = 250_000_000
MAX_SINGLE_LINE_BYTES = 2_000_000
MAX_ROWS = 250_000
HTTP_TIMEOUT_SECONDS = 45
TARGET_EVENT_ID = "1186553"
SELECTED_FIELDS = (
    "EVENT_ID", "EPISODE_ID", "YEAR", "STATE", "EVENT_TYPE",
    "BEGIN_DATE_TIME", "CZ_TIMEZONE", "SOURCE", "MAGNITUDE",
    "MAGNITUDE_TYPE", "BEGIN_LAT", "BEGIN_LON", "END_LAT", "END_LON",
    "BEGIN_LOCATION", "CZ_NAME",
)


class NCEIProofBlocked(ValueError):
    """Missing/changed original annual CSV or no authoritative event crosswalk."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def origin_opener() -> Any:
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirect(),
    )


def _bounded_gzip_text_rows(blob: bytes) -> Iterable[str]:
    expanded = 0
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(blob)) as gz:
            for line in gz:
                expanded += len(line)
                if expanded > MAX_EXPANDED_BYTES or len(line) > MAX_SINGLE_LINE_BYTES:
                    raise NCEIProofBlocked("original CSV expanded byte guard exceeded")
                yield line.decode("utf-8-sig")
    except (EOFError, OSError, UnicodeError) as exc:
        raise NCEIProofBlocked("original CSV gzip/UTF-8 integrity error") from exc


def audit_original_csv(blob: bytes) -> dict:
    if type(blob) is not bytes or len(blob) != EXPECTED_COMPRESSED_BYTES:
        raise NCEIProofBlocked("original NCEI release compressed size mismatch")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != EXPECTED_ORIGINAL_SHA256:
        raise NCEIProofBlocked("pinned original annual NOAA release SHA256 mismatch")
    previous_size_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(100_000)
        reader = csv.DictReader(_bounded_gzip_text_rows(blob))
        if not reader.fieldnames or not set(SELECTED_FIELDS).issubset(reader.fieldnames):
            raise NCEIProofBlocked("NCEI original schema/required columns drift")
        matches: list[dict] = []
        rowcount = 0
        for row in reader:
            rowcount += 1
            if rowcount > MAX_ROWS:
                raise NCEIProofBlocked("unexpected NCEI annual row count")
            if row.get("EVENT_ID", "") == TARGET_EVENT_ID:
                if len(matches) > 0:
                    raise NCEIProofBlocked("duplicate NCEI event ID in annual source")
                matches.append({col: row.get(col, "") for col in SELECTED_FIELDS})
    except (csv.Error, UnicodeError) as exc:
        raise NCEIProofBlocked("NCEI CSV parser blocked malformed source") from exc
    finally:
        csv.field_size_limit(previous_size_limit)
    if len(matches) != 1:
        raise NCEIProofBlocked("candidate event ID absent from original yearly CSV")
    row = matches[0]
    # Only conservative fixed fields. Date/time and source coordinates remain
    # as the NOAA CSV actually labels them, not silently converted to UTC.
    if (row["EVENT_TYPE"].upper() != "HAIL"
            or row["STATE"].upper() != "TEXAS"
            or row["YEAR"] != "2024"
            or "MAY" not in row["BEGIN_DATE_TIME"].upper()):
        raise NCEIProofBlocked("original NCEI record not expected TX hail case")
    return {
        "schema_version": "noaa-ncei-2024-hail-event-original-row-v0",
        "provider": "NOAA NCEI Storm Events original annual CSV",
        "source_exact_url": PROVIDER_URL,
        "source_compressed_bytes": len(blob),
        "source_compressed_sha256": digest,
        "source_decoded_csv_rows_checked": rowcount,
        "candidate_id_checked_against_original": TARGET_EVENT_ID,
        "provider_original_fields": row,
        "nws_preliminary_mping_2024_05_27_report_identical": False,
        "ncei_source_row_verified": True,
        "event_independent_storm_id_resolved": False,
        "source_rights_or_cat_model_admitted": False,
        "annual_hail_frequency_or_losses_estimated": False,
        "provider_source_bytes_committed_or_published": False,
    }


def direct_original_probe(opener: Any = None) -> dict:
    opener = origin_opener() if opener is None else opener
    req = urllib.request.Request(
        PROVIDER_URL,
        method="GET",
        headers={
            "Accept": "application/octet-stream",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-data-original-NCEI-research/0.1",
        },
    )
    try:
        with opener.open(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
            if resp.status != 200 or resp.geturl() != PROVIDER_URL:
                raise NCEIProofBlocked("non-200 or redirected original NCEI release")
            if resp.headers.get("Content-Encoding", "identity") not in ("", "identity"):
                raise NCEIProofBlocked("unexpected HTTP transfer content encoding")
            size_header = resp.headers.get("Content-Length")
            if size_header is not None and (
                not size_header.isdecimal()
                or int(size_header) != EXPECTED_COMPRESSED_BYTES
            ):
                raise NCEIProofBlocked("original provider Content-Length differs")
            body = resp.read(MAX_COMPRESSED_BYTES + 1)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        raise NCEIProofBlocked("original provider HTTPS unavailable") from exc
    if len(body) > MAX_COMPRESSED_BYTES:
        raise NCEIProofBlocked("original provider response too large")
    return audit_original_csv(body)


def main() -> int:
    try:
        record = direct_original_probe()
    except NCEIProofBlocked:
        # No untrusted external exception/body/narrative/credentials in logs.
        print("BLOCKED: NOAA NCEI 2024 original event row verification", file=sys.stderr)
        return 2
    print(json.dumps(record, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
