#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two fixed genuine original CBS 83673NED regional 2026VJ06 OData GETs.

Public CC BY 4.0 source: research-only. No API credentials, arbitrary URLs,
retries, redirects, proxies, full downloads, provider body persistence or
insured replacement-cost/CAT model admission. Network requires --live-two.
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

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access" / "nl.cbs.new-housing-permit-2026v06-regional-two.83673ned.json"
ACCESS_ID = "nl.cbs.new-housing-permit-2026v06-regional-two.83673ned"
SOURCE_ID = "nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned"
OPERATION = "get_two_fixed_2026v06_regional_rows"
BASE = "https://opendata.cbs.nl/ODataApi/OData/83673NED/"
PERIOD = "2026VJ06"
REGIONS = ("NL01  ", "LD01  ", "LD02  ", "LD03  ", "LD04  ")
FIELDS = (
    "GemiddeldeBouwkostenPerWoning_1",
    "GemiddeldeBouwkostenPerM_2",  # SOURCE: EUR per cubic metre
    "GemiddeldeBouwkostenPerM_3",  # SOURCE: EUR per square metre
    "GemiddeldeInhoudWoningen_4",
    "GemiddeldeOppervlakteVanWoningen_5",
)
# ID, thousand EUR/dwelling, EUR/m3, EUR/m2, mean m3, mean m2.
NATIVE = {
    "rental": (
        (54, 149, 488, 1473, 306, 101),
        (109, 144, 400, 1223, 361, 118),
        (164, 135, 446, 1356, 304, 100),
        (219, 161, 552, 1647, 291, 97),
        (274, 138, 417, 1280, 332, 108),
    ),
    "owner": (
        (329, 215, 438, 1297, 490, 165),
        (384, 235, 442, 1308, 531, 180),
        (439, 208, 417, 1234, 499, 169),
        (494, 229, 481, 1425, 476, 161),
        (549, 193, 394, 1171, 489, 164),
    ),
}
ORIGINAL = (
    ("rental", BASE + "TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5",
     1457, "2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0"),
    ("owner", BASE + "TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5",
     1459, "67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3"),
)
MAX_BYTES = 8192
TIMEOUT = 25


class CBS2026RegionalBlocked(ValueError):
    """The original source, contract, typed metrics or transport drifted."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CBS2026RegionalBlocked("redirect is not approved for original CBS source")


def _direct_get(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)  # keyword, not HTTP request body


def verify_contract(path: Path = CONTRACT) -> dict[str, Any]:
    c = validate_path(path)
    if (
        c["access_id"] != ACCESS_ID
        or c["source_ids"] != [SOURCE_ID]
        or c["service_root"] != "https://opendata.cbs.nl"
        or c["interface_type"] != "rest"
        or c["status"] != "probe_ready"
        or c["authentication"]["mode"] != "none"
        or c["authentication"]["secret_in_repository"] is not False
        or c["request_contract"]["allowed_operations"] != [OPERATION]
        or c["request_contract"]["path_templates"] != [
            "/ODataApi/OData/83673NED/TypedDataSet"
        ]
        or c["probe_contract"]["mode"] != "provider_specific"
        or c["probe_contract"]["operation"] != OPERATION
        or c["probe_contract"]["requires_credentials"] is not False
        or c["rights_and_policy"]["dataset_rights_status"] != "verified"
        or c["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or c["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or c["operational_constraints"]["retry_policy"] != "none"
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or c["operational_constraints"]["max_sample_bytes"] != MAX_BYTES
    ):
        raise CBS2026RegionalBlocked("source-specific 2026 regional access gate changed")
    return c


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CBS2026RegionalBlocked("duplicate JSON key in source original")
        out[key] = value
    return out


def _nonfinite(_: str):
    raise CBS2026RegionalBlocked("nonfinite CBS OData number")


def _finite_float(x: str) -> float:
    n = float(x)
    if not math.isfinite(n):
        raise CBS2026RegionalBlocked("overlarge nonfinite CBS number")
    return n


def parse_original(raw: bytes) -> list[dict[str, Any]]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise CBS2026RegionalBlocked("original JSON response empty or oversized")
    try:
        obj = json.loads(
            raw.decode("utf-8", "strict"),
            object_pairs_hook=_no_duplicates,
            parse_constant=_nonfinite,
            parse_float=_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as ex:
        raise CBS2026RegionalBlocked("not strict UTF-8 CBS OData JSON") from ex
    if type(obj) is not dict or type(obj.get("value")) is not list:
        raise CBS2026RegionalBlocked("missing CBS OData original value array")
    if any(type(x) is not dict for x in obj["value"]):
        raise CBS2026RegionalBlocked("non-object source native row")
    return obj["value"]


def validate_native(tenure: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if tenure not in NATIVE or len(rows) != 5:
        raise CBS2026RegionalBlocked("expected exactly five original public regional rows")
    native_tenure = {"rental": "A028867", "owner": "A028868"}[tenure]
    checked = []
    for i, (row, region, numbers) in enumerate(zip(rows, REGIONS, NATIVE[tenure])):
        if (
            type(row.get("ID")) is not int or row["ID"] != numbers[0]
            or row.get("RegioS") != region
            or row.get("Perioden") != PERIOD
            or row.get("Eigendom") != native_tenure
        ):
            raise CBS2026RegionalBlocked(f"original row/region/tenure/period drift: {tenure}:{i}")
        for field, expected in zip(FIELDS, numbers[1:]):
            if type(row.get(field)) is not int or row[field] != expected:
                raise CBS2026RegionalBlocked(f"original data value or native unit drift: {tenure}:{i}")
        _, cost_k, eur_per_m3, eur_per_m2, volume, area = numbers
        if (
            abs(cost_k * 1000 - eur_per_m3 * volume) > 3000
            or abs(cost_k * 1000 - eur_per_m2 * area) > 3000
        ):
            raise CBS2026RegionalBlocked("source publication rounding/sanity mismatch")
        checked.append({
            "original_row_ID": numbers[0], "original_region_code": region,
            "original_tenure_code": native_tenure,
            "original_period": PERIOD, "original_period_final": False,
            "published_1000eur_per_permitted_dwelling": cost_k,
            "published_eur_per_m3": eur_per_m3,
            "published_eur_per_m2": eur_per_m2,
            "published_mean_volume_m3": volume,
            "published_mean_area_m2": area,
        })
    return checked


def prove(
    *,
    open_request: Callable[[request.Request, int], Any] = _direct_get,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT,
) -> dict[str, Any]:
    verify_contract(contract_path)
    checked = []
    for tenure, url, expected_bytes, expected_sha in ORIGINAL:
        req = request.Request(
            url,
            method="GET",
            headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        )
        try:
            with open_request(req, TIMEOUT) as response:
                if response.status != 200 or response.geturl() != url:
                    raise CBS2026RegionalBlocked("direct source HTTP 200 exact URL required")
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if content_type != "application/json":
                    raise CBS2026RegionalBlocked("unreviewed CBS response media type")
                if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                    raise CBS2026RegionalBlocked("unexpected compressed source response")
                body = response.read(MAX_BYTES + 1)
        except CBS2026RegionalBlocked:
            raise
        except (error.HTTPError, error.URLError, TimeoutError, OSError) as ex:
            raise CBS2026RegionalBlocked("bounded direct CBS HTTPS source request failed") from ex
        digest = hashlib.sha256(body).hexdigest()
        if len(body) != expected_bytes or digest != expected_sha:
            raise CBS2026RegionalBlocked("CBS original complete-body SHA/size changed; source review required")
        typed = validate_native(tenure, parse_original(body))
        checked.append({
            "operation": tenure,
            "exact_source_url": url,
            "direct_original_http_status": 200,
            "original_complete_body_bytes": len(body),
            "original_complete_body_sha256": digest,
            "public_native_aggregates": typed,
        })
    now = clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise CBS2026RegionalBlocked("original response UTC timestamp absent")
    return {
        "profile": "oc-cbs-83673ned-2026-regional-two-direct-original-v0",
        "source_id": SOURCE_ID,
        "access_id": ACCESS_ID,
        "official_period": PERIOD,
        "period_status_from_independent_nine_originals": "Voorlopig",
        "provider_table_modified_from_independent_nine_originals": "2026-08-20T02:00:00",
        "retrieved_at_utc": now.astimezone(timezone.utc).isoformat(),
        "original_usable_public_response_count": 2,
        "direct_original_response_provenance": checked,
        "source_rights": "CC BY 4.0 (CBS StatLine 83673NED)",
        "response_original_json_persisted": False,
        "trusted_runner_self_attested": False,
        "individual_insured_building_values_retrieved": False,
        "insurance_rebuilding_tiv_approved": False,
        "scientific_cat_model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--live-two", action="store_true", help="explicitly read the two fixed original public CBS 2026 GETs")
    args = parser.parse_args(argv)
    if not args.live_two:
        parser.error("provider network disabled without explicit --live-two")
    try:
        print(json.dumps(prove(), sort_keys=True, ensure_ascii=False))
    except CBS2026RegionalBlocked:
        print("BLOCKED: direct CBS original 2026 regional source evidence failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
