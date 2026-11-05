# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Discover notices in each original WBM BT-04 family via official TED Search.

Research-only, bounded index expansion, *not* a source XML replacement.
Exact known BT-04 IDs are read from a dated, independently reviewed official
Search API receipt. Return all matching publication numbers without claiming
shared real coverage or predecessor identity if no prior notice is indexed.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

from . import ted_berlin_insurance_search_api_preflight_v0 as api
from . import ted_wbm_2026_procedure_lineage_v0 as lineage
from . import ted_wbm_2026_procedure_search_index_v0 as index

RECEIPT = (
    Path(__file__).resolve().parents[1] / "research" / "observations" /
    "ted_wbm_2026_search_bt04_lineage_observation_v0.toml"
)
LIMIT = 25
FIELDS = (
    "publication-number", "procedure-identifier",
    "buyer-name", "notice-title", "publication-date",
)
MAX_TITLE = 420
MAX_RESULTS = LIMIT


def known_procedures(*, receipt: dict | None = None) -> dict[str, str]:
    if receipt is None:
        receipt = tomllib.loads(RECEIPT.read_text(encoding="utf-8"))
    if (
        receipt.get("schema_version")
            != "WBM_2026_TED_OFFICIAL_SEARCH_BT04_LINEAGE_OBSERVATION_V0"
        or receipt.get("api_payload_is_original_eforms_xml") is not False
        or receipt.get("indexed_procedure_ids_identical") is not False
        or receipt.get("exact_original_xml_pair_rechecked_this_run") is not False
    ):
        raise ValueError("TED_WBM_FAMILY_SOURCE_RECEIPT_NOT_RESEARCH_ONLY")
    out = {}
    for role, pub in (("competition", "286307-2026"), ("award", "668506-2026")):
        row = receipt.get(role)
        if not isinstance(row, dict) or row.get("publication_number") != pub:
            raise ValueError("TED_WBM_FAMILY_UNKNOWN_SOURCE_NOTICE")
        if row.get("official_api_response_bytes") != 7127:
            raise ValueError("TED_WBM_FAMILY_UNEXPECTED_REVIEWED_INDEX_SIZE")
        p = lineage._uuid4(row.get("indexed_BT04_procedure_uuid", ""), "PROCEDURE")
        out[role] = p
    if out["competition"] == out["award"]:
        raise ValueError("TED_WBM_FAMILY_INCONSISTENT_INDEXED_PROCEDURE_SET")
    return out


def query_body(procedure_uuid: str, *, known: dict[str, str] | None = None) -> bytes:
    values = (known or known_procedures())
    procedure_uuid = lineage._uuid4(procedure_uuid, "PROCEDURE")
    if procedure_uuid not in values.values():
        raise ValueError("TED_WBM_FAMILY_PROCEDURE_NOT_ALLOWLISTED")
    return json.dumps({
        "query": f"procedure-identifier = {procedure_uuid}",
        "fields": list(FIELDS),
        "limit": LIMIT, "page": 1,
        "scope": "ALL", "paginationMode": "PAGE_NUMBER",
        "checkQuerySyntax": False, "onlyLatestVersions": False,
    }, sort_keys=True).encode("utf-8")


def fetch(procedure_uuid: str, *, opener=urllib.request.urlopen,
          known: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(
        api.ENDPOINT, data=query_body(procedure_uuid, known=known),
        headers={"Content-Type": "application/json",
                 "Accept": "application/json",
                 "User-Agent": "OpenCatastrophe-WBM-TED-BT04-family/1.0"},
        method="POST",
    )
    with opener(request, timeout=40) as response:
        destination = urllib.parse.urlsplit(response.geturl())
        if (destination.scheme != "https"
                or destination.hostname != "api.ted.europa.eu"
                or destination.path != "/v3/notices/search"
                or destination.query or destination.fragment):
            raise ValueError("TED_WBM_FAMILY_NONOFFICIAL_RESPONSE_URL")
        status = getattr(response, "status", 200)
        if status != 200:
            raise ValueError("TED_WBM_FAMILY_HTTP_NON200_" + str(status))
        raw = response.read(api.MAX_BYTES + 1)
    if not 50 <= len(raw) <= api.MAX_BYTES:
        raise ValueError("TED_WBM_FAMILY_RESPONSE_NOT_BOUNDED")
    return raw


def parse(procedure_uuid: str, raw: bytes,
          *, known: dict[str, str] | None = None) -> dict:
    procedures = known or known_procedures()
    procedure_uuid = lineage._uuid4(procedure_uuid, "PROCEDURE")
    if procedure_uuid not in procedures.values():
        raise ValueError("TED_WBM_FAMILY_NOT_ALLOWLISTED")
    if type(raw) is not bytes or not 50 <= len(raw) <= api.MAX_BYTES:
        raise ValueError("TED_WBM_FAMILY_INVALID_SOURCE")
    try:
        data = json.loads(
            raw.decode("utf-8"), object_pairs_hook=api._no_duplicate_json,
            parse_constant=lambda x: (_ for _ in ()).throw(
                ValueError("TED_WBM_FAMILY_NONFINITE_JSON")),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("TED_WBM_FAMILY_INVALID_JSON") from exc
    if not isinstance(data, dict) or data.get("timedOut") is True:
        raise ValueError("TED_WBM_FAMILY_TIMED_OUT_OR_WRONG_ROOT")
    total = data.get("totalNoticeCount")
    rows = data.get("notices")
    if (type(total) is not int or not 1 <= total <= MAX_RESULTS
            or not isinstance(rows, list) or len(rows) != total):
        # No silent truncation, missing pagination or syntax-check-only reply.
        raise ValueError("TED_WBM_FAMILY_SOURCE_RESULTS_NOT_EXHAUSTIVE")
    result = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("TED_WBM_FAMILY_INVALID_NOTICE_ROW")
        pubs = index._values(row.get("publication-number"))
        if len(pubs) != 1 or not lineage.PUBLICATION_NUMBER.fullmatch(pubs[0]):
            raise ValueError("TED_WBM_FAMILY_BAD_PUBLICATION")
        if pubs[0] in seen:
            raise ValueError("TED_WBM_FAMILY_DUPLICATE_PUBLICATION")
        seen.add(pubs[0])
        proc = index._values(row.get("procedure-identifier"))
        if len(proc) != 1 or lineage._uuid4(proc[0], "PROCEDURE") != procedure_uuid:
            raise ValueError("TED_WBM_FAMILY_RESPONSE_PROCEDURE_MISMATCH")
        buyer = " ".join(index._values(row.get("buyer-name")))
        if not re.search(r"\bWBM\b", buyer, re.I):
            raise ValueError("TED_WBM_FAMILY_OTHER_BUYER_OR_UNKNOWN")
        titles = index._values(row.get("notice-title"))
        if not titles or any(len(t) > MAX_TITLE for t in titles):
            raise ValueError("TED_WBM_FAMILY_MISSING_OR_OVERSIZED_TITLE")
        # The official API may return 24 translated titles. Publish one
        # stable display sample; never flood CI logs with redundant locales.
        title = next((t for t in titles if t.startswith("Deutschland")), sorted(titles)[0])
        dates = sorted(set(index._values(row.get("publication-date"))))
        if len(dates) > 2:
            raise ValueError("TED_WBM_FAMILY_UNEXPECTED_PUBLICATION_DATES")
        result.append({
            "publication_number": pubs[0],
            "official_notice_url": "https://ted.europa.eu/en/notice/" + pubs[0],
            "publisher_index_notice_title_example": title,
            "publisher_index_publication_dates": dates,
            "indexed_same_BT04_as_queried": True,
            "same_procedure_confirmed_by_pinned_original_xml": False,
        })
    return {
        "procedure_uuid_index_query": procedure_uuid,
        "source_official_search_api": api.ENDPOINT,
        "official_publisher_index_response_sha256": hashlib.sha256(raw).hexdigest(),
        "official_publisher_index_response_bytes": len(raw),
        "matching_index_notice_count": total,
        "indexed_notices": sorted(result, key=lambda x: x["publication_number"]),
        "complete_first_page_for_reported_count": True,
        "source_xml_bytes_verified_during_this_index_query": False,
        "index_candidates_prove_original_predecessor_link": False,
        "current_signed_insurer_cover_or_50_40_10_policy_shares_proved": False,
        "real_geolocated_insurer_CAT_exposure_admitted": False,
        "raw_original_search_json_committed_or_printed": False,
    }


def main() -> int:
    try:
        p = known_procedures()
        results = []
        for role in ("competition", "award"):
            source = fetch(p[role], known=p)
            result = parse(p[role], source, known=p)
            result["requested_family"] = role
            result["known_notice_anchor"] = (
                "286307-2026" if role == "competition" else "668506-2026"
            )
            result["known_notice_anchor_found_in_index"] = (
                result["known_notice_anchor"] in
                {n["publication_number"] for n in result["indexed_notices"]}
            )
            if not result["known_notice_anchor_found_in_index"]:
                raise ValueError("TED_WBM_FAMILY_KNOWN_NOTICE_ANCHOR_MISSING")
            results.append(result)
        print(json.dumps({
            "schema_version": "TED_WBM_2026_INDEXED_PROCEDURE_FAMILIES_V0",
            "families": results,
            "exact_source_eforms_procedure_lineage_confirmed": False,
            "real_coinsurance_quota_or_CAT_exposure_admitted": False,
        }, ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("TED_WBM_PROCEDURE_FAMILY_SOURCE_BLOCKED: " +
              str(exc)[:160], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
