# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Trusted-main, opt-in acquisition of two exact GRWL original ZIPs for byte evidence.

Downloads only two public Zenodo files to temporary local storage. No source
bytes are committed, printed or uploaded. Run --live only from reviewed main.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request, build_opener

from research_runners.grwl_original_member_digest_compare_v0 import compare_original_archives
from research_runners.grwl_original_zip_structure_preflight_v0 import SOURCE_FILES, OriginalZipError

SCHEMA = "opencatastrophe-grwl-trusted-original-byte-evidence-v0"
ORIGINAL_URLS = {
    "2018": "https://zenodo.org/api/records/1297434/files/GRWL_summaryStats_V01.01.zip/content",
    "2026": "https://zenodo.org/api/records/18624542/files/GRWL_summaryStats_V01.02.zip/content",
}
CHUNK = 1 << 20
MAX_REDIRECTS = 3
_ALLOWED_DOMAINS = ("zenodo.org", "cern.ch", "amazonaws.com")


class OriginalAcquisitionError(ValueError):
    """Acquisition blocked without implying missing/approved provider data."""


def _safe_redirect_host(url):
    p = urlsplit(url)
    h = (p.hostname or "").lower().rstrip(".")
    if p.scheme != "https" or p.username or p.password or p.port not in (None, 443):
        return False
    if not h or h == "localhost":
        return False
    try:
        ipaddress.ip_address(h)
        return False
    except ValueError:
        pass
    return any(h == suffix or h.endswith("." + suffix) for suffix in _ALLOWED_DOMAINS)


class BoundedRedirects(HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.redirects = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirects += 1
        if self.redirects > MAX_REDIRECTS or not _safe_redirect_host(newurl):
            raise OriginalAcquisitionError("provider redirect outside allowed HTTPS hosts/limit")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def default_open(url):
    if url not in ORIGINAL_URLS.values():
        raise OriginalAcquisitionError("URL outside two frozen original archives")
    handler = BoundedRedirects()
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), handler)
    request = Request(url, headers={
        "Accept": "application/octet-stream, application/zip",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-GRWL-trusted-original-byte-evidence/0",
    }, method="GET")
    return opener.open(request, timeout=60)


def download_fixed(release, target: Path, *, open_stream=default_open):
    if release not in SOURCE_FILES or release not in ORIGINAL_URLS:
        raise OriginalAcquisitionError("unexpected original release")
    filename, expected_size, expected_md5 = SOURCE_FILES[release]
    if target.name != filename or target.is_symlink() or target.exists():
        raise OriginalAcquisitionError("unsafe original temporary destination")
    url = ORIGINAL_URLS[release]
    size, md5, sha256 = 0, hashlib.md5(), hashlib.sha256()
    try:
        with closing(open_stream(url)) as source:
            if getattr(source, "status", None) != 200:
                raise OriginalAcquisitionError("original download did not return HTTP 200")
            headers = getattr(source, "headers", {})
            raw_size = headers.get("Content-Length")
            if raw_size is not None and (not raw_size.isdecimal() or int(raw_size) != expected_size):
                raise OriginalAcquisitionError("original Content-Length disagrees with pinned source bytes")
            content_type = headers.get("Content-Type", "").lower()
            if "text/html" in content_type or "application/json" in content_type:
                raise OriginalAcquisitionError("provider returned HTML/JSON instead of original ZIP")
            with target.open("xb") as sink:
                while block := source.read(CHUNK):
                    if not isinstance(block, bytes):
                        raise OriginalAcquisitionError("non-byte source response")
                    size += len(block)
                    if size > expected_size:
                        raise OriginalAcquisitionError("original source stream exceeded expected size")
                    md5.update(block)
                    sha256.update(block)
                    sink.write(block)
        if size != expected_size or md5.hexdigest() != expected_md5:
            raise OriginalAcquisitionError("original ZIP byte size/MD5 mismatch against Zenodo")
    except HTTPError as exc:
        raise OriginalAcquisitionError(f"original Zenodo HTTP {exc.code}; no source proof") from exc
    except (URLError, TimeoutError) as exc:
        raise OriginalAcquisitionError("original Zenodo endpoint unreachable; no source proof") from exc
    except OSError as exc:
        raise OriginalAcquisitionError("original temporary download failed; no source proof") from exc
    return {"release": release, "bytes": size,
            "independent_original_zip_md5": md5.hexdigest(),
            "independent_original_zip_sha256": sha256.hexdigest()}


def run_live():
    # TemporaryDirectory does not persist source data as a GitHub artifact.
    with tempfile.TemporaryDirectory(prefix="grwl-original-readonly-") as directory:
        originals = {}
        receipts = []
        for release in ("2018", "2026"):
            path = Path(directory) / SOURCE_FILES[release][0]
            receipt = download_fixed(release, path)
            receipts.append(receipt)
            originals[release] = path
        comparison = compare_original_archives(originals["2018"], originals["2026"])
        for item in comparison["original_zip_sha256_receipts"]:
            expected = next(x for x in receipts if x["release"] == item["release"])
            if expected["independent_original_zip_sha256"] != item["sha256"]:
                raise OriginalAcquisitionError("original download changed during byte comparison")
        return {
            "schema": SCHEMA,
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_records": ["https://zenodo.org/records/1297434",
                               "https://zenodo.org/records/18624542"],
            "original_zip_receipts": receipts,
            "original_member_byte_comparison": comparison,
            "third_party_payloads_printed_or_persisted": False,
            "geospatial_justification_for_width_changes": False,
            "source_data_admitted": False,
            "production_database_modified": False,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="opt-in exact 2 original ZIP downloads; no PR-head execution")
    args = parser.parse_args(argv)
    if not args.live:
        parser.print_help()
        return 2
    try:
        output = run_live()
    except (OriginalZipError, OriginalAcquisitionError) as exc:
        parser.error(str(exc))
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
