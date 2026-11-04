#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Three frozen ACT BD-Adresses 2026-10-12 resource metadata receipts.

Only metadata GETs: no original address data GET/HEAD, redirects, pagination,
arbitrary URLs, credentials, DB writes or model admission. Live access opt-in.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_ROOT = "https://data.public.lu/api/1/datasets/56fd16fa855e9b6a1088f552/resources/"
ASSETS = (
    ("7b58cf20-cbb0-4970-83f7-53a277f691b8", "addresses.geojson", "20261012-023133", "e3f184a823ed9715091dbde663789d75", 50_000_000, 110_000_000),
    ("5cadc5b8-6a7d-4283-87bc-f9e58dd771f7", "addresses.csv", "20261012-023119", "e677763d0376b5419ab4aafa5fa09366", 15_000_000, 50_000_000),
    ("2a17ddc2-b961-45ce-83a2-be751d3af9b8", "addresses-shp.zip", "20261012-023147", "782fb9d3e44102093bd4257d2c620982", 10_000_000, 30_000_000),
)
MAX_METADATA_BYTES = 128 * 1024


class MetadataReceiptError(ValueError):
    """Nonconforming publisher metadata must fail closed."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MetadataReceiptError("Unexpected publisher metadata redirect")


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MetadataReceiptError("Duplicate metadata JSON key")
        result[key] = value
    return result


def _reject_nonfinite(value):
    raise MetadataReceiptError("Non-finite metadata JSON number")


def _validate_url(value, filename, timestamp):
    if not isinstance(value, str) or len(value) > 500:
        raise MetadataReceiptError("Malformed official asset URL")
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise MetadataReceiptError("Malformed official asset URL") from exc
    if (parts.scheme != "https" or parts.hostname != "download.data.public.lu"
            or parts.username is not None or parts.password is not None
            or port not in (None, 443) or parts.query or parts.fragment
            or parts.path != f"/resources/adresses-georeferencees-bd-adresses/{timestamp}/{filename}"):
        raise MetadataReceiptError("Official asset URL/version/host drift")


def _parse(raw: bytes, asset):
    rid, filename, timestamp, expected_md5, low, high = asset
    if len(raw) > MAX_METADATA_BYTES:
        raise MetadataReceiptError("Metadata exceeds strict byte cap")
    try:
        entry = json.loads(raw, object_pairs_hook=_object_pairs, parse_constant=_reject_nonfinite)
    except (UnicodeError, ValueError) as exc:
        if isinstance(exc, MetadataReceiptError):
            raise
        raise MetadataReceiptError("Invalid metadata JSON") from exc
    if isinstance(entry, dict) and isinstance(entry.get("data"), dict):
        entry = entry["data"]
    if not isinstance(entry, dict) or entry.get("id") != rid:
        raise MetadataReceiptError("Metadata resource identity mismatch")
    name = entry.get("filename") or entry.get("name")
    if name != filename:
        raise MetadataReceiptError("Official filename mismatch")
    _validate_url(entry.get("url"), filename, timestamp)
    checksum = entry.get("md5")
    if not isinstance(checksum, str) or not re.fullmatch("[0-9a-fA-F]{32}", checksum):
        raise MetadataReceiptError("No unambiguous original-provider MD5")
    if checksum.lower() != expected_md5:
        raise MetadataReceiptError("Original-provider MD5 differs from frozen 2026-10-12 receipt")
    byte_count = entry.get("filesize") if "filesize" in entry else entry.get("size")
    if type(byte_count) is not int or not low <= byte_count <= high:
        raise MetadataReceiptError("Source byte size outside pinned resource band")
    modified = entry.get("last_modified") or entry.get("modified")
    if not isinstance(modified, str) or not modified.startswith("2026-10-12"):
        raise MetadataReceiptError("Publication vintage not pinned to 2026-10-12")
    return {"resource_id": rid, "name": filename, "release_date": "2026-10-12",
            "publisher_md5": checksum.lower(), "publisher_file_size_bytes": byte_count,
            "metadata_response_sha256": hashlib.sha256(raw).hexdigest(),
            "metadata_only": True, "source_bytes_downloaded": 0,
            "scientific_approval": False, "rights_approval": False, "model_admitted": False}


def collect(opener):
    out = []
    for asset in ASSETS:
        url = API_ROOT + asset[0] + "/"
        req = Request(url, method="GET", headers={"Accept": "application/json",
            "Accept-Encoding": "identity", "User-Agent": "OpenCatastrophe-metadata-canary/0"})
        try:
            with opener.open(req, timeout=15) as res:
                if res.getcode() != 200:
                    raise MetadataReceiptError("Unexpected official API HTTP status")
                raw = res.read(MAX_METADATA_BYTES + 1)
        except (OSError, URLError) as exc:
            if isinstance(exc, MetadataReceiptError):
                raise
            raise MetadataReceiptError("Publisher metadata unavailable") from exc
        out.append(_parse(raw, asset))
    return {"probe": "lu-act-bd-adresses-metadata-v0", "source": "ACT official portal 2026-10-12",
            "resources": out, "metadata_only": True,
            "asset_bytes_downloaded": 0, "model_admitted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Opt in to exactly three metadata API GET requests")
    args = parser.parse_args(argv)
    if not args.live:
        print("No network access performed; use --live for three fixed ACT metadata records")
        return 0
    try:
        receipt = collect(build_opener(NoRedirect()))
    except MetadataReceiptError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
