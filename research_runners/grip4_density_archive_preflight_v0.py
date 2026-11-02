#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed receipt for an independently obtained GRIP4 density ZIP.

Only the exact Zenodo 6420961 GRIP4_density_total.zip artifact is in scope.
This program makes no network requests, extracts no external bytes, and NEVER
approves data rights, public redistribution or CAT model use. The published
MD5 is a legacy provider checksum; a separately pinned SHA-256 is mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

SOURCE_NAME = "GRIP4_density_total.zip"
ZENODO_RECORD = "https://zenodo.org/records/6420961"
PUBLISHED_MD5 = "24d3ed5c079f7a898fbc4a5d68be337a"
MAX_ARCHIVE_BYTES = 10 * 1024 * 1024
MAX_MEMBER_BYTES = 300 * 1024 * 1024
MAX_EXPANDED_BYTES = 350 * 1024 * 1024
MAX_MEMBERS = 30
MAX_COMPRESSION_RATIO = 500
SHA256_PATTERN = re.compile(r"[a-f0-9]{64}\Z")
EXPECTED_MEMBERS = frozenset({
    "GRIP4_density_m_km2.lyr",
    "ReadMe.txt",
    "grip4_area_land_km2.asc",
    "grip4_total_dens_m_km2.asc",
})
EXPECTED_RASTERS = frozenset({
    "grip4_area_land_km2.asc",
    "grip4_total_dens_m_km2.asc",
})
ROOT = Path(__file__).resolve().parents[1]


class Grip4PreflightError(ValueError):
    """Source identity, ZIP metadata, or declared validation boundaries failed."""


def read_archive_bounded(path: Path) -> bytes:
    """Read at most MAX_ARCHIVE_BYTES+1 without following source symlinks."""
    if path.resolve().is_relative_to(ROOT):
        raise Grip4PreflightError("source archives must remain outside Git checkout")
    if not hasattr(os, "O_NOFOLLOW"):
        raise Grip4PreflightError("platform lacks safe no-follow source opening")
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_BINARY", 0)
        with os.fdopen(os.open(path, flags), "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise Grip4PreflightError("source archive must be regular file")
            if not 0 < info.st_size <= MAX_ARCHIVE_BYTES:
                raise Grip4PreflightError("source archive exceeds 10 MiB byte limit")
            data = handle.read(MAX_ARCHIVE_BYTES + 1)
            if len(data) != info.st_size:
                raise Grip4PreflightError("source size changed during read")
            return data
    except OSError as exc:
        raise Grip4PreflightError("source could not be opened safely") from exc


def write_receipt_exclusive(path: Path, result: dict) -> None:
    """Create private receipt outside Git without following or overwriting files."""
    if path.suffix != ".json" or path.resolve().is_relative_to(ROOT):
        raise Grip4PreflightError("JSON receipt must remain outside Git checkout")
    if not hasattr(os, "O_NOFOLLOW"):
        raise Grip4PreflightError("platform lacks safe no-follow receipt creation")
    blob = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_BINARY", 0)
        with os.fdopen(os.open(path, flags, 0o600), "wb") as handle:
            handle.write(blob)
    except OSError as exc:
        raise Grip4PreflightError("receipt already exists or cannot be created safely") from exc



def inspect_zip(data: bytes, *, expected_sha256: str,
                expected_published_md5: str = PUBLISHED_MD5) -> dict:
    """Inspect metadata without extracting any archive members."""
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_ARCHIVE_BYTES:
        raise Grip4PreflightError("GRIP4 original ZIP must be nonempty and <= 10 MiB")
    if not SHA256_PATTERN.fullmatch(expected_sha256):
        raise Grip4PreflightError("expected SHA-256 must be a pinned lowercase hex digest")
    sha = hashlib.sha256(data).hexdigest()
    if sha != expected_sha256:
        raise Grip4PreflightError("original ZIP SHA-256 differs from pinned digest")
    md5 = hashlib.md5(data, usedforsecurity=False).hexdigest()
    if md5 != expected_published_md5:
        raise Grip4PreflightError("original ZIP MD5 differs from the published Zenodo checksum")
    from io import BytesIO
    try:
        with zipfile.ZipFile(BytesIO(data), "r", allowZip64=True) as archive:
            members = archive.infolist()
            if not 0 < len(members) <= MAX_MEMBERS:
                raise Grip4PreflightError("unexpected ZIP entry count")
            names: set[str] = set()
            total = 0
            raster_count = 0
            for item in members:
                name = item.filename
                path = PurePosixPath(name)
                if (not name or "\\" in name or "\x00" in name
                    or path.is_absolute() or any(part in {"..", "."} for part in name.split("/"))
                    or ":" in name or name.startswith("//")):
                    raise Grip4PreflightError("ZIP member has unsafe path")
                if name.casefold() in names:
                    raise Grip4PreflightError("ZIP contains duplicate member name")
                names.add(name.casefold())
                if item.flag_bits & 1:
                    raise Grip4PreflightError("encrypted ZIP member is unsupported")
                mode = (item.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    raise Grip4PreflightError("ZIP symlinks are prohibited")
                if not item.is_dir():
                    if item.file_size > MAX_MEMBER_BYTES:
                        raise Grip4PreflightError("ZIP member declares excessive expanded bytes")
                    if item.file_size and not item.compress_size:
                        raise Grip4PreflightError("ZIP member has impossible size metadata")
                    if item.compress_size and item.file_size / item.compress_size > MAX_COMPRESSION_RATIO:
                        raise Grip4PreflightError("ZIP member expansion ratio exceeds cap")
                    if name in EXPECTED_RASTERS:
                        raster_count += 1
                total += item.file_size
                if total > MAX_EXPANDED_BYTES:
                    raise Grip4PreflightError("ZIP total expanded-size cap exceeded")
            if names != {name.casefold() for name in EXPECTED_MEMBERS}:
                raise Grip4PreflightError("ZIP members differ from the publisher archive preview")
            if raster_count != len(EXPECTED_RASTERS):
                raise Grip4PreflightError("missing required original GRIP4 density rasters")
    except (zipfile.BadZipFile, EOFError) as exc:
        raise Grip4PreflightError("GRIP4 file is not a well-formed ZIP") from exc
    return {
        "source_candidate_id": "pbl.grip4.global-roads",
        "publisher_record": ZENODO_RECORD,
        "original_artifact_filename": SOURCE_NAME,
        "zip_bytes": len(data),
        "zip_sha256": sha,
        "zenodo_published_md5": expected_published_md5,
        "published_md5_matched": True,
        "zip_member_count": len(members),
        "raster_member_count": raster_count,
        "raster_units_claimed_not_validated": "road metres per square kilometre (m/km2)",
        "raster_values_or_georeferencing_validated": False,
        "declared_total_uncompressed_bytes": total,
        "member_names": sorted(info.filename for info in members),
        "zip_member_payloads_decompressed_or_parsed": False,
        "upstream_lineage_verified": False,
        "license_rights_cleared": False,
        "commercial_automation_authorized": False,
        "model_source_admission_approved": False,
        "scientific_fitness_approved": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--expected-sha256", required=True,
                    help="Independently pinned SHA256 of the exact Zenodo original bytes")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.archive.name != SOURCE_NAME:
        raise Grip4PreflightError("unexpected GRIP4 filename; only the exact density_total ZIP is in scope")
    if args.archive.resolve() == args.out.resolve():
        raise Grip4PreflightError("refusing to overwrite original archive")
    original_bytes = read_archive_bounded(args.archive)
    result = inspect_zip(original_bytes, expected_sha256=args.expected_sha256)
    write_receipt_exclusive(args.out, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
