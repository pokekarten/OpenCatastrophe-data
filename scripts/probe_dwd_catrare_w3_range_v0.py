#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exactly two original DWD CatRaRE W3/T5 Eta 2026.01 4096-byte CSV probes.

No caller-supplied host, URL, filename, version or date range; W3 and T5 are
scientifically related thresholds, not independent rainfall-event samples.
The provider's first 4096 bytes are inspected transiently only. Neither
full CSV nor geodatabase/geometry is downloaded, logged or committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.parse import urlsplit

BASE = ("https://opendata.dwd.de/climate_environment/CDC/event_catalogues/"
        "germany/precipitation/CatRaRE_v2026.01/data/")
ALLOWED = {
    "W3": {
        "source": "dwd.catrare.w3-eta.v2026.01",
        "filename": "CatRaRE_2001_2025_W3_Eta_v2026_01.csv",
        "total_bytes": 12_410_601,
        "doi": "10.5676/DWD/CatRaRE_W3_Eta_v2026.01",
    },
    "T5": {
        "source": "dwd.catrare.t5-eta.v2026.01",
        "filename": "CatRaRE_2001_2025_T5_Eta_v2026_01.csv",
        "total_bytes": 17_208_653,
        "doi": "10.5676/DWD/CatRaRE_T5_Eta_v2026.01",
    },
}
MAX_BYTES = 4096
RANGE_HEADER = "bytes=0-4095"
SOURCE = ALLOWED["W3"]["source"]  # compatibility for earlier W3-only tests
URL = BASE + ALLOWED["W3"]["filename"]
ORIGINAL_TOTAL_BYTES = ALLOWED["W3"]["total_bytes"]
EXPECTED_CONTENT_RANGE = f"bytes 0-4095/{ORIGINAL_TOTAL_BYTES}"


class DWDRangeBlocked(ValueError):
    """Provider identity, legal scope, transport or CSV contract rejected."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DWDRangeBlocked("redirect not authorized for fixed DWD CSV")


def verify_csv_prefix(raw: bytes, *, status: int, content_range: str,
                      media_type: str, variant: str = "W3") -> dict:
    if variant not in ALLOWED:
        raise DWDRangeBlocked("unknown CatRaRE variant")
    expected = f"bytes 0-4095/{ALLOWED[variant]['total_bytes']}"
    if status != 206 or content_range.strip() != expected:
        raise DWDRangeBlocked("exact partial content and original CSV size required")
    if media_type.split(";", 1)[0].strip().lower() not in {
        "application/octet-stream", "text/csv", "text/plain"
    }:
        raise DWDRangeBlocked("unexpected content type for original CSV prefix")
    if not isinstance(raw, bytes) or len(raw) != MAX_BYTES:
        raise DWDRangeBlocked("not the exact bounded first 4096 original bytes")
    try:
        lines = raw.decode("utf-8").split("\n")
    except UnicodeDecodeError as exc:
        raise DWDRangeBlocked("invalid UTF-8 in original CSV prefix") from exc
    if len(lines) < 5:
        raise DWDRangeBlocked("need schema plus three original event rows")
    header = lines[0].rstrip("\r").split(";")
    if (len(header) != 67 or len(set(header)) != 67
            or header[:3] != ["CatVersion", "KEY_FIELD", "Event_ID"]):
        raise DWDRangeBlocked("CatRaRE 2026.01 schema drift")
    for index in (1, 2, 3):
        fields = lines[index].rstrip("\r").split(";")
        if (len(fields) != len(header)
                or fields[0] != f"{variant}_Eta_v2026_01"
                or fields[1] != f"{variant}_Eta_{index:06d}"
                or fields[2] != str(index)):
            raise DWDRangeBlocked("unexpected version, event ID or truncated record")
    return {
        "source_id": ALLOWED[variant]["source"],
        "variant": variant,
        "release": f"{variant} Eta v2026.01",
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "csv_schema_columns": len(header),
        "complete_source_events_examined": 3,
        "historical_scope": "2001-01-01 through 2025-12-31",
        "full_file_bytes_verified": False,
        "event_polygon_geometry_verified": False,
        "w3_t5_independent": False,
        "model_input_approved": False,
        "provider_bytes_persisted": False,
    }


def probe(variant: str = "W3") -> dict:
    if variant not in ALLOWED:
        raise DWDRangeBlocked("only exact reviewed W3/T5 variants allowed")
    cfg = ALLOWED[variant]
    url = BASE + cfg["filename"]
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "opendata.dwd.de"
            or parsed.path != urlsplit(BASE).path + cfg["filename"]
            or parsed.query or parsed.fragment):
        raise DWDRangeBlocked("fixed host or original dataset identity changed")
    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(url, headers={
        "Range": RANGE_HEADER,
        "Accept": "text/csv,application/octet-stream",
        "User-Agent": "OpenCatastrophe-CatRaRE-Bounded-Probe/0.1",
    }, method="GET")
    try:
        with opener.open(request, timeout=30) as response:
            if response.status != 206 or response.geturl() != url:
                raise DWDRangeBlocked("provider did not honor fixed Range")
            c_range = response.headers.get("Content-Range", "")
            media = response.headers.get("Content-Type", "")
            body = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise DWDRangeBlocked("DWD bounded CSV access failed") from exc
    result = verify_csv_prefix(body, status=206, content_range=c_range,
                               media_type=media, variant=variant)
    result.update({
        "operation": f"exact_{variant.lower()}_v2026_01_first_4096_csv_bytes",
        "request_sha256": hashlib.sha256(
            (url + " ; Range: " + RANGE_HEADER).encode()).hexdigest(),
        "license": "CC BY 4.0",
        "license_evidence_url": "https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf",
        "source_doi": cfg["doi"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(ALLOWED), default="W3")
    args = parser.parse_args()
    try:
        print(json.dumps(probe(args.variant), sort_keys=True))
        return 0
    except DWDRangeBlocked as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
