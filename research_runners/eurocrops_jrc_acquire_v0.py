#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Explicit opt-in acquisition of ONE original JRC EuroCrops GeoParquet file.

Stores the original in a fresh EXTERNAL directory only. No source bytes in Git,
no automatic network action in CI, no data/licence/scientific model admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.request import (
    Request, HTTPRedirectHandler, build_opener,
)

BASE = "https://jeodpp.jrc.ec.europa.eu"
FILE = "de4_2023.parquet"
PATHS = frozenset({
    "/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202/" + FILE,
    "/ftp/public/JRC-OpenData/DRLL/EuroCropsV2/gpqtv202/" + FILE,
})
SOURCE = BASE + "/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202/" + FILE
LIMIT_BYTES = 180 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024
ROOT = Path(__file__).resolve().parents[1]


class Blocked(ValueError):
    """Acquisition fails closed, without changing any pre-existing output."""


def allowed(url: str) -> bool:
    parsed = urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == "jeodpp.jrc.ec.europa.eu"
        and parsed.port is None
        and parsed.username is None
        and parsed.password is None
        and not parsed.query and not parsed.fragment
        and parsed.path in PATHS
    )


class StrictJrcRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl):
            raise Blocked("redirect outside exact original official JRC asset")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def acquire(
    directory: Path, *,
    open_response=None,
    byte_limit: int = LIMIT_BYTES,
) -> dict:
    if byte_limit < 9 or byte_limit > LIMIT_BYTES:
        raise Blocked("invalid bounded original size cap")
    if directory.is_symlink() or not directory.is_dir():
        raise Blocked("destination must already exist and must not be a symlink")
    resolved = directory.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise Blocked("external original bytes must remain OUTSIDE Git checkout")
    output = resolved / FILE
    if output.exists() or output.is_symlink():
        raise Blocked("original output already exists; never overwrite")
    if open_response is None:
        opener = build_opener(StrictJrcRedirect)
        open_response = lambda request: opener.open(request, timeout=30)
    request = Request(
        SOURCE,
        headers={"User-Agent": "OpenCatastrophe-source-research/0.1",
                 "Accept": "application/octet-stream", "Accept-Encoding": "identity"},
        method="GET",
    )
    created = False
    try:
        with open_response(request) as response:
            url = response.geturl()
            if not allowed(url):
                raise Blocked("unexpected final original asset URL")
            if getattr(response, "status", None) != 200:
                raise Blocked("not an HTTP 200 complete original")
            headers = response.headers
            if headers.get("Content-Encoding", "identity").lower() != "identity":
                raise Blocked("encoded original response is not byte-identical")
            claimed_length = headers.get("Content-Length")
            if claimed_length is not None:
                try:
                    number = int(claimed_length)
                except (TypeError, ValueError) as exc:
                    raise Blocked("invalid provider Content-Length") from exc
                if not 9 <= number <= byte_limit:
                    raise Blocked("provider file exceeds bounded size cap")
            else:
                number = None
            digest = hashlib.sha256()
            count = 0
            with output.open("xb") as sink:
                created = True
                while True:
                    chunk = response.read(CHUNK_BYTES)
                    if not chunk:
                        break
                    if not isinstance(chunk, bytes):
                        raise Blocked("source response did not return bytes")
                    count += len(chunk)
                    if count > byte_limit:
                        raise Blocked("download exceeded explicit byte limit")
                    digest.update(chunk)
                    sink.write(chunk)
            if count <= 8 or (number is not None and number != count):
                raise Blocked("original source empty or Content-Length mismatch")
            with output.open("rb") as source:
                if source.read(4) != b"PAR1":
                    raise Blocked("original is not Parquet (header)")
                source.seek(-4, 2)
                if source.read(4) != b"PAR1":
                    raise Blocked("original is not Parquet (footer)")
            return {
                "profile": "eurocrops-jrc-de4-2023-first-seen-original-receipt-v0",
                "original_publisher": "European Commission JRC",
                "requested_url": SOURCE,
                "effective_url": url,
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                "original_name": FILE,
                "original_bytes": count,
                "original_sha256": digest.hexdigest(),
                "provider_etag_unverified": headers.get("ETag"),
                "provider_last_modified_unverified": headers.get("Last-Modified"),
                "publisher_checksum_independently_verified": False,
                "first_seen_hash_is_original_publisher_checksum": False,
                "bytes_committed_to_repository": False,
                "rights_review_status": "NOT_REVIEWED",
                "scientific_review_status": "NOT_REVIEWED",
                "source_admitted": False,
                "cat_model_ready": False,
            }
    except Exception:
        if created:
            output.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="explicitly opt in to the fixed original GET")
    parser.add_argument("--destination-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.live:
        parser.exit(2, "BLOCKED: explicit --live required; no automatic downloads\n")
    try:
        result = acquire(args.destination_dir)
    except (Blocked, OSError, RuntimeError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
