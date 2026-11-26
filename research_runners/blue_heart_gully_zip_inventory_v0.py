# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline Blue Heart highway-gully ZIP structure and publisher-identity preflight.

Version-specific source: Zenodo 20699635, 6_highway_gully_telemetry_data.zip.
Does not extract, inspect CSV contents, emit member names or admit any bytes.
For original ZIP provenance, compare exact size and advertised MD5 then compute
a locally reproducible SHA-256; member data CRCs are NOT checked in this gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath


ZIP_NAME = "6_highway_gully_telemetry_data.zip"
EXPECTED_ZIP_BYTES = 4_229_095
PUBLISHER_MD5 = "64ebe2a3fe9d9cb09f820802d134b8fb"
EXPECTED_PAIRS = 15
EXPECTED_MEMBERS = 31
MAX_TOTAL_UNCOMPRESSED = 30_000_000
MAX_SINGLE_UNCOMPRESSED = 12_000_000
MAX_RATIO = 100.0
MAX_NAME_LENGTH = 255
MAX_HASH_CHUNK = 1 << 20


class BlueHeartZipError(ValueError):
    """ZIP source identity or archive safety preflight failed."""


def inspect_zip_structure(archive: zipfile.ZipFile) -> dict[str, object]:
    """Analyze entry metadata only; never open or extract ZIP members."""

    items = archive.infolist()
    if len(items) != EXPECTED_MEMBERS:
        raise BlueHeartZipError("unexpected archive member count")

    seen = set()
    roots = set()
    measurements: set[str] = set()
    quality: set[str] = set()
    folders = 0
    total = 0

    for item in items:
        name = item.filename
        if (
            not name or len(name) > MAX_NAME_LENGTH
            or name.startswith("/") or "\\" in name or "\x00" in name
            or any(part in ("", ".", "..") for part in name.rstrip("/").split("/"))
            or PurePosixPath(name).is_absolute()
        ):
            raise BlueHeartZipError("unsafe ZIP path")

        key = name.casefold()
        if key in seen:
            raise BlueHeartZipError("duplicate ZIP path")
        seen.add(key)

        if item.flag_bits & 1 or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise BlueHeartZipError("encrypted or unsupported ZIP entry")
        if item.create_system == 3 and stat.S_ISLNK(item.external_attr >> 16):
            raise BlueHeartZipError("ZIP entry is a symbolic link")

        parts = PurePosixPath(name).parts
        roots.add(parts[0])
        if item.is_dir():
            folders += 1
            if len(parts) != 1 or item.file_size or item.compress_size:
                raise BlueHeartZipError("unexpected folder marker")
            continue

        if len(parts) != 2 or not name.lower().endswith(".csv"):
            raise BlueHeartZipError("unexpected file path or format")
        if (
            item.file_size <= 0 or item.file_size > MAX_SINGLE_UNCOMPRESSED
            or item.compress_size <= 0 or item.file_size / item.compress_size > MAX_RATIO
        ):
            raise BlueHeartZipError("unsafe expansion ratio or source member size")
        total += item.file_size
        if total > MAX_TOTAL_UNCOMPRESSED:
            raise BlueHeartZipError("source archive uncompressed size too large")

        basename = parts[1]
        if basename.lower().endswith("_quality_flags.csv"):
            stem = basename[:-len("_quality_flags.csv")].casefold()
            if not stem or stem in quality:
                raise BlueHeartZipError("duplicate or empty QC stem")
            quality.add(stem)
        else:
            stem = basename[:-len(".csv")].casefold()
            if not stem or stem in measurements:
                raise BlueHeartZipError("duplicate or empty measurement stem")
            measurements.add(stem)

    if folders != 1 or len(roots) != 1:
        raise BlueHeartZipError("ZIP must have one root directory marker")
    if (
        len(measurements) != EXPECTED_PAIRS
        or len(quality) != EXPECTED_PAIRS
        or measurements != quality
    ):
        raise BlueHeartZipError("measurement/QC stems are not one-to-one")

    return {
        "zip_member_count": len(items),
        "directory_member_count": folders,
        "measurement_csv_count": len(measurements),
        "quality_csv_count": len(quality),
        "unpaired_csv_count": 0,
        "uncompressed_member_bytes_advertised": total,
        "all_entries_unencrypted": True,
        "zip_member_crc_read": False,
        "measurement_rows_or_timestamps_read": False,
        "member_names_emitted": False,
        "source_bytes_admitted": False,
    }


def inspect_original_zip(path: Path) -> dict[str, object]:
    """Require the publisher-listed ZIP identity, then inspect local metadata."""

    path = Path(path)
    if path.name != ZIP_NAME or path.is_symlink() or not path.is_file():
        raise BlueHeartZipError("wrong or nonregular original ZIP path")
    if path.stat().st_size != EXPECTED_ZIP_BYTES:
        raise BlueHeartZipError("original ZIP size does not match published record")

    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while block := stream.read(MAX_HASH_CHUNK):
                md5.update(block)
                sha256.update(block)
            if md5.hexdigest() != PUBLISHER_MD5:
                raise BlueHeartZipError("original ZIP MD5 does not match publisher record")
            stream.seek(0)
            with zipfile.ZipFile(stream) as archive:
                structure = inspect_zip_structure(archive)
    except (OSError, UnicodeError, zipfile.BadZipFile) as exc:
        raise BlueHeartZipError("invalid or unreadable original ZIP") from exc

    return {
        "provider": "zenodo.org",
        "record_id": 20699635,
        "release": "v1.0",
        "archive_size_bytes": EXPECTED_ZIP_BYTES,
        "original_archive_sha256": sha256.hexdigest(),
        "publisher_advertised_md5_verified": True,
        **structure,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline source-bound Blue Heart ZIP inventory")
    parser.add_argument("archive", type=Path, help="Original ZIP on local filesystem")
    args = parser.parse_args()
    try:
        result = inspect_original_zip(args.archive)
    except BlueHeartZipError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
