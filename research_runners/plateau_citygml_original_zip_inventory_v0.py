# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline inventory of an independently acquired PLATEAU CityGML original ZIP.

No provider HTTP, decompression, extraction, geometry import, licence decision,
source admission, or insurer exposure. Checking ZIP metadata is NOT CRC checking.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import zipfile
from pathlib import Path

class ZipPreflightError(ValueError):
    """A candidate ZIP is unsafe, ambiguous or over a finite budget."""

MAX_ZIP_BYTES = 16 * 1024 ** 3
MAX_MEMBERS = 100_000
MAX_SINGLE_UNCOMPRESSED = 16 * 1024 ** 3
MAX_TOTAL_UNCOMPRESSED = 256 * 1024 ** 3
MAX_COMPRESSION_RATIO = 1000
CHUNK_BYTES = 1024 * 1024
ACCEPTED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
SHA256_RE = re.compile(r"[a-f0-9]{64}\Z", re.ASCII)


def _file_identity(info: os.stat_result) -> tuple[int, ...]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _safe_member_name(name: str) -> list[str]:
    if not name or len(name) > 1024:
        raise ZipPreflightError("ZIP entry name is missing or over budget")
    if name.startswith("/") or "\\" in name or "\x00" in name or "//" in name:
        raise ZipPreflightError("ZIP entry path is noncanonical or unsafe")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise ZipPreflightError("ZIP entry path has control characters")
    parts = name.rstrip("/").split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ZipPreflightError("ZIP entry path has ambiguous segments")
    if re.match(r"^[A-Za-z]:", parts[0]):
        raise ZipPreflightError("ZIP entry path resembles a drive path")
    return parts


def _zip_inventory(source) -> dict[str, int | bool]:
    try:
        with zipfile.ZipFile(source, mode="r", allowZip64=True) as archive:
            infos = archive.infolist()
            if not 0 < len(infos) <= MAX_MEMBERS:
                raise ZipPreflightError("ZIP member count outside safe bounds")
            total = 0
            gml_count = 0
            bldg_count = 0
            names: set[str] = set()
            for info in infos:
                parts = _safe_member_name(info.filename)
                duplicate_key = "/".join(parts).casefold()
                if duplicate_key in names:
                    raise ZipPreflightError("ZIP has duplicate/case-colliding entry names")
                names.add(duplicate_key)
                if info.flag_bits & 1:
                    raise ZipPreflightError("ZIP contains encrypted entries")
                if info.compress_type not in ACCEPTED_COMPRESSION:
                    raise ZipPreflightError("ZIP uses unsupported compression")
                unix_type = stat.S_IFMT(info.external_attr >> 16)
                if info.create_system == 3 and unix_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ZipPreflightError("ZIP contains symbolic links or special entries")
                if info.is_dir():
                    if unix_type == stat.S_IFREG:
                        raise ZipPreflightError("ZIP directory is incorrectly tagged as regular file")
                    continue
                if unix_type == stat.S_IFDIR:
                    raise ZipPreflightError("ZIP file is incorrectly tagged as directory")
                if info.file_size < 0 or info.file_size > MAX_SINGLE_UNCOMPRESSED:
                    raise ZipPreflightError("ZIP individual uncompressed size exceeds budget")
                if info.compress_size < 0 or (info.file_size > 0 and info.compress_size == 0):
                    raise ZipPreflightError("ZIP compressed size is invalid")
                if info.compress_size and info.file_size > info.compress_size * MAX_COMPRESSION_RATIO:
                    raise ZipPreflightError("ZIP member compression ratio exceeds budget")
                total += info.file_size
                if total > MAX_TOTAL_UNCOMPRESSED:
                    raise ZipPreflightError("ZIP total uncompressed size exceeds budget")
                if info.filename.lower().endswith(".gml"):
                    gml_count += 1
                    # PLATEAU official folder convention: .../udx/bldg/*.gml.
                    # Do not assume any particular archive-root city/year.
                    lower = [part.lower() for part in parts]
                    if any(lower[i:i+2] == ["udx", "bldg"] for i in range(len(lower)-2)):
                        bldg_count += 1
            if not bldg_count:
                raise ZipPreflightError("ZIP contains no CityGML files under udx/bldg")
            return {
                "zip_member_count": len(infos),
                "citygml_file_count": gml_count,
                "building_citygml_file_count": bldg_count,
                "declared_total_uncompressed_bytes": total,
                "archive_member_paths_reviewed": True,
                "compressed_data_crc_verified": False,
            }
    except (zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError, EOFError, OSError, ValueError) as exc:
        if isinstance(exc, ZipPreflightError):
            raise
        raise ZipPreflightError("candidate ZIP cannot be safely inventoried") from exc


def inspect_zip_file(
    path: Path, *, expected_sha256: str | None = None,
    expected_byte_count: int | None = None,
) -> dict[str, object]:
    """Hash the same stable regular file used for archive member inspection."""
    if expected_sha256 is not None and not SHA256_RE.fullmatch(expected_sha256):
        raise ZipPreflightError("expected SHA-256 must have 64 lowercase hex characters")
    if expected_byte_count is not None and (
        type(expected_byte_count) is not int
        or not 0 < expected_byte_count <= MAX_ZIP_BYTES
    ):
        raise ZipPreflightError("expected byte count invalid or outside budget")

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ZipPreflightError("candidate ZIP cannot be opened as safe local input") from exc
    try:
        with os.fdopen(descriptor, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ZipPreflightError("candidate ZIP must be a regular file")
            if not 0 < before.st_size <= MAX_ZIP_BYTES:
                raise ZipPreflightError("candidate ZIP byte count outside budget")
            if expected_byte_count is not None and before.st_size != expected_byte_count:
                raise ZipPreflightError("candidate ZIP byte count does not match expected bytes")
            inventory = _zip_inventory(source)
            source.seek(0)
            digest = hashlib.sha256()
            actual = 0
            while True:
                chunk = source.read(CHUNK_BYTES)
                if not chunk:
                    break
                actual += len(chunk)
                if actual > MAX_ZIP_BYTES:
                    raise ZipPreflightError("candidate ZIP exceeded read budget")
                digest.update(chunk)
            after = os.fstat(source.fileno())
            if actual != before.st_size or _file_identity(after) != _file_identity(before):
                raise ZipPreflightError("candidate ZIP changed while being inspected")
            hexdigest = digest.hexdigest()
            if expected_sha256 is not None and hexdigest != expected_sha256:
                raise ZipPreflightError("candidate ZIP SHA-256 does not match expected digest")
    except OSError as exc:
        raise ZipPreflightError("candidate ZIP file reading failed") from exc

    return {
        "source_id": "jp.mlit.plateau.citygml.3d-city-models",
        # The ZIP's actual municipality and vintage are NOT authenticated
        # from member names, even if a caller has pinned a catalogue row.
        "municipality_and_year_in_archive_verified": False,
        "local_zip_byte_count": actual,
        "local_zip_sha256": hexdigest,
        "expected_sha256_supplied": expected_sha256 is not None,
        "expected_byte_count_supplied": expected_byte_count is not None,
        **inventory,
        "evidence": "local_original_candidate_archive_structure_only",
        "upstream_provider_authenticated": False,
        "zip_member_contents_crc_verified": False,
        "building_geometry_parsed": False,
        "crs_and_vertical_datum_verified": False,
        "exact_dataset_licence_reviewed": False,
        "model_input_approved": False,
        "provider_network_access": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="separately acquired local CityGML ZIP")
    parser.add_argument("--expected-sha256", type=str, default=None)
    parser.add_argument("--expected-byte-count", type=int, default=None)
    args = parser.parse_args(argv)
    try:
        result = inspect_zip_file(
            args.input, expected_sha256=args.expected_sha256,
            expected_byte_count=args.expected_byte_count,
        )
    except ZipPreflightError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
