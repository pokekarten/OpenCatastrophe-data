#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One opt-in metadata-only MeteoSwiss Hail Climatology archive STAC Item check.

A fixed FSDI/OGC STAC Item metadata GET; NO asset links followed, no
NetCDF/COG/GeoTIFF bytes fetched, no pagination, no user-controlled URL.
The official FSDI fair-use policy applies. Manual --live opt-in required.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

SOURCE_ID = "meteoswiss.national-hail-climatology"
COLLECTION_ID = "ch.meteoschweiz.ogd-radar-derived-grid"
ITEM_ID = "archive-ch"
URL = (
    "https://data.geo.admin.ch/api/stac/v1/collections/"
    "ch.meteoschweiz.ogd-radar-derived-grid/items/archive-ch"
)
MAX_BYTES = 131072
TIMEOUT = 30
MIME = re.compile(r"^[A-Za-z0-9.+_-]+/[A-Za-z0-9.+_-]+$")
USER_AGENT = "OpenCatastrophe-data/1.0 (manual bounded MeteoSwiss hail climate metadata canary)"


class ArchiveBlocked(ValueError):
    """Source or transport does not match the exact public metadata contract."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ArchiveBlocked("provider redirect blocked")


def _unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ArchiveBlocked("duplicate JSON key")
        out[k] = v
    return out


def _no_nan(value):
    raise ArchiveBlocked("non-finite source JSON")


def check_archive_metadata(raw: bytes) -> dict:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_BYTES):
        raise ArchiveBlocked("original source metadata bytes outside cap")
    try:
        data = json.loads(raw.decode("utf-8"),
                          object_pairs_hook=_unique, parse_constant=_no_nan)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ArchiveBlocked("non-strict original provider JSON") from exc
    if (
        type(data) is not dict
        or data.get("type") != "Feature"
        or data.get("id") != ITEM_ID
        or data.get("collection") != COLLECTION_ID
    ):
        raise ArchiveBlocked("wrong exact MeteoSwiss Hail Climatology archive item")
    assets = data.get("assets")
    if type(assets) is not dict or not (1 <= len(assets) <= 5000):
        raise ArchiveBlocked("archive metadata contains no bounded asset index")
    media = Counter()
    for key, value in assets.items():
        if type(key) is not str or not key or len(key) > 180:
            raise ArchiveBlocked("malformed archive asset identifier")
        if type(value) is not dict or type(value.get("href")) is not str:
            raise ArchiveBlocked("missing archive metadata asset pointer")
        # Returned hrefs are references only; no URL resolution or network follows.
        reported = value.get("type")
        if reported is None:
            media["unspecified"] += 1
        elif type(reported) is str and len(reported) <= 120 and MIME.fullmatch(reported):
            media[reported] += 1
        else:
            raise ArchiveBlocked("unsupported archive media-type metadata")
    return {
        "schema": "meteoswiss-hail-archive-item-metadata-v0",
        "source_id": SOURCE_ID,
        "collection_id": COLLECTION_ID,
        "fixed_item_id": ITEM_ID,
        "response_bytes": len(raw),
        "original_response_sha256": hashlib.sha256(raw).hexdigest(),
        "archive_asset_metadata_count": len(assets),
        "archive_media_type_counts": dict(sorted(media.items())),
        "asset_links_followed": 0,
        "raw_asset_bytes_downloaded": 0,
        "original_metadata_body_persisted": False,
        "model_input_approved": False,
        "commercial_cat_model_admission": False,
    }


def probe(opener=None) -> dict:
    client = opener if opener is not None else build_opener(NoRedirect(), ProxyHandler({}))
    req = Request(
        URL, method="GET",
        headers={"Accept": "application/geo+json", "User-Agent": USER_AGENT},
    )
    try:
        with client.open(req, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise ArchiveBlocked("unexpected metadata HTTP status")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in {"application/geo+json", "application/json"}:
                raise ArchiveBlocked("unexpected metadata media type")
            declared = response.headers.get("Content-Length")
            if declared is not None and (
                not declared.isdecimal() or int(declared) < 1 or int(declared) > MAX_BYTES
            ):
                raise ArchiveBlocked("oversized declared metadata body")
            raw = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ArchiveBlocked("exact provider metadata GET unavailable") from exc
    result = check_archive_metadata(raw)
    result["retrieved_utc"] = datetime.now(timezone.utc).isoformat()
    result["exact_request_sha256"] = hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest()
    result["runner_code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="exactly one manual official archive metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: --live required", file=sys.stderr)
        return 2
    try:
        report = probe()
    except ArchiveBlocked:
        # Never echo third-party URLs, provider error bodies, filenames or attributes.
        print("BLOCKED: fixed MeteoSwiss archive metadata, rights or transport gate", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
