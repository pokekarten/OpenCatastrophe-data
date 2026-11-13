#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original Eurostat Census Grid 2021 V3 *complete ZIP* parity gate.

Provides a safer route for a separately authorized, locally supplied V3 ZIP:
do not manually carve raw CSV DEFLATE bytes out of the provider archive.

Exact V3 ZIP identity: 566,125,577 bytes, nine frozen member paths, and exact
CSV entry CRC32/offset/size from independently inspected original provider
central-directory metadata (private Neon sample #60).

No web/network, no provider bytes committed, no original CSV values printed.
The complete local ZIP's SHA is computed as a research receipt, NOT asserted
to be independently provider-signed or release-authenticated. Scientific CAT
admission and acquisition rights remain FALSE even after matching one cell.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile

from research_runners.eurostat_census_v3_full_csv_member_parity_v0 import (
    CSV_MEMBER,
    CSVParityBlocked,
    EXPECTED_COMPRESSED_BYTES,
    EXPECTED_UNCOMPRESSED_BYTES,
    EXPECTED_ZIP_MEMBER_CRC32,
    EXPECTED_TIFF_PIXEL_14_BAND_SHA256,
    ZIP_MEMBER_LOCAL_HEADER_OFFSET,
    verify_csv_deflate_member,
    verify_original_zip_local_header,
)

ORIGINAL_ZIP_BYTES = 566_125_577
MAX_ZIP_BYTES = 600_000_000
ZIP_NAMES = (
    "Eurostat_Census-GRID_2021_V3/",
    "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_country.csv.zip",
    "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_LAND_SURFACE_V3.tiff",
    CSV_MEMBER,
    "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.gpkg",
    "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.parquet",
    "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.tiff",
    "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3_SDMX_Metadata.zip",
    "Eurostat_Census-GRID_2021_V3/read.me",
)
HASH_CHUNK = 1_048_576


def _require(value: bool, reason: str) -> None:
    if not value:
        raise CSVParityBlocked(reason)


def _digest_file(file: Path) -> str:
    h = hashlib.sha256()
    with file.open("rb") as handle:
        while block := handle.read(HASH_CHUNK):
            h.update(block)
    return h.hexdigest()


def verify_complete_local_v3_zip(
    local_zip: Path,
    *,
    expected_zip_bytes: int = ORIGINAL_ZIP_BYTES,
    expected_member_names: tuple[str, ...] = ZIP_NAMES,
    expected_csv_header_offset: int = ZIP_MEMBER_LOCAL_HEADER_OFFSET,
    expected_csv_compressed_bytes: int = EXPECTED_COMPRESSED_BYTES,
    expected_csv_uncompressed_bytes: int = EXPECTED_UNCOMPRESSED_BYTES,
    expected_csv_crc32: int = EXPECTED_ZIP_MEMBER_CRC32,
    expected_pixel_sha256: str = EXPECTED_TIFF_PIXEL_14_BAND_SHA256,
) -> dict:
    """Process a preapproved original source ZIP read-only; synthetic overrides in tests.

    Acceptance is limited to archive identity, whole-file digest, one CSV
    member's structural/CRC integrity and matching ONE TIFF cell fingerprint.
    It is NOT evidence of independently signed provider-origin authenticity.
    """
    _require(isinstance(local_zip, Path) and not local_zip.is_symlink()
             and local_zip.is_file(), "existing regular non-symlink local ZIP required")
    _require(isinstance(expected_zip_bytes, int)
             and 100 <= expected_zip_bytes <= MAX_ZIP_BYTES
             and local_zip.stat().st_size == expected_zip_bytes,
             "complete original ZIP source file size mismatch")
    _require(isinstance(expected_member_names, tuple)
             and len(expected_member_names) >= 1
             and CSV_MEMBER in expected_member_names
             and len(set(expected_member_names)) == len(expected_member_names),
             "invalid original ZIP central-directory member contract")

    archive_sha = _digest_file(local_zip)
    try:
        with ZipFile(local_zip, "r") as archive:
            infos = archive.infolist()
            names = tuple(info.filename for info in infos)
            _require(archive.comment == b"", "original ZIP comment is unexpected")
            _require(len(infos) == len(expected_member_names)
                     and len(set(names)) == len(names)
                     and set(names) == set(expected_member_names),
                     "ZIP central directory member count or exact paths changed")
            for item in infos:
                _require(not item.flag_bits & 0x0001,
                         "encrypted ZIP member not accepted")
                _require(item.compress_type in (ZIP_DEFLATED, ZIP_STORED),
                         "unapproved original ZIP compression method")
                _require(not item.filename.startswith("/")
                         and "\\" not in item.filename
                         and ".." not in item.filename.split("/"),
                         "unsafe original ZIP path")
            member = archive.getinfo(CSV_MEMBER)
            _require(not member.is_dir() and member.compress_type == ZIP_DEFLATED,
                     "V3 CSV is not the exact raw ZIP DEFLATE member")
            _require(member.header_offset == expected_csv_header_offset
                     and member.compress_size == expected_csv_compressed_bytes
                     and member.file_size == expected_csv_uncompressed_bytes
                     and member.CRC == expected_csv_crc32,
                     "original central directory CSV offsets, sizes or CRC32 changed")
            _require(not member.flag_bits & 1, "CSV member encrypted")
    except (BadZipFile, OSError, ValueError, KeyError) as exc:
        raise CSVParityBlocked("original ZIP central directory is invalid") from exc

    with local_zip.open("rb") as handle:
        handle.seek(expected_csv_header_offset)
        first = handle.read(30)
        _require(len(first) == 30, "original ZIP CSV local header truncated")
        _require(first[:4] == b"PK\x03\x04", "original ZIP CSV local signature wrong")
        name_len, extra_len = struct.unpack_from("<HH", first, 26)
        _require(0 < name_len <= 160 and extra_len <= 256,
                 "original ZIP CSV local member fields outside bounds")
        raw_header = first + handle.read(name_len + extra_len)
        header = verify_original_zip_local_header(
            raw_header,
            expected_compressed_bytes=expected_csv_compressed_bytes,
            expected_uncompressed_bytes=expected_csv_uncompressed_bytes,
            expected_crc32=expected_csv_crc32,
            expected_local_header_offset=expected_csv_header_offset,
        )
        payload_offset = header["absolute_compressed_payload_offset"]
        _require(payload_offset + expected_csv_compressed_bytes <= expected_zip_bytes,
                 "ZIP member payload outside original provider archive")
        handle.seek(payload_offset)
        result = verify_csv_deflate_member(
            handle,
            expected_compressed_bytes=expected_csv_compressed_bytes,
            expected_uncompressed_bytes=expected_csv_uncompressed_bytes,
            expected_crc32=expected_csv_crc32,
            expected_cell_sha256=expected_pixel_sha256,
        )
        # Source ZIP data descriptors may be absent or present. When present,
        # both the descriptor CRC and file lengths must agree with central dir.
        if header["uses_zip_data_descriptor"]:
            trailer = handle.read(16)
            _require(len(trailer) == 16, "ZIP descriptor missing or truncated")
            if trailer[:4] == b"PK\x07\x08":
                crc, compressed, plain = struct.unpack("<III", trailer[4:16])
            else:
                # No-signature 12B descriptor; other 4B belong to next member.
                crc, compressed, plain = struct.unpack("<III", trailer[:12])
            _require((crc, compressed, plain) ==
                     (expected_csv_crc32, expected_csv_compressed_bytes,
                      expected_csv_uncompressed_bytes),
                     "ZIP data descriptor mismatches central directory")
    result.update({
        "entire_local_zip_sha256_computed": archive_sha,
        "entire_local_zip_source_bytes": expected_zip_bytes,
        "source_archive_member_count": len(expected_member_names),
        "local_zip_header_sha256": header["header_sha256"],
        "local_zip_csv_payload_offset": header["absolute_compressed_payload_offset"],
        "provider_origin_independently_authenticated": False,
        "provider_acquisition_rights_verified": False,
        "original_bytes_committed_to_public_git": False,
        "commercial_insurance_model_input_admitted": False,
    })
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preapproved-v3-zip", required=True, type=Path,
                        help="local 566125577-byte V3 provider ZIP obtained only after access review")
    args = parser.parse_args(argv)
    try:
        result = verify_complete_local_v3_zip(args.preapproved_v3_zip)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (CSVParityBlocked, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "commercial_insurance_model_input_admitted": False}),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
