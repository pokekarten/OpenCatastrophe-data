#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed, reviewed U.S. NOAA original -> private Neon cat-raw upload.

This is a quarantined source-byte archive, NOT registry.artifact admission,
scientific QA, a simulated loss or a source-contract revision. The upload
presigned URL must be provided via an ephemeral environment variable and
must never appear in a command line, receipt, log, Git object or exception.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import sys
from typing import Any, Callable
from urllib import request, error, parse

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.probe_ghcnd_ncei_us_station_gzip_v0 import (
    URL as SOURCE_URL, MAX_COMPRESSED, MEDIA, TIMEOUT,
    NCEIStationError, NoRedirect, _open as open_source,
    inflate_validated_gzip_members, validation_view_for_original_csv, verify_contract,
)
from scripts.probe_ghcnd_full_station_original_v0 import inspect_full_csv

PROFILE = "ghcnd-ncei-us-central-park-cat-raw-quarantine-v0"
BUCKET = "cat-raw"
S3_HOST = "br-late-recipe-ba1cr8hc.storage.c-8.eu-central-1.aws.neon.tech"
SOURCE_SHA = "d7b482aea03c3d7cbd61cfffc13413c0383f12198b663e2ea203cc0ea03887b1"
INFLATED_SHA = "95018bf74aea808a70c4495e527e35fcfceaa2eb7cdb4020c532a02b1d1b45c0"
SOURCE_BYTES = 1_820_608
INFLATED_BYTES = 16_272_298
ROWS = 465_584
LAST_DAY = "20261028"
GZIP_MEMBERS = 6
OBJECT_KEY = "research/noaa/ncei/ghcnd/USW00094728/" + SOURCE_SHA + ".csv.gz"
TARGET_PATH = "/" + BUCKET + "/" + OBJECT_KEY
PRESIGNED_ENV = "NEON_CAT_RAW_UPLOAD_URL"


class TransferBlocked(ValueError):
    """No transfer can proceed under the reviewed restrictions."""


@dataclass(frozen=True)
class OriginalIdentity:
    compressed_sha256: str = SOURCE_SHA
    inflated_sha256: str = INFLATED_SHA
    compressed_bytes: int = SOURCE_BYTES
    inflated_bytes: int = INFLATED_BYTES
    rows: int = ROWS
    last_day: str = LAST_DAY
    gzip_members: int = GZIP_MEMBERS


def _check_presigned_target(url: str) -> None:
    """Only the one fixed, private, content-addressed Neon object is permitted."""
    if not isinstance(url, str) or not url or any(x.isspace() for x in url):
        raise TransferBlocked("missing/invalid opaque Neon upload authorization")
    try:
        p = parse.urlsplit(url)
        fields = dict(parse.parse_qsl(p.query, keep_blank_values=True))
        port = p.port
    except ValueError as exc:
        raise TransferBlocked("invalid opaque Neon upload authorization") from exc
    if (
        p.scheme != "https"
        or p.hostname != S3_HOST
        or port not in (None, 443)
        or p.username is not None or p.password is not None
        or p.path != TARGET_PATH
        or p.fragment
        or fields.get("X-Amz-Algorithm") != "AWS4-HMAC-SHA256"
        or not fields.get("X-Amz-Signature")
        or not fields.get("X-Amz-Credential")
        or not fields.get("X-Amz-Date")
        or not fields.get("X-Amz-Expires")
    ):
        raise TransferBlocked("presigned authorization targets an unreviewed storage object")
    # Do not log, print, copy, or return the URL, even on failure.


def _provider_original(
    get: Callable[[request.Request, int], Any] = open_source,
) -> bytes:
    req = request.Request(
        SOURCE_URL, method="GET",
        headers={"Accept": "application/gzip", "Accept-Encoding": "identity"},
    )
    try:
        with get(req, TIMEOUT) as response:
            if response.geturl() != SOURCE_URL or type(response.status) is not int or response.status != 200:
                raise TransferBlocked("provider returned non-original location/status")
            if response.headers.get("Content-Range") is not None:
                raise TransferBlocked("partial source response")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise TransferBlocked("source HTTP encoding alters original bytes")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in MEDIA:
                raise TransferBlocked("unexpected provider original GZIP media type")
            content_length = response.headers.get("Content-Length", "")
            if content_length and (
                not content_length.isdecimal() or int(content_length) > MAX_COMPRESSED
            ):
                raise TransferBlocked("provider declares unreviewed original file size")
            raw = response.read(MAX_COMPRESSED + 1)
            if len(raw) > MAX_COMPRESSED or (content_length and len(raw) != int(content_length)):
                raise TransferBlocked("original bytes truncated or larger than reviewed limit")
            return raw
    except TransferBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise TransferBlocked("fixed NOAA original request failed") from exc


def verify_bytes(original: bytes, expected: OriginalIdentity = OriginalIdentity()) -> dict[str, Any]:
    """Validate pinned original and every observation before an upload request."""
    if len(original) != expected.compressed_bytes:
        raise TransferBlocked("original GZIP length no longer matches reviewed release")
    digest = hashlib.sha256(original).hexdigest()
    if digest != expected.compressed_sha256:
        raise TransferBlocked("original GZIP hash changed; independent review required")
    try:
        csv_original, count = inflate_validated_gzip_members(original)
        view, has_header = validation_view_for_original_csv(csv_original)
        detail = inspect_full_csv(view)
    except (NCEIStationError, ValueError, OSError) as exc:
        raise TransferBlocked("original GHCN gzip or CSV scientific-format gate failed") from exc
    inflated_digest = hashlib.sha256(csv_original).hexdigest()
    if (
        len(csv_original) != expected.inflated_bytes
        or inflated_digest != expected.inflated_sha256
        or count != expected.gzip_members
        or detail["complete_original_rows_checked"] != expected.rows
        or detail["last_observation_day"] != expected.last_day
        or has_header is not False
    ):
        raise TransferBlocked("original station provenance/row/version evidence drift")
    return {
        "original_gzip_sha256": digest,
        "original_gzip_bytes": len(original),
        "original_csv_sha256": inflated_digest,
        "original_csv_bytes": len(csv_original),
        "validated_gzip_members": count,
        "original_rows_checked": detail["complete_original_rows_checked"],
        "last_original_observation": detail["last_observation_day"],
        "original_csv_header_present": has_header,
        "scientific_model_admitted": False,
    }


def _put(req: request.Request, timeout: int) -> Any:
    opener = request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def transfer(
    *,
    authorization: str,
    get: Callable[[request.Request, int], Any] = open_source,
    put: Callable[[request.Request, int], Any] = _put,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    expected: OriginalIdentity = OriginalIdentity(),
) -> dict[str, Any]:
    # Validate target before initiating source network traffic.
    _check_presigned_target(authorization)
    verify_contract()
    raw = _provider_original(get)
    evidence = verify_bytes(raw, expected)
    stamp = clock()
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise TransferBlocked("UTC source receipt requires timezone-aware timestamp")
    upload = request.Request(
        authorization, data=raw, method="PUT",
        headers={"Content-Type": "application/gzip"},
    )
    try:
        with put(upload, TIMEOUT) as response:
            if type(response.status) is not int or response.status not in {200, 201, 204}:
                raise TransferBlocked("private object store rejected upload")
            if response.geturl() != authorization:
                raise TransferBlocked("private object store redirected upload")
            status = response.status
    except TransferBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        # No underlying exception text, which may reveal signed query secrets.
        raise TransferBlocked("private object upload failed; no storage success asserted") from None
    return {
        "profile": PROFILE,
        "source_url": SOURCE_URL,
        "private_bucket": BUCKET,
        "immutable_object_key": OBJECT_KEY,
        "storage_ref": f"neon-private-storage://{BUCKET}/{OBJECT_KEY}",
        "provider_source_contract": "access/noaa.ncei.ghcnd-central-park-gzip.json",
        "recorded_at_utc": stamp.astimezone(timezone.utc).isoformat(),
        "upload_http_status": status,
        "upload_acknowledged": True,
        "independent_download_hash_verified": False,
        **evidence,
        "registry_artifact_row_created": False,
        "neon_source_contract_revision_created": False,
        "raw_observation_model_admitted": False,
        "insured_exposure_derived": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true", help="single fixed-provider GET and signed PUT")
    args = ap.parse_args(argv)
    if not args.live:
        ap.error("No network by default. --live requires ephemeral Neon presigned upload URL.")
    # Read secret only from environment, never CLI arguments or checked-in config.
    authorization = os.environ.get(PRESIGNED_ENV, "")
    try:
        result = transfer(authorization=authorization)
    except (TransferBlocked, NCEIStationError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
