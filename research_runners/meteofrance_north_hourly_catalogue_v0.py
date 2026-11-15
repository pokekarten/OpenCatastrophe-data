# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed-scope, metadata-only Météo-France hourly 2020-2024 department screen.

Fetches one official public catalogue JSON, never station records, and checks
five explicit northern French department resource identities. Access metadata
is not data admission or permission to use measurements for CAT calibration.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import urlsplit
from typing import Any

from research_runners.meteofrance_hourly_gust_v0 import (
    CATALOGUE_URL, MAX_CATALOGUE_BYTES, Blocked, _read_url, sha256
)

DEPARTMENTS = ("02", "59", "62", "76", "80")
PERIOD = "2020-2024"
BASE = "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/"
MAX_RESOURCE_BYTES = 32 * 1024 * 1024
MAX_CATALOGUE_RESOURCES = 2500
REQUIRED_FIELDS = ("id", "title", "url", "filesize")


def _unique_dict(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    d: dict[str, Any] = {}
    for key, value in pairs:
        if key in d:
            raise Blocked("duplicate provider catalogue JSON key")
        d[key] = value
    return d


def _verify_metadata(candidate: dict[str, Any], department: str) -> dict[str, Any]:
    if type(candidate) is not dict or any(key not in candidate for key in REQUIRED_FIELDS):
        raise Blocked("source resource metadata fields missing")
    rid = candidate["id"]
    title = candidate["title"]
    url = candidate["url"]
    size = candidate["filesize"]
    if not isinstance(rid, str) or not re.fullmatch(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}", rid):
        raise Blocked("invalid official resource UUID")
    if title != f"HOR_departement_{department}_periode_{PERIOD}":
        raise Blocked("resource title differs from fixed department/year identity")
    if type(size) is not int or size < 18 or size > MAX_RESOURCE_BYTES:
        raise Blocked("original file declared byte size invalid/out of bound")
    if not isinstance(url, str) or not url.startswith(BASE):
        raise Blocked("resource URL not on frozen official source path")
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname != "meteofrance.s3.sbg.io.cloud.ovh.net"
            or parts.username or parts.password or parts.query or parts.fragment or parts.port):
        raise Blocked("unapproved URL or URL parameters")
    basename = url[len(BASE):]
    if not re.fullmatch(r"H_" + department + r"_[a-z0-9-]+" + PERIOD + r"\.csv\.gz", basename):
        raise Blocked("original file basename/department/period mismatch")
    # A changed naming convention is not automatically a corrupt resource,
    # but cannot be promoted to the existing Paris verified byte identity.
    return {
        "department": department,
        "period": PERIOD,
        "resource_id": rid.lower(),
        "title": title,
        "original_url": url,
        "declared_compressed_bytes": size,
        "original_filename": basename,
        "original_bytes_fetched": False,
        "original_sha256_verified": False,
        "source_admitted": False,
        "commercial_model_calibration_authorized": False,
        "annual_ep_authorized": False,
    }


def audit_catalogue(body: bytes) -> dict[str, Any]:
    if not body or len(body) > MAX_CATALOGUE_BYTES:
        raise Blocked("original catalogue exceeds size cap")
    try:
        root = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_dict)
    except (UnicodeError, ValueError) as exc:
        raise Blocked("invalid original UTF-8 catalogue JSON") from exc
    if type(root) is not dict or type(root.get("resources")) is not list:
        raise Blocked("source catalogue missing resources list")
    rows = root["resources"]
    if len(rows) > MAX_CATALOGUE_RESOURCES:
        raise Blocked("source catalogue has too many resources for bounded screen")
    found: dict[str, list[dict[str, Any]]] = {dep: [] for dep in DEPARTMENTS}
    wanted = {f"HOR_departement_{dep}_periode_{PERIOD}": dep for dep in DEPARTMENTS}
    for resource in rows:
        if type(resource) is not dict:
            raise Blocked("malformed official resource record")
        title = resource.get("title")
        if isinstance(title, str) and title in wanted:
            found[wanted[title]].append(resource)
    result = []
    for dep in DEPARTMENTS:
        matches = found[dep]
        if len(matches) != 1:
            # Do not infer which source is preferred when the official
            # catalogue is missing or has duplicates for a frozen identity.
            raise Blocked(f"department {dep}: expected one period resource, got {len(matches)}")
        result.append(_verify_metadata(matches[0], dep))
    ids = [r["resource_id"] for r in result]
    if len(set(ids)) != len(ids):
        raise Blocked("same provider UUID assigned to multiple departments")
    return {
        "profile": "meteofrance-hourly-north-2020-2024-metadata-v0",
        "catalogue_url": CATALOGUE_URL,
        "catalogue_bytes": len(body),
        "catalogue_sha256": sha256(body),
        "original_asset_count": 0,
        "sources": result,
        "source_admitted": False,
        "annual_ep_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--live-catalogue", action="store_true",
                     help="read one public metadata catalogue, never station files")
    src.add_argument("--catalogue-json", help="offline catalogue JSON for deterministic re-check")
    args = parser.parse_args(argv)
    try:
        if args.live_catalogue:
            source = _read_url(CATALOGUE_URL, MAX_CATALOGUE_BYTES)
        else:
            from pathlib import Path
            path = Path(args.catalogue_json)
            if path.stat().st_size > MAX_CATALOGUE_BYTES:
                raise Blocked("source catalogue too large")
            source = path.read_bytes()
        print(json.dumps(audit_catalogue(source), indent=2, sort_keys=True))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
