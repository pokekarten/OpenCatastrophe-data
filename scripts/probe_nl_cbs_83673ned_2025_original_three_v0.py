#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One strictly source-scoped, opt-in, three-GET ORIGINAL CBS public probe.

Official CBS StatLine table 83673NED, period 2025VJ06 only.
This is NOT a bulk data reader, OData URL builder or insurer TIV model.
No provider bytes saved to disk, logs, GitHub artifact or Neon.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import error, request

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "access" / "nl.cbs.new-housing-permit-2025v06-direct-three.83673ned.json"
SOURCE_ID = "nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned"
ACCESS_ID = "nl.cbs.new-housing-permit-2025v06-direct-three.83673ned"
OPERATION = "get_three_fixed_2025v06_rows"
ROOT_URL = "https://opendata.cbs.nl"
BASE = ROOT_URL + "/ODataApi/OData/83673NED/"
EXPECTED = (
    ("rental", BASE + "TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5",
     1457, "70731cf7be6e73813059c250db9f1f21ad4024f0fb7cba5075ad8af666d90a5e"),
    ("owner", BASE + "TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5",
     1459, "7c9b9e307fd7fbf4ef8d5e9e26eaf3d9b9a991dd54a6b95c01409d22663c5908"),
    ("period", BASE + "Perioden?$filter=Key%20eq%20%272025VJ06%27&$top=1",
     234, "626dac3ab357839e615bcf0260237651d4a3983a88a0f18f6c8e3bfc24272c4d"),
)
BYTES_MAX = 8192
TIMEOUT = 25
PERIOD = "2025VJ06"
STATUS = "Definitief"
REGIONS = ("NL01  ", "LD01  ", "LD02  ", "LD03  ", "LD04  ")
FIELDS = (
    "GemiddeldeBouwkostenPerWoning_1",
    "GemiddeldeBouwkostenPerM_2",  # CBS originally means EUR / cubic meter
    "GemiddeldeBouwkostenPerM_3",  # CBS originally means EUR / square meter
    "GemiddeldeInhoudWoningen_4",
    "GemiddeldeOppervlakteVanWoningen_5",
)
# Country followed by all four landsdelen, exact source-native values:
# ID, thousand EUR per dwelling, EUR/m3, EUR/m2, mean m3, mean m2.
ROWS = {
    "rental": (
        (50, 144, 474, 1417, 303, 101),
        (105, 159, 463, 1371, 343, 116),
        (160, 135, 449, 1337, 300, 101),
        (215, 149, 529, 1577, 281, 94),
        (270, 135, 416, 1258, 324, 107),
    ),
    "owner": (
        (325, 211, 411, 1221, 515, 173),
        (380, 216, 418, 1258, 517, 172),
        (435, 203, 392, 1159, 517, 175),
        (490, 225, 447, 1328, 504, 170),
        (545, 198, 374, 1114, 528, 178),
    ),
}


class CBSDirectBlocked(ValueError):
    """A source response or request is outside the exact review contract."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CBSDirectBlocked("original source redirected: outside allowed identity")


def direct_open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def verify_contract(path: Path = PATH) -> dict[str, Any]:
    c = validate_path(path)
    if (
        c["access_id"] != ACCESS_ID
        or c["source_ids"] != [SOURCE_ID]
        or c["interface_type"] != "rest"
        or c["status"] != "probe_ready"
        or c["service_root"] != ROOT_URL
        or c["request_contract"]["allowed_operations"] != [OPERATION]
        or c["request_contract"]["path_templates"] != [
            "/ODataApi/OData/83673NED/TypedDataSet",
            "/ODataApi/OData/83673NED/Perioden",
        ]
        or c["probe_contract"]["mode"] != "provider_specific"
        or c["probe_contract"]["operation"] != OPERATION
        or c["probe_contract"]["requires_credentials"] is not False
        or c["authentication"]["mode"] != "none"
        or c["authentication"]["secret_in_repository"] is not False
        or c["rights_and_policy"]["dataset_rights_status"] != "verified"
        or c["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or c["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or c["rights_and_policy"]["redistribution_status"] != "allowed"
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["max_probe_bytes"] != BYTES_MAX
        or c["operational_constraints"]["max_sample_bytes"] != BYTES_MAX
        or c["operational_constraints"]["retry_policy"] != "none"
    ):
        raise CBSDirectBlocked("exact rights/request/access gate changed")
    return c


def _strict_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise CBSDirectBlocked("duplicate original JSON key")
        result[key] = value
    return result


def _bad_constant(_: str):
    raise CBSDirectBlocked("nonfinite JSON literal")


def _finite_float(x: str) -> float:
    value = float(x)
    if not math.isfinite(value):
        raise CBSDirectBlocked("nonfinite overflow JSON float")
    return value


def parse(raw: bytes) -> list[dict[str, Any]]:
    if type(raw) is not bytes or not 0 < len(raw) <= BYTES_MAX:
        raise CBSDirectBlocked("empty or oversized original body")
    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_pairs,
            parse_constant=_bad_constant,
            parse_float=_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CBSDirectBlocked("not strict UTF-8 JSON") from exc
    if type(payload) is not dict or type(payload.get("value")) is not list:
        raise CBSDirectBlocked("original OData JSON value collection absent")
    if any(type(item) is not dict for item in payload["value"]):
        raise CBSDirectBlocked("original OData row is not JSON object")
    return payload["value"]


def validate(name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    if name == "period":
        if len(records) != 1 or any(
            records[0].get(key) != value for key, value in {
                "Key": PERIOD,
                "Title": "2024 juli - 2025 juni",
                "Status": STATUS,
            }.items()
        ):
            raise CBSDirectBlocked("official prior rolling period not definitive")
        return {"source_period": PERIOD, "period_status": STATUS,
                "period_name": "2024 juli - 2025 juni", "source_rows": 1}
    if name not in ROWS or len(records) != 5:
        raise CBSDirectBlocked("five rows per tenure required")
    tenure = {"rental": "A028867", "owner": "A028868"}[name]
    typed = []
    for i, (record, region, expected) in enumerate(zip(records, REGIONS, ROWS[name])):
        if (type(record.get("ID")) is not int
                or record["ID"] != expected[0]
                or record.get("Perioden") != PERIOD
                or record.get("Eigendom") != tenure
                or record.get("RegioS") != region):
            raise CBSDirectBlocked(f"native row/region/tenure/period mismatch {name}:{i}")
        for key, val in zip(FIELDS, expected[1:]):
            if type(record.get(key)) is not int or record[key] != val:
                raise CBSDirectBlocked(f"original permit field/unit mismatch {name}:{i}:{key}")
        _, cost_k, cost_m3, cost_m2, m3, m2 = expected
        if (abs(1000 * cost_k - cost_m3 * m3) > 3000
                or abs(1000 * cost_k - cost_m2 * m2) > 3000):
            raise CBSDirectBlocked("rounded average cost dimensions inconsistent")
        typed.append({
            "native_region": region, "tenure": name,
            "original_row_id": expected[0],
            "avg_permitted_eur_m3": cost_m3,
            "avg_permitted_eur_m2": cost_m2,
            "avg_permitted_1000eur_dwelling": cost_k,
            "avg_volume_m3": m3,
            "avg_floor_m2": m2,
        })
    return {"source_period": PERIOD, "tenure": name,
            "regional_mean_count": 5, "source_rows": typed}


def probe(
    *,
    open_source: Callable[[request.Request, int], Any] = direct_open,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = PATH,
) -> dict[str, Any]:
    verify_contract(contract_path)
    receipts: list[dict[str, Any]] = []
    for name, url, expected_bytes, expected_sha in EXPECTED:
        req = request.Request(
            url, method="GET",
            headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        )
        try:
            with open_source(req, TIMEOUT) as response:
                if response.status != 200 or response.geturl() != url:
                    raise CBSDirectBlocked("CBS public source not exact original HTTP 200")
                mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if mime != "application/json":
                    raise CBSDirectBlocked("source Content-Type not application/json")
                if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                    raise CBSDirectBlocked("source response compression unsupported")
                body = response.read(BYTES_MAX + 1)
        except CBSDirectBlocked:
            raise
        except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
            raise CBSDirectBlocked(f"CBS public network response did not pass source request contract ({name})") from exc
        digest = hashlib.sha256(body).hexdigest()
        if len(body) != expected_bytes or digest != expected_sha:
            raise CBSDirectBlocked(f"published CBS source body/version changed for {name}: stop for review")
        checked = validate(name, parse(body))
        receipts.append({
            "operation": name, "exact_original_source_url": url,
            "original_response_http_status": 200,
            "complete_original_bytes": len(body),
            "original_body_sha256": digest,
            "typed_public_source_summary": checked,
        })
    when = now()
    if when.tzinfo is None or when.utcoffset() is None:
        raise CBSDirectBlocked("original proof UTC must have timezone")
    return {
        "profile": "oc-nl-cbs-83673ned-2025-three-direct-original-v0",
        "source_id": SOURCE_ID,
        "access_id": ACCESS_ID,
        "retrieval_utc": when.astimezone(timezone.utc).isoformat(),
        "source_product_licence": "CBS StatLine 83673NED CC BY 4.0",
        "provider_original_response_count": 3,
        "full_original_provider_response_sha256_verified": True,
        "original_response_provenance": receipts,
        "original_provider_source_bodies_saved": False,
        "all_provider_data_downloaded": False,
        "remote_direct_runner_trusted": False,  # trust comes from GitHub job, not self-attestation
        "insured_replacement_costs_inferred": False,
        "scientific_cat_model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--live-three", action="store_true",
                        help="opt in once to exact three public CBS requests")
    args = parser.parse_args(argv)
    if not args.live_three:
        parser.error("CBS source transport is OFF; supply --live-three explicitly")
    try:
        result = probe()
    except CBSDirectBlocked:
        print("BLOCKED: CBS 83673NED direct 2025 original proof failed closed", file=sys.stderr)
        return 2
    # No original provider response body is ever printed. A GitHub runner
    # number and conclusion are external attestations, not self-reported.
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
