#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed ESA WorldCover 2021 v200 tile HEAD: zero raster bytes downloaded.

Only tests the N48E009 Map object inferred from ESA's 3x3-degree tile naming.
Not an object inventory, source-byte receipt, COG validation or CAT admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import ssl
import sys
from urllib import error, request
from urllib.parse import urlsplit

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "esa.worldcover.2021.v200"
CONTRACT_PATH = ROOT / "access" / (SOURCE + ".json")
OBJECT_PATH = "/v200/2021/map/ESA_WorldCover_10m_2021_v200_N48E009_Map.tif"
SERVICE_ROOT = "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
URL = SERVICE_ROOT + OBJECT_PATH
OPERATION = "probe_exact_v200_tile_head"
MAX_DECLARED_OBJECT_BYTES = 4 * 1024 * 1024 * 1024
EXPECTED_MEDIA = {"image/tiff", "application/octet-stream", "binary/octet-stream"}


class WorldCoverProbeBlocked(ValueError):
    """Fail closed if HEAD or metadata no longer satisfies source-specific review."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise WorldCoverProbeBlocked("redirect is not authorized")


def validate_reviewed_contract(path: Path = CONTRACT_PATH) -> tuple[int, str]:
    contract = validate_path(path)
    parsed = urlsplit(URL)
    if (
        contract["access_id"] != SOURCE
        or contract["source_ids"] != [SOURCE]
        or contract["interface_type"] != "object_store"
        or contract["status"] != "probe_ready"
        or contract["service_root"] != SERVICE_ROOT
        or contract["authentication"]["mode"] != "none"
        or contract["probe_contract"]["mode"] != "head"
        or contract["probe_contract"]["operation"] != OPERATION
        or contract["probe_contract"]["requires_credentials"] is not False
        or OPERATION not in contract["request_contract"]["allowed_operations"]
        or OBJECT_PATH not in contract["request_contract"]["path_templates"]
        or contract["rights_and_policy"]["dataset_rights_status"] != "verified"
        or contract["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or contract["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or contract["response_contract"]["expected_media_types"] !=
           ["image/tiff", "application/octet-stream", "binary/octet-stream"]
        or parsed.scheme != "https" or parsed.netloc != urlsplit(SERVICE_ROOT).netloc
        or parsed.path != OBJECT_PATH or parsed.query or parsed.fragment
    ):
        raise WorldCoverProbeBlocked("exact WorldCover HEAD probe contract drift")
    timeout = contract["operational_constraints"]["timeout_seconds"]
    if type(timeout) is not int or not 0 < timeout <= 60:
        raise WorldCoverProbeBlocked("invalid reviewed request timeout")
    return timeout, hashlib.sha256(path.read_bytes()).hexdigest()


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def probe(*, open_request=_open, contract_path: Path = CONTRACT_PATH) -> dict:
    timeout, contract_sha = validate_reviewed_contract(contract_path)
    req = request.Request(
        URL, method="HEAD",
        headers={"Accept": "image/tiff,application/octet-stream",
                 "User-Agent": "OpenCatastrophe-ESA-WorldCover-HEAD/0.1"},
    )
    try:
        with open_request(req, timeout) as reply:
            if reply.geturl() != URL or reply.status != 200:
                raise WorldCoverProbeBlocked("source returned unexpected URL or HTTP status")
            media = reply.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in EXPECTED_MEDIA:
                safe_media = media if re.fullmatch(r"[a-z0-9.+-]+/[a-z0-9.+-]+", media) else "<invalid>"
                raise WorldCoverProbeBlocked("provider media type not reviewed: " + safe_media)
            value = reply.headers.get("Content-Length", "")
            if not value.isdigit():
                raise WorldCoverProbeBlocked("missing or invalid Content-Length")
            size = int(value)
            if not 0 < size <= MAX_DECLARED_OBJECT_BYTES:
                raise WorldCoverProbeBlocked("unreasonable declared tile object size")
            etag = reply.headers.get("ETag", "")
            if len(etag) > 256:
                raise WorldCoverProbeBlocked("unbounded ETag header")
    except WorldCoverProbeBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise WorldCoverProbeBlocked("exact WorldCover HEAD request unavailable") from exc
    return {
        "profile": "oc-esa-worldcover-v200-tile-head-v0",
        "source_id": SOURCE,
        "operation": OPERATION,
        "tile": "N48E009",
        "product": "ESA WorldCover 2021 v200 Map",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": 200,
        "media_type": media,
        "declared_object_bytes": size,
        "etag_header_sha256": hashlib.sha256(etag.encode("utf-8")).hexdigest() if etag else None,
        "request_sha256": hashlib.sha256(("HEAD " + URL).encode("ascii")).hexdigest(),
        "access_contract_sha256": contract_sha,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_raster_bytes_downloaded": 0,
        "raster_header_inspected": False,
        "cog_structure_validated": False,
        "original_object_sha256_verified": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("requires explicit --live: no network operation by default")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (WorldCoverProbeBlocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
