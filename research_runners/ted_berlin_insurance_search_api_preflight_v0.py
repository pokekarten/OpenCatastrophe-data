# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded direct TED Search API cross-check for two insurance notice numbers.

Official primary structured metadata, NOT original eForms XML bytes, insured
risk location, insurer award share or immutable original-source certification.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request

from .ted_berlin_insurance_original_xml_preflight_v0 import SOURCES

ENDPOINT = "https://api.ted.europa.eu/v3/notices/search"
MAX_BYTES = 300_000
ACCEPTED_NOTICE_FIELDS = (
    "publication-number", "buyer-name", "notice-title", "publication-date",
    "ojs-number",
)
# These are the *exact* official Search field list names. They are retrieved
# only by the separate WBM research-only candidate path. An indexed
# winner-name is NOT a confirmed SettledContract -> LotTender evidence edge.
WBM_AWARD_CANDIDATE_FIELDS = ACCEPTED_NOTICE_FIELDS + (
    "winner-name", "winner-identifier", "winner-selection-status",
    "contract-identifier", "contract-tender-id", "contract-conclusion-date",
    "winner-decision-date",
)


def _no_duplicate_json(pairs: list[tuple[str, object]]) -> dict:
    x = {}
    for key, value in pairs:
        if key in x:
            raise ValueError("TED_API_DUPLICATE_JSON_KEY")
        x[key] = value
    return x


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)


def query_body(notice: str, *, fields: tuple[str,...] | None = None) -> bytes:
    if notice not in SOURCES:
        raise ValueError("TED_API_NOTICE_NOT_ALLOWLISTED")
    if fields is None:
        fields = ACCEPTED_NOTICE_FIELDS
    if fields not in (ACCEPTED_NOTICE_FIELDS, WBM_AWARD_CANDIDATE_FIELDS):
        raise ValueError("TED_API_UNAPPROVED_FIELD_SELECTION")
    if fields == WBM_AWARD_CANDIDATE_FIELDS and notice != "668506-2026":
        raise ValueError("TED_API_AWARD_FIELDS_NOT_ALLOWED_FOR_TENDER")
    return json.dumps({
        "query": f"publication-number = {notice}",
        "fields": list(fields),
        "limit": 2,
        "page": 1,
        "scope": "ALL",
        "paginationMode": "PAGE_NUMBER",
        "checkQuerySyntax": False,
        "onlyLatestVersions": False,
    }, sort_keys=True).encode("utf-8")


def fetch(
    notice: str, *, fields: tuple[str,...] | None = None,
    opener=urllib.request.urlopen,
) -> bytes:
    request = urllib.request.Request(
        ENDPOINT, data=query_body(notice, fields=fields),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-TED-public-metadata-preflight/1.0",
        }, method="POST",
    )
    with opener(request, timeout=40) as response:
        target = urllib.parse.urlsplit(response.geturl())
        if (target.scheme != "https" or target.hostname != "api.ted.europa.eu"
                or target.path != "/v3/notices/search"):
            raise ValueError("TED_API_RESPONSE_NOT_FROM_OFFICIAL_HOST")
        status = getattr(response, "status", 200)
        if status != 200:
            raise ValueError(f"TED_API_HTTP_STATUS_{status}")
        raw = response.read(MAX_BYTES + 1)
    if not 50 <= len(raw) <= MAX_BYTES:
        raise ValueError("TED_API_TOO_BIG_OR_MISSING_RESPONSE")
    return raw


def parse(notice: str, raw: bytes) -> dict:
    if notice not in SOURCES or type(raw) is not bytes or not 50 <= len(raw) <= MAX_BYTES:
        raise ValueError("TED_API_WRONG_NOTICE_OR_RESPONSE")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_json,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError(
                               "TED_API_NONFINITE")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("TED_API_NOT_COMPLETE_JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("TED_API_WRONG_JSON_SHAPE")
    # The TED API's checkQuerySyntax=true mode validates the query only;
    # it deliberately does NOT execute an actual search. A validation
    # envelope must not be treated as real zero-result research evidence.
    if value.get("totalNoticeCount", "__absent__") is None:
        raise ValueError("TED_API_SYNTAX_ONLY_RESPONSE_NOT_SEARCH_RESULT")
    if value.get("timedOut") is True:
        raise ValueError("TED_API_SEARCH_TIMED_OUT")
    notices = value.get("notices")
    if not isinstance(notices, list) or len(notices) != 1 or not isinstance(notices[0], dict):
        raise ValueError("TED_API_EXPECT_ONE_EXACT_PUBLICATION")
    row = notices[0]
    published = row.get("publication-number")
    if published != notice and published != [notice]:
        raise ValueError("TED_API_RETURNED_WRONG_PUBLICATION")
    buyer = " ".join(_strings(row.get("buyer-name")))
    subject = " ".join(_strings(row.get("notice-title")))
    if not buyer or not subject:
        raise ValueError("TED_API_BUYER_OR_TITLE_FIELDS_ABSENT")
    if notice == "558592-2024":
        if not re.search("Gewobag", buyer, flags=re.IGNORECASE):
            raise ValueError("TED_API_BUYER_MISMATCH")
        if not re.search("Gebäudeversicherung", subject, flags=re.IGNORECASE):
            raise ValueError("TED_API_PRODUCT_MISMATCH")
    else:
        if not re.search("WBM", buyer, flags=re.IGNORECASE):
            raise ValueError("TED_API_BUYER_MISMATCH")
        if not re.search("Industrielle\\s+Sachversicherung", subject, flags=re.IGNORECASE):
            raise ValueError("TED_API_PRODUCT_MISMATCH")
    return {
        "publication_number": notice,
        "official_api_url": ENDPOINT,
        "structured_publisher_data_sha256": hashlib.sha256(raw).hexdigest(),
        "structured_publisher_data_bytes": len(raw),
        "publication_number_and_buyer_title_match": True,
        "original_eforms_xml_bytes_fetched_or_sha_pinned": False,
        "awarded_underwriter_roles_extracted_from_original_eforms": False,
        "insurer_site_allocation_or_tiv_observed": False,
        "original_api_json_body_stored_or_logged": False,
    }


def main() -> int:
    try:
        results = [parse(n, fetch(n)) for n in sorted(SOURCES)]
        print(json.dumps({
            "schema": "TED_BERLIN_PRIMARY_SEARCH_METADATA_RECEIPT_V0",
            "one_exact_primary_official_record_per_publication": True,
            "original_xml_retrieved": False,
            "carrier_contract_risk_allocation_or_cat_exposure_admitted": False,
            "source_receipts": results,
        }, ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError) as exc:
        print("TED_SEARCH_PRIMARY_METADATA_BLOCKED: " + str(exc)[:170], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
