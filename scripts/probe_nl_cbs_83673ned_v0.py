#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One opt-in original CBS 83673NED public housing-permit cost probe.

Nine EXACT small official OData GETs. No provider network without --live,
no dynamic URLs, no credentials, redirects, retries, feeds, bulk data, source
body persistence, or insurance model admission. PR CI uses synthetic fixtures.
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

SOURCE_ID = "nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned"
ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned.json"
SERVICE_ROOT = "https://opendata.cbs.nl"
BASE = SERVICE_ROOT + "/ODataApi/OData/83673NED/"
OBJECTS = (
    ("table", BASE + "TableInfos?$top=1"),
    ("historic_rental", BASE + "TypedDataSet?$top=1"),
    ("properties", BASE + "DataProperties?$top=10"),
    ("tenures", BASE + "Eigendom?$top=3"),
    ("regions", BASE + "RegioS?$top=5"),
    ("historic_period", BASE + "Perioden?$top=1"),
    ("recent_rental", BASE + "TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27&$top=1"),
    ("recent_period", BASE + "Perioden?$filter=Key%20eq%20%272026VJ06%27&$top=1"),
    ("recent_owner", BASE + "TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27%20and%20RegioS%20eq%20%27NL01%20%20%27&$top=1"),
)
MAX_BYTES = 16_384
TIMEOUT = 30
REVISION = "2026-08-20T02:00:00"
REGIONS = {
    "NL01  ": "Nederland",
    "LD01  ": "Noord-Nederland (LD)",
    "LD02  ": "Oost-Nederland (LD)",
    "LD03  ": "West-Nederland (LD)",
    "LD04  ": "Zuid-Nederland (LD)",
}
TENURES = {"A028867": "Huurwoningen", "A028868": "Koopwoningen"}
PRICE_FIELDS = (
    "GemiddeldeBouwkostenPerWoning_1",
    "GemiddeldeBouwkostenPerM_2",  # NOTE: euro per CUBIC metre (m³), despite suffix
    "GemiddeldeBouwkostenPerM_3",  # NOTE: euro per SQUARE metre (m²), despite suffix
    "GemiddeldeInhoudWoningen_4",
    "GemiddeldeOppervlakteVanWoningen_5",
)
EXPECTED_PROPERTIES = {
    PRICE_FIELDS[0]: ("1 000 euro", "Gemiddelde bouwkosten per woning"),
    PRICE_FIELDS[1]: ("euro", "Gemiddelde bouwkosten per m³"),
    PRICE_FIELDS[2]: ("euro", "Gemiddelde bouwkosten per m²"),
    PRICE_FIELDS[3]: ("m³", "Gemiddelde inhoud woningen"),
    PRICE_FIELDS[4]: ("m²", "Gemiddelde oppervlakte van woningen"),
}


class CBS83673Blocked(ValueError):
    """Provider returned something outside the reviewed fixed request contract."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CBS83673Blocked("CBS source redirect is not in the reviewed contract")


def _direct_open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout)


def verify_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    c = validate_path(path)
    exact_paths = [
        "/ODataApi/OData/83673NED/TableInfos",
        "/ODataApi/OData/83673NED/TypedDataSet",
        "/ODataApi/OData/83673NED/DataProperties",
        "/ODataApi/OData/83673NED/Eigendom",
        "/ODataApi/OData/83673NED/RegioS",
        "/ODataApi/OData/83673NED/Perioden",
    ]
    if (
        c["access_id"] != SOURCE_ID
        or c["source_ids"] != [SOURCE_ID]
        or c["service_root"] != SERVICE_ROOT
        or c["interface_type"] != "rest"
        or c["status"] != "probe_ready"
        or c["authentication"]["mode"] != "none"
        or c["request_contract"]["allowed_operations"] != [
            "original_metadata_small_rows",
            "first_2012_permit_cost_row",
            "rolling_2026_june_rental_owner_exact_rows",
        ]
        or c["request_contract"]["path_templates"] != exact_paths
        or c["probe_contract"]["mode"] != "provider_specific"
        or c["probe_contract"]["operation"] != "nine_fixed_83673ned_odata_rows"
        or c["probe_contract"]["requires_credentials"] is not False
        or c["rights_and_policy"]["dataset_rights_status"] != "verified"
        or c["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or c["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or c["operational_constraints"]["max_sample_bytes"] != MAX_BYTES
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["retry_policy"] != "none"
    ):
        raise CBS83673Blocked("one or more exact 83673NED source-access gates changed")
    return c


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise CBS83673Blocked("duplicate JSON field in original body")
        result[name] = value
    return result


def _reject_nonfinite(value: str):
    raise CBS83673Blocked("non-finite JSON number in original CBS source")


def _finite_float(value: str) -> float:
    num = float(value)
    if not math.isfinite(num):
        raise CBS83673Blocked("overflowing CBS JSON floating-point literal")
    return num


def parse_original(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_BYTES):
        raise CBS83673Blocked("original source byte limit or empty body")
    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
            parse_float=_finite_float,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CBS83673Blocked("original response not strict UTF-8 OData JSON") from exc
    if type(payload) is not dict or type(payload.get("value")) is not list:
        raise CBS83673Blocked("original CBS JSON lacks OData value array")
    return payload


def _one(result: dict[str, Any], which: str) -> dict[str, Any]:
    rows = result["value"]
    if len(rows) != 1 or type(rows[0]) is not dict:
        raise CBS83673Blocked(f"{which} original result cardinality changed")
    return rows[0]


def _native_row(
    obj: dict[str, Any], *, expected_id: int, period: str, tenure: str,
    dwelling_thousand: int, per_m3: int, per_m2: int, cubic_m: int, square_m: int,
) -> dict[str, Any]:
    if (
        type(obj.get("ID")) is not int or obj["ID"] != expected_id
        or obj.get("Perioden") != period
        or obj.get("Eigendom") != tenure
        or obj.get("RegioS") != "NL01  "
    ):
        raise CBS83673Blocked("CBS native row ID/tenure/period/region drift")
    expected = (dwelling_thousand, per_m3, per_m2, cubic_m, square_m)
    for key, num in zip(PRICE_FIELDS, expected):
        if type(obj.get(key)) is not int or obj[key] != num:
            raise CBS83673Blocked(f"unexpected CBS native public numeric field: {key}")
    # Sanity only: source figures are independently rounded aggregate means.
    if (
        abs(1000 * dwelling_thousand - per_m3 * cubic_m) > 2000
        or abs(1000 * dwelling_thousand - per_m2 * square_m) > 2000
    ):
        raise CBS83673Blocked("source dimensional sanity check failed")
    return {
        "row_id": expected_id, "period": period, "region_code_exact": "NL01  ",
        "tenure_code": tenure,
        "average_per_dwelling_eur_thousands": dwelling_thousand,
        "average_eur_per_m3": per_m3,
        "average_eur_per_m2": per_m2,
        "mean_dwelling_volume_m3": cubic_m,
        "mean_dwelling_area_m2": square_m,
    }


def validate_rows(documents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if set(documents) != {name for name, _ in OBJECTS}:
        raise CBS83673Blocked("missing or unreviewed original request body")
    table = _one(documents["table"], "TableInfos")
    if (
        table.get("ID") != 0 or table.get("Identifier") != "83673NED"
        or table.get("Source") != "CBS."
        or table.get("Modified") != REVISION
        or table.get("Frequency") != "Perkwartaal"
        or "Bouwvergunningen; kerncijfers nieuwbouwwoningen" not in table.get("Title", "")
        or "50 duizend euro" not in table.get("Description", "")
        or "exclusief BTW" not in table.get("Description", "")
    ):
        raise CBS83673Blocked("official CBS table/version/permit selection definition changed")

    props = documents["properties"]["value"]
    if len(props) != 8 or any(type(p) is not dict for p in props):
        raise CBS83673Blocked("CBS property definitions changed")
    if [p.get("Key") for p in props] != [
        "Eigendom", "RegioS", "Perioden", *PRICE_FIELDS
    ]:
        raise CBS83673Blocked("CBS native data-property keys/order changed")
    for item in props[3:]:
        unit, title = EXPECTED_PROPERTIES[item["Key"]]
        if item.get("Unit") != unit or item.get("Title") != title:
            raise CBS83673Blocked("CBS output unit/title mismatch (€/m3 vs €/m2)")
    if [p.get("Type") for p in props[:3]] != ["Dimension", "GeoDimension", "TimeDimension"]:
        raise CBS83673Blocked("CBS tenure, region or period dimension changed")

    tenure = documents["tenures"]["value"]
    if len(tenure) != 2 or any(type(t) is not dict for t in tenure):
        raise CBS83673Blocked("CBS tenure codebook changed")
    if {x.get("Key"): x.get("Title") for x in tenure} != TENURES:
        raise CBS83673Blocked("CBS rental/owner native codes changed")

    regions = documents["regions"]["value"]
    if len(regions) != 5 or any(type(r) is not dict for r in regions):
        raise CBS83673Blocked("CBS regional codebook changed")
    if {r.get("Key"): r.get("Title") for r in regions} != REGIONS:
        raise CBS83673Blocked("CBS original region identifiers changed")

    old = _one(documents["historic_period"], "first period")
    if (
        old.get("Key") != "2012VJ12"
        or old.get("Title") != "2012 januari - 2012 december"
        or old.get("Status") != "Definitief"
    ):
        raise CBS83673Blocked("2012 rolling period or definitive status changed")
    recent = _one(documents["recent_period"], "2026 period")
    if (
        recent.get("Key") != "2026VJ06"
        or recent.get("Title") != "2025 juli - 2026 juni"
        or recent.get("Status") != "Voorlopig"
    ):
        raise CBS83673Blocked("2026 rolling period or provisional status changed")

    historic = _native_row(
        _one(documents["historic_rental"], "historic rental"),
        expected_id=0,period="2012VJ12",tenure="A028867",
        dwelling_thousand=95,per_m3=258,per_m2=748,cubic_m=370,square_m=127,
    )
    rental = _native_row(
        _one(documents["recent_rental"], "latest rental"),
        expected_id=54,period="2026VJ06",tenure="A028867",
        dwelling_thousand=149,per_m3=488,per_m2=1473,cubic_m=306,square_m=101,
    )
    owner = _native_row(
        _one(documents["recent_owner"], "latest owner"),
        expected_id=329,period="2026VJ06",tenure="A028868",
        dwelling_thousand=215,per_m3=438,per_m2=1297,cubic_m=490,square_m=165,
    )
    return {
        "source_table": "83673NED", "publisher_revision": REVISION,
        "rolling_period": "2025 Juli–2026 Juni", "recent_status": "provisional",
        "historic_period_definitive": True, "source_values": {
            "national_rental_2012": historic,
            "national_rental_2026": rental,
            "national_owner_2026": owner,
        },
        "regional_data_retrieved": False,
        "individual_dwelling_values_retrieved": False,
        "insured_replacement_values_approved": False,
        "cat_model_input_approved": False,
    }


def probe(
    *,
    open_request: Callable[[request.Request, int], Any] = _direct_open,
    utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    verify_contract(contract_path)
    content: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    for name, url in OBJECTS:
        req = request.Request(
            url, method="GET",
            headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        )
        try:
            with open_request(req, TIMEOUT) as response:
                if response.status != 200 or response.geturl() != url:
                    raise CBS83673Blocked("direct response not exact original source HTTP 200")
                mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if mime != "application/json":
                    raise CBS83673Blocked("unexpected source content type")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise CBS83673Blocked("unreviewed CBS source compression")
                raw = response.read(MAX_BYTES + 1)
        except CBS83673Blocked:
            raise
        except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
            raise CBS83673Blocked("bounded CBS source read failed") from exc
        content[name] = parse_original(raw)
        evidence[name] = {
            "exact_source_url": url, "full_original_body_bytes": len(raw),
            "full_original_body_sha256": hashlib.sha256(raw).hexdigest(),
        }

    validated = validate_rows(content)
    now = utc_clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise CBS83673Blocked("time attestation must be offset-aware")
    return {
        "profile": "oc-cbs-83673ned-nine-bounded-direct-originals-v0",
        "source_id": SOURCE_ID,
        "retrieved_utc": now.astimezone(timezone.utc).isoformat(),
        "contract": "access/nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned.json",
        "verified_exact_direct_response_http": True,
        "trusted_github_runner_attestation": False,
        "original_response_provenance": evidence,
        **validated,
        "source_original_bodies_saved": False,
        "public_original_bodies_committed": False,
        "entire_source_dataset_downloaded": False,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="explicitly request the reviewed nine original CBS GETs")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("source network operation is opt-in only; supply --live")
    try:
        print(json.dumps(probe(), sort_keys=True))
    except CBS83673Blocked:
        print("BLOCKED: CBS 83673NED original-source validation did not pass", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
