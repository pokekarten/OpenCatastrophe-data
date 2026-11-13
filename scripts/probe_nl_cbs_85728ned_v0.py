#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Four exact original CBS StatLine 85728NED read-only OData source checks.

Explicit --live only; zero provider calls during CI and tests. Four fixed
requests, each <=16 KiB. No unreviewed URL/filter/table/period, redirect,
credential, retry, pagination, original bytes, insurer values or CAT admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import error, request

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "nl.cbs.new-build-input-cost-index.85728ned.json"
SOURCE_ID = "nl.cbs.new-build-input-cost-index.85728ned"
ROOT_URL = "https://opendata.cbs.nl"
BASE = ROOT_URL + "/ODataApi/OData/85728NED/"
OBJECTS = (
    ("table_info", BASE + "TableInfos?$top=1"),
    ("components", BASE + "Componenten?$top=3"),
    ("periods", BASE + "Perioden?$top=1"),
    ("first_observation", BASE + "TypedDataSet?$top=1"),
)
MAX_BYTES = 16384
TIMEOUT = 30
PROFILE = "oc-cbs-statline-85728ned-bounded-first-row-v0"
COMPONENTS = {
    "T001363": "Bouwkosten totaal",
    "A043942": "Looncomponent",
    "A043943": "Materiaalcomponent",
}


class CBSProbeBlocked(ValueError):
    """An original source response or reviewed access contract is not valid."""


def verify_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    c = validate_path(path)
    if (
        c["access_id"] != SOURCE_ID
        or c["source_ids"] != [SOURCE_ID]
        or c["service_root"] != ROOT_URL
        or c["status"] != "probe_ready"
        or c["authentication"]["mode"] != "none"
        or c["request_contract"]["allowed_operations"] != ["four_fixed_odata_rows"]
        or c["request_contract"]["path_templates"] != [
            "/ODataApi/OData/85728NED/TableInfos",
            "/ODataApi/OData/85728NED/Componenten",
            "/ODataApi/OData/85728NED/Perioden",
            "/ODataApi/OData/85728NED/TypedDataSet",
        ]
        or c["probe_contract"]["operation"] != "four_fixed_odata_rows"
        or c["probe_contract"]["mode"] != "provider_specific"
        or c["probe_contract"]["requires_credentials"] is not False
        or c["rights_and_policy"]["dataset_rights_status"] != "verified"
        or c["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or c["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or c["operational_constraints"]["max_sample_bytes"] != MAX_BYTES
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["retry_policy"] != "none"
    ):
        raise CBSProbeBlocked("fixed CBS StatLine source-access contract changed")
    return c


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CBSProbeBlocked("source redirect is prohibited")


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout)


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise CBSProbeBlocked("duplicated original JSON field")
        obj[key] = value
    return obj


def _reject_nan(value: str):
    raise CBSProbeBlocked("non-finite original CBS JSON token")


def decode_json(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise CBSProbeBlocked("empty or oversized original CBS JSON")
    try:
        content = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_nan,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CBSProbeBlocked("not strict original UTF-8 JSON") from exc
    if type(content) is not dict or type(content.get("value")) is not list:
        raise CBSProbeBlocked("not CBS OData JSON result")
    return content


def validate_rows(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if set(payloads) != {name for name, _ in OBJECTS}:
        raise CBSProbeBlocked("missing or additional CBS OData results")
    info, components, periods, observations = (
        payloads[name]["value"]
        for name in ("table_info", "components", "periods", "first_observation")
    )
    if (
        len(info) != 1 or type(info[0]) is not dict
        or info[0].get("ID") != 0
        or info[0].get("Identifier") != "85728NED"
        or info[0].get("Source") != "CBS."
        or "inputprijsindex bouwkosten 2021=100" not in info[0].get("Title", "")
        or type(info[0].get("Modified")) is not str
        or len(info[0]["Modified"]) > 32
    ):
        raise CBSProbeBlocked("CBS table identity or version metadata changed")
    try:
        modified = datetime.fromisoformat(info[0]["Modified"])
    except ValueError as exc:
        raise CBSProbeBlocked("malformed CBS table modification timestamp") from exc
    if modified.year < 2026:
        raise CBSProbeBlocked("unexpected old CBS index revision")

    if (
        len(components) != 3
        or any(type(row) is not dict for row in components)
        or {row.get("Key"): row.get("Title") for row in components} != COMPONENTS
    ):
        raise CBSProbeBlocked("CBS native input index component crosswalk changed")
    if (
        len(periods) != 1 or type(periods[0]) is not dict
        or periods[0].get("Key") != "2018MM01"
        or periods[0].get("Status") != "Definitief"
        or periods[0].get("Title") != "2018 januari"
    ):
        raise CBSProbeBlocked("CBS first month identity/status changed")
    if len(observations) != 1 or type(observations[0]) is not dict:
        raise CBSProbeBlocked("CBS first data row cardinality changed")
    row = observations[0]
    index_value = row.get("InputprijsindexBouwkosten_1")
    if (
        row.get("ID") != 0
        or row.get("Perioden") != "2018MM01"
        or row.get("Componenten") != "T001363"
        or type(index_value) not in {float, int}
        or index_value != 90.1
        or row.get("OntwikkelingTOVEenJaarEerder_2", "missing") is not None
    ):
        raise CBSProbeBlocked("CBS first native price-index observation changed")

    return {
        "table_id": "85728NED",
        "table_modified": info[0]["Modified"],
        "start_period": "2018MM01",
        "start_period_final": True,
        "component_id": "T001363",
        "component_meaning": "Dutch new-dwelling input construction costs",
        "first_price_index_2021_100": 90.1,
        "first_year_over_year_change": None,
        "observed_data_rows": 1,
        "observed_metadata_rows": 5,
        "individual_insured_buildings": 0,
        "full_rebuilding_tiv_validated": False,
        "cat_model_input_approved": False,
    }


def probe(
    *,
    open_request: Callable[[request.Request, int], Any] = _open,
    utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    verify_contract(contract_path)
    bodies: dict[str, dict[str, Any]] = {}
    receipts: dict[str, dict[str, Any]] = {}
    for name, url in OBJECTS:
        req = request.Request(
            url, method="GET",
            headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        )
        try:
            with open_request(req, TIMEOUT) as response:
                if response.status != 200 or response.geturl() != url:
                    raise CBSProbeBlocked("CBS request did not return exact direct HTTP 200")
                mime = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
                if mime != "application/json":
                    raise CBSProbeBlocked("unexpected CBS OData content type")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise CBSProbeBlocked("CBS response content encoding changed")
                raw = response.read(MAX_BYTES + 1)
        except CBSProbeBlocked:
            raise
        except (error.URLError, error.HTTPError, OSError, TimeoutError) as exc:
            raise CBSProbeBlocked("bounded original CBS OData fetch failed") from exc
        bodies[name] = decode_json(raw)
        receipts[name] = {
            "url": url, "original_body_bytes": len(raw),
            "original_body_sha256": hashlib.sha256(raw).hexdigest(),
            "response_media_type": mime,
        }
    safe = validate_rows(bodies)
    now = utc_clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise CBSProbeBlocked("UTC receipt must be timezone-aware")
    return {
        "profile": PROFILE, "source_id": SOURCE_ID,
        "source_access_contract": "access/nl.cbs.new-build-input-cost-index.85728ned.json",
        "retrieved_at_utc": now.astimezone(timezone.utc).isoformat(),
        "original_requests": receipts,
        **safe,
        "original_provider_bytes_persisted": False,
        "provider_payloads_committed": False,
        "full_source_asset_downloaded": False,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="explicitly opt in to four fixed public CBS GETs")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("live network access is opt-in; provide --live")
    try:
        print(json.dumps(probe(), sort_keys=True))
    except CBSProbeBlocked:
        print("BLOCKED: CBS bounded exact-source check failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
