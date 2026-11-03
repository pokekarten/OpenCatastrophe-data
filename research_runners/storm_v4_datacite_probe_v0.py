#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One exact, opt-in, anonymous DataCite STORM v4 DOI metadata probe.

Only a fixed public DOI metadata JSON response may be read. Provider bytes
are hashed in memory and discarded. No 4TU track file or response body is
written, admitted, downloaded or uploaded to the repository or CAT database.
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

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_source_access import SourceAccessError, validate_path
from research_runners.storm_v4_datacite_preflight_v0 import (
    Blocked, MAX_BYTES, inspect_metadata,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "storm.ibtracs.present-climate.v4.datacite.json"
URL = "https://api.datacite.org/dois/10.4121/12706085.v4"
TIMEOUT = 20
MEDIA_TYPES = frozenset({"application/json", "application/vnd.api+json"})
PROFILE = "storm-v4-datacite-singleton-metadata-t1-v0"


class ProbeBlocked(ValueError):
    """Unreviewed execution or unexpected metadata/transport state."""


def verify_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        c = validate_path(path)
    except (SourceAccessError, OSError) as exc:
        raise ProbeBlocked("invalid approved STORM metadata contract") from exc
    if (
        c["access_id"] != "storm.ibtracs.present-climate.v4.datacite"
        or c["source_ids"] != ["storm.ibtracs.present-climate.v4"]
        or c["service_root"] != "https://api.datacite.org"
        or c["status"] != "probe_ready"
        or c["interface_type"] != "rest"
        or c["authentication"]["mode"] != "none"
        or c["request_contract"]["allowed_operations"] != ["retrieve_fixed_v4_doi_metadata"]
        or c["request_contract"]["path_templates"] != ["/dois/10.4121/12706085.v4"]
        or c["probe_contract"]["mode"] != "metadata_get"
        or c["probe_contract"]["operation"] != "retrieve_fixed_v4_doi_metadata"
        or c["probe_contract"]["requires_credentials"] is not False
        or c["rights_and_policy"]["dataset_rights_status"] != "verified"
        or c["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or c["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or c["operational_constraints"]["retry_policy"] != "none"
        or set(c["response_contract"]["expected_media_types"]) != MEDIA_TYPES
    ):
        raise ProbeBlocked("STORM contract drift: metadata probe disabled")
    return c


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeBlocked("redirected DataCite metadata request not permitted")


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
    utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    verify_contract(contract_path)
    req = request.Request(URL, headers={"Accept": "application/json"}, method="GET")
    try:
        with open_request(req, TIMEOUT) as resp:
            if resp.geturl() != URL or type(resp.status) is not int or resp.status != 200:
                raise ProbeBlocked("wrong DOI response URL/status")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in MEDIA_TYPES:
                raise ProbeBlocked("unexpected DOI metadata media type")
            raw = resp.read(MAX_BYTES + 1)
    except ProbeBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise ProbeBlocked("fixed public DataCite DOI request failed") from exc
    # A hash of the received bytes is a response receipt, not an independently
    # published original-track-file checksum.
    digest = hashlib.sha256(raw).hexdigest()
    try:
        checked = inspect_metadata(raw, digest)
    except Blocked as exc:
        raise ProbeBlocked("DOI source metadata identity or licence drift") from exc
    at = utc_clock()
    if at.tzinfo is None or at.utcoffset() is None:
        raise ProbeBlocked("receipt time must be timezone-aware")
    return {
        "profile": PROFILE,
        "source_id": "storm.ibtracs.present-climate.v4",
        "access_contract": "access/storm.ibtracs.present-climate.v4.datacite.json",
        "request_url": URL,
        "retrieved_at_utc": at.astimezone(timezone.utc).isoformat(),
        "response_media_type": media,
        "response_bytes": len(raw),
        "response_sha256": digest,
        "metadata_identity_checked": checked["data_cite_dataset_identity_verified"],
        "datacite_cc0_claim_observed": checked["datacite_cc0_claim_observed"],
        "provider_body_persisted": False,
        "provider_track_file_downloaded": False,
        "original_track_bytes_verified": False,
        "model_input_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-once", action="store_true",
                        help="explicit opt-in for one reviewed public DOI metadata GET")
    args = parser.parse_args()
    if not args.probe_once:
        parser.error("live probe requires explicit --probe-once")
    try:
        receipt = probe()
    except ProbeBlocked as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
