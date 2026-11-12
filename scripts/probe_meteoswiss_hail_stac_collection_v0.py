#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One rights-gated MeteoSwiss hail climatology STAC Collection metadata GET.

Never follow item/asset links or download NetCDF/POH/MESHS/hazard files.
Public API discovery alone does not authorize scientific CAT-model admission.
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
from urllib import request, error

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
ACCESS_ID = "meteoswiss.national-hail-climatology"
COLLECTION_ID = "ch.meteoschweiz.ogd-radar-derived-grid"
URL = "https://data.geo.admin.ch/api/stac/v1/collections/" + COLLECTION_ID
ITEMS_URL = URL + "/items"
CONTRACT = ROOT / "access" / (ACCESS_ID + ".json")
MAX_BYTES = 262144
TIMEOUT = 30


class HailSTACBlocked(ValueError):
    """Unexpected rights, provider, schema or network conditions."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HailSTACBlocked("unreviewed STAC redirect")


def verify_contract(path: Path = CONTRACT) -> None:
    contract = validate_path(path)
    rights = contract["rights_and_policy"]
    probe = contract["probe_contract"]
    if (
        contract["access_id"] != ACCESS_ID
        or contract["source_ids"] != [ACCESS_ID]
        or contract["interface_type"] != "stac"
        or contract["service_root"] != "https://data.geo.admin.ch"
        or contract["status"] != "probe_ready"
        or contract["implementation_decision"] != "build_later"
        or contract["access_scope"] != ["metadata"]
        or contract["request_contract"]["allowed_operations"] != ["collection_metadata_get"]
        or contract["request_contract"]["path_templates"] != ["/api/stac/v1/collections/" + COLLECTION_ID]
        or contract["authentication"]["mode"] != "none"
        or probe["mode"] != "metadata_get"
        or probe["operation"] != "read_fixed_hail_climate_stac_collection"
        or probe["requires_credentials"] is not False
        or rights["dataset_rights_status"] != "verified"
        or rights["api_terms_status"] != "separate_reviewed"
        or rights["commercial_automation_status"] != "allowed"
        or rights["redistribution_status"] != "allowed"
        or rights["terms_url"] != "https://www.geo.admin.ch/en/general-terms-of-use-fsdi"
        or contract["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or contract["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or contract["operational_constraints"]["retry_policy"] != "none"
    ):
        raise HailSTACBlocked("frozen MeteoSwiss rights or metadata-only contract changed")


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict:
    result: dict[str, Any] = {}
    for key, val in pairs:
        if key in result:
            raise HailSTACBlocked("duplicate original STAC JSON property")
        result[key] = val
    return result


def _reject_constant(_: str):
    raise HailSTACBlocked("non-finite original STAC JSON number")


def inspect_collection(raw: bytes) -> dict:
    if not raw or len(raw) > MAX_BYTES:
        raise HailSTACBlocked("original collection JSON exceeds reviewed byte bound")
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_keys, parse_constant=_reject_constant)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HailSTACBlocked("original collection is not valid strict UTF-8 JSON") from exc
    if type(payload) is not dict:
        raise HailSTACBlocked("original STAC Collection is not an object")
    if (
        payload.get("type") != "Collection"
        or payload.get("stac_version") != "1.0.0"
        or payload.get("id") != COLLECTION_ID
        or payload.get("title") != "Spatial climate analyses - Hail"
        or payload.get("license") != "CC-BY"
    ):
        raise HailSTACBlocked("hail collection identity, STAC version or licence changed")

    providers = payload.get("providers")
    if type(providers) is not list or not any(
        type(p) is dict
        and p.get("name") == "Federal Office of Meteorology and Climatology MeteoSwiss"
        and type(p.get("roles")) is list
        and "producer" in p["roles"]
        and "licensor" in p["roles"]
        for p in providers
    ):
        raise HailSTACBlocked("MeteoSwiss origin/licensor identity changed")
    links = payload.get("links")
    if type(links) is not list:
        raise HailSTACBlocked("missing original STAC links")
    for rel, expected in (("self", URL), ("items", ITEMS_URL)):
        found = [x for x in links if type(x) is dict and x.get("rel") == rel]
        if len(found) != 1 or found[0].get("href") != expected:
            raise HailSTACBlocked("original STAC self/items identity drift")

    extent = payload.get("extent")
    if type(extent) is not dict:
        raise HailSTACBlocked("missing spatial and temporal metadata")
    spatial = extent.get("spatial")
    temporal = extent.get("temporal")
    if (type(spatial) is not dict or type(temporal) is not dict
            or type(spatial.get("bbox")) is not list
            or not spatial["bbox"]
            or type(spatial["bbox"][0]) is not list
            or len(spatial["bbox"][0]) != 4
            or type(temporal.get("interval")) is not list):
        raise HailSTACBlocked("malformed spatial or temporal extent")
    bbox = spatial["bbox"][0]
    if (any(type(x) not in (float, int) or isinstance(x, bool) for x in bbox)
            or not (5 <= bbox[0] <= 7 and 45 <= bbox[1] <= 47
                    and 9 <= bbox[2] <= 11 and 47 <= bbox[3] <= 49)
            or not all(bbox[j] < bbox[j + 2] for j in (0, 1))):
        raise HailSTACBlocked("hail collection coverage outside reviewed Swiss extent")
    if payload.get("assets") != {}:
        raise HailSTACBlocked("unreviewed collection-level asset expansion")
    # Only the fixed collection's schema/rights; provider asset URLs are not visited.
    return {
        "stac_version_verified": "1.0.0",
        "collection_id_verified": COLLECTION_ID,
        "provider_identity_verified": True,
        "collection_licence_verified": "CC-BY",
        "spatial_extent_schema_checked": True,
        "temporal_extent_present": bool(temporal["interval"]),
        "stac_item_requests": 0,
        "netcdf_assets_downloaded": 0,
    }


def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, open_request: Callable = _open,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    verify_contract()
    req = request.Request(
        URL, method="GET", headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-MeteoSwiss-Hail-STAC-Metadata/0.1",
        },
    )
    try:
        with open_request(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != URL:
                raise HailSTACBlocked("provider status or final request URL changed")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media != "application/json":
                raise HailSTACBlocked("unreviewed STAC media type")
            if resp.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise HailSTACBlocked("unreviewed content encoding")
            declared = resp.headers.get("Content-Length")
            if declared is not None and (
                not declared.isascii() or not declared.isdecimal()
                or int(declared) > MAX_BYTES
            ):
                raise HailSTACBlocked("original response Content-Length outside cap")
            raw = resp.read(MAX_BYTES + 1)
            if declared is not None and len(raw) != int(declared):
                raise HailSTACBlocked("original response Content-Length mismatch")
    except HailSTACBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise HailSTACBlocked("fixed original MeteoSwiss STAC metadata GET unavailable") from exc

    verified = inspect_collection(raw)
    stamp = clock()
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise HailSTACBlocked("UTC-aware receipt clock required")
    return {
        "profile": "oc-meteoswiss-hail-climate-stac-one-collection-v0",
        "source_access_contract": "access/" + ACCESS_ID + ".json",
        "retrieval_utc": stamp.astimezone(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "original_response_bytes": len(raw),
        "probe_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        **verified,
        "original_provider_bytes_persisted": False,
        "hurricane_or_hail_event_catalogue_inferred": False,
        "cat_model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="opt into one reviewed STAC collection metadata request")
    opts = parser.parse_args(argv)
    if not opts.live:
        parser.error("network is disabled by default; use --live for the fixed original metadata request")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (HailSTACBlocked, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
