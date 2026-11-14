#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One manually opted-in original MeteoSwiss hail STAC Collection metadata GET.

No item search, linked asset traversal, NetCDF retrieval, credentials,
user-controlled URLs, retries, sample values or repository-persisted provider
bytes. Successful metadata identity is not CAT model data admission.
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
from urllib.parse import urlsplit

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
ACCESS_ID = "meteoswiss.national-hail-climatology"
CONTRACT_PATH = ROOT / "access" / (ACCESS_ID + ".json")
COLLECTION_ID = "ch.meteoschweiz.ogd-radar-derived-grid"
URL = "https://data.geo.admin.ch/api/stac/v1/collections/" + COLLECTION_ID
PROVIDER = "Federal Office of Meteorology and Climatology MeteoSwiss"
MAX_BYTES = 262_144
TIMEOUT = 30


class HailCollectionBlocked(ValueError):
    """The reviewed STAC metadata scope or provider identity failed closed."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HailCollectionBlocked("STAC redirect outside reviewed route")


def verify_reviewed_contract(path: Path = CONTRACT_PATH) -> None:
    c = validate_path(path)
    p = urlsplit(URL)
    rights = c["rights_and_policy"]
    if (c["access_id"] != ACCESS_ID
            or c["source_ids"] != [ACCESS_ID]
            or c["interface_type"] != "stac"
            or c["status"] != "probe_ready"
            or c["service_root"] != "https://data.geo.admin.ch"
            or c["api_version"] != "STAC 1.0.0"
            or c["access_scope"] != ["metadata"]
            or c["request_contract"]["allowed_operations"] != ["collection_metadata_get"]
            or c["request_contract"]["path_templates"] != ["/api/stac/v1/collections/" + COLLECTION_ID]
            or c["authentication"]["mode"] != "none"
            or c["probe_contract"]["mode"] != "metadata_get"
            or c["probe_contract"]["operation"] != "collection_metadata_get"
            or c["probe_contract"]["requires_credentials"] is not False
            or rights["dataset_rights_status"] != "verified"
            or rights["api_terms_status"] != "separate_reviewed"
            or rights["commercial_automation_status"] != "allowed"
            or rights["terms_url"] != "https://www.geo.admin.ch/en/general-terms-of-use-fsdi"
            or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
            or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
            or c["operational_constraints"]["retry_policy"] != "none"
            or p.scheme != "https" or p.netloc != "data.geo.admin.ch"
            or p.path != "/api/stac/v1/collections/" + COLLECTION_ID
            or p.query or p.fragment or p.username or p.password):
        raise HailCollectionBlocked("MeteoSwiss metadata-only reviewed contract changed")


def _strict_mapping(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise HailCollectionBlocked("duplicate STAC JSON key")
        out[key] = value
    return out


def _reject_nonfinite(text: str) -> None:
    raise HailCollectionBlocked("non-finite STAC JSON value")


def inspect_collection(raw: bytes) -> dict[str, Any]:
    if not raw or len(raw) > MAX_BYTES:
        raise HailCollectionBlocked("STAC response byte limit")
    try:
        item = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_strict_mapping,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HailCollectionBlocked("invalid original STAC Collection JSON") from exc
    if type(item) is not dict:
        raise HailCollectionBlocked("STAC Collection must be one object")
    if (item.get("type") != "Collection"
            or item.get("stac_version") != "1.0.0"
            or item.get("id") != COLLECTION_ID
            or item.get("title") != "Spatial climate analyses - Hail"
            or item.get("license") != "CC-BY"):
        raise HailCollectionBlocked("official STAC collection or license identity drift")
    desc = item.get("description")
    if type(desc) is not str or "hail" not in desc.casefold():
        raise HailCollectionBlocked("official hail climatology description missing")
    providers = item.get("providers")
    if type(providers) is not list or not any(
        type(p) is dict
        and p.get("name") == PROVIDER
        and type(p.get("roles")) is list
        and {"producer", "licensor"}.issubset(set(r for r in p["roles"] if type(r) is str))
        for p in providers
    ):
        raise HailCollectionBlocked("MeteoSwiss producer/licensor identity drift")

    links = item.get("links")
    if type(links) is not list:
        raise HailCollectionBlocked("STAC links missing")
    if sum(type(link) is dict and link.get("rel") == "self"
           and link.get("href") == URL for link in links) != 1:
        raise HailCollectionBlocked("canonical STAC self-link mismatch")

    spatial = item.get("extent")
    if type(spatial) is not dict or type(spatial.get("spatial")) is not dict:
        raise HailCollectionBlocked("STAC Swiss spatial scope missing")
    bboxes = spatial["spatial"].get("bbox")
    if type(bboxes) is not list or len(bboxes) != 1:
        raise HailCollectionBlocked("unexpected Swiss STAC spatial extent")
    bbox = bboxes[0]
    if (type(bbox) is not list or len(bbox) != 4
            or not all(type(v) in {int, float} and math.isfinite(v) for v in bbox)):
        raise HailCollectionBlocked("invalid STAC bbox")
    west, south, east, north = bbox
    if not (5 <= west < east <= 11 and 45 <= south < north <= 49):
        raise HailCollectionBlocked("unexpected Swiss hail-climatology footprint")
    # Never follow returned links: item and asset rights/science require another gate.
    return {
        "collection_id_verified": COLLECTION_ID,
        "stac_version_verified": "1.0.0",
        "source_provider_verified": PROVIDER,
        "collection_license_label": "CC-BY",
        "swiss_spatial_scope_verified": True,
        "hail_climatology_identity_verified": True,
        "stac_item_gets_executed": 0,
        "linked_asset_requests_executed": 0,
        "netcdf_files_downloaded": 0,
    }


def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, open_request: Callable = _open,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict[str, Any]:
    verify_reviewed_contract()
    req = request.Request(URL, method="GET", headers={
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-data/0.1 (+https://github.com/pokekarten/OpenCatastrophe-data)",
    })
    try:
        with open_request(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != URL:
                raise HailCollectionBlocked("STAC HTTP status, redirect or source URL mismatch")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media != "application/json":
                raise HailCollectionBlocked("unreviewed STAC response MIME type")
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise HailCollectionBlocked("compressed provider responses not reviewed")
            stated = response.headers.get("Content-Length")
            if stated is not None:
                if not stated.isascii() or not stated.isdecimal() or int(stated) > MAX_BYTES:
                    raise HailCollectionBlocked("invalid or excessive STAC Content-Length")
            raw = response.read(MAX_BYTES + 1)
            if stated is not None and len(raw) != int(stated):
                raise HailCollectionBlocked("STAC Content-Length mismatch")
    except HailCollectionBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise HailCollectionBlocked("fixed MeteoSwiss Collection request unavailable") from exc

    parsed = inspect_collection(raw)
    now = clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise HailCollectionBlocked("timezone-aware UTC receipt required")
    return {
        "profile": "oc-meteoswiss-hail-stac-collection-metadata-v0",
        "access_id": ACCESS_ID,
        "retrieval_utc": now.astimezone(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "source_access_contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "source_probe_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **parsed,
        "original_provider_body_persisted": False,
        "derived_model_input_approved": False,
        "commercial_bulk_hail_data_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="one reviewed MeteoSwiss STAC Collection metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network disabled by default; explicitly specify --live")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (HailCollectionBlocked, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
