#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""At most one fixed original HEAD request to an official Berlin depth ZIP.

Never GET or read source ZIP bytes, never follow redirects. Object-size, ETag
and claimed Accept-Ranges are headers only, not full-source SHA-256, proven
byte-range support, TIFF content, CRS, water depth, loss or model admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
from pathlib import Path
import ssl
import sys
from typing import Callable
from urllib import error, request

ROOT = "https://gdi.berlin.de/data/ua_srhk/atom/"
OBJECTS = {
    "extreme": "wasserstand_extrem2022.zip",
    "extraordinary": "wasserstand_aussergewoehnliches_ereignis2022.zip",
}
PROFILE = "berlin-srhk-bounded-depth-zip-head-metadata-v0"
TIMEOUT = 40
MAX_REVIEWED_SIZE = 20 * 1024**3
ALLOWED_MIME = {
    "application/zip", "application/x-zip-compressed",
    "application/octet-stream", "binary/octet-stream",
    "application/x-zip", "application/x-compressed",
}


class ZipHeadError(ValueError):
    """Original source ZIP metadata is changed, inaccessible or unbounded."""


def inspect_headers(headers, *, source: str) -> dict:
    if source not in OBJECTS:
        raise ZipHeadError("unknown fixed Berlin flood scenario")
    length = headers.get("Content-Length")
    if (type(length) is not str or not 0 < len(length) <= 20
            or not length.isascii() or not length.isdecimal()):
        raise ZipHeadError("official ZIP object size not declared")
    n = int(length)
    if n <= 0 or n > MAX_REVIEWED_SIZE:
        raise ZipHeadError("official ZIP object exceeds bounded source-size preflight")
    media = headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if media not in ALLOWED_MIME:
        raise ZipHeadError("official ZIP object has unsupported response Content-Type")
    encoding = headers.get("Content-Encoding", "identity").lower().strip()
    if encoding != "identity":
        raise ZipHeadError("unreviewed encoded HTTP ZIP payload")
    mtime = headers.get("Last-Modified")
    valid_date = None
    if mtime:
        if len(mtime) > 120:
            raise ZipHeadError("oversized Last-Modified source metadata")
        try:
            dt = parsedate_to_datetime(mtime)
        except (ValueError, TypeError, IndexError) as exc:
            raise ZipHeadError("invalid Last-Modified source metadata") from exc
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ZipHeadError("Last-Modified missing timezone")
        valid_date = dt.astimezone(timezone.utc).isoformat()
    ranges = headers.get("Accept-Ranges", "").strip().lower()
    if ranges not in ("", "none", "bytes"):
        raise ZipHeadError("unreviewed Accept-Ranges metadata")
    etag = headers.get("ETag")
    if etag is not None and len(etag) > 512:
        raise ZipHeadError("oversized ETag source metadata")
    return {
        "source_scenario": source,
        "original_zip_filename": OBJECTS[source],
        "declared_content_length_bytes": n,
        "server_content_type": media,
        "declared_last_modified_utc": valid_date,
        "server_etag_present": bool(etag),
        "server_claims_accept_ranges_bytes": ranges == "bytes",
        "server_accept_ranges_not_proven_by_get": True,
        "head_request_only": True,
        "zip_bytes_fetched": False,
        "zip_payload_magic_verified": False,
        "full_object_sha256_verified": False,
        "geotiff_crs_25832_vs_25833_unresolved": True,
        "actual_depth_units_values_or_nodata_verified": False,
        "provider_rights_or_science_admitted": False,
        "building_hazard_or_insurer_loss_calculated": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ZipHeadError("official ZIP server redirected exact metadata HEAD")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(source: str, *, opener: Callable = _fetch,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    if source not in OBJECTS:
        raise ZipHeadError("unknown fixed Berlin flood scenario")
    url = ROOT + OBJECTS[source]
    req = request.Request(
        url, method="HEAD",
        headers={"Accept": "application/zip, application/octet-stream;q=0.9",
                 "Accept-Encoding": "identity"}
    )
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != url:
                raise ZipHeadError("unexpected original ZIP response status/URL")
            result = inspect_headers(resp.headers, source=source)
    except ZipHeadError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise ZipHeadError("bounded original ZIP HEAD probe failed") from exc
    when = clock()
    if not isinstance(when, datetime) or when.tzinfo is None or when.utcoffset() is None:
        raise ZipHeadError("source receipt clock must include timezone offset")
    return {
        "profile": PROFILE,
        "original_head_url": url,
        "retrieved_at_utc": when.astimezone(timezone.utc).isoformat(),
        "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_zip_downloaded_or_persisted": False,
        "no_http_get_performed": True,
        **result,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", choices=sorted(OBJECTS), required=True)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("exact ZIP HEAD request requires explicit --live")
    try:
        print(json.dumps(probe(args.source), sort_keys=True, allow_nan=False))
    except (ZipHeadError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
