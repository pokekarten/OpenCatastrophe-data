# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original-byte BKG VG250 31.12.2025 UTM32s GeoPackage ZIP T2 research gate.

One lawful, separately acquired local original ZIP. No downloader, writing to
Git or DB, coordinates, source feature IDs or raw feature payloads in output.
The BKG /aktuell/ URL is MUTABLE: exact release SHA-256 is discovered and
reported, not assumed to be previously pinned. Its 2025 vintage is based on
the publisher's official product listing, not yet independently proved by an
archive-embedded date. The official MD5 sidecar is NOT a cryptographic
substitute for the computed full ZIP SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import sys
import tempfile
from typing import Any
from zipfile import ZipFile, BadZipFile

from research_runners.bkg_vg250_2025_original_md5_sidecar_v0 import (
    ARCHIVE_NAME, ARCHIVE_URL, OFFICIAL_PUBLISHED_MD5,
)

MAX_ZIP_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 512
MAX_UNCOMPRESSED_TOTAL = 1600 * 1024 * 1024
MAX_GPKG_BYTES = 1250 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1000
EXPECTED_LAYERS = ("vg250_sta", "vg250_lan")
EXPECTED_SRS = 25832
LAND_GF = 4
WATER_GF = 2


class BkgOriginalArchiveBlocked(ValueError):
    """Exact source or bounded original archive/GPKG semantic gate blocked."""


def _scan_members(archive: ZipFile) -> tuple[Any, int, int]:
    members = archive.infolist()
    if not 1 <= len(members) <= MAX_ARCHIVE_MEMBERS:
        raise BkgOriginalArchiveBlocked("unexpected ZIP member count")
    seen: set[str] = set()
    gpkg_members = []
    total_uncompressed = 0
    for m in members:
        name = m.filename
        parts = PurePosixPath(name).parts
        if (not name or len(name) > 250 or name.startswith(("/", "\\"))
                or "\\" in name or "\x00" in name or ":" in name
                or any(part in {"", ".", ".."} for part in parts)
                or m.flag_bits & 1
                or (m.create_system == 3 and stat.S_IFMT(m.external_attr >> 16)
                    == stat.S_IFLNK)):
            raise BkgOriginalArchiveBlocked("unsafe original archive member")
        key = name.casefold()
        if key in seen:
            raise BkgOriginalArchiveBlocked("duplicate archive member")
        seen.add(key)
        if m.is_dir():
            continue
        if m.file_size < 0 or m.compress_size < 0:
            raise BkgOriginalArchiveBlocked("invalid archive member size")
        if m.compress_size == 0 and m.file_size:
            raise BkgOriginalArchiveBlocked("invalid nonempty ZIP member")
        if (m.file_size > 0 and m.compress_size > 0
                and m.file_size / m.compress_size > MAX_COMPRESSION_RATIO):
            raise BkgOriginalArchiveBlocked("excessive archive compression ratio")
        total_uncompressed += m.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_TOTAL:
            raise BkgOriginalArchiveBlocked("archive decompression budget exceeded")
        if name.lower().endswith(".gpkg"):
            gpkg_members.append(m)
    if len(gpkg_members) != 1:
        raise BkgOriginalArchiveBlocked("expected exactly one original GPKG in BKG ZIP")
    gpkg = gpkg_members[0]
    if not 100 <= gpkg.file_size <= MAX_GPKG_BYTES:
        raise BkgOriginalArchiveBlocked("unexpected GPKG size")
    return gpkg, len(members), total_uncompressed


def _sql_identifier(name: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z_0-9]{0,60}", name):
        raise BkgOriginalArchiveBlocked("invalid fixed GPKG layer identity")
    return '"' + name + '"'


def _inspect_gpkg(path: Path) -> dict[str, Any]:
    if path.stat().st_size < 100:
        raise BkgOriginalArchiveBlocked("GPKG SQLite signature missing")
    with path.open("rb") as opened:
        if opened.read(16) != b"SQLite format 3\x00":
            raise BkgOriginalArchiveBlocked("GPKG SQLite signature missing")
    try:
        # Strictly read-only/immutable; no migrations, pragmas that write, or
        # third-party extensions. All table names below are fixed constants.
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1",uri=True,timeout=2) as db:
            db.execute("PRAGMA query_only=ON")
            names = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not {"gpkg_contents", "gpkg_geometry_columns", *EXPECTED_LAYERS} <= names:
                raise BkgOriginalArchiveBlocked("expected original GPKG layer schema missing")
            layers: dict[str, dict[str, Any]] = {}
            for name in EXPECTED_LAYERS:
                key = _sql_identifier(name)
                geo = db.execute(
                    "SELECT geometry_type_name,srs_id FROM gpkg_geometry_columns WHERE table_name=?",
                    (name,)).fetchall()
                if (len(geo) != 1 or str(geo[0][0]).upper() not in
                        {"POLYGON", "MULTIPOLYGON"}
                        or geo[0][1] != EXPECTED_SRS):
                    raise BkgOriginalArchiveBlocked("unexpected GPKG spatial reference or type")
                columns = {row[1].lower() for row in db.execute(f"PRAGMA table_info({key})")}
                if not {"gf","ags"} <= columns:
                    raise BkgOriginalArchiveBlocked("missing BKG source GF and AGS")
                physical = db.execute(f"SELECT count(*) FROM {key}").fetchone()[0]
                gf = {
                    (str(row[0]) if row[0] is not None else "NULL"): row[1]
                    for row in db.execute(f"SELECT GF,count(*) FROM {key} GROUP BY GF")
                }
                for raw_gf in gf:
                    if raw_gf not in {"2", "4"}:
                        raise BkgOriginalArchiveBlocked("unexpected land/water GF class")
                count_gf4_distinct = db.execute(
                    f"SELECT count(DISTINCT AGS) FROM {key} WHERE CAST(GF AS INTEGER)=4"
                ).fetchone()[0]
                if not isinstance(physical,int) or physical < 1 or physical > 500:
                    raise BkgOriginalArchiveBlocked("implausible administrative feature count")
                layers[name] = {
                    "original_feature_records": physical,
                    "gf4_land_records": gf.get("4",0),
                    "gf2_water_records": gf.get("2",0),
                    "distinct_ags_gf4_land": count_gf4_distinct,
                    "srs_id": geo[0][1],
                    "original_geometry_type": str(geo[0][0]).upper(),
                    "original_GPKG_GF_2_water_and_GF_4_land_kept_distinct": True,
                }
            if layers["vg250_lan"]["distinct_ags_gf4_land"] != 16:
                raise BkgOriginalArchiveBlocked("expected 16 official state land keys")
            if layers["vg250_sta"]["distinct_ags_gf4_land"] != 1:
                raise BkgOriginalArchiveBlocked("expected 1 official Germany land key")
    except (sqlite3.Error, OSError, TypeError) as exc:
        raise BkgOriginalArchiveBlocked("unreadable GPKG source schema") from exc
    return layers


def inspect_original_archive(path: Path, *,
                             synthetic_expected_md5: str | None = None) -> dict[str, Any]:
    """Verify one ZIP, then structural GPKG and exact state/country cardinals.

    synthetic_expected_md5 is only a test escape hatch; the returned receipt
    explicitly says provider original identity is NOT verified in this mode.
    """
    if path.is_symlink() or not path.is_file() or not 1024 <= path.stat().st_size <= MAX_ZIP_BYTES:
        raise BkgOriginalArchiveBlocked("missing, symlink or wrong original ZIP size")
    if synthetic_expected_md5 is not None and not re.fullmatch(r"[0-9a-f]{32}",synthetic_expected_md5):
        raise BkgOriginalArchiveBlocked("bad synthetic MD5 parameter")
    sha = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        while part := stream.read(1024 * 1024):
            sha.update(part)
            md5.update(part)
    digest = md5.hexdigest()
    expected = synthetic_expected_md5 or OFFICIAL_PUBLISHED_MD5
    if digest != expected:
        raise BkgOriginalArchiveBlocked("whole-source ZIP differs from publisher MD5 sidecar")
    with path.open("rb") as opened:
        if opened.read(4) != b"PK\x03\x04":
            raise BkgOriginalArchiveBlocked("original bytes are not a ZIP")
    try:
        with ZipFile(path, "r") as archive:
            gpkg_member, count, uncompressed = _scan_members(archive)
            with tempfile.TemporaryDirectory(prefix="bkg-vg250-2025-") as work:
                gpkg_path = Path(work) / "original.gpkg"
                gpkg_sha = hashlib.sha256()
                total = 0
                with archive.open(gpkg_member, "r") as incoming, gpkg_path.open("xb") as outgoing:
                    while block := incoming.read(1024 * 1024):
                        total += len(block)
                        if total > MAX_GPKG_BYTES:
                            raise BkgOriginalArchiveBlocked("GPKG streaming size exceeded")
                        gpkg_sha.update(block)
                        outgoing.write(block)
                if total != gpkg_member.file_size:
                    raise BkgOriginalArchiveBlocked("GPKG uncompressed member length drift")
                layers = _inspect_gpkg(gpkg_path)
                gpkg_sha256 = gpkg_sha.hexdigest()
    except (BadZipFile, EOFError, OSError, RuntimeError, OverflowError) as exc:
        raise BkgOriginalArchiveBlocked("invalid or corrupt full ZIP/GPKG archive") from exc

    is_official = synthetic_expected_md5 is None
    return {
        "source_id": "de.bkg.vg250.3112.2025",
        "source_original_url": ARCHIVE_URL if is_official else None,
        "claimed_product_from_publisher_listing": "VG250 31.12.2025 UTM32s GeoPackage Ebenen ZIP",
        "full_zip_original_bytes": path.stat().st_size,
        "full_zip_sha256": sha.hexdigest(),
        "full_zip_md5": digest,
        "official_publisher_sidecar_md5_matches_full_zip": is_official,
        "source_original_file_identity_verified": is_official,
        "zip_member_count": count,
        "zip_uncompressed_total_declared_bytes": uncompressed,
        "gpkg_original_sha256": gpkg_sha256,
        "gpkg_original_uncompressed_bytes": total,
        "source_gpkg_layers": layers,
        "source_vintage_inside_zip_independently_verified": False,
        "all_geom_coordinates_and_topology_validated": False,
        "naturalearth_geoboundaries_bkg_three_way_spatial_comparison_done": False,
        "original_zip_or_gpkg_persisted_in_git_or_neon": False,
        "cat_model_input_approved": False,
        "insurance_geolocation_approved": False,
        "scientific_scope": "whole_original_archive_identity_and_country_state_GPKG_attribute_cardinality_only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = inspect_original_archive(args.original_zip)
    except BkgOriginalArchiveBlocked as exc:
        # Only raise this error with author-controlled constant strings.
        # Provider names, feature values, CRS payload, paths and coordinates
        # must never be injected into exception text.
        print(f"BLOCKED: BKG 2025 source proof — {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, OverflowError, MemoryError):
        print("BLOCKED: BKG 2025 original archive unexpected system failure", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
