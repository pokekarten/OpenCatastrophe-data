# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, bounded original-ZIP receipt for the Luxembourg ACT2023v2 2D GPKG.

Read-only: archive SHA pin, ZIP member safety, full decompression CRC and GPKG
SQLite signature. No provider network, extraction-to-disk, model admission or
claim about the inner GeoPackage's CRS, fields or scientific fitness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

RESOURCE_ID = "d62942ec-0dc8-40e2-9fa4-27841e6e1ac1"
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_EXTRACTED_BYTES = 512 * 1024 * 1024
MAX_MEMBERS = 100
MAX_RATIO = 250
SQLITE_HEADER = b"SQLite format 3\0"
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class ArchivePreflightError(ValueError):
    """Unpinned or unsafe source archive; nothing is admitted."""


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def inspect_original_zip(path: Path, *, expected_sha256: str) -> dict:
    """Verify an externally obtained, predeclared exact ZIP without extraction."""
    path = Path(path)
    if not SHA_RE.fullmatch(expected_sha256):
        raise ArchivePreflightError("expected SHA256 must be predeclared lowercase hex")
    if path.is_symlink() or not path.is_file():
        raise ArchivePreflightError("archive must be a non-symlink regular file")
    size = path.stat().st_size
    if not 0 < size <= MAX_ARCHIVE_BYTES:
        raise ArchivePreflightError("archive exceeds bounded size or is empty")
    digest = _hash_file(path)
    if digest != expected_sha256:
        raise ArchivePreflightError("original ZIP SHA256 mismatches predeclared receipt")
    try:
        with zipfile.ZipFile(path, "r") as source:
            members = source.infolist()
            if not 1 <= len(members) <= MAX_MEMBERS:
                raise ArchivePreflightError("invalid ZIP member count")
            paths = set()
            data = []
            total = 0
            for member in members:
                name = member.filename
                pure = PurePosixPath(name)
                if (not name or name.startswith("/") or "\\" in name or
                    any(part in {".", ".."} for part in name.split("/")) or
                    pure.is_absolute() or "\x00" in name):
                    raise ArchivePreflightError("unsafe member path")
                if name in paths:
                    raise ArchivePreflightError("duplicate ZIP member name")
                paths.add(name)
                if member.flag_bits & 1 or stat.S_ISLNK(member.external_attr >> 16):
                    raise ArchivePreflightError("encrypted or symlink ZIP member")
                if member.is_dir():
                    continue
                if member.file_size <= 0:
                    raise ArchivePreflightError("empty ZIP member")
                if member.compress_size <= 0 or member.file_size > member.compress_size * MAX_RATIO:
                    raise ArchivePreflightError("excessive ZIP compression ratio")
                total += member.file_size
                if total > MAX_EXTRACTED_BYTES:
                    raise ArchivePreflightError("expanded ZIP exceeds bounded size")
                if name.lower().endswith(".gpkg"):
                    data.append(member)
            if len(data) != 1:
                raise ArchivePreflightError("exactly one GeoPackage member required")
            gpkg = data[0]
            file_hash = hashlib.sha256()
            seen = 0
            first = b""
            with source.open(gpkg, "r") as stream:
                while block := stream.read(1024 * 1024):
                    if not first:
                        first = block[:16]
                    file_hash.update(block)
                    seen += len(block)
                    if seen > MAX_EXTRACTED_BYTES:
                        raise ArchivePreflightError("decompressed GeoPackage exceeds bounded size")
            if seen != gpkg.file_size or first != SQLITE_HEADER:
                raise ArchivePreflightError("GeoPackage size/header invalid")
    except (zipfile.BadZipFile, OSError, RuntimeError, EOFError, NotImplementedError) as exc:
        raise ArchivePreflightError("original archive structure or CRC invalid") from exc
    return {
        "profile": "lu-act2023v2-original-gpkg-zip-preflight-v0",
        "scope": "research_only_not_admitted",
        "provider_resource_id": RESOURCE_ID,
        "original_zip_sha256": digest,
        "original_zip_bytes": size,
        "gpkg_sha256": file_hash.hexdigest(),
        "gpkg_uncompressed_bytes": seen,
        "zip_member_count": len(members),
        "zip_crc_verified_for_gpkg": True,
        "gpkg_sqlite_header_verified": True,
        "gpkg_schema_and_crs_verified": False,
        "rights_review_completed": False,
        "model_input_admitted": False,
        "database_or_provider_writes": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    a = parser.parse_args(argv)
    try:
        result = inspect_original_zip(a.archive, expected_sha256=a.expected_sha256)
    except (ArchivePreflightError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
