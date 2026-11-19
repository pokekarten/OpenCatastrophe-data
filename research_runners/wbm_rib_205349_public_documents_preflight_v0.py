# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded public-access check of the exact WBM Berlin RIB tender 205349.

Read only the public announcement landing page; NO authentication, no document
downloads, no JS scripts, and never infer insurer-risk or policy terms from
generic page instructions or absent document links.
"""
from __future__ import annotations

import hashlib
from html import unescape
from html.parser import HTMLParser
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

OFFICIAL_URL = (
    "https://www.meinauftrag.rib.de/public/"
    "DetailsByPlatformIdAndTenderId/platformId/2/tenderId/205349"
)
ALLOWED_HOSTS = frozenset({"www.meinauftrag.rib.de", "meinauftrag.rib.de"})
EXACT_PATH = "/public/DetailsByPlatformIdAndTenderId/platformId/2/tenderId/205349"
MAX_BYTES = 750_000
NO_LONGER_PUBLIC_MARKERS = (
    "announcement not found",
    "desired announcement is no longer publicly available",
    "bekanntmachung nicht gefunden",
    "bekanntmachung ist nicht mehr öffentlich verfügbar",
)
NOT_FOUND_STATUSES = {404, 410}


class ReadableHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth_excluded = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("style", "script", "noscript", "svg"):
            self.depth_excluded += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("style", "script", "noscript", "svg") and self.depth_excluded:
            self.depth_excluded -= 1

    def handle_data(self, data: str) -> None:
        if not self.depth_excluded and data.strip():
            self.parts.append(data)


def _verify_url(url: str) -> None:
    x = urllib.parse.urlsplit(url)
    if (x.scheme != "https" or x.hostname not in ALLOWED_HOSTS
            or x.path != EXACT_PATH or x.query or x.fragment
            or x.username or x.password or x.port is not None):
        raise ValueError("RIB_TENDER_UNEXPECTED_HOST_REDIRECT_PATH_OR_QUERY")


def inspect(raw: bytes, *, status: int = 200,
            response_url: str = OFFICIAL_URL, content_type: str = "text/html") -> dict:
    _verify_url(response_url)
    if status not in (200, 404, 410):
        raise ValueError("RIB_TENDER_NONPUBLIC_HTTP_STATUS_" + str(status))
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError("RIB_TENDER_INVALID_OR_OVERSIZE_BODY")
    # A not-found response is not proof the final procurement never existed.
    if status in NOT_FOUND_STATUSES:
        classification = "PUBLIC_LANDING_PAGE_HTTP_NOT_FOUND"
        html_match = False
        target_tender_visible = False
    else:
        if not 75 <= len(raw) or "html" not in content_type.lower():
            raise ValueError("RIB_TENDER_UNEXPECTED_DOCUMENT_OR_SHORT_HTML")
        doc = ReadableHTML()
        try:
            doc.feed(raw.decode("utf-8", errors="replace"))
        except ValueError as exc:
            raise ValueError("RIB_TENDER_HTML_PARSE_FAILED") from exc
        text = re.sub(r"\s+", " ", unescape(" ".join(doc.parts))).strip().lower()
        html_match = any(m in text for m in NO_LONGER_PUBLIC_MARKERS)
        target_tender_visible = bool(
            "vv 2026-0069" in text and
            "industrielle sachversicherung" in text)
        classification = (
            "PUBLIC_ANNOUNCEMENT_EXPIRED_OR_NOT_FOUND_RENDERED"
            if html_match else
            "PUBLIC_TENDER_METADATA_VISIBLE_BUT_ATTACHMENTS_UNVERIFIED"
            if target_tender_visible else
            "PUBLIC_CLIENT_PAGE_OR_DYNAMIC_CONTENT_UNRESOLVED"
        )
    return {
        "schema_version": "WBM_RIB_205349_PUBLIC_DOCUMENT_ACCESS_PREFLIGHT_V0",
        "source_url": OFFICIAL_URL,
        "http_status": status,
        "response_body_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "classification": classification,
        "explicit_not_available_message_observed_in_html": html_match,
        "target_tender_number_and_insurance_subject_visible": target_tender_visible,
        "public_attachments_enumerated_or_downloaded": False,
        "full_insurance_terms_or_signed_contract_observed": False,
        "nine_real_insured_locations_or_tiv_observed": False,
        "actual_HDI_Helvetia_RV_company_policy_shares_observed": False,
        "actual_RV_CAT_exposure_admitted": False,
        "raw_provider_html_committed_or_logged": False,
        "no_credentials_cookies_or_logins_used": True,
    }


def fetch(*, opener=urllib.request.urlopen) -> dict:
    request = urllib.request.Request(
        OFFICIAL_URL, headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "OpenCatastrophe-public-procurement-readonly/1.0",
        },
    )
    try:
        with opener(request, timeout=25) as r:
            final_url = r.geturl()
            _verify_url(final_url)
            status = getattr(r, "status", 200)
            content_type = r.headers.get("Content-Type", "") if getattr(
                r, "headers", None) is not None else ""
            if status not in (200, 404, 410):
                raise ValueError("RIB_TENDER_UNEXPECTED_HTTP_STATUS_" + str(status))
            raw = r.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        _verify_url(e.geturl())
        if e.code not in NOT_FOUND_STATUSES:
            raise ValueError("RIB_TENDER_UNEXPECTED_HTTP_STATUS_" + str(e.code)) from e
        status = e.code
        final_url = e.geturl()
        content_type = e.headers.get("Content-Type", "") if e.headers else ""
        raw = e.read(MAX_BYTES + 1)
    return inspect(raw, status=status, response_url=final_url,
                   content_type=content_type)


def main() -> int:
    try:
        print(json.dumps(fetch(), ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError) as exc:
        print("RIB_WBM_205349_PUBLIC_ACCESS_BLOCKED: " + str(exc)[:180],
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
