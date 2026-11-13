#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline full-member checksum and *one-cell* parity for Eurostat Census 2021 V3.

No network, no background provider API, no GitHub Actions live probe, no raw
source output. Input must be the original *raw deflate bytes of precisely one
ZIP CSV member*, acquired separately only after the versioned access contract
has been reviewed/approved for that operation. Never pass the whole outer ZIP.

The exact V3 member sizes/CRC derive from the original provider central
directory (research-only Neon sample #60); the expected 14-field fingerprint
derives from independently observed private original V3 GeoTIFF cell #63.
No original 14-band population values are embedded in this public repo.

An independent match validates SAME-RELEASE CSV ↔ TIFF value parity ONLY,
not scientific model-input admission or availability of the complete archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib

SOURCE_ID = "eurostat.gisco.census-population-grid.2021"
PROVIDER_ARCHIVE = (
    "https://gisco-services.ec.europa.eu/census/2021/"
    "Eurostat_Census-GRID_2021_V3.zip"
)
CSV_MEMBER = "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.csv"
ZIP_MEMBER_LOCAL_HEADER_OFFSET = 209_230_036
EXPECTED_COMPRESSED_BYTES = 49_110_575
EXPECTED_UNCOMPRESSED_BYTES = 339_625_996
EXPECTED_ZIP_MEMBER_CRC32 = 0x54CDC404
MAX_COMPRESSED_BYTES = 52_428_800
MAX_UNCOMPRESSED_BYTES = 350_000_000
CHUNK = 65_536
MAX_OUTPUT_PER_CHUNK = 2_097_152
MAX_ROW_BYTES = 1024
MAX_ROWS = 10_000_000
TARGET_GRID_ID = "CRS3035RES1000mN5399000E5018000"
TARGET_CNTR_ID = "NO"
TIFF_PIXEL_SAMPLE_ID = 63
TIFF_RANGE_SHA256 = "80238bea7841928b220fbf61c980bafd61290f4bf2214a997686441593c09155"
# sha256 of comma-joined decimal int values in the fixed 14-band order below.
# Computed in private research Neon from sample #63; not source data bytes.
EXPECTED_TIFF_PIXEL_14_BAND_SHA256 = (
    "206185ef8953f67e5c8516a8b9d95b2e66907b28b5e5f1a4d98836e913ac7ec8"
)
HEADER = (
    "GRD_ID,T,M,F,Y_LT15,Y_1564,Y_GE65,EMP,NAT,EU_OTH,OTH,"
    "SAME,CHG_IN,CHG_OUT,LAND_SURFACE,POPULATED,CNTR_ID"
).split(",")
BANDS = (
    "T", "M", "F", "Y_LT15", "Y_1564", "Y_GE65", "EMP",
    "NAT", "EU_OTH", "OTH", "SAME", "CHG_IN", "CHG_OUT", "POPULATED"
)
BAND_INDICES = tuple(HEADER.index(x) for x in BANDS)


class CSVParityBlocked(ValueError):
    pass


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise CSVParityBlocked(reason)


def _int_field(data: bytes) -> str:
    _require(re.fullmatch(rb"-?[0-9]{1,12}", data) is not None,
             "source cell contains noninteger or oversized band value")
    number = int(data)
    _require(number >= 0 or number in (-8888, -9999),
             "unexpected census negative value or disclosure sentinel")
    return str(number)


def verify_original_zip_local_header(
    raw: bytes,
    *,
    expected_member_name: str = CSV_MEMBER,
    expected_compressed_bytes: int = EXPECTED_COMPRESSED_BYTES,
    expected_uncompressed_bytes: int = EXPECTED_UNCOMPRESSED_BYTES,
    expected_crc32: int = EXPECTED_ZIP_MEMBER_CRC32,
    expected_local_header_offset: int = ZIP_MEMBER_LOCAL_HEADER_OFFSET,
) -> dict:
    """Check exact V3 original CSV member header, never an arbitrary ZIP entry.

    The required first 30+filename+extra bytes must have been separately
    acquired from the documented ORIGINAL provider ZIP at the fixed offset,
    after approval of that operation. No network access is performed here.
    """
    _require(isinstance(raw, bytes) and 30 <= len(raw) <= 512,
             "original ZIP local header must be 30..512 bounded bytes")
    _require(expected_member_name == CSV_MEMBER,
             "ZIP member identity must remain exact official Eurostat V3 CSV")
    _require(isinstance(expected_local_header_offset, int)
             and 0 <= expected_local_header_offset < 1_000_000_000,
             "invalid ZIP original local header offset")
    _require(isinstance(expected_compressed_bytes, int)
             and 1 <= expected_compressed_bytes <= MAX_COMPRESSED_BYTES
             and isinstance(expected_uncompressed_bytes, int)
             and 1 <= expected_uncompressed_bytes <= MAX_UNCOMPRESSED_BYTES,
             "source ZIP member sizes outside bounded contract")
    _require(isinstance(expected_crc32, int) and 0 <= expected_crc32 <= 0xffffffff,
             "invalid source ZIP CRC32")
    (signature, version, flags, method, mtime, mdate, crc,
     compressed, plain, filename_size, extra_size) = struct.unpack_from(
        "<IHHHHHIIIHH", raw, 0
    )
    _require(signature == 0x04034B50, "original source ZIP local header signature changed")
    _require(version == 20 and method == 8,
             "expected classic V3 ZIP DEFLATE member (version 20)")
    _require(flags & ~(0x0808) == 0, "encrypted or unsupported ZIP general-purpose flags")
    _require(0 < filename_size <= 160 and 0 <= extra_size <= 256,
             "original ZIP header filename/extra size outside bounds")
    _require(len(raw) == 30 + filename_size + extra_size,
             "original ZIP local header byte count mismatch")
    try:
        name = raw[30:30 + filename_size].decode("utf-8")
    except UnicodeError as exc:
        raise CSVParityBlocked("original ZIP member name invalid UTF-8") from exc
    _require(name == expected_member_name, "wrong original CSV archive member name")
    descriptor = bool(flags & 0x0008)
    if descriptor:
        _require(crc in (0, expected_crc32),
                 "original ZIP local header CRC conflicts with central directory")
        _require(compressed in (0, expected_compressed_bytes)
                 and plain in (0, expected_uncompressed_bytes),
                 "original ZIP local header sizes conflict with central directory")
    else:
        _require(crc == expected_crc32
                 and compressed == expected_compressed_bytes
                 and plain == expected_uncompressed_bytes,
                 "original ZIP local header differs from original central directory")
    return {
        "original_source_archive": PROVIDER_ARCHIVE,
        "original_member": expected_member_name,
        "local_header_offset": expected_local_header_offset,
        "local_header_bytes": len(raw),
        "absolute_compressed_payload_offset": expected_local_header_offset + len(raw),
        "header_sha256": hashlib.sha256(raw).hexdigest(),
        "general_purpose_flags": flags,
        "uses_zip_data_descriptor": descriptor,
        "original_member_crc32_match": True,
        "original_provider_bytes_written_by_runner": False,
        "model_input_approved": False,
    }


def verify_csv_deflate_member(
    stream,
    *,
    expected_compressed_bytes: int = EXPECTED_COMPRESSED_BYTES,
    expected_uncompressed_bytes: int = EXPECTED_UNCOMPRESSED_BYTES,
    expected_crc32: int = EXPECTED_ZIP_MEMBER_CRC32,
    expected_cell_sha256: str = EXPECTED_TIFF_PIXEL_14_BAND_SHA256,
    target_grid_id: str = TARGET_GRID_ID,
    target_country: str = TARGET_CNTR_ID,
) -> dict:
    """One pass, O(chunk + one CSV line) RAM; no original data returned."""
    _require(isinstance(expected_compressed_bytes, int)
             and 1 <= expected_compressed_bytes <= MAX_COMPRESSED_BYTES,
             "unapproved compressed source size")
    _require(isinstance(expected_uncompressed_bytes, int)
             and 1 <= expected_uncompressed_bytes <= MAX_UNCOMPRESSED_BYTES,
             "unapproved uncompressed source size")
    _require(isinstance(expected_crc32, int) and 0 <= expected_crc32 <= 0xFFFFFFFF,
             "invalid central-directory CRC32")
    _require(re.fullmatch(r"[0-9a-f]{64}", expected_cell_sha256 or "") is not None,
             "untrusted original TIFF 14-band SHA-256 fingerprint")
    _require(re.fullmatch(r"CRS3035RES1000mN[0-9]+E[0-9]+", target_grid_id or "")
             is not None, "unreviewed raster cell identity")
    _require(re.fullmatch(r"[A-Z]{2}", target_country or "") is not None,
             "unreviewed country code")
    expected_grid_bytes = target_grid_id.encode("ascii")
    country_bytes = target_country.encode("ascii")
    reader = zlib.decompressobj(wbits=-15)
    compressed_digest = hashlib.sha256()
    member_digest = hashlib.sha256()
    uncompressed_crc = 0
    consumed_compressed = 0
    consumed_uncompressed = 0
    csv_rows = 0
    header_read = False
    matched_rows = 0
    same_release_parity = False
    pending = b""

    def visit_line(line: bytes) -> None:
        nonlocal header_read, csv_rows, matched_rows, same_release_parity
        line = line.rstrip(b"\r")
        _require(len(line) <= MAX_ROW_BYTES, "original CSV row oversized")
        try:
            fields = line.decode("ascii").split(",")
        except UnicodeError as exc:
            raise CSVParityBlocked("original CSV is not plain ASCII") from exc
        if not header_read:
            _require(fields == HEADER, "incorrect original V3 CSV header/column order")
            header_read = True
            return
        _require(len(fields) == len(HEADER), "wrong original source column count")
        csv_rows += 1
        _require(csv_rows <= MAX_ROWS, "original source row count guard")
        # All millions of other rows remain in memory only until this function returns.
        if fields[0] != target_grid_id:
            return
        _require(fields[HEADER.index("CNTR_ID")] == target_country,
                 "target grid has a different official reporting country")
        matched_rows += 1
        _require(matched_rows == 1, "duplicate original V3 target census cell")
        ordered = [_int_field(fields[i].encode("ascii")) for i in BAND_INDICES]
        parity_sha = hashlib.sha256(",".join(ordered).encode("ascii")).hexdigest()
        _require(parity_sha == expected_cell_sha256,
                 "original V3 CSV 14 bands disagree with original V3 TIFF pixel")
        same_release_parity = True

    def consume_inflated(chunk: bytes) -> None:
        nonlocal uncompressed_crc, consumed_uncompressed, pending
        consumed_uncompressed += len(chunk)
        _require(consumed_uncompressed <= MAX_UNCOMPRESSED_BYTES,
                 "uncompressed source exceeded absolute guard")
        _require(consumed_uncompressed <= expected_uncompressed_bytes,
                 "uncompressed source exceeded central-directory bound")
        member_digest.update(chunk)
        uncompressed_crc = zlib.crc32(chunk, uncompressed_crc)
        joined = pending + chunk
        parts = joined.split(b"\n")
        pending = parts.pop()
        _require(len(pending) <= MAX_ROW_BYTES, "original CSV line exceeded guard")
        for line in parts:
            visit_line(line)

    while consumed_compressed < expected_compressed_bytes:
        want = min(CHUNK, expected_compressed_bytes - consumed_compressed)
        block = stream.read(want)
        _require(isinstance(block, bytes) and len(block) == want,
                 "original compressed member incomplete")
        compressed_digest.update(block)
        consumed_compressed += len(block)
        # A legitimate highly compressible census CSV block may inflate past
        # MAX_OUTPUT_PER_CHUNK. Stream the DEFLATE tail through repeated bounded
        # outputs rather than rejecting valid data or allocating unbounded RAM.
        tail = block
        while tail:
            try:
                plain = reader.decompress(tail, MAX_OUTPUT_PER_CHUNK)
            except zlib.error as exc:
                raise CSVParityBlocked("original raw deflate data invalid") from exc
            remainder = reader.unconsumed_tail
            _require(not reader.unused_data, "unexpected extra ZIP member data")
            _require(bool(plain) or len(remainder) < len(tail),
                     "original compressed member inflater made no progress")
            consume_inflated(plain)
            tail = remainder
    try:
        consume_inflated(reader.flush())
    except zlib.error as exc:
        raise CSVParityBlocked("original CSV inflater flush failed") from exc
    _require(reader.eof and not reader.unused_data and not reader.unconsumed_tail,
             "original ZIP CSV deflate stream incomplete")
    _require(consumed_uncompressed == expected_uncompressed_bytes,
             "original CSV uncompressed length mismatch")
    _require(uncompressed_crc == expected_crc32, "original member CRC32 mismatch")
    # Accept a final line without LF, but never an empty final record.
    if pending:
        visit_line(pending)
    _require(header_read and csv_rows > 0, "no original CSV records")
    _require(matched_rows == 1 and same_release_parity,
             "target official census grid row not found in complete V3 CSV")
    return {
        "source_id": SOURCE_ID,
        "source_release": "Eurostat_Census-GRID_2021_V3",
        "original_member_name": CSV_MEMBER,
        "member_local_header_offset_from_original_zip": ZIP_MEMBER_LOCAL_HEADER_OFFSET,
        "member_compressed_bytes": consumed_compressed,
        "member_uncompressed_bytes": consumed_uncompressed,
        "compressed_member_sha256": compressed_digest.hexdigest(),
        "uncompressed_original_csv_sha256": member_digest.hexdigest(),
        "original_zip_member_crc32_matches": True,
        "original_csv_row_count": csv_rows,
        "source_cell_id": target_grid_id,
        "source_country": target_country,
        "target_row_match_count": matched_rows,
        "source_same_release_csv_tiff_14_band_parity": True,
        "original_tiff_sample_reference": TIFF_PIXEL_SAMPLE_ID,
        "original_tiff_range_sha256": TIFF_RANGE_SHA256,
        "full_566mb_source_zip_sha256_verified": False,
        "raw_source_values_in_output": False,
        "original_source_bytes_persisted": False,
        "legal_automation_review_cleared_by_this_script": False,
        "cat_model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-deflate-member", required=True, type=Path,
                        help="pre-approved original ZIP CSV *compressed member* only")
    parser.add_argument("--original-local-header", required=True, type=Path,
                        help="separately authenticated exact <=512-byte ZIP local header at the fixed provider offset")
    args = parser.parse_args(argv)
    try:
        file = args.raw_deflate_member
        header_path = args.original_local_header
        if (header_path.is_symlink() or not header_path.is_file()
                or not 30 <= header_path.stat().st_size <= 512):
            raise CSVParityBlocked("original ZIP member local header missing or outside bound")
        original_header = verify_original_zip_local_header(header_path.read_bytes())
        if file.is_symlink() or not file.is_file() or file.stat().st_size != EXPECTED_COMPRESSED_BYTES:
            raise CSVParityBlocked("input must be exact pre-acquired CSV member, not ZIP")
        with file.open("rb") as stream:
            result = verify_csv_deflate_member(stream)
        result["original_zip_local_header"] = original_header
        print(json.dumps(result,sort_keys=True))
        return 0
    except (CSVParityBlocked,OSError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc),
                          "cat_model_input_approved":False}),file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
