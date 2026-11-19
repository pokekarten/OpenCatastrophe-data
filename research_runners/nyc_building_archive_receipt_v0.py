# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline integrity and header gate for a *claimed* 2024 NYC BUILDING archive.

Input bytes remain local. This is not evidence of a verified provider release,
complete historic stock, rights approval or valid insured exposure. No rows,
individual IDs, geometry, path names, or addresses are printed or written.

Supported input: Socrata CSV export, or ZIP containing a single CSV member.
An export of the *current* NYC view is never an archival snapshot merely
because a user provides a 2024 date and a matching SHA-256 checksum.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
from zipfile import ZipFile, BadZipFile, ZIP_DEFLATED, ZIP_STORED

SOURCE_ID = "5zhs-2jue"
MAX_ON_DISK = 12 * 1024**3
MAX_CSV_MEMBER_UNCOMPRESSED = 12 * 1024**3
MAX_HEADER_BYTES = 32768
MAX_COLUMNS = 128
REQUIRED = frozenset({
    "the_geom", "bin", "doitt_id", "base_bbl", "mappluto_bbl",
    "feature_code", "construction_year", "last_edited_date",
})
ALIASES = {
    "map_pluto_bbl": "mappluto_bbl",
    "geometry": "the_geom",
    "the_geometry": "the_geom",
    "construction_yr": "construction_year",
    "featurecode": "feature_code",
    "lastediteddate": "last_edited_date",
}


class ArchiveGateError(ValueError):
    """Nonadmitted/unsafe archive or missing integrity evidence."""


def parse_version_date(value: str) -> str:
    if type(value) is not str or not re.fullmatch(r"2024-[0-9]{2}-[0-9]{2}", value):
        raise ArchiveGateError("archived provider-version date must be explicit 2024 ISO YYYY-MM-DD")
    try:
        if date.fromisoformat(value) > date(2024, 12, 31):
            raise ValueError("future")
    except ValueError as exc:
        raise ArchiveGateError("invalid 2024 source version date") from exc
    return value


def _local_file(path: str) -> Path:
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ArchiveGateError("archive must be a regular non-symlink local file")
    if p.suffix.lower() not in (".csv", ".zip"):
        raise ArchiveGateError("only original CSV or single-CSV ZIP archive supported")
    size = p.stat().st_size
    if not 0 < size <= MAX_ON_DISK:
        raise ArchiveGateError("source file is empty or exceeds configured byte cap")
    return p


def sha256_file(path: Path) -> tuple[str, int]:
    checksum = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ArchiveGateError("non-regular archive source")
        while chunk := stream.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_ON_DISK:
                raise ArchiveGateError("archive exceeded configured byte cap")
            checksum.update(chunk)
    if path.stat().st_size != total:
        raise ArchiveGateError("archive file changed during hash stream")
    return checksum.hexdigest(), total


def _csv_header(stream) -> tuple[str, ...]:
    """Parse one bounded CSV header record, never reading any data row."""
    buffer = bytearray()
    while len(buffer) <= MAX_HEADER_BYTES:
        char = stream.read(1)
        if not char:
            raise ArchiveGateError("missing terminated CSV header")
        buffer.extend(char)
        if char == b"\n":
            break
    if len(buffer) > MAX_HEADER_BYTES or b"\x00" in buffer:
        raise ArchiveGateError("oversized/binary CSV header")
    try:
        text = buffer.decode("utf-8-sig", errors="strict")
        fields = next(csv.reader(io.StringIO(text), strict=True))
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise ArchiveGateError("malformed CSV header") from exc
    if not 1 <= len(fields) <= MAX_COLUMNS:
        raise ArchiveGateError("unexpected column count")
    names = []
    for raw in fields:
        normal = re.sub(r"[^a-z0-9]+", "_", raw.casefold()).strip("_")
        normal = ALIASES.get(normal, normal)
        if not normal or len(normal) > 64:
            raise ArchiveGateError("empty or invalid normalized header field")
        names.append(normal)
    if len(names) != len(set(names)):
        raise ArchiveGateError("ambiguous duplicate header fields")
    return tuple(names)


def _zip_header(path: Path) -> tuple[str, ...]:
    try:
        with ZipFile(path, "r", allowZip64=True) as archive:
            infos = archive.infolist()
            if not 1 <= len(infos) <= 16:
                raise ArchiveGateError("unsafe ZIP member count")
            files = [f for f in infos if not f.is_dir()]
            if len(files) != 1 or not files[0].filename.lower().endswith(".csv"):
                raise ArchiveGateError("ZIP must contain precisely one CSV file")
            for info in infos:
                raw = info.filename.replace("\\", "/")
                parts = raw.rstrip("/").split("/")
                if raw.startswith("/") or any(part in ("", ".", "..") for part in parts):
                    raise ArchiveGateError("unsafe ZIP member path")
                if info.flag_bits & 1:
                    raise ArchiveGateError("encrypted ZIP not supported")
            member = files[0]
            if member.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                raise ArchiveGateError("unapproved ZIP compression type")
            if not 0 < member.file_size <= MAX_CSV_MEMBER_UNCOMPRESSED:
                raise ArchiveGateError("invalid ZIP uncompressed member size")
            if member.file_size > 200 * max(member.compress_size, 1):
                raise ArchiveGateError("suspicious ZIP compression ratio")
            with archive.open(member, "r") as stream:
                return _csv_header(stream)
    except (BadZipFile, EOFError, RuntimeError, OSError) as exc:
        raise ArchiveGateError("malformed or unreadable ZIP structure") from exc


def inspect(path: str, expected_sha256: str, provider_date: str, source_view: str = SOURCE_ID) -> dict:
    if source_view != SOURCE_ID:
        raise ArchiveGateError("archived view ID is not pinned to reviewed original OTI BUILDING")
    date_claim = parse_version_date(provider_date)
    if type(expected_sha256) is not str or not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
        raise ArchiveGateError("expected complete 64-hex SHA-256 receipt required")
    local = _local_file(path)
    actual, size = sha256_file(local)
    if not hmac.compare_digest(actual, expected_sha256.lower()):
        raise ArchiveGateError("archived source bytes do not match externally supplied SHA-256")
    if local.suffix.lower() == ".zip":
        names = _zip_header(local)
        kind = "single_csv_zip"
    else:
        with local.open("rb") as stream:
            names = _csv_header(stream)
        kind = "csv"
    missing = sorted(REQUIRED - set(names))
    if missing:
        raise ArchiveGateError("missing required original NYC building columns: " + ",".join(missing))
    return {
        "profile": "nyc_building_2024_archive_local_integrity_header_v0",
        "source_view_id": SOURCE_ID,
        "declared_archived_version_date": date_claim,
        "date_is_caller_declaration_not_provider_verified": True,
        "container_format": kind,
        "size_bytes": size,
        "entire_container_sha256_matches_expected": True,
        "required_header_fields_found": len(REQUIRED),
        "header_column_count": len(names),
        "full_csv_record_count_verified": False,
        "all_building_geometry_or_2024_taxlot_links_verified": False,
        "official_snapshot_release_authenticity_verified": False,
        "historic_inventory_year_2024_admitted": False,
        "source_license_rights_approved": False,
        "insured_tiv_or_losses_calculated": False,
        "raw_source_rows_identifiers_geometry_or_file_path_printed": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Local original archived CSV or single-CSV ZIP; never uploaded")
    parser.add_argument("--expected-sha256", required=True, help="Independent externally recorded whole-file SHA-256")
    parser.add_argument("--provider-version-date", required=True, help="Exact provider-claimed release date, YYYY-MM-DD in 2024")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect(args.archive, args.expected_sha256, args.provider_version_date), sort_keys=True))
        return 0
    except ArchiveGateError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
