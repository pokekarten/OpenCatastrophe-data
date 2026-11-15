#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One manually reviewed original DWD corrected 2021 2KiB range probe.

Never fetch full corrected 820MB TAR, follow redirects, retry, or log source
bytes. Strict HTTP 206, Content-Range and original-response SHA-256 required.
This is *not* an API harvesting or scientific model admission runner.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from research_runners.dwd_radklim_2021_corrected_prefix_header_v0 import (
    CORRECTED_URL,
    DWD2021PrefixBlocked,
    FROZEN_PREFIX_LENGTH,
    inspect_frozen_original_prefix,
)

RANGE_VALUE = "bytes=0-2047"
EXPECTED_TOTAL_SIZE = 820_143_312
EXPECTED_CONTENT_RANGE = f"bytes 0-2047/{EXPECTED_TOTAL_SIZE}"
ALLOWED_CONTENT_TYPES = {
    "application/octet-stream",
    "application/gzip",
    "application/x-gzip",
    "application/x-compressed-tar",
    "application/x-tar",
    "binary/octet-stream",
}
TIMEOUT_SECONDS = 25


class ProviderProbeBlocked(ValueError):
    pass


class RefuseRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise ProviderProbeBlocked("provider redirect blocked: exact source identity lost")


def one_fixed_range_probe(*, opener=None) -> dict:
    """Read exactly 2048 compressed ORIGINAL bytes, without byte persistence."""
    client = opener if opener is not None else build_opener(RefuseRedirect(), ProxyHandler({}))
    request = Request(
        CORRECTED_URL,
        headers={
            "Range": RANGE_VALUE,
            "Accept-Encoding": "identity",
            "Accept": "application/octet-stream",
            "User-Agent": "OpenCatastrophe-DWD-RADKLIM-RW-2021-fixed-header-research/0.1",
        },
        method="GET",
    )
    try:
        with client.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 206:
                raise ProviderProbeBlocked("provider did not honor strict HTTP 206 range")
            content_range = response.headers.get("Content-Range", "").strip()
            if content_range != EXPECTED_CONTENT_RANGE:
                raise ProviderProbeBlocked("provider original Content-Range or asset size drift")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in ALLOWED_CONTENT_TYPES:
                raise ProviderProbeBlocked("provider original compressed media type unexpected")
            content_encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
            if content_encoding != "identity":
                raise ProviderProbeBlocked("provider transport changed compressed original bytes")
            length = response.headers.get("Content-Length")
            if length is not None:
                try:
                    declared = int(length)
                except (TypeError, ValueError) as exc:
                    raise ProviderProbeBlocked("invalid provider Content-Length") from exc
                if declared != FROZEN_PREFIX_LENGTH:
                    raise ProviderProbeBlocked("provider original compressed range length drift")
            raw = response.read(FROZEN_PREFIX_LENGTH + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ProviderProbeBlocked("bounded original DWD range access failed") from exc
    if len(raw) != FROZEN_PREFIX_LENGTH:
        raise ProviderProbeBlocked("provider returned incomplete or oversized original range")
    try:
        structural = inspect_frozen_original_prefix(raw)
    except DWD2021PrefixBlocked as exc:
        raise ProviderProbeBlocked("original corrected 2021 compressed prefix failed strict identity/shape gate") from exc
    # Original bytes intentionally die with this function. No user data or
    # precipitation values enter the receipt.
    return {
        "profile": "dwd-radklim-corrected-2021-original-2k-direct-github-v0",
        "source_id": structural["source_id"],
        "status": "ORIGINAL_206_PREFIX_MATCHED",
        "retrieval_utc": datetime.now(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(
            ("GET " + CORRECTED_URL + "\nRange: " + RANGE_VALUE).encode("ascii")
        ).hexdigest(),
        "probe_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "validator_code_sha256": hashlib.sha256(
            Path(__file__).with_name("dwd_radklim_2021_corrected_prefix_header_v0.py").read_bytes()
        ).hexdigest(),
        "original_prefix_sha256": structural["original_prefix_sha256"],
        "original_response_bytes": FROZEN_PREFIX_LENGTH,
        "http_status": 206,
        "content_range_verified": True,
        "source_archive_size_declared": EXPECTED_TOTAL_SIZE,
        "corrected_original_header_signature_verified": True,
        "full_original_archive_downloaded": False,
        "full_archive_sha256_verified": False,
        "original_month_precipitation_values_verified": False,
        "model_input_approved": False,
        "provider_bytes_persisted": False,
        "original_source_http_request_executed_directly": True,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Explicit opt-in to one no-retry original HTTP Range GET")
    args = parser.parse_args(argv)
    if not args.live:
        print(json.dumps({"status": "BLOCKED", "reason": "explicit --live required"}), file=sys.stderr)
        return 2
    try:
        receipt = one_fixed_range_probe()
    except ProviderProbeBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "source_id": "dwd.radklim.rw.v2017.002",
                          "reason": str(exc), "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
