#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline FULL-archive receipt for exact historical BD TOPO 2016 D077 .7z.

No download, decryption, decompression, source admission or CAT-loss modelling.
Source descriptor is a research inventory, not independent provider checksum proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path
import re
from typing import Any

MAGIC_7Z = bytes.fromhex("377abcaf271c")
MAX_ARCHIVE_BYTES = 500 * 1024 * 1024
BUF = 1024 * 1024


class ArchiveReceiptError(ValueError):
    """Input asset or metadata cannot prove the required research identity."""


def _descriptor(d: dict[str, Any]) -> tuple[str, int]:
    if not isinstance(d, dict):
        raise ArchiveReceiptError("source descriptor must be an object")
    if d.get("research_only") is not True or d.get("model_input_approved") is not False:
        raise ArchiveReceiptError("source descriptor must remain research-only and blocked")
    if d.get("original_sha256") is not None:
        raise ArchiveReceiptError("unverified original provider hash must remain null")
    name, size = d.get("archive_filename"), d.get("mirror_listed_size_bytes")
    if not isinstance(name, str) or not re.fullmatch(
        r"BDTOPO_2-1_TOUSTHEMES_SHP_LAMB93_D077_2016-03-24\.7z", name
    ):
        raise ArchiveReceiptError("wrong historical edition / geography / artifact name")
    if type(size) is not int or not 0 < size <= MAX_ARCHIVE_BYTES:
        raise ArchiveReceiptError("bad listed archive byte size")
    return name, size


def inspect_archive(path: Path, descriptor: dict[str, Any]) -> dict[str, Any]:
    """Check a user-supplied full local archive against the reviewed mirror listing."""
    name, expected_size = _descriptor(descriptor)
    if path.name != name or path.is_symlink() or not path.is_file():
        raise ArchiveReceiptError("not a regular exact-name source file")
    if path.stat().st_size != expected_size:
        raise ArchiveReceiptError("size differs from research listing: possible truncated or newer archive")
    sha = hashlib.sha256()
    md5 = hashlib.md5()  # noqa: S324 - non-security legacy comparison digest
    n = 0
    with path.open("rb") as stream:
        magic = stream.read(len(MAGIC_7Z))
        if magic != MAGIC_7Z:
            raise ArchiveReceiptError("7z file signature is missing or invalid")
        sha.update(magic)
        md5.update(magic)
        n += len(magic)
        while block := stream.read(BUF):
            n += len(block)
            if n > MAX_ARCHIVE_BYTES:
                raise ArchiveReceiptError("archive exceeds bounded receipt limit")
            sha.update(block)
            md5.update(block)
    if n != expected_size:
        raise ArchiveReceiptError("source file changed during read")
    observed_sha256 = sha.hexdigest()
    pinned_mirror_sha256 = descriptor.get("mirror_full_archive_sha256_verified_in_ci")
    if pinned_mirror_sha256 is not None:
        if not isinstance(pinned_mirror_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", pinned_mirror_sha256):
            raise ArchiveReceiptError("invalid pinned full mirror SHA-256")
        if observed_sha256 != pinned_mirror_sha256:
            raise ArchiveReceiptError("full archive SHA-256 differs from pinned mirror receipt")
    return {
        "schema": "fr-bdtopo-d077-2016-mirror-complete-archive-receipt-v0",
        "archive_filename": name,
        "source_release_date": "2016-03-24",
        "department": "D077",
        "compressed_archive_bytes": n,
        "full_archive_sha256_local": observed_sha256,
        "pinned_mirror_sha256_matched": pinned_mirror_sha256 is not None,
        "full_archive_md5_legacy_comparison_only": md5.hexdigest(),
        "mirror_listed_size_matches": True,
        "7z_file_signature_verified": True,
        "original_provider_full_archive_sha256_independently_verified": False,
        "7z_decompression_and_inner_files_verified": False,
        "historical_building_geometry_verified": False,
        "2016_flood_impact_verified": False,
        "insured_replacement_value_verified": False,
        "licence_review_complete": False,
        "model_input_approved": False,
        "research_only": True,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--descriptor", type=Path, required=True)
    args = p.parse_args()
    try:
        d = tomllib.loads(args.descriptor.read_text(encoding="utf-8"))
        result = inspect_archive(args.archive, d)
    except (ArchiveReceiptError, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
