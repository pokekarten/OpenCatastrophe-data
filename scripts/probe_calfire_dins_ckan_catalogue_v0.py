#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One manually dispatched, public CAL FIRE DINS CKAN metadata-only probe.

The canary never follows the eleven provider-returned resource links and
never downloads damage features, locations, addresses, parcels or assets.
No network request happens without --live; any provider/version drift fails closed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib import error, request
from urllib.parse import urlsplit

from scripts.preflight_calfire_dins_ckan_catalogue_v0 import (
    ENDPOINT, MAX_BYTES, CkanMetadataError, inspect_ckan_metadata,
)
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
ACCESS_ID = "us.calfire.dins.ckan-package-catalogue"
CONTRACT_PATH = ROOT / "access" / (ACCESS_ID + ".json")
TIMEOUT = 30
CURRENT_METADATA_MODIFIED = "2026-11-11T01:27:13.459792"
OBSERVED_20261112_RESPONSE_SHA256 = "83b75ccd9fe2ce7b2f2ee95ba3170b6e87554aa943d2e55748fdc01005fbf2ce"
USER_AGENT = "OpenCatastrophe-data/1.0 (one-shot reviewed CAL FIRE CKAN catalogue metadata canary)"


class CkanProbeBlocked(ValueError):
    """No approved original-provider metadata receipt can be produced."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CkanProbeBlocked("redirect blocked")


def verify_reviewed_contract(path: Path = CONTRACT_PATH) -> None:
    c = validate_path(path)
    rights = c["rights_and_policy"]
    u = urlsplit(ENDPOINT)
    if (
        c["access_id"] != ACCESS_ID
        or c["source_ids"] != ["us.calfire.dins.structure-damage"]
        or c["interface_type"] != "rest"
        or c["status"] != "probe_ready"
        or c["service_root"] != "https://publish.data.ca.gov"
        or c["access_scope"] != ["catalogue", "metadata"]
        or c["authentication"]["mode"] != "none"
        or c["request_contract"]["allowed_operations"] != ["dins_package_show_catalogue"]
        or c["request_contract"]["path_templates"] != ["/api/3/action/package_show"]
        or c["probe_contract"]["mode"] != "metadata_get"
        or c["probe_contract"]["operation"] != "dins_package_show_catalogue"
        or c["probe_contract"]["requires_credentials"] is not False
        or rights["dataset_rights_status"] != "verified"
        or rights["api_terms_status"] != "separate_reviewed"
        or rights["commercial_automation_status"] != "allowed"
        or rights["terms_url"] != "https://data.ca.gov/docs/developer-documentation"
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or c["operational_constraints"]["retry_policy"] != "none"
        or u.scheme != "https"
        or u.netloc != "publish.data.ca.gov"
        or u.path != "/api/3/action/package_show"
        or u.query != "id=1fdaea07-4bcd-4795-aa88-cd72b98e8a03"
        or u.fragment or u.username or u.password
    ):
        raise CkanProbeBlocked("CKAN fixed metadata-only contract changed")


def fetch_one_original(opener=None) -> bytes:
    """One exact GET, no caller URL, redirect, retry, auth or asset traversal."""
    if opener is None:
        opener = request.build_opener(NoRedirect, request.ProxyHandler({}))
    req = request.Request(
        ENDPOINT,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise CkanProbeBlocked("CKAN status differs from reviewed 200")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media != "application/json":
                raise CkanProbeBlocked("CKAN content type differs from reviewed JSON")
            declared = response.headers.get("Content-Length")
            if declared is not None:
                if not declared.isdecimal() or not 0 < int(declared) <= MAX_BYTES:
                    raise CkanProbeBlocked("CKAN content-length outside reviewed bound")
            raw = response.read(MAX_BYTES + 1)
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise CkanProbeBlocked("fixed CKAN provider read unavailable") from exc
    if not raw or len(raw) > MAX_BYTES:
        raise CkanProbeBlocked("CKAN response byte bound exceeded")
    return raw


def probe_one(opener=None) -> dict:
    verify_reviewed_contract()
    original = fetch_one_original(opener)
    checked = inspect_ckan_metadata(original, expected_metadata_modified=CURRENT_METADATA_MODIFIED)
    return {
        "schema_version": "CALFIRE_DINS_CKAN_META_CANARY_V1",
        "access_id": ACCESS_ID,
        "request_sha256": hashlib.sha256(("GET " + ENDPOINT).encode("ascii")).hexdigest(),
        "response_sha256": checked["source_response_sha256"],
        "response_bytes": checked["source_response_bytes"],
        "historical_original_sha256_matches": checked["matches_recorded_original_provider_response_sha256"],
        "reviewed_20261112_response_sha256_matches": checked["source_response_sha256"] == OBSERVED_20261112_RESPONSE_SHA256,
        "source_package_modified": checked["dataset_metadata_modified"],
        "source_resource_count": checked["resource_count"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "provider_asset_downloads_performed": 0,
        "external_bytes_persisted": False,
        "individual_damage_features_read": 0,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="opt in to one reviewed public metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: manually opt in with --live", file=sys.stderr)
        return 2
    try:
        receipt = probe_one()
    except (CkanProbeBlocked, CkanMetadataError, OSError, ValueError) as exc:
        # Never echo provider body, API error content, returned resource URLs, contacts or identifiers.
        print("BLOCKED: CKAN metadata identity, access or rights gate", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
