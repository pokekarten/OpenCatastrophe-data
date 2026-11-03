#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Single exact, explicitly opt-in USGS TNM Florida S1M metadata receipt.

This is an S1M product-catalogue probe. No GeoTIFF/source pixels are retrieved
or stored, no building overlay is computed and no CAT model input is admitted.
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
from research_runners.usgs_s1m_tnm_metadata_preflight_v0 import (
    Blocked, PILOT_SOURCE_ID, PILOT_TITLE, PILOT_DOWNLOAD_URL, check_products,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "usgs.3dep.s1m.tnmaccess.json"
SERVICE_ROOT = "https://tnmaccess.nationalmap.gov"
PATH = "/api/v1/products"
QUERY = (
    "datasets=Seamless%201-m%20DEM%20%28S1M%29"
    "&bbox=-81.00,25.95,-80.95,26.00&max=1&offset=0"
)
URL = SERVICE_ROOT + PATH + "?" + QUERY
TIMEOUT = 20
MAX_BYTES = 131072
OPERATION = "probe_single_florida_s1m_product"
PROFILE = "oc-usgs-3dep-s1m-florida-t1-metadata-v0"


class ProbeBlocked(ValueError):
    """Fail closed if the fixed access contract or provider response changes."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ProbeBlocked("duplicate provider JSON field")
        out[key] = value
    return out


def _reject_constant(_value: str) -> None:
    raise ProbeBlocked("non-finite JSON value")


def verify_frozen_contract(contract_path: Path = CONTRACT_PATH) -> dict[str, Any]:
    obj = validate_path(contract_path)
    auth = obj["authentication"]
    rights = obj["rights_and_policy"]
    probe = obj["probe_contract"]
    if (
        obj["access_id"] != "usgs.3dep.s1m.tnmaccess"
        or obj["source_ids"] != ["usgs.3dep.seamless-1m.s1m"]
        or obj["status"] != "probe_ready"
        or obj["interface_type"] != "rest"
        or obj["service_root"] != SERVICE_ROOT
        or obj["request_contract"]["allowed_operations"] != [OPERATION]
        or obj["request_contract"]["path_templates"] != [PATH]
        or QUERY not in obj["request_contract"]["parameter_rules"]
        or auth["mode"] != "none"
        or auth["secret_in_repository"] is not False
        or probe["mode"] != "metadata_get"
        or probe["operation"] != OPERATION
        or probe["requires_credentials"] is not False
        or rights["dataset_rights_status"] != "verified"
        or rights["api_terms_status"] != "separate_reviewed"
        or rights["commercial_automation_status"] != "allowed"
        or obj["implementation_decision"] != "build_adapter_now"
        or obj["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or obj["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or obj["operational_constraints"]["retry_policy"] != "none"
    ):
        raise ProbeBlocked("reviewed exact Florida TNM metadata contract changed")
    return obj


def inspect_original(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ProbeBlocked("empty or oversized TNM original response")
    try:
        response = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProbeBlocked("TNM original response is not strict UTF-8 JSON") from exc
    try:
        result = check_products(response)
    except Blocked as exc:
        raise ProbeBlocked("S1M original response failed strict identity preflight") from exc
    if type(response) is not dict or response.get("total") != 1:
        raise ProbeBlocked("fixed Florida box no longer has exactly one result")
    item = response["items"][0]
    if (
        item.get("datasets") != []
        or item.get("sourceId") != PILOT_SOURCE_ID
        or item.get("title") != PILOT_TITLE
        or item.get("downloadURL") != PILOT_DOWNLOAD_URL
        or result.get("identity_evidence") != "frozen_florida_s1m_record"
    ):
        raise ProbeBlocked("S1M pilot identity or provider shape changed")
    return result


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeBlocked("redirect forbidden for fixed TNM request")


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def probe(
    *,
    open_request: Callable[[request.Request, int], Any] = _open,
    contract_path: Path = CONTRACT_PATH,
    utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    verify_frozen_contract(contract_path)
    req = request.Request(
        URL,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-S1M-T1-Metadata/0.1",
        },
        method="GET",
    )
    try:
        with open_request(req, TIMEOUT) as reply:
            if reply.geturl() != URL or type(reply.status) is not int or reply.status != 200:
                raise ProbeBlocked("TNM response URL or HTTP status differs")
            media = reply.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media != "application/json":
                raise ProbeBlocked("TNM returned unreviewed response media type")
            if reply.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise ProbeBlocked("TNM compressed encoding not reviewed")
            content_length = reply.headers.get("Content-Length")
            if content_length is not None and (
                not content_length.isascii() or not content_length.isdigit()
                or int(content_length) > MAX_BYTES
            ):
                raise ProbeBlocked("TNM response length exceeds permitted bound")
            original = reply.read(MAX_BYTES + 1)
    except ProbeBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise ProbeBlocked("fixed USGS TNM metadata request unavailable") from exc
    model_safe = inspect_original(original)
    now = utc_clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise ProbeBlocked("receipt needs timezone-aware UTC")
    return {
        "status": "metadata_probe_verified",
        "profile": PROFILE,
        "source_access_contract": "access/usgs.3dep.s1m.tnmaccess.json",
        "retrieval_utc": now.astimezone(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "original_response_bytes": len(original),
        "original_response_sha256": hashlib.sha256(original).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "http_status": 200,
        "response_media_type": "application/json",
        "source_id": PILOT_SOURCE_ID,
        "catalogue_identity": model_safe["identity_evidence"],
        "external_bytes_persisted": False,
        "original_geotiff_downloaded": False,
        "insurer_exposure_admitted": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one fixed anonymous metadata GET; no provider files saved")
    options = parser.parse_args(argv)
    if not options.live:
        parser.error("this reviewed T1 metadata request requires explicit --live")
    try:
        print(json.dumps(probe(), sort_keys=True, indent=2, allow_nan=False))
    except (ProbeBlocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
