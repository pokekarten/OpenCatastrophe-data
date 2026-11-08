# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Opt-in acquisition of original Zenodo hail330 v2 metadata, never HDF5.

Downloads only the fixed metadata.csv to an unused external file path after
checking the publisher's exact MD5 and the existing 56-row CSV contract.
There is no remote access on import or in offline CI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from zenodo_hail330_metadata_preflight_v0 import (
    MAX_METADATA_BYTES,
    HailMetadataError,
    audit_metadata_bytes,
)

SOURCE_URL = "https://zenodo.org/records/17860440/files/metadata.csv?download=1"
REPO_ROOT = Path(__file__).resolve().parents[1]


class AcquisitionError(ValueError):
    """Unsafe location, remote response or source identity."""


def _check_url(url: str) -> None:
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname != "zenodo.org" or
            parts.port not in (None, 443) or parts.username or parts.password or
            parts.fragment):
        raise AcquisitionError("nonallowlisted URL/redirect")


class _RestrictedRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_bytes() -> bytes:
    """Bounded HTTPS GET. The caller verifies the original file digest."""
    _check_url(SOURCE_URL)
    request = Request(SOURCE_URL, headers={"User-Agent": "OpenCatastrophe-source-preflight/0.1"})
    opener = build_opener(_RestrictedRedirects())
    with opener.open(request, timeout=25) as response:
        _check_url(response.geturl())
        declared = response.headers.get("Content-Length")
        if declared is not None:
            try:
                length = int(declared)
            except ValueError as exc:
                raise AcquisitionError("invalid Content-Length") from exc
            if length < 1 or length > MAX_METADATA_BYTES:
                raise AcquisitionError("Content-Length outside metadata budget")
        data = response.read(MAX_METADATA_BYTES + 1)
    if not data or len(data) > MAX_METADATA_BYTES:
        raise AcquisitionError("empty or oversized metadata response")
    return data


def write_verified_external(destination: Path, data: bytes) -> dict[str, object]:
    """Refuse existing/symlink and in-repository paths; verify before creating."""
    try:
        report = audit_metadata_bytes(data)
    except HailMetadataError as exc:
        raise AcquisitionError(f"source integrity / schema blocked: {exc}") from exc
    if not destination.is_absolute() or not destination.parent.is_dir():
        raise AcquisitionError("destination must be absolute in an existing directory")
    parent = destination.parent.resolve(strict=True)
    target = parent / destination.name
    if parent == REPO_ROOT or REPO_ROOT in parent.parents:
        raise AcquisitionError("original publisher bytes must remain outside Git checkout")
    if target.exists() or target.is_symlink():
        raise AcquisitionError("destination must be an unused, non-symlink path")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(target, flags, 0o600)
    except OSError as exc:
        raise AcquisitionError(f"cannot create external original metadata: {exc}") from exc
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return {**report, "output_path": str(target), "acquired_from": SOURCE_URL}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="unused ABSOLUTE path outside Git checkout")
    args = parser.parse_args(argv)
    try:
        if not args.out.is_absolute() or not args.out.parent.is_dir() or args.out.exists() or args.out.is_symlink():
            raise AcquisitionError("--out must be a new absolute external file path")
        parent = args.out.parent.resolve(strict=True)
        if parent == REPO_ROOT or REPO_ROOT in parent.parents:
            raise AcquisitionError("--out must be outside Git checkout")
        report = write_verified_external(args.out, _download_bytes())
    except (AcquisitionError, OSError, ValueError) as exc:
        print(f"NOT_ADMITTED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
