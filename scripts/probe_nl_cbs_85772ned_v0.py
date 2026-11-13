#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""CBS 85772NED six frozen original OData JSON proofs; only explicit --live.

No network in tests or normal CI; no original source bytes/insurer data saved.
The source output-price index is not replacement value, exposure or CAT loss.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import error, request

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "nl.cbs.new-build-output-cost-index.85772ned.json"
SOURCE_ID = "nl.cbs.new-build-output-cost-index.85772ned"
ROOT_URL = "https://opendata.cbs.nl"
BASE = ROOT_URL + "/ODataApi/OData/85772NED/"
OBJECTS = (
    ("table_info", BASE + "TableInfos?$top=1"),
    ("first_index", BASE + "TypedDataSet?$top=1"),
    ("first_period", BASE + "Perioden?$top=1"),
    ("properties", BASE + "DataProperties?$top=6"),
    ("q2_2026_index", BASE + "TypedDataSet?$filter=Perioden%20eq%20%272026KW02%27&$top=1"),
    ("q2_2026_period", BASE + "Perioden?$filter=Key%20eq%20%272026KW02%27&$top=1"),
)
MAX_BYTES = 16384
TIMEOUT = 30
EXPECTED_MODIFIED = "2026-09-30T02:00:00"


class CBSOutputBlocked(ValueError):
    """Review is required before a changed provider payload can be accepted."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CBSOutputBlocked("redirect not allowed by fixed CBS contract")


def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout)


def verify_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    c = validate_path(path)
    expected_paths = [
        "/ODataApi/OData/85772NED/TableInfos",
        "/ODataApi/OData/85772NED/TypedDataSet",
        "/ODataApi/OData/85772NED/Perioden",
        "/ODataApi/OData/85772NED/DataProperties",
    ]
    if (
        c["access_id"] != SOURCE_ID
        or c["source_ids"] != [SOURCE_ID]
        or c["service_root"] != ROOT_URL
        or c["status"] != "probe_ready"
        or c["interface_type"] != "rest"
        or c["authentication"]["mode"] != "none"
        or c["request_contract"]["allowed_operations"] != ["six_fixed_original_odata_rows"]
        or c["request_contract"]["path_templates"] != expected_paths
        or c["probe_contract"]["mode"] != "provider_specific"
        or c["probe_contract"]["operation"] != "six_fixed_original_odata_rows"
        or c["probe_contract"]["requires_credentials"] is not False
        or c["rights_and_policy"]["dataset_rights_status"] != "verified"
        or c["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or c["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or c["operational_constraints"]["max_sample_bytes"] != MAX_BYTES
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["retry_policy"] != "none"
    ):
        raise CBSOutputBlocked("CBS 85772NED access contract changed")
    return c


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, val in pairs:
        if key in result:
            raise CBSOutputBlocked("duplicate original JSON key")
        result[key] = val
    return result


def _no_constant(value: str):
    raise CBSOutputBlocked("non-finite original JSON number")


def _safe_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise CBSOutputBlocked("overflowing original JSON floating point")
    return result


def decode_original(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise CBSOutputBlocked("original body exceeds fixed request bound")
    try:
        obj = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_fields,
            parse_constant=_no_constant, parse_float=_safe_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CBSOutputBlocked("CBS original response is not strict UTF-8 JSON") from exc
    if type(obj) is not dict or type(obj.get("value")) is not list:
        raise CBSOutputBlocked("CBS original response is not OData JSON")
    return obj


def validate_rows(bodies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if set(bodies) != {name for name, _ in OBJECTS}:
        raise CBSOutputBlocked("not exactly six reviewed CBS responses")
    info, first, early, properties, recent, late = (
        bodies[name]["value"]
        for name in ("table_info", "first_index", "first_period",
                     "properties", "q2_2026_index", "q2_2026_period")
    )
    if len(info) != 1 or type(info[0]) is not dict:
        raise CBSOutputBlocked("invalid CBS table metadata count")
    meta = info[0]
    if (
        meta.get("ID") != 0
        or meta.get("Identifier") != "85772NED"
        or meta.get("Source") != "CBS."
        or meta.get("Modified") != EXPECTED_MODIFIED
        or "outputprijsindex bouwkosten 2021=100" not in meta.get("Title", "")
        or meta.get("Frequency") != "Perkwartaal"
    ):
        raise CBSOutputBlocked("unreviewed CBS table identity or publication revision")

    if len(properties) != 6 or any(type(x) is not dict for x in properties):
        raise CBSOutputBlocked("changed CBS data-property list")
    if (
        [(x.get("ID"), x.get("Type"), x.get("Key")) for x in properties]
        != [(0, "TimeDimension", "Perioden"), (1, "TopicGroup", ""),
            (2, "Topic", "Prijsindex_1"),
            (3, "Topic", "OntwikkelingTOVEenJaarEerder_2"),
            (4, "TopicGroup", ""), (5, "Topic", "Prijsindex_3")]
        or properties[1].get("Title") != "Outputprijsindex bouwkosten incl. btw"
        or properties[4].get("Title") != "Outputprijsindex bouwkosten excl. btw"
        or properties[2].get("Unit") != "2021=100"
        or properties[5].get("Unit") != "2021=100"
        or properties[2].get("ParentID") != 1
        or properties[5].get("ParentID") != 4
    ):
        raise CBSOutputBlocked("CBS VAT/field/unit/topic mapping changed")
    if (
        len(early) != 1 or type(early[0]) is not dict
        or early[0].get("Key") != "2018KW01"
        or early[0].get("Title") != "2018 1e kwartaal"
        or early[0].get("Status") != "Definitief"
        or len(late) != 1 or type(late[0]) is not dict
        or late[0].get("Key") != "2026KW02"
        or late[0].get("Title") != "2026 2e kwartaal"
        or late[0].get("Status") != "Voorlopig"
    ):
        raise CBSOutputBlocked("CBS quarter identity or finality changed")

    if len(first) != 1 or type(first[0]) is not dict or len(recent) != 1 or type(recent[0]) is not dict:
        raise CBSOutputBlocked("changed CBS numeric-row cardinality")
    a, b = first[0], recent[0]
    for row, expected_id, quarter, level, pct in [
        (a, 0, "2018KW01", 87.7, None),
        (b, 41, "2026KW02", 133.4, 4.4),
    ]:
        if (
            row.get("ID") != expected_id
            or row.get("Perioden") != quarter
            or type(row.get("Prijsindex_1")) not in {int, float}
            or type(row.get("Prijsindex_3")) not in {int, float}
            or row["Prijsindex_1"] != level or row["Prijsindex_3"] != level
            or row.get("OntwikkelingTOVEenJaarEerder_2", object()) != pct
            or row.get("OntwikkelingTOVEenJaarEerder_4", object()) != pct
            or any(type(row.get(key)) not in {int, float}
                   for key in ("OntwikkelingTOVEenJaarEerder_2",
                               "OntwikkelingTOVEenJaarEerder_4"))
                 if pct is not None else False
        ):
            raise CBSOutputBlocked("CBS original numeric value or VAT series changed")
    return {
        "table_id": "85772NED",
        "table_modified": EXPECTED_MODIFIED,
        "index_base_year": 2021,
        "first_quarter": "2018KW01",
        "first_quarter_final": True,
        "first_vat_included_and_excluded_index": 87.7,
        "recent_quarter": "2026KW02",
        "recent_quarter_final": False,
        "recent_vat_included_and_excluded_index": 133.4,
        "recent_vat_included_and_excluded_yoy_percent": 4.4,
        "december_2025_publisher_correction_requires_vintage_review": True,
        "insured_replacement_eur_computed": False,
        "model_input_approved": False,
    }


def probe(
    *,
    open_request: Callable[[request.Request, int], Any] = _open,
    now_utc: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    verify_contract(contract_path)
    data: dict[str, dict[str, Any]] = {}
    receipts: dict[str, dict[str, Any]] = {}
    for name, url in OBJECTS:
        req = request.Request(
            url, method="GET",
            headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        )
        try:
            with open_request(req, TIMEOUT) as response:
                if response.status != 200 or response.geturl() != url:
                    raise CBSOutputBlocked("CBS direct HTTP 200 and exact URL required")
                mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if mime != "application/json":
                    raise CBSOutputBlocked("unexpected CBS original media type")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise CBSOutputBlocked("compressed original CBS response not permitted")
                raw = response.read(MAX_BYTES + 1)
        except CBSOutputBlocked:
            raise
        except (error.URLError, error.HTTPError, OSError, TimeoutError) as exc:
            raise CBSOutputBlocked("original CBS response could not be acquired") from exc
        data[name] = decode_original(raw)
        receipts[name] = {
            "url": url,
            "original_response_bytes": len(raw),
            "original_response_sha256": hashlib.sha256(raw).hexdigest(),
        }
    observations = validate_rows(data)
    now = now_utc()
    if now.tzinfo is None or now.utcoffset() is None:
        raise CBSOutputBlocked("UTC timestamp must be timezone-aware")
    return {
        "profile": "oc-cbs-85772ned-six-original-rows-v0",
        "source_id": SOURCE_ID,
        "contract": "access/nl.cbs.new-build-output-cost-index.85772ned.json",
        "retrieved_at_utc": now.astimezone(timezone.utc).isoformat(),
        "original_response_receipts": receipts,
        **observations,
        "provider_bytes_persisted": False,
        "provider_payload_committed": False,
        "full_table_downloaded": False,
        "strict_repository_runner_executed": True,
        "scientific_model_admission": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="explicitly opt into six exact CBS provider GETs")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("direct provider network is opt-in: --live required")
    try:
        print(json.dumps(probe(), sort_keys=True))
    except CBSOutputBlocked:
        print("BLOCKED: CBS output-index original six-source probe failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
