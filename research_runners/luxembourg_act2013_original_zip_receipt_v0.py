#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, offline original ACT Luxembourg 2013 national LoD1 ZIP receipt.

The source is the 2019 publication of the 2013 BD-TOPO-L photogrammetric
CityGML building product. This validates the official published SHA1,
records SHA256, checks archive path integrity and stream-decompresses every
regular member through its ZIP CRC. It does NOT read/parse CityGML polygons,
assert an ACT2013/EUBUCCO crosswalk, or approve any model input.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

ORIGINAL_URL = (
    "https://download.data.public.lu/resources/"
    "batiments-3d-lod-1-level-of-detail-1-1/"
    "20190528-082153/lod1-par-pays.zip"
)
PROVIDER_RESOURCE_ID = "c54d412a-23f9-4ee8-bfbe-002f7e6d3213"
PROVIDER_SHA1 = "83b9b4b3ff4f4f145ecd1322cfd7fd4ad9688652"
MAX_ZIP_BYTES = 45 * 1024 * 1024
MAX_EXPANDED_BYTES = 1200 * 1024 * 1024
MAX_MEMBER_BYTES = 1200 * 1024 * 1024
MAX_MEMBERS = 10000
MAX_EXPANSION_RATIO = 2000
HEX_SHA1 = re.compile(r"[a-f0-9]{40}\Z")


class ACT2013SourceError(ValueError):
    """Original country-level source receipt is unsafe or not provider-pinned."""


def _fingerprints(path: Path) -> tuple[str, str]:
    sha1, sha256 = hashlib.sha1(), hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha1.update(block)
            sha256.update(block)
    return sha1.hexdigest(), sha256.hexdigest()


def verify_original(path: Path, *, expected_provider_sha1: str = PROVIDER_SHA1) -> dict:
    path = Path(path)
    if not HEX_SHA1.fullmatch(expected_provider_sha1):
        raise ACT2013SourceError("Original provider SHA1 pin is malformed")
    if not path.is_file() or path.is_symlink():
        raise ACT2013SourceError("Requires a regular non-symlink original ZIP file")
    size = path.stat().st_size
    if not 0 < size <= MAX_ZIP_BYTES:
        raise ACT2013SourceError("Original ZIP outside bounded byte limit")
    digest_sha1, digest_sha256 = _fingerprints(path)
    if digest_sha1 != expected_provider_sha1:
        raise ACT2013SourceError("Original ZIP does not match the publisher SHA1")
    try:
        with zipfile.ZipFile(path) as original:
            members = original.infolist()
            if not 1 <= len(members) <= MAX_MEMBERS:
                raise ACT2013SourceError("Unsafe archive member count")
            seen: set[str] = set()
            types: Counter[str] = Counter()
            total_expanded = 0
            regular_count = 0
            for info in members:
                name = info.filename
                parts = name.rstrip("/").split("/")
                mode = (info.external_attr >> 16) & 0o170000
                if (not name or name.startswith("/") or "\\" in name or ":" in name
                    or any(part in ("", ".", "..") for part in parts)
                    or "\x00" in name or name in seen
                    or mode == stat.S_IFLNK or info.flag_bits & 1):
                    raise ACT2013SourceError("Unsafe or repeated ZIP member")
                seen.add(name)
                if info.is_dir():
                    continue
                if (info.file_size <= 0 or info.file_size > MAX_MEMBER_BYTES
                    or info.compress_size <= 0
                    or info.file_size > MAX_EXPANSION_RATIO * info.compress_size):
                    raise ACT2013SourceError("Invalid member size or decompression ratio")
                total_expanded += info.file_size
                if total_expanded > MAX_EXPANDED_BYTES:
                    raise ACT2013SourceError("Archive exceeds bounded expanded byte count")
                regular_count += 1
                suffix = Path(name).suffix.lower().lstrip(".") or "no_extension"
                types[suffix] += 1
                actual = 0
                with original.open(info, "r") as stream:
                    while data := stream.read(1024 * 1024):
                        actual += len(data)
                        if actual > info.file_size:
                            raise ACT2013SourceError("Decompression expanded beyond declared member size")
                if actual != info.file_size:
                    raise ACT2013SourceError("Archive member uncompressed size mismatch")
            if not regular_count:
                raise ACT2013SourceError("No nonempty original archive files")
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, EOFError, NotImplementedError) as exc:
        raise ACT2013SourceError("Unsafe ZIP structure, decompression failure or bad member CRC") from exc
    return {
        "profile": "luxembourg-act2013-official-lod1-archive-receipt-v0",
        "provider_resource_id": PROVIDER_RESOURCE_ID,
        "publisher_provided_sha1_verified": True,
        "publisher_sha1": digest_sha1,
        "original_zip_sha256": digest_sha256,
        "original_zip_bytes": size,
        "archive_regular_members": regular_count,
        "archive_total_members": len(members),
        "original_expanded_bytes": total_expanded,
        "member_extensions": dict(sorted(types.items())),
        "all_regular_member_crc_checks_passed": True,
        "original_citygml_feature_ids_read": False,
        "original_polygon_coordinate_order_verified": False,
        "eubucco_act2013_record_crosswalk_verified": False,
        "source_license_and_scientific_admission_approved": False,
        "model_input_admitted": False,
        "source_bytes_persisted_by_script": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_original(args.source_zip)
    except (ACT2013SourceError, OSError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
