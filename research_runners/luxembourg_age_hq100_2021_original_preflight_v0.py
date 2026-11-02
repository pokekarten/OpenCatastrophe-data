# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only original-provider AGE HQ100 (2021 model / 2022 release) receipt.

Verifies the catalogue SHA-1, records independent SHA-256 and the full
ZIP member CRC; inspects only file format headers, declared CRS keywords,
and field names/counts. NEVER reads or emits original hazard geometries,
per-feature depths, addresses, or insurer properties. Not model-admitted.
"""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import zipfile

SOURCE_URL = ("https://download.data.public.lu/resources/flood-hazard-maps-100-year-flood/"
              "20220613-154804/hwgk2021-hq100.zip")
CATALOGUE_URL = "https://data.public.lu/en/datasets/flood-hazard-maps-100-year-flood/"
RESOURCE_ID = "1f529004-dd4d-42f1-8bd3-3b33a3f54ffd"
CATALOGUE_SHA1 = "41b58cb5e0c9509d39824919dce85702ceda0540"
MAX_ZIP_BYTES = 16 * 1024 * 1024
MAX_EXPANDED_BYTES = 1024 * 1024 * 1024
MAX_MEMBERS = 320
MAX_RATIO = 1200
MAX_DBF_HEADER = 16384
MAX_PRJ_BYTES = 64 * 1024


class HQ100OriginalError(ValueError):
    """Unexpected/corrupted provider bytes; no data admission permitted."""


def _checksum(source: Path) -> tuple[str, str]:
    h1, h2 = hashlib.sha1(), hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h1.update(block)
            h2.update(block)
    return h1.hexdigest(), h2.hexdigest()


def _safe_member(member: zipfile.ZipInfo) -> None:
    name = member.filename
    mode = (member.external_attr >> 16) & 0o170000
    parts = name.rstrip("/").split("/")
    if (not name or len(name) > 255 or name.startswith("/")
            or "\\" in name or ":" in name or "\x00" in name
            or any(p in ("", ".", "..") for p in parts)
            or (member.flag_bits & 1) or mode == stat.S_IFLNK):
        raise HQ100OriginalError("Unsafe ZIP member path or encryption")


def _dbf_header(stream, length: int) -> dict:
    header = stream.read(32)
    if len(header) != 32 or length < 33:
        raise HQ100OriginalError("Truncated DBF header")
    version = header[0]
    rows, header_size, record_size = struct.unpack_from("<IHH", header, 4)
    if (version not in (0x03, 0x30, 0x31, 0x32, 0x83)
            or not 33 <= header_size <= MAX_DBF_HEADER
            or (header_size - 33) % 32 != 0 or not 1 <= record_size <= 65535
            or not 0 <= rows <= 20000000
            or header_size + rows * record_size > length + 1):
        raise HQ100OriginalError("Invalid DBF version, header or declared rows")
    raw = stream.read(header_size - 32)
    if len(raw) != header_size - 32 or raw[-1] != 0x0D:
        raise HQ100OriginalError("Invalid DBF field descriptor terminator")
    fields = []
    for offset in range(0, len(raw) - 1, 32):
        entry = raw[offset:offset + 32]
        if len(entry) != 32:
            raise HQ100OriginalError("Truncated DBF descriptor")
        name = entry[:11].split(b"\x00", 1)[0].decode("ascii", "replace")
        sanitized = name if re.fullmatch(r"[A-Za-z0-9_]{1,11}", name) else "unrecognized"
        fields.append({"name": sanitized, "dbf_type": chr(entry[11])
                       if 32 <= entry[11] <= 126 else "unknown",
                       "width": entry[16], "decimal_places": entry[17]})
    if not fields or len(fields) > 100:
        raise HQ100OriginalError("Unexpected number of DBF fields")
    return {"dbf_declared_records": rows, "dbf_field_schema": fields}


def _shp_header(stream, length: int) -> dict:
    b = stream.read(100)
    if len(b) != 100 or length < 100:
        raise HQ100OriginalError("Truncated SHP main header")
    magic = struct.unpack_from(">i", b, 0)[0]
    declared_words = struct.unpack_from(">i", b, 24)[0]
    version, kind = struct.unpack_from("<ii", b, 28)
    if magic != 9994 or version != 1000 or declared_words * 2 != length:
        raise HQ100OriginalError("Invalid SHP magic/version/declared byte length")
    if kind not in (0, 1, 3, 5, 8, 11, 13, 15, 18, 21, 23, 25, 28, 31):
        raise HQ100OriginalError("Unsupported original SHP shape type")
    return {"shp_shape_type_code": kind, "shp_declared_bytes_valid": True}


def _prj_hint(stream, length: int) -> dict:
    if not 0 < length <= MAX_PRJ_BYTES:
        raise HQ100OriginalError("Excessive PRJ file")
    raw = stream.read(length)
    if len(raw) != length:
        raise HQ100OriginalError("Truncated PRJ")
    t = raw.decode("latin-1").upper()
    hints = [label for label in ("LUREF", "2169", "ETRS", "WGS_1984",
                                "WGS 84", "3035", "LUXEMBOURG")
             if label in t]
    return {"prj_crs_text_hints_only": hints,
            "prj_coordinate_frame_and_axis_verified": False}


def inspect(source: Path, *, expected_sha1: str = CATALOGUE_SHA1) -> dict:
    path = Path(source)
    if (not re.fullmatch("[0-9a-f]{40}", expected_sha1)
            or not path.is_file() or path.is_symlink()
            or not 0 < path.stat().st_size <= MAX_ZIP_BYTES):
        raise HQ100OriginalError("Invalid source identity, size or published checksum")
    sha1, sha256 = _checksum(path)
    if sha1 != expected_sha1:
        raise HQ100OriginalError("Original ZIP differs from published AGE source SHA-1")
    files = []
    suffixes: Counter[str] = Counter()
    total_size = 0
    names = set()
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if not 1 <= len(members) <= MAX_MEMBERS:
                raise HQ100OriginalError("Unsupported number of source archive members")
            for member in members:
                _safe_member(member)
                if member.filename in names:
                    raise HQ100OriginalError("Duplicate original archive member")
                names.add(member.filename)
                if member.is_dir():
                    continue
                if (member.file_size <= 0 or member.compress_size <= 0
                        or member.file_size > member.compress_size * MAX_RATIO):
                    raise HQ100OriginalError("Unsupported uncompressed size or ZIP compression ratio")
                total_size += member.file_size
                if total_size > MAX_EXPANDED_BYTES:
                    raise HQ100OriginalError("Archive exceeds expanded byte budget")
                suffix = PurePosixPath(member.filename).suffix.lower() or "[none]"
                suffixes[suffix] += 1
                metadata = {}
                with archive.open(member) as stream:
                    if suffix == ".dbf":
                        metadata = _dbf_header(stream, member.file_size)
                    elif suffix == ".shp":
                        metadata = _shp_header(stream, member.file_size)
                    elif suffix == ".prj":
                        metadata = _prj_hint(stream, member.file_size)
                    # Read the rest to verify all ZIP member CRCs.
                    while stream.read(1024 * 1024):
                        pass
                if metadata:
                    files.append({"format": suffix, "source_member_bytes": member.file_size,
                                  **metadata})
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError, EOFError,
            RuntimeError, NotImplementedError) as exc:
        raise HQ100OriginalError("Source archive/member CRC or read failure") from exc
    return {
        "schema_version": "lu-age-hq100-2021-original-format-preflight-v0",
        "publisher_catalogue_url": CATALOGUE_URL,
        "publisher_original_url": SOURCE_URL,
        "publisher_resource_id": RESOURCE_ID,
        "source_model_label": "HWGK2021 HQ100",
        "catalogue_resource_updated": "2022-06-13",
        "catalogue_license_label": "CC0",
        "original_zip_sha1_matches_publisher": True,
        "original_zip_sha256_observed": sha256,
        "original_zip_bytes": path.stat().st_size,
        "archive_uncompressed_bytes": total_size,
        "archive_member_count": len(members),
        "original_member_suffix_counts": dict(sorted(suffixes.items())),
        "format_header_inventory_only": files,
        "actual_hazard_geometry_read": False,
        "depth_units_verified": False,
        "individual_depth_values_read": False,
        "hazard_area_geometries_ingested": False,
        "original_source_bytes_persisted": False,
        "model_input_admitted": False,
        "real_insurer_exposure_ingested": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect(args.source_zip), sort_keys=True,
                         indent=2, ensure_ascii=False, allow_nan=False))
    except (OSError, HQ100OriginalError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
