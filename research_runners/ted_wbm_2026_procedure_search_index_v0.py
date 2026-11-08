# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Official TED Search API index BT-04 lineage for WBM 2026, research only.

Unlike the pinned XML, Search API index fields are not original eForms bytes;
index procedure UUIDs and previous publication references are *candidates*.
Do not promote a matching title, buyer or indexed UUID to exact original
document verification. Never infer signed insurance contracts or CAT exposure.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request

from . import ted_berlin_insurance_search_api_preflight_v0 as api
from . import ted_wbm_2026_procedure_lineage_v0 as source_lineage

NOTICES = ("286307-2026", "668506-2026")
SEARCH_FIELDS = (
    "publication-number", "buyer-name", "notice-title",
    "procedure-identifier", "previous-notice-id-proc",
)
MAX_FIELD_VALUES = 30
MAX_FIELD_CHARS = 320


def _values(value, depth=0) -> list[str]:
    if depth > 4:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_FIELD_TOO_DEEP")
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        if len(s) > MAX_FIELD_CHARS or any(ord(c) < 32 for c in s):
            raise ValueError("TED_WBM_PROCEDURE_INDEX_TEXT_INVALID")
        return [s]
    if isinstance(value, list):
        if len(value) > MAX_FIELD_VALUES:
            raise ValueError("TED_WBM_PROCEDURE_INDEX_FIELD_TOO_MANY_VALUES")
        return [x for v in value for x in _values(v, depth + 1)]
    if isinstance(value, dict):
        if len(value) > MAX_FIELD_VALUES:
            raise ValueError("TED_WBM_PROCEDURE_INDEX_FIELD_TOO_MANY_VALUES")
        return [x for v in value.values() for x in _values(v, depth + 1)]
    raise ValueError("TED_WBM_PROCEDURE_INDEX_UNSUPPORTED_FIELD_TYPE")


def query_body(notice: str) -> bytes:
    if notice not in NOTICES:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_NOTICE_NOT_ALLOWLISTED")
    return json.dumps({
        "query": f"publication-number = {notice}",
        "fields": list(SEARCH_FIELDS),
        "limit": 2, "page": 1, "scope": "ALL",
        "paginationMode": "PAGE_NUMBER",
        "checkQuerySyntax": False, "onlyLatestVersions": False,
    }, sort_keys=True).encode("utf-8")


def fetch(notice: str, *, opener=urllib.request.urlopen) -> bytes:
    request = urllib.request.Request(
        api.ENDPOINT, data=query_body(notice), method="POST",
        headers={"Content-Type": "application/json",
                 "Accept": "application/json",
                 "User-Agent": "OpenCatastrophe-WBM-TED-procedure-index/1.0"},
    )
    with opener(request, timeout=40) as response:
        u = urllib.parse.urlsplit(response.geturl())
        if (u.scheme != "https" or u.hostname != "api.ted.europa.eu"
                or u.path != "/v3/notices/search" or u.query or u.fragment):
            raise ValueError("TED_WBM_PROCEDURE_INDEX_NOT_OFFICIAL_HOST")
        if getattr(response, "status", 200) != 200:
            raise ValueError("TED_WBM_PROCEDURE_INDEX_NON200_RESPONSE")
        raw = response.read(api.MAX_BYTES + 1)
    if not 50 <= len(raw) <= api.MAX_BYTES:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_SOURCE_NOT_BOUNDED")
    return raw


def parse(notice: str, raw: bytes) -> dict:
    if notice not in NOTICES or type(raw) is not bytes or not 50 <= len(raw) <= api.MAX_BYTES:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_NOTICE_OR_SOURCE_NOT_ALLOWLISTED")
    try:
        data = json.loads(
            raw.decode("utf-8"), object_pairs_hook=api._no_duplicate_json,
            parse_constant=lambda x: (_ for _ in ()).throw(
                ValueError("TED_WBM_PROCEDURE_INDEX_NONFINITE_JSON")),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_INVALID_JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("TED_WBM_PROCEDURE_INDEX_WRONG_JSON_ROOT")
    if data.get("timedOut") is True or data.get("totalNoticeCount") is None:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_TIMED_OUT_OR_SYNTAX_ONLY")
    records = data.get("notices")
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        raise ValueError("TED_WBM_PROCEDURE_INDEX_EXPECT_EXACTLY_ONE_PUBLICATION")
    row = records[0]
    pub = _values(row.get("publication-number"))
    if pub != [notice]:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_WRONG_PUBLICATION")
    buyer = " ".join(_values(row.get("buyer-name")))
    subject = " ".join(_values(row.get("notice-title")))
    if not re.search(r"\bWBM\b", buyer, re.I):
        raise ValueError("TED_WBM_PROCEDURE_INDEX_WRONG_BUYER")
    if not re.search(r"Industrielle\s+Sachversicherung", subject, re.I):
        raise ValueError("TED_WBM_PROCEDURE_INDEX_WRONG_PRODUCT")
    ids = sorted(set(_values(row.get("procedure-identifier"))))
    if len(ids) != 1:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_NOT_ONE_PROCEDURE_UUID")
    procedure = source_lineage._uuid4(ids[0], "SEARCH_PROCEDURE")
    refs = sorted(set(_values(row.get("previous-notice-id-proc"))))
    if len(refs) > MAX_FIELD_VALUES or any(
        not source_lineage.PUBLICATION_NUMBER.fullmatch(x) for x in refs
    ):
        raise ValueError("TED_WBM_PROCEDURE_INDEX_BAD_PREVIOUS_REFERENCE")
    return {
        "notice": notice,
        "official_search_api_url": api.ENDPOINT,
        "indexed_procedure_uuid_BT04": procedure,
        "indexed_previous_publication_references_OPP090": refs,
        "source_api_response_sha256": hashlib.sha256(raw).hexdigest(),
        "source_api_response_bytes": len(raw),
        "one_exact_publisher_index_record_and_wbm_subject": True,
        "original_xml_retrieved_and_byte_sha_verified": False,
        "same_procedure_proved_from_original_eforms": False,
        "signed_policy_coinsurance_shares_and_risk_sites_verified": False,
        "real_cat_exposure_admitted": False,
        "raw_json_committed_or_logged": False,
    }


def compare(competition: dict, award: dict) -> dict:
    if competition.get("notice") != NOTICES[0] or award.get("notice") != NOTICES[1]:
        raise ValueError("TED_WBM_PROCEDURE_INDEX_COMPARE_WRONG_NOTICE_PAIR")
    for row in (competition, award):
        if (row.get("one_exact_publisher_index_record_and_wbm_subject") is not True
                or row.get("original_xml_retrieved_and_byte_sha_verified") is not False
                or row.get("same_procedure_proved_from_original_eforms") is not False
                or row.get("real_cat_exposure_admitted") is not False):
            raise ValueError("TED_WBM_PROCEDURE_INDEX_PROVENANCE_OVERCLAIM")
    p1 = source_lineage._uuid4(
        competition.get("indexed_procedure_uuid_BT04", ""), "SEARCH_PROCEDURE")
    p2 = source_lineage._uuid4(
        award.get("indexed_procedure_uuid_BT04", ""), "SEARCH_PROCEDURE")
    refs = award.get("indexed_previous_publication_references_OPP090")
    if not isinstance(refs, list):
        raise ValueError("TED_WBM_PROCEDURE_INDEX_WRONG_PREVIOUS_REFS")
    return {
        "schema_version": "TED_WBM_2026_OFFICIAL_SEARCH_INDEX_BT04_LINEAGE_CANDIDATE_V0",
        "competition_notice": NOTICES[0],
        "award_notice": NOTICES[1],
        "competition_search_index_BT04": p1,
        "award_search_index_BT04": p2,
        "search_index_procedure_uuids_identical": p1 == p2,
        "search_index_award_explicitly_references_earlier_publication":
            NOTICES[0] in refs,
        "classification": (
            "INDEXED_SAME_BT04_REQUIRES_ORIGINAL_REPLAY"
            if p1 == p2 else "INDEXED_DIFFERENT_BT04_REQUIRES_ORIGINAL_REPLAY"
        ),
        "individual_official_json_research_receipts": [
            {"notice": row["notice"],
             "response_sha256": row["source_api_response_sha256"],
             "response_bytes": row["source_api_response_bytes"]}
            for row in (competition, award)
        ],
        "original_eforms_source_uuid_link_confirmed": False,
        "actual_insurance_share_or_CAT_model_exposure_admitted": False,
        "raw_api_json_committed_or_logged": False,
    }


def main() -> int:
    try:
        early = parse(NOTICES[0], fetch(NOTICES[0]))
        late = parse(NOTICES[1], fetch(NOTICES[1]))
        print(json.dumps(compare(early, late),
                         ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("TED_WBM_PROCEDURE_SEARCH_INDEX_BLOCKED: " +
              str(exc)[:165], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
