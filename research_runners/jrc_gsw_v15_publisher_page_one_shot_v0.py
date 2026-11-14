# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One exact bounded GET of JRC's published HTML *documentation* page.

This is NOT a CloudFerro listing/tile request; the JRC source access contract
remains documented_only and has no approved source-asset GET. The script
does not acquire, persist or hash original raster values or original Swift
listing bytes. It prints metadata, provenance, and the actual HTML page digest.
One shot only, no retries, redirects, proxies or caller-supplied endpoints.
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
from urllib import error, request

SOURCE = "ec-jrc.global-surface-water.1984-2024"
PUBLISHER_URL = "https://global-surface-water.appspot.com/download"
ORIGINAL_CATALOGUE_URL = "https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/"
FIXED_PRODUCT_TILE = (
    "download2024/Aggregated/VER1-5/occurrence/"
    "occurrence_10E_50N_v1_5_2024.tif"
)
MAX_HTML_BYTES = 262_144
TIMEOUT_SECONDS = 20


class PublisherPageBlocked(ValueError):
    """The original JRC publisher page could not be proven by a bounded read."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LinkAndTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: set[str] = set()
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for key, value in attrs:
                if key.lower() == "href" and value is not None:
                    self.links.add(value.strip())

    def handle_data(self, data):
        self.text.append(data)


def inspect_publisher_html(raw: bytes) -> dict[str, object]:
    """Schema-only: the HTML is publisher documentation, not a TIFF receipt."""
    if type(raw) is not bytes or not raw or len(raw) > MAX_HTML_BYTES:
        raise PublisherPageBlocked("original publisher HTML exceeds fixed byte budget")
    try:
        markup = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PublisherPageBlocked("publisher HTML not valid UTF-8") from exc
    if "\x00" in markup:
        raise PublisherPageBlocked("NUL within publisher HTML")
    page = LinkAndTextParser()
    page.feed(markup)
    normalized = re.sub(r"\s+", " ", " ".join(page.text)).lower()
    if not (
        "global surface water" in normalized
        and "data access" in normalized
        and "2026" in normalized
        and "november 10" in normalized
        and "occurrence" in normalized
        and "exceeding 100" in normalized
        and "source: ec jrc/google" in normalized
        and "without restriction of use" in normalized
        and ORIGINAL_CATALOGUE_URL in page.links
    ):
        raise PublisherPageBlocked("exact JRC v1.5 page update/link/rights shape not proven")
    # Link proves the publisher explicitly lists the Swift catalogue,
    # not that any individual GeoTIFF bytes or current file version exist.
    return {
        "profile": "jrc_gsw_v15_original_publisher_html_one_shot_metadata_v0",
        "source_id": SOURCE,
        "publisher_original_page_url": PUBLISHER_URL,
        "original_publisher_html_response_bytes": len(raw),
        "original_publisher_html_response_sha256": hashlib.sha256(raw).hexdigest(),
        "published_swift_catalogue_link_url": ORIGINAL_CATALOGUE_URL,
        "published_swift_catalogue_link_found": True,
        "product_version_1984_2024_v15_publisher_context": "1984-2024" in normalized and "v1.5" in normalized,
        "november_10_2026_occurrence_correction_announcement_found": True,
        "publisher_dataset_rights_statement_found": True,
        "publisher_required_attribution_found": True,
        "source_original_catalogue_bytes_hashed": False,
        "source_original_catalogue_complete": False,
        "individual_tile_path_in_html_proven": False,
        "individual_tile_original_bytes_hashed": False,
        "individual_tile_post_correction_bytes_verified": False,
        "cloudferro_service_api_terms_reviewed": False,
        "source_model_input_approved": False,
        "publisher_html_bytes_saved": False,
    }


def _open_fixed(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def probe(*, open_request=_open_fixed) -> dict[str, object]:
    req = request.Request(
        PUBLISHER_URL, method="GET",
        headers={
            "Accept": "text/html",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-Source-Documentation-Once/0.1",
        },
    )
    try:
        with open_request(req, TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != PUBLISHER_URL:
                raise PublisherPageBlocked("JRC publisher HTML response not exact HTTP 200")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media != "text/html":
                raise PublisherPageBlocked("JRC original page has unexpected media type")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise PublisherPageBlocked("unexpected compressed HTML bytes")
            announced = response.headers.get("Content-Length")
            if announced is not None:
                try:
                    length = int(announced)
                except (TypeError, ValueError) as exc:
                    raise PublisherPageBlocked("bad Content-Length") from exc
                if length < 1 or length > MAX_HTML_BYTES:
                    raise PublisherPageBlocked("publisher Content-Length outside fixed limit")
            raw = response.read(MAX_HTML_BYTES + 1)
    except PublisherPageBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise PublisherPageBlocked("bounded original publisher documentation GET unavailable") from exc
    parsed = inspect_publisher_html(raw)
    return {
        **parsed,
        "retrieval_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": 200,
        "request_sha256": hashlib.sha256(
            ("GET " + PUBLISHER_URL + " Accept:text/html Accept-Encoding:identity").encode("ascii")
        ).hexdigest(),
        "response_type": "text/html",
        "original_publisher_http_request_executed": True,
        "no_redirects": True,
        "no_retries": True,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--one-shot", action="store_true",
                        help="explicitly execute exactly one publisher HTML GET")
    args = parser.parse_args(argv)
    if not args.one_shot:
        parser.error("disabled by default; explicit --one-shot required")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except PublisherPageBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
