#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed 4096-byte DWD CDC CatRaRE W3 Eta v2026.01 CSV capability probe.

No caller URL, file version, spatial window or date range. Never print, upload or
persist provider bytes. Range response and first three unmodified event records
are inspected transiently; this does not validate full CSV, GDB, CRS, T5,
RADKLIM input or quantitative insurance loss modeling.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.parse import urlsplit

SOURCE = "dwd.catrare.w3-eta.v2026.01"
URL = ("https://opendata.dwd.de/climate_environment/CDC/event_catalogues/"
       "germany/precipitation/CatRaRE_v2026.01/data/"
       "CatRaRE_2001_2025_W3_Eta_v2026_01.csv")
MAX_BYTES = 4096
ORIGINAL_TOTAL_BYTES = 12_410_601  # official immutable v2026.01 directory listing
RANGE_HEADER = "bytes=0-4095"
EXPECTED_CONTENT_RANGE = f"bytes 0-4095/{ORIGINAL_TOTAL_BYTES}"


class DWDRangeBlocked(ValueError):
    """Provider identity, legal scope, transport or CSV contract rejected."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DWDRangeBlocked("redirect not authorized for fixed DWD CSV")


def verify_csv_prefix(raw: bytes, *, status: int, content_range: str, media_type: str) -> dict:
    if status != 206 or content_range.strip() != EXPECTED_CONTENT_RANGE:
        raise DWDRangeBlocked("exact partial content and original CSV identity required")
    if media_type.split(";", 1)[0].strip().lower() not in {
        "application/octet-stream", "text/csv", "text/plain"
    }:
        raise DWDRangeBlocked("unexpected content type for original CSV prefix")
    if not isinstance(raw, bytes) or len(raw) != MAX_BYTES:
        raise DWDRangeBlocked("not the exact bounded first 4096 original bytes")
    try:
        lines = raw.decode("utf-8").split("\n")
    except UnicodeDecodeError as exc:
        raise DWDRangeBlocked("invalid UTF-8 in original fixed CSV prefix") from exc
    if len(lines) < 5:
        raise DWDRangeBlocked("need header plus three complete event rows")
    header = lines[0].rstrip("\r").split(";")
    if (len(header) != 67 or len(set(header)) != 67 or
            header[:3] != ["CatVersion", "KEY_FIELD", "Event_ID"]):
        raise DWDRangeBlocked("W3 Eta v2026.01 CSV schema drift")
    for index in (1, 2, 3):
        fields = lines[index].rstrip("\r").split(";")
        if (len(fields) != len(header) or fields[0] != "W3_Eta_v2026_01"
                or fields[1] != f"W3_Eta_{index:06d}"
                or fields[2] != str(index)):
            raise DWDRangeBlocked("unexpected event ID, exact version or truncated row")
    return {
        "source_id": SOURCE,
        "release": "W3 Eta v2026.01",
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "csv_schema_columns": len(header),
        "complete_source_events_examined": 3,
        "historical_scope": "2001-01-01 through 2025-12-31",
        "full_file_bytes_verified": False,
        "event_polygon_geometry_verified": False,
        "t5_is_independent_dataset": False,
        "model_input_approved": False,
        "provider_bytes_persisted": False,
    }


def probe() -> dict:
    parsed = urlsplit(URL)
    if (parsed.scheme != "https" or parsed.netloc != "opendata.dwd.de"
            or not parsed.path.endswith("/CatRaRE_2001_2025_W3_Eta_v2026_01.csv")
            or parsed.query or parsed.fragment):
        raise DWDRangeBlocked("fixed host or dataset identity changed")
    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(URL, headers={
        "Range": RANGE_HEADER,
        "Accept": "text/csv,application/octet-stream",
        "User-Agent": "OpenCatastrophe-CatRaRE-Bounded-Probe/0.1",
    }, method="GET")
    try:
        with opener.open(request, timeout=30) as response:
            if response.status != 206 or response.geturl() != URL:
                raise DWDRangeBlocked("provider did not honor bounded fixed Range")
            c_range = response.headers.get("Content-Range", "")
            media = response.headers.get("Content-Type", "")
            body = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise DWDRangeBlocked("DWD bounded CSV access failed") from exc
    result = verify_csv_prefix(body, status=206, content_range=c_range, media_type=media)
    result.update({
        "operation": "exact_w3_v2026_01_first_4096_csv_bytes",
        "request_sha256": hashlib.sha256((URL + " ; Range: " + RANGE_HEADER).encode()).hexdigest(),
        "license": "CC BY 4.0",
        "license_evidence_url": "https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf",
        "source_doi": "10.5676/DWD/CatRaRE_W3_Eta_v2026.01",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    return result


def main() -> int:
    try:
        print(json.dumps(probe(), sort_keys=True))
        return 0
    except DWDRangeBlocked as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
