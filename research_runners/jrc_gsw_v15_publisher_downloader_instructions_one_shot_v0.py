# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One bounded ORIGINAL JRC instruction-page HTML GET, never a raster GET.

Strict offline source-content checks prove that the publisher explicitly
documents a Python downloader and its unscoped 360-tile default. They do NOT
grant CloudFerro quotas, assert a corrected 2026-11-10 TIFF byte identity,
run the publisher's bulk downloader, or approve insurer/CAT-model input.

No network without --one-shot-instructions. Exact URL, no proxy/redirect/
retry, 32768-byte cap, 20s, anonymous GET, only typed metadata output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import re
import ssl
import sys
from typing import Any, Callable
from urllib import error, request

SOURCE = "ec-jrc.global-surface-water.1984-2024"
URL = "https://global-surface-water.appspot.com/gsw/Download_Instructions.html"
SOURCE_PAGE = "https://global-surface-water.appspot.com/download"
CLOUDFERRO_ROOT = (
    "https://s3.waw4-1.cloudferro.com/swift/v1/"
    "global-surface-water/download2024/Aggregated/VER1-5/"
)
FIXED_TIFF = CLOUDFERRO_ROOT + "occurrence/occurrence_10E_50N_v1_5_2024.tif"
MAX_HTML_BYTES = 32768
TIMEOUT = 20

class InstructionBlocked(ValueError):
    """Original public publisher instruction identity or HTTP scope changed."""

class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
    def handle_data(self, data: str):
        self.chunks.append(data)

def inspect_instructions(original: bytes) -> dict[str, Any]:
    if type(original) is not bytes or not (0 < len(original) <= MAX_HTML_BYTES):
        raise InstructionBlocked("original JRC instruction HTML absent or over byte cap")
    try:
        html = original.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise InstructionBlocked("publisher HTML invalid UTF-8") from exc
    if "\x00" in html or "<html" not in html.lower():
        raise InstructionBlocked("original JRC instructions not an HTML page")
    parser = TextOnly()
    parser.feed(html)
    normalized = re.sub(r"\s+", " ", " ".join(parser.chunks)).lower()
    needles = (
        "global surface water explorer",
        "downloadwaterdata_python3_v1_5.py",
        "360 tiles",
        "aggregated products",
        "downloads a single file per tile",
        "monthly history",
        "all years",
        "all tiles",
        "download2024/aggregated/ver1-5/",
        "download2024/monthlyhistory/ver1-5/",
        "occurrence",
        "european commission",
    )
    if not all(token in normalized for token in needles):
        raise InstructionBlocked("GSW v1.5 published bulk/script/data scope drift")
    if "https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/" not in normalized:
        raise InstructionBlocked("publisher CloudFerro delivery route not found")
    # Exact external data URL is a deliberate research target only;
    # never select the 360-tile downloader, even when JRC publishes one.
    return {
        "profile": "jrc_gsw_v15_original_publisher_downloader_instructions_v0",
        "source_id": SOURCE,
        "original_publisher_instructions_url": URL,
        "original_page_body_bytes": len(original),
        "original_page_full_sha256": hashlib.sha256(original).hexdigest(),
        "publisher_ec_python_downloader_documented": True,
        "publisher_downloader_name": "downloadWaterData_Python3_v1_5.py",
        "publisher_cloudferro_aggregated_delivery_root_documented": True,
        "original_publisher_aggregated_default_tile_count": 360,
        "aggregated_mode_explicit_one_tile_option_verified": False,
        "publisher_monthlyhistory_without_tile_filter_is_bulk": True,
        "fixed_research_aggregated_product": "occurrence",
        "single_fixed_research_tile_id": "10E_50N",
        "reviewed_future_original_tile_url": FIXED_TIFF,
        "publisher_downloader_executed": False,
        "cloudferro_original_tile_get_performed": False,
        "cloudferro_anonymous_host_quota_verified": False,
        "cloudferro_automated_bulk_access_approved": False,
        "original_tiff_version_correction_verified": False,
        "raw_html_body_stored": False,
        "raw_tiff_body_stored": False,
        "source_asset_network_requests_approved": 0,
        "scientific_cat_model_input_approved": False,
    }

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)

def probe(*, open_request: Callable[[request.Request, int], Any] = _open,
          clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> dict[str, Any]:
    req = request.Request(
        URL, method="GET", headers={
            "Accept": "text/html", "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-JRC-Publisher-Instructions-Once/0.1",
        }
    )
    try:
        with open_request(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != URL:
                raise InstructionBlocked("publisher instruction response must be original HTTP200 exact URL")
            if response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "text/html":
                raise InstructionBlocked("publisher instructions expected text/html")
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise InstructionBlocked("compressed HTTP body not allowed")
            claimed = response.headers.get("Content-Length")
            if claimed is not None:
                try:
                    size = int(claimed)
                except ValueError as exc:
                    raise InstructionBlocked("invalid publisher Content-Length") from exc
                if not (0 < size <= MAX_HTML_BYTES):
                    raise InstructionBlocked("declared publisher content exceeds 32768 bytes")
            raw = response.read(MAX_HTML_BYTES + 1)
    except InstructionBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise InstructionBlocked("fixed public JRC instruction GET failed") from exc
    receipt = inspect_instructions(raw)
    now = clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise InstructionBlocked("original source timestamp not timezone-aware")
    return {
        **receipt,
        "retrieval_utc": now.astimezone(timezone.utc).isoformat(),
        "original_publisher_http_status": 200,
        "original_publisher_page_get_count": 1,
        "original_publisher_html_only": True,
        "original_request_sha256": hashlib.sha256(
            ("GET " + URL + " Accept:text/html Accept-Encoding:identity").encode("ascii")
        ).hexdigest(),
        "original_publisher_bytes_persisted": False,
        "direct_GitHub_runner_self_attested": False,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--one-shot-instructions", action="store_true")
    args = parser.parse_args(argv)
    if not args.one_shot_instructions:
        parser.error("no provider network without --one-shot-instructions")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except InstructionBlocked:
        print("BLOCKED: bounded original publisher instructions metadata", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
