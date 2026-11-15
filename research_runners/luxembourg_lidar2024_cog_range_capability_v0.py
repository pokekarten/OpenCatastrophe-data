#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read ONLY 4096 byte range headers from fixed official 2024 MNT/MNS COGs.

This is HTTP range capability research, NOT a raster/height read or original
full-file verification. Never GET an unbounded 37-40 GB source object. No
provider byte or building identity is written to disk or the model database.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

OFFICIAL_BASE = (
    "https://download.data.public.lu/resources/"
    "bd-l-lidar2024-releve-3d-du-territoire-luxembourgeois/"
    "20241223-093912/"
)
FILES = {"MNT": "MNT_Lidar2024.tif", "MNS": "MNS_Lidar2024.tif"}
RANGE_BYTES = 4096
MAX_TOTAL_BYTES = 120 * 1024**3
MIN_TOTAL_BYTES = 10 * 1024**3
CONTENT_RANGE = re.compile(r"bytes 0-4095/([1-9][0-9]*)\Z")


class CogRangeError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CogRangeError("Original provider redirected; redirect destination requires review")


def read_header_range(kind: str, opener=None) -> dict:
    if kind not in FILES:
        raise CogRangeError("Unrecognized original official raster asset")
    url = OFFICIAL_BASE + FILES[kind]
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "download.data.public.lu"
            or parsed.query or parsed.fragment or parsed.username or parsed.password):
        raise CogRangeError("Unreviewed original provider URL")
    if opener is None:
        opener = build_opener(NoRedirect())
    request = Request(url, headers={
        "Range": "bytes=0-4095",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-LiDAR2024-COG-range-research/0",
    }, method="GET")
    try:
        with opener.open(request, timeout=20) as response:
            status = response.getcode()
            if status != 206:
                # IMPORTANT: do not read a byte from an unbounded HTTP 200
                raise CogRangeError("Provider did not honour HTTP byte-range request")
            headers = response.info()
            content_range = headers.get("Content-Range", "").strip()
            matched = CONTENT_RANGE.fullmatch(content_range)
            if not matched:
                raise CogRangeError("Missing or wrong Content-Range for fixed 4KiB request")
            declared_total = int(matched.group(1))
            if not MIN_TOTAL_BYTES <= declared_total <= MAX_TOTAL_BYTES:
                raise CogRangeError("Original COG total byte count outside researched range")
            declared_fragment = headers.get("Content-Length", "")
            if declared_fragment and int(declared_fragment) != RANGE_BYTES:
                raise CogRangeError("Returned content-length differs from bounded fragment")
            header = response.read(RANGE_BYTES + 1)
            if len(header) != RANGE_BYTES:
                raise CogRangeError("Truncated/oversized provider response fragment")
            if header[:4] not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
                raise CogRangeError("Original provider fragment is not a TIFF/BigTIFF header")
            return {
                "asset": kind,
                "provider_http_status": status,
                "range_request_bytes": RANGE_BYTES,
                "range_verified": True,
                "original_entire_file_bytes_declared_by_http": declared_total,
                "first_4k_sha256_only_not_full_file": hashlib.sha256(header).hexdigest(),
                "tiff_header_format": "BigTIFF" if header[2:4] in (b"+\x00", b"\x00+") else "TIFF",
                "actual_cog_spatial_window_read": False,
                "source_full_file_sha256_verified": False,
                "actual_building_heights_measured": False,
                "source_original_bytes_exported": False,
                "model_input_admitted": False,
            }
    except (HTTPError, URLError, OSError, ValueError) as exc:
        if isinstance(exc, CogRangeError):
            raise
        raise CogRangeError("Provider byte-range request could not be verified") from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", choices=sorted(FILES), required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(read_header_range(args.asset), sort_keys=True, indent=2, allow_nan=False))
    except CogRangeError as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
