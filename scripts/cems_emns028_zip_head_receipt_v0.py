# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict HEAD-only metadata receipt for official Copernicus EMSN028 archive.

Explicit --live required. No ZIP bytes, presigned URL or credentials printed.
No source-licence, layer-provenance or CAT-model admission is inferred.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit

SOURCE_URL = ("https://mapping.emergency.copernicus.eu/download/EMSN028/"
              "EMNS028_AOI_FRANCE_utm31n.gdb.zip")
BASENAME = "EMNS028_AOI_FRANCE_utm31n.gdb.zip"
VALID_HOSTS = frozenset({
    "mapping.emergency.copernicus.eu",
    "cems-mapping-website.s3.amazonaws.com",
    "cems-mapping-website.s3.eu-west-1.amazonaws.com",
})


def assert_expected_destination(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in VALID_HOSTS:
        raise ValueError("off-allowlist or non-HTTPS archive destination")
    if not parsed.path.endswith("/" + BASENAME):
        raise ValueError("redirect to unexpected archive path")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("unexpected host credentials or port")
    return parsed.hostname


class OfficialRedirectOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        assert_expected_destination(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def probe(opener=None) -> dict:
    assert_expected_destination(SOURCE_URL)
    opener = opener or urllib.request.build_opener(OfficialRedirectOnly())
    req = urllib.request.Request(
        SOURCE_URL, method="HEAD",
        headers={"User-Agent": "OpenCatastrophe-Research-Receipt/0.1 (metadata-only)"},
    )
    # Never call response.read() or fall back to GET.
    with opener.open(req, timeout=18) as response:
        final_host = assert_expected_destination(response.geturl())
        status = response.status
        headers = response.headers
        raw_length = headers.get("Content-Length")
        length = (int(raw_length) if raw_length
                  and re.fullmatch(r"[0-9]+", raw_length) else None)
        return {
            "receipt_kind": "CEMS_EMSN028_OFFICIAL_HEAD_V0",
            "activation": "EMSN028",
            "coverage_scope": "2016 France ZIP; AOI04 member unverified",
            "source_url": SOURCE_URL,
            "request_method": "HEAD",
            "response_status": status,
            "final_host": final_host,  # no expiring presigned S3 URL
            "content_type": headers.get("Content-Type"),
            "content_length_bytes": length,
            "content_disposition_present": bool(headers.get("Content-Disposition")),
            "head_accessible": status == 200 and length is not None and length > 0,
            "archive_bytes_downloaded": False,
            "archive_sha256_verified": False,
            "archive_members_inspected": False,
            "aoi04_observed_flood_polygon_verified": False,
            "specific_activation_rights_cleared": False,
            "cat_model_admitted": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="explicitly permit one public HEAD, never download")
    args = parser.parse_args()
    if not args.live:
        parser.error("--live required; no implicit network")
    try:
        result = probe()
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError) as exc:
        # Error strings can contain presigned credentials: do NOT print them.
        result = {
            "receipt_kind": "CEMS_EMSN028_OFFICIAL_HEAD_V0",
            "source_url": SOURCE_URL,
            "head_accessible": False,
            "error_type": type(exc).__name__,
            "archive_bytes_downloaded": False,
            "archive_sha256_verified": False,
            "specific_activation_rights_cleared": False,
            "cat_model_admitted": False,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["head_accessible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
