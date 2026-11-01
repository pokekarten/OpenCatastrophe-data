# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read at most 4 bytes from public CEMS EMSN028 ZIP; never download archive."""
from __future__ import annotations
import argparse
import json
import re
import urllib.error
import urllib.request
from scripts.cems_emns028_zip_head_receipt_v0 import (
    SOURCE_URL, OfficialRedirectOnly, assert_expected_destination,
)


def probe_prefix(opener=None) -> dict:
    opener = opener or urllib.request.build_opener(OfficialRedirectOnly())
    request = urllib.request.Request(
        SOURCE_URL, method="GET", headers={
            "Range": "bytes=0-3",
            "User-Agent": "OpenCatastrophe-Research-Receipt/0.1 (4-byte range only)",
        })
    with opener.open(request, timeout=18) as response:
        host = assert_expected_destination(response.geturl())
        status = response.status
        cr = response.headers.get("Content-Range", "")
        parsed_range = re.fullmatch(r"bytes 0-3/([1-9][0-9]*|\*)", cr)
        ranged = status == 206 and parsed_range is not None
        archive_size = (int(parsed_range.group(1))
                        if ranged and parsed_range.group(1) != "*" else None)
        data = response.read(4)  # hard cap: 4 bytes, then close connection
        looks_zip = data == b"PK\x03\x04"
        return {
            "receipt_kind": "CEMS_EMSN028_ZIP_PREFIX_V0",
            "stable_source_url": SOURCE_URL,
            "final_host": host, "http_status": status,
            "content_type": response.headers.get("Content-Type"),
            "range_honored": ranged,
            "archive_size_bytes_from_range": archive_size,
            "prefix_bytes_received": len(data),
            "zip_local_file_magic_verified": looks_zip,
            "source_zip_available_for_further_rights_review":
                status in (200, 206) and looks_zip and (status != 206 or ranged),
            "full_zip_downloaded": False,
            "full_source_sha256_verified": False,
            "aoi04_observed_flood_layer_verified": False,
            "commercial_rights_cleared": False,
            "cat_model_admitted": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="explicitly allow up to 4 response bytes")
    args = parser.parse_args()
    if not args.live:
        parser.error("--live required")
    try:
        result = probe_prefix()
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError) as exc:
        # Error strings can expose presigned URL credentials: do not print them.
        result = {"receipt_kind": "CEMS_EMSN028_ZIP_PREFIX_V0",
                  "stable_source_url": SOURCE_URL,
                  "error_type": type(exc).__name__,
                  "source_zip_available_for_further_rights_review": False,
                  "full_zip_downloaded": False,
                  "full_source_sha256_verified": False,
                  "commercial_rights_cleared": False,
                  "cat_model_admitted": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["source_zip_available_for_further_rights_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
