# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed local original-byte receipt for one Zenodo GTSM NetCDF asset.

Read only: never fetches, persists or publishes provider data or model inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
import sys

RECORD_URL = "https://zenodo.org/records/14671593"
SOURCE_NAME = "ds_GTSM-ERA5-E_1950-2024_stats.nc"
SOURCE_BYTES = 9_652_424
SOURCE_MD5 = "0f2b7071c6ec3585768be6cf427e6eab"
CHUNK = 65536
HDF5_MAGIC = b"\x89HDF\r\n\x1a\n"
CDF_MAGIC = (b"CDF\x01", b"CDF\x02", b"CDF\x05")


class GtsmReceiptError(ValueError):
    """Original bytes cannot be matched with the published source identity."""


def _file_receipt(path: Path, *, expected_size: int, expected_md5: str) -> dict[str, object]:
    """Testable pure local verifier; public CLI never accepts overridden pins."""
    if not path.is_file() or path.is_symlink():
        raise GtsmReceiptError("original path is not an ordinary non-symlink file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise GtsmReceiptError("unable to open original file safely") from exc
    with os.fdopen(fd, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size != expected_size:
            raise GtsmReceiptError("original file size differs from pinned publisher asset")
        md5 = hashlib.md5(usedforsecurity=False)
        sha256 = hashlib.sha256()
        prefix = b""
        seen = 0
        while True:
            block = source.read(CHUNK)
            if not block:
                break
            seen += len(block)
            if seen > expected_size:
                raise GtsmReceiptError("original file grew beyond pinned source size")
            if len(prefix) < 8:
                prefix += block[:8 - len(prefix)]
            md5.update(block)
            sha256.update(block)
        after = os.fstat(source.fileno())
        if seen != expected_size or after.st_size != expected_size or before.st_ino != after.st_ino:
            raise GtsmReceiptError("original size/identity changed during read")
    actual_md5 = md5.hexdigest()
    if not hmac.compare_digest(actual_md5, expected_md5):
        raise GtsmReceiptError("original MD5 does not match the publisher's fixed asset")
    if prefix != HDF5_MAGIC and not prefix.startswith(CDF_MAGIC):
        raise GtsmReceiptError("pinned asset lacks a recognized NetCDF/HDF5 file signature")
    return {"byte_length": seen, "publisher_md5_verified": actual_md5,
            "sha256_observed_not_publisher_pinned": sha256.hexdigest(),
            "container_signature": "netcdf4_hdf5" if prefix == HDF5_MAGIC else "netcdf_classic"}


def verify_original(path: Path) -> dict[str, object]:
    receipt = _file_receipt(path, expected_size=SOURCE_BYTES, expected_md5=SOURCE_MD5)
    return {"schema_version": "gtsm-era5-e-original-byte-receipt-v0",
            "source_record": RECORD_URL, "source_filename": SOURCE_NAME,
            "source_version": "Zenodo 14671593 v2 / 1950-2024 statistics",
            "original_byte_evidence": receipt,
            "publisher_sha256_available": False, "netcdf_variables_inspected": False,
            "scientific_fitness_approved": False, "data_rights_approved": False,
            "model_admitted": False, "insurer_exposure_inferred": False,
            "provider_bytes_persisted_by_this_tool": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True,
                        help="already acquired original Zenodo NetCDF (read-only, no network)")
    args = parser.parse_args(argv)
    try:
        receipt = verify_original(args.original)
    except (GtsmReceiptError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
