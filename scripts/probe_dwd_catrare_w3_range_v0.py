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
from pathlib import Path

from scripts.validate_source_access import validate_path
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
ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 4096
KNOWN_PREFIX_SHA256 = {
    "W3": "a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12",
    "T5": "5dc4b6f0dac14f0a442103b78c16f647556bd870898aabff6d9f62aa4534f542",
}
RANGE_HEADER = "bytes=0-4095"
SOURCE = ALLOWED["W3"]["source"]  # compatibility for earlier W3-only tests
URL = BASE + ALLOWED["W3"]["filename"]
ORIGINAL_TOTAL_BYTES = ALLOWED["W3"]["total_bytes"]
EXPECTED_CONTENT_RANGE = f"bytes 0-4095/{ORIGINAL_TOTAL_BYTES}"


class DWDRangeBlocked(ValueError):
    """Provider identity, legal scope, transport or CSV contract rejected."""


def verify_reviewed_contract(variant: str) -> Path:
    """Require exact source/version/rights contract before any original request."""
    if variant not in ALLOWED:
        raise DWDRangeBlocked("only exact reviewed W3/T5 variants allowed")
    cfg = ALLOWED[variant]
    path = ROOT / "access" / (cfg["source"] + ".json")
    contract = validate_path(path)
    rights = contract["rights_and_policy"]
    probe_contract = contract["probe_contract"]
    limits = contract["operational_constraints"]
    if (contract["access_id"] != cfg["source"]
            or contract["source_ids"] != [cfg["source"]]
            or contract["interface_type"] != "http_file"
            or contract["status"] != "probe_ready"
            or contract["service_root"] != BASE.rstrip("/")
            or contract["access_scope"] != ["metadata", "sample"]
            or contract["authentication"]["mode"] != "none"
            or contract["request_contract"]["allowed_operations"] != ["read_fixed_csv_prefix"]
            or contract["request_contract"]["path_templates"] != ["/" + cfg["filename"]]
            or rights["dataset_rights_status"] != "verified"
            or rights["api_terms_status"] != "same_as_dataset"
            or rights["terms_url"] != "https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf"
            or rights["commercial_automation_status"] != "allowed"
            or probe_contract["mode"] != "provider_specific"
            or probe_contract["operation"] != "read_fixed_csv_prefix"
            or probe_contract["requires_credentials"] is not False
            or limits["max_probe_bytes"] != MAX_BYTES
            or limits["max_sample_bytes"] != MAX_BYTES
            or limits["timeout_seconds"] != 30
            or limits["retry_policy"] != "none"
            or KNOWN_PREFIX_SHA256[variant] not in limits["mutability_notes"]
            or str(cfg["total_bytes"]) not in limits["mutability_notes"]):
        raise DWDRangeBlocked("original CatRaRE rights/variant/route contract changed")
    return path


def verify_original_prefix_digest(result: dict, *, variant: str) -> None:
    """Provider byte witness must match previously frozen original 4KiB SHA."""
    if variant not in KNOWN_PREFIX_SHA256 or result.get("response_sha256") != KNOWN_PREFIX_SHA256[variant]:
        raise DWDRangeBlocked("original CatRaRE 2026.01 4096-byte SHA-256 drift")


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
    contract_path = verify_reviewed_contract(variant)
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
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise DWDRangeBlocked("compressed source response is not reviewed")
            stated = response.headers.get("Content-Length")
            if stated is not None and (not stated.isascii() or not stated.isdecimal()
                                       or int(stated) != MAX_BYTES):
                raise DWDRangeBlocked("original partial-response Content-Length mismatch")
            body = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise DWDRangeBlocked("DWD bounded CSV access failed") from exc
    result = verify_csv_prefix(body, status=206, content_range=c_range,
                               media_type=media, variant=variant)
    verify_original_prefix_digest(result, variant=variant)
    result.update({
        "source_access_contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "source_probe_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "operation": f"exact_{variant.lower()}_v2026_01_first_4096_csv_bytes",
        "request_sha256": hashlib.sha256(
            (url + " ; Range: " + RANGE_HEADER).encode()).hexdigest(),
        "license": "CC BY 4.0",
        "license_evidence_url": "https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf",
        "source_doi": cfg["doi"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(ALLOWED), default="W3")
    parser.add_argument("--live", action="store_true", help="one original bounded DWD source GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("original provider network access disabled by default; --live required")
    try:
        print(json.dumps(probe(args.variant), sort_keys=True))
        return 0
    except DWDRangeBlocked as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
