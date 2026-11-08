#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline verification for exact USFS FPA FOD 7th archive metadata and GPKG ZIP.

Checks original publisher SHA-256, bounded ZIP member identity and SQLite
file signature. Never reads source event rows or location data, writes GPKG,
constructs loss models or claims CAT admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import tempfile
from zipfile import ZipFile, BadZipFile, ZIP_STORED, ZIP_DEFLATED

RELEASE = "FPA_FOD_20260615"
DOI = "10.2737/RDS-2013-0009.7"
METADATA_NAME = "RDS-2013-0009.7_Metadata_Fileindex.zip"
METADATA_BYTES = 31_583
METADATA_SHA256 = "1e94a5cab0cdcf77ed92d3b5810dbe1960e704422363ee731367646ac9781a49"
DATA_NAME = "RDS-2013-0009.7_Data_Format3_GPKG.zip"
DATA_BYTES = 238_170_979
DATA_SHA256 = "9e36ecd0d70dd5fa126be7b5ce5b02003867da04c41f3bd137f5ccdfca81b9b2"
GPKG_MEMBER = "Data/FPA_FOD_20260615.gpkg"
PUBLISHER_2024_SIZE_COUNTS = dict(A=43445, B=34441, C=7296, D=1263, E=640, F=388, G=235)
PUBLISHER_2024_LINK_COUNTS = dict(A=1, B=0, C=0, D=6, E=31, F=224, G=153)
VARIABLES_MEMBER = "Data/_variable_descriptions.csv"
VARIABLES_MEMBER_BYTES = 31_310
EXPECTED_META_MEMBERS = {
    "_fileindex_RDS-2013-0009.7.html",
    "_metadata_RDS-2013-0009.7.html",
    "_metadata_RDS-2013-0009.7.xml",
}
SHA = re.compile("[a-f0-9]{64}\\Z")
SQLITE_HEADER = b"SQLite format 3\x00"


class ArchiveBlocked(ValueError):
    """Exact release ZIP bytes or metadata content cannot be substantiated."""


def _digest_bytes(blob: bytes, expected_size: int, expected_sha: str):
    if type(blob) is not bytes or len(blob) != expected_size:
        raise ArchiveBlocked("original archive bytes missing or wrong exact size")
    if type(expected_sha) is not str or not SHA.fullmatch(expected_sha):
        raise ArchiveBlocked("invalid pinned original archive SHA256")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected_sha:
        raise ArchiveBlocked("original archive raw-byte SHA256 mismatch")
    return digest


def _safe_members(archive: ZipFile):
    items = archive.infolist()
    if not items or len(items) > 20:
        raise ArchiveBlocked("unexpected original ZIP member population")
    names = set()
    for info in items:
        name = info.filename
        if (not name or name.startswith("/") or "\\" in name or "\x00" in name
            or re.match(r"^[A-Za-z]:", name)
            or any(part in ("", ".", "..") for part in name.rstrip("/").split("/"))):
            raise ArchiveBlocked("unsafe source ZIP path")
        folded = name.rstrip("/").casefold()
        if folded in names:
            raise ArchiveBlocked("duplicate ZIP member path")
        names.add(folded)
        if info.flag_bits & 0x1 or info.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
            raise ArchiveBlocked("encrypted or unsupported ZIP member")
        if info.create_system == 3 and stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
            raise ArchiveBlocked("symlink ZIP member forbidden")
    return items


def verify_original_metadata_zip(
    blob: bytes, *, expected_bytes=METADATA_BYTES, expected_sha256=METADATA_SHA256
):
    sha = _digest_bytes(blob, expected_bytes, expected_sha256)
    try:
        with ZipFile(BytesIO(blob)) as archive:
            items = _safe_members(archive)
            if set(info.filename for info in items) != EXPECTED_META_MEMBERS:
                raise ArchiveBlocked("source version file index HTML/XML members drifted")
            if sum(info.file_size for info in items) > 250_000 or any(info.file_size > 150_000 for info in items):
                raise ArchiveBlocked("unbounded original metadata ZIP expansion")
            if archive.testzip() is not None:
                raise ArchiveBlocked("metadata ZIP member CRC failure")
            body = {info.filename: archive.read(info).decode("utf8") for info in items}
    except (BadZipFile, UnicodeError, OSError, RuntimeError) as exc:
        raise ArchiveBlocked("malformed original publisher metadata ZIP") from exc
    idx = body["_fileindex_RDS-2013-0009.7.html"]
    html = body["_metadata_RDS-2013-0009.7.html"]
    xml = body["_metadata_RDS-2013-0009.7.xml"]
    if RELEASE not in idx or "FPA_FOD_20260615.gpkg" not in idx or "1992-2024" not in idx:
        raise ArchiveBlocked("original file index is not the exact seventh-edition GeoPackage")
    for filename, data in (("HTML", html), ("XML", xml)):
        if RELEASE not in data or DOI not in data or "2024" not in data:
            raise ArchiveBlocked("original " + filename + " metadata release and DOI differ")
    if "without additional permissions or fees" not in html or "without additional permissions or fees" not in xml:
        raise ArchiveBlocked("original publisher general use-rights statement not present")
    return {
        "audit": "us-fpa-fod-v7-publisher-metadata-archive-v0",
        "state": "OFFICIAL_ORIGINAL_METADATA_BYTES_AND_CRC_VERIFIED_NOT_GPKG",
        "publisher_archive_release": RELEASE,
        "publisher_doi": DOI,
        "metadata_original_bytes": len(blob),
        "metadata_original_sha256_verified": sha,
        "metadata_original_zip_crc_valid": True,
        "original_member_count": len(body),
        "metadata_names_exactly_match_expected": True,
        "publisher_general_use_without_additional_permissions_stated": True,
        "publisher_GPKG_archive_sha256_from_catalog_not_download": DATA_SHA256,
        "publisher_GPKG_archive_bytes_from_catalog_not_download": DATA_BYTES,
        "GPKG_original_data_file_sha256_verified": False,
        "actual_GPKG_fire_event_rows_inspected": False,
        "publisher_source_not_event_perimeter_or_exposure_model": True,
        "CAT_source_scientific_or_insurance_loss_admission_granted": False,
        "original_source_bytes_or_individual_fire_rows_emitted": False,
    }



def audit_extracted_fires_2024_sqlite(
    original_db: Path, *, expected_records=87_708, expected_mtbs_id_present=415,
    expected_state_codes=53, expected_state_size_cells=299,
    expected_size_counts=None, expected_link_counts=None,
):
    """Read-only, source-aggregated 2024 numbers; no event-level rows emitted.

    Called by the original SHA-verified ZIP gate after private temporary
    extraction. Expected values are independently obtained ArcGIS totals.
    """
    if not original_db.is_file():
        raise ArchiveBlocked("missing original extracted source GPKG file")
    try:
        db = sqlite3.connect(
            "file:" + original_db.as_posix() + "?mode=ro&immutable=1", uri=True
        )
        try:
            db.execute("PRAGMA query_only = ON")
            sources = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if "Fires" not in sources:
                raise ArchiveBlocked("publisher Fires feature table not found")
            columns = {
                row[1].upper() for row in db.execute('PRAGMA table_info("Fires")')
            }
            if not {"FIRE_YEAR", "STATE", "FIRE_SIZE_CLASS", "MTBS_ID"}.issubset(columns):
                raise ArchiveBlocked("publisher Fires native linkage fields absent")
            groups = list(db.execute(
                "SELECT STATE,FIRE_SIZE_CLASS,COUNT(*),"
                "SUM(CASE WHEN MTBS_ID IS NOT NULL THEN 1 ELSE 0 END) "
                'FROM "Fires" WHERE FIRE_YEAR=2024 '
                "GROUP BY STATE,FIRE_SIZE_CLASS"
            ))
        finally:
            db.close()
    except (sqlite3.Error, OSError) as exc:
        raise ArchiveBlocked("read-only source GPKG database query failed") from exc
    codes = set()
    a = Counter()
    linked = Counter()
    for state, size, total, yes in groups:
        if not isinstance(state, str) or not re.fullmatch("[A-Z]{2}", state):
            raise ArchiveBlocked("original FPA state code malformed")
        if type(size) is not str or size not in "ABCDEFG":
            raise ArchiveBlocked("unknown source NWCG fire-size class")
        if type(total) is not int or type(yes) is not int or not 0 <= yes <= total:
            raise ArchiveBlocked("original archive invalid source group count")
        codes.add(state)
        a[size] += total
        linked[size] += yes
    if (len(codes) != expected_state_codes or len(groups) != expected_state_size_cells
            or sum(a.values()) != expected_records
            or sum(linked.values()) != expected_mtbs_id_present):
        raise ArchiveBlocked("original archived 2024 cohort differs from source control")
    if set(a) != set("ABCDEFG"):
        raise ArchiveBlocked("original 2024 A-G reported classes incomplete")
    if expected_size_counts is None:
        expected_size_counts = PUBLISHER_2024_SIZE_COUNTS
    if expected_link_counts is None:
        expected_link_counts = PUBLISHER_2024_LINK_COUNTS
    if any(a[key] != expected_size_counts.get(key) or linked[key] != expected_link_counts.get(key)
           for key in "ABCDEFG"):
        raise ArchiveBlocked("source archive A-G totals differ from independently observed ArcGIS cohort")
    return {
        "original_2024_fpa_report_count": sum(a.values()),
        "original_2024_mtbs_id_nonnull_count": sum(linked.values()),
        "original_2024_state_codes": len(codes),
        "original_2024_state_size_group_count": len(groups),
        "original_2024_size_class_record_counts": {
            key: a[key] for key in "ABCDEFG"
        },
        "original_2024_size_class_mtbs_id_counts": {
            key: linked[key] for key in "ABCDEFG"
        },
        "archived_2024_counts_match_independently_read_original_arcgis": True,
        "original_fire_ids_coordinates_geometries_or_loss_rows_emitted": False,
        "source_identity_join_or_insurance_loss_model_admitted": False,
    }


def verify_original_gpkg_zip(path: Path, *, expected_bytes=DATA_BYTES, expected_sha256=DATA_SHA256, audit_2024=False):
    """Stream SHA, read ZIP metadata and first 16 bytes only; no data extraction."""
    if not path.is_file() or path.stat().st_size != expected_bytes:
        raise ArchiveBlocked("missing/incorrect full original GPKG archive length")
    if type(expected_sha256) is not str or not SHA.fullmatch(expected_sha256):
        raise ArchiveBlocked("invalid expected original GPKG archive checksum")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(4 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        raise ArchiveBlocked("complete original GPKG archive SHA256 mismatch")
    try:
        with ZipFile(path, "r") as archive:
            entries = _safe_members(archive)
            names = [item.filename for item in entries if not item.is_dir()]
            if set(names) != {GPKG_MEMBER, VARIABLES_MEMBER} or len(names) != 2:
                raise ArchiveBlocked("pinned seventh-edition ZIP GPKG/variable-descriptions membership drift")
            if archive.getinfo(VARIABLES_MEMBER).file_size != VARIABLES_MEMBER_BYTES:
                raise ArchiveBlocked("original publisher variable descriptions size drifted")
            info = archive.getinfo(GPKG_MEMBER)
            if not 100_000 <= info.file_size <= 10_000_000_000:
                raise ArchiveBlocked("implausible original FPA GPKG file length")
            with archive.open(info) as original_gpkg:
                if original_gpkg.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
                    raise ArchiveBlocked("original GPKG does not have SQLite header")
            cohort = None
            if audit_2024:
                if info.file_size != 1_082_466_304:
                    raise ArchiveBlocked("original complete GPKG expanded byte length drift")
                with tempfile.TemporaryDirectory(prefix="source-fpa-v7-") as directory:
                    temporary_gpkg = Path(directory) / "FPA_FOD_20260615.gpkg"
                    with archive.open(info) as original, temporary_gpkg.open("wb") as output:
                        shutil.copyfileobj(original, output, length=4 * 1024 * 1024)
                    if temporary_gpkg.stat().st_size != info.file_size:
                        raise ArchiveBlocked("truncated original GPKG member extraction")
                    cohort = audit_extracted_fires_2024_sqlite(temporary_gpkg)
    except (BadZipFile, OSError, RuntimeError) as exc:
        raise ArchiveBlocked("unreadable original GPKG ZIP") from exc
    result = {
        "audit": "us-fpa-fod-v7-gpkg-full-original-archive-v0",
        "state": "ORIGINAL_GPKG_ARCHIVE_SHA_AND_SQLITE_MAGIC_VERIFIED_NOT_EVENT_ADMITTED",
        "release": RELEASE,
        "archive_original_bytes": expected_bytes,
        "original_archive_sha256_verified": digest.hexdigest(),
        "source_gpkg_member_exists": True,
        "original_variable_descriptions_member_exists": True,
        "original_variable_descriptions_uncompressed_bytes": VARIABLES_MEMBER_BYTES,
        "member_sqlite_header_checked": True,
        "full_member_sqlite_table_or_spatial_integrity_checked": False,
        "source_event_rows_extracted_or_published": False,
        "MTBS_fire_identity_join_or_wildfire_footprint_verified": False,
        "CAT_model_scientific_admission_granted": False,
    }
    if cohort is not None:
        result["original_2024_sqlite_aggregate"] = cohort
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-zip", required=True, type=Path)
    parser.add_argument("--data-gpkg-zip", type=Path)
    parser.add_argument("--audit-2024-sqlite", action="store_true",
                        help="Extract the already SHA-verified ~1.08 GB GPKG privately and query only 2024 aggregate counts")
    args = parser.parse_args(argv)
    try:
        file = args.metadata_zip
        if not file.is_file() or file.stat().st_size != METADATA_BYTES:
            raise ArchiveBlocked("missing or wrong-sized original metadata archive")
        report = verify_original_metadata_zip(file.read_bytes())
        if args.audit_2024_sqlite and args.data_gpkg_zip is None:
            raise ArchiveBlocked("2024 SQL audit requires the SHA-verified full GPKG archive")
        if args.data_gpkg_zip is not None:
            report["optional_full_gpkg_receipt"] = verify_original_gpkg_zip(
                args.data_gpkg_zip, audit_2024=args.audit_2024_sqlite
            )
            report["state"] = "METADATA_AND_ORIGINAL_GPKG_ARCHIVE_BYTES_VERIFIED_NOT_CAT_ADMITTED"
    except (ArchiveBlocked, OSError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
