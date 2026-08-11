# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire one frozen DWD extreme-wind ZIP ephemerally and emit metadata-only evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

SCHEMA_VERSION = "oc-acquisition-receipt-v1"
DATASET_ID = "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03"
FILENAME = "10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip"
SOURCE_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
    "10_minutes/extreme_wind/historical/" + FILENAME
)
EXPECTED_HOST = "opendata.dwd.de"
MAX_BYTES = 52_428_800
MAX_ARCHIVE_MEMBERS = 32
MAX_UNCOMPRESSED_BYTES = 104_857_600
TIMEOUT_SECONDS = 60
CHUNK_SIZE = 65_536
PRODUCT_MEMBER_PREFIX = "produkt_extrema_wind_"


class AcquisitionError(RuntimeError):
    """Raised when acquisition cannot produce bounded trustworthy evidence."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_source_url(url: str) -> bool:
    """Accept only the exact frozen HTTPS source identity."""
    if url != SOURCE_URL:
        return False
    parsed = urllib.parse.urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == EXPECTED_HOST
        and parsed.username is None
        and parsed.password is None
        and parsed.port in (None, 443)
        and parsed.query == ""
        and parsed.fragment == ""
    )


class FrozenSourceRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects before urllib follows them to any alternate resource."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        resolved = urllib.parse.urljoin(req.full_url, newurl)
        if resolved != SOURCE_URL:
            raise AcquisitionError("provider redirect left the frozen source identity")
        raise AcquisitionError("provider redirect is forbidden for the frozen source identity")


def _open_frozen_source(request: urllib.request.Request, timeout: int):
    opener = urllib.request.build_opener(FrozenSourceRedirectHandler())
    return opener.open(request, timeout=timeout)


def _validate_member_name(name: str) -> None:
    if not name or len(name) > 512 or "\\" in name or "\x00" in name:
        raise AcquisitionError("archive contains an unsafe member name")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise AcquisitionError("archive contains an unsafe member path")


def _validate_zip(path: str) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if not (1 <= len(members) <= MAX_ARCHIVE_MEMBERS):
                raise AcquisitionError("archive member count is outside the bounded policy")
            total_uncompressed = 0
            product_members: list[str] = []
            for member in members:
                _validate_member_name(member.filename)
                mode = (member.external_attr >> 16) & 0o170000
                if mode == stat.S_IFLNK:
                    raise AcquisitionError("archive symlinks are forbidden")
                if member.flag_bits & 0x1:
                    raise AcquisitionError("encrypted archive members are forbidden")
                if member.file_size < 0 or member.compress_size < 0:
                    raise AcquisitionError("archive member sizes are invalid")
                total_uncompressed += member.file_size
                if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                    raise AcquisitionError("archive exceeds uncompressed-size bound")
                base = PurePosixPath(member.filename).name
                if base.startswith(PRODUCT_MEMBER_PREFIX) and base.endswith(".txt"):
                    product_members.append(member.filename)
            if total_uncompressed < 1:
                raise AcquisitionError("archive uncompressed payload is empty")
            if len(product_members) != 1:
                raise AcquisitionError("archive must contain exactly one DWD extreme-wind product text member")
            if archive.testzip() is not None:
                raise AcquisitionError("archive CRC validation failed")
    except (OSError, zipfile.BadZipFile) as exc:
        raise AcquisitionError("downloaded object is not a valid ZIP archive") from exc
    return {
        "archive_member_count": len(members),
        "archive_uncompressed_bytes": total_uncompressed,
        "product_member": product_members[0],
    }


def _header_value(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    value = headers.get(name)
    if value is None:
        return None
    value = str(value).strip()
    return value[:512] if value else None


def acquire(*, opener: Any | None = None, now: Any = utc_now) -> dict[str, Any]:
    """Download only the frozen DWD ZIP, validate it, then return a strict small receipt."""
    if not _safe_source_url(SOURCE_URL):  # defensive constant-integrity check
        raise AcquisitionError("trusted source recipe is invalid")
    requested_at = now()
    open_response = opener or _open_frozen_source
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"Accept": "application/zip", "User-Agent": "OpenCatastrophe-acquisition-receipt-v1"},
        method="GET",
    )
    sha256 = hashlib.sha256()
    byte_count = 0
    final_url: str | None = None
    content_type: str | None = None
    last_modified: str | None = None
    etag: str | None = None

    with tempfile.TemporaryDirectory(prefix="oc-dwd-acquisition-") as tmpdir:
        target = os.path.join(tmpdir, FILENAME)
        try:
            with open_response(request, timeout=TIMEOUT_SECONDS) as response:
                status_code = getattr(response, "status", 200)
                if type(status_code) is not int or status_code != 200:
                    raise AcquisitionError("provider response status is not 200")
                final_url = response.geturl()
                if type(final_url) is not str or not _safe_source_url(final_url):
                    raise AcquisitionError("provider redirected outside the frozen source identity")
                content_length = _header_value(response, "Content-Length")
                if content_length is not None:
                    try:
                        declared = int(content_length)
                    except ValueError as exc:
                        raise AcquisitionError("provider Content-Length is invalid") from exc
                    if declared < 1 or declared > MAX_BYTES:
                        raise AcquisitionError("provider Content-Length exceeds bounded policy")
                content_type = _header_value(response, "Content-Type")
                last_modified = _header_value(response, "Last-Modified")
                etag = _header_value(response, "ETag")
                with open(target, "wb") as output:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        if type(chunk) is not bytes:
                            raise AcquisitionError("provider response yielded non-byte content")
                        byte_count += len(chunk)
                        if byte_count > MAX_BYTES:
                            raise AcquisitionError("download exceeded bounded byte limit")
                        sha256.update(chunk)
                        output.write(chunk)
        except AcquisitionError:
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise AcquisitionError(f"provider download failed: {type(exc).__name__}") from exc

        if byte_count < 1:
            raise AcquisitionError("provider returned an empty object")
        archive_evidence = _validate_zip(target)

    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "source_issue": 162,
        "requested_url": SOURCE_URL,
        "final_url": final_url,
        "filename": FILENAME,
        "retrieved_at": requested_at,
        "byte_count": byte_count,
        "sha256": sha256.hexdigest(),
        "content_type": content_type,
        "last_modified": last_modified,
        "etag": etag,
        **archive_evidence,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    try:
        receipt = acquire()
    except AcquisitionError as exc:
        print(json.dumps({"status": "blocked", "failure": str(exc)}, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
