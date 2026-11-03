#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read bounded GeoTIFF magic/first IFD from original official SRGK ZIP member.

Five source-locked HTTP 206 Range GETs per ZIP: EOCD tail, ZIP central
directory, 30-byte local header, local filename, compressed DEFLATE prefix.
No full ZIP, no complete TIFF, no raster-cell interpretation, no database writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import struct
import sys
import zlib

from research_runners import berlin_srgk_depth_zip_central_range_v0 as original

PROFILE = "berlin-srgk-original-tiff-first-ifd-bounded-v0"
MAX_LOCAL_META = 4096
MAX_COMPRESSED_PREFIX = 65536
MAX_DECOMPRESSED_PREFIX = 131072
MAX_IFD_ENTRIES = 512
EXPECTED = {
    original.SOURCE_BASE + "wasserstand_seltenes_ereignis.zip": {
        "directory_sha256": "9a593d9d3e39c21ee99c34d13550c16ae9c0d8c3390c653dfb566f49f00be7b3",
        "filename": "wasserstand_T50_1.tif", "compressed": 132689170, "uncompressed": 167298853,
    },
    original.SOURCE_BASE + "wasserstand_aussergewoehnliches_ereignis.zip": {
        "directory_sha256": "95083ca9e30236032ec995571d9436be82030f827c0de0fbbbaf91d80974b01b",
        "filename": "wasserstand_T100.tif", "compressed": 136928037, "uncompressed": 171875427,
    },
    original.SOURCE_BASE + "wasserstand_extrem.zip": {
        "directory_sha256": "cae92cb9db21fef568eb5f66ca5c5a034ffa6c1190a95747eba7098fe09fbe71",
        "filename": "Wasserstand_TExtrem_1.tif", "compressed": 93562450, "uncompressed": 115931327,
    },
}


class TiffPrefixBlocked(ValueError):
    """Original ZIP / first TIFF metadata incompatible with approved source."""


def tiff_first_ifd(prefix: bytes) -> dict:
    if not isinstance(prefix, bytes) or len(prefix) < 8 or len(prefix) > MAX_DECOMPRESSED_PREFIX:
        raise TiffPrefixBlocked("bounded TIFF member prefix missing")
    if prefix[:2] not in (b"II", b"MM"):
        raise TiffPrefixBlocked("source member not a TIFF endian signature")
    endian = "<" if prefix[:2] == b"II" else ">"
    magic = struct.unpack_from(endian + "H", prefix, 2)[0]
    if magic != 42:
        # Do not infer GTiff semantics from a BigTIFF or unsupported variant.
        raise TiffPrefixBlocked("original TIFF is not supported classic TIFF magic 42")
    offset = struct.unpack_from(endian + "I", prefix, 4)[0]
    out = {
        "tiff_classic_header_verified": True,
        "tiff_byte_order": "little" if endian == "<" else "big",
        "first_ifd_offset": offset,
        "first_ifd_fully_in_prefix": False,
        "width_from_first_ifd": None,
        "height_from_first_ifd": None,
        "first_ifd_entry_count": None,
        "geokey_directory_tag_present": False,
        "model_pixel_scale_tag_present": False,
        "model_tiepoint_tag_present": False,
        "gdal_nodata_ascii_tag_present": False,
        "original_epsg_code_or_raster_extent_verified": False,
        "original_water_depth_unit_scale_nodata_semantics_verified": False,
    }
    if offset > MAX_DECOMPRESSED_PREFIX or offset + 2 > len(prefix):
        return out
    count = struct.unpack_from(endian + "H", prefix, offset)[0]
    if not 0 < count <= MAX_IFD_ENTRIES:
        raise TiffPrefixBlocked("empty or unbounded original first TIFF IFD")
    end = offset + 2 + 12 * count + 4
    if end > len(prefix):
        return out
    tags = {}
    for i in range(count):
        off = offset + 2 + i * 12
        tag, kind, length = struct.unpack_from(endian + "HHI", prefix, off)
        raw_inline = prefix[off+8:off+12]
        if tag in tags:
            raise TiffPrefixBlocked("duplicate TIFF IFD tag")
        tags[tag] = (kind, length, raw_inline)
    for code, label in ((256, "width_from_first_ifd"), (257, "height_from_first_ifd")):
        if code in tags:
            kind, length, inline = tags[code]
            if kind not in (3, 4) or length != 1:
                raise TiffPrefixBlocked("non-inline or unexpected TIFF width/height")
            value = struct.unpack(endian + ("H" if kind == 3 else "I"),
                                  inline[:2] if kind == 3 else inline)[0]
            if not 0 < value <= 200000:
                raise TiffPrefixBlocked("unreasonable original TIFF dimension")
            out[label] = value
    out.update({
        "first_ifd_fully_in_prefix": True,
        "first_ifd_entry_count": count,
        "geokey_directory_tag_present": 34735 in tags,
        "model_pixel_scale_tag_present": 33550 in tags,
        "model_tiepoint_tag_present": 33922 in tags,
        "gdal_nodata_ascii_tag_present": 42113 in tags,
    })
    return out


def inspect_one(url: str, opener=original._open) -> dict:
    if url not in EXPECTED or url not in original.SOURCE_URLS:
        raise TiffPrefixBlocked("unreviewed source ZIP identity")
    expected = EXPECTED[url]
    scenario, size = original.SOURCE_URLS[url]
    tail = original.fetch_range(url, size - original.TAIL, size - 1, opener)
    cd_offset, cd_size, members = original.locate_eocd(tail, size)
    cd = original.fetch_range(url, cd_offset, cd_offset + cd_size - 1, opener)
    if sha256(cd).hexdigest() != expected["directory_sha256"]:
        raise TiffPrefixBlocked("pinned original central-directory SHA256 drift")
    parsed = original.parse_directory(cd, members)
    if members != 1 or len(parsed["bounded_tiff_name_samples"]) != 1:
        raise TiffPrefixBlocked("exact original one-TIFF ZIP structure changed")
    observed = parsed["bounded_tiff_name_samples"][0]
    if (observed["name"] != expected["filename"]
        or observed["compressed_size_bytes"] != expected["compressed"]
        or observed["uncompressed_size_bytes"] != expected["uncompressed"]):
        raise TiffPrefixBlocked("pinned original TIFF name or sizes drift")
    fields = struct.unpack_from("<4s6H3I5H2I", cd)
    (_, _, _, flags, method, _, _, crc, compressed, uncompressed,
     nlen, elen, comment, disk, _, _, local_offset) = fields
    if (method != 8 or flags & 1 or disk != 0 or local_offset + 30 >= cd_offset
            or compressed != expected["compressed"] or uncompressed != expected["uncompressed"]):
        raise TiffPrefixBlocked("unexpected original compression / member location")
    header = original.fetch_range(url, local_offset, local_offset + 29, opener)
    (magic, version, local_flags, local_method, _, _,
     local_crc, local_compressed, local_uncompressed,
     local_nlen, local_elen) = struct.unpack("<4s5H3I2H", header)
    if magic != b"PK\x03\x04" or version > 63 or local_flags != flags or local_method != 8:
        raise TiffPrefixBlocked("original ZIP local header mismatch")
    if (local_nlen != nlen or not 0 < local_nlen + local_elen <= MAX_LOCAL_META):
        raise TiffPrefixBlocked("unbounded or inconsistent local ZIP name/extra")
    if not flags & (1 << 3) and (
        local_crc != crc or local_compressed != compressed or local_uncompressed != uncompressed
    ):
        raise TiffPrefixBlocked("local ZIP CRC/size does not match pinned central directory")
    local_meta = original.fetch_range(
        url, local_offset + 30, local_offset + 29 + local_nlen + local_elen, opener
    )
    try:
        member_name = local_meta[:local_nlen].decode(
            "utf-8" if flags & (1 << 11) else "cp437"
        )
    except UnicodeError as exc:
        raise TiffPrefixBlocked("invalid original member name encoding") from exc
    if member_name != expected["filename"]:
        raise TiffPrefixBlocked("local ZIP name does not match original central index")
    start = local_offset + 30 + local_nlen + local_elen
    if start + compressed > cd_offset:
        raise TiffPrefixBlocked("original compressed member exceeds central index")
    comp_count = min(MAX_COMPRESSED_PREFIX, compressed)
    payload = original.fetch_range(url, start, start + comp_count - 1, opener)
    try:
        inflation = zlib.decompressobj(-zlib.MAX_WBITS)
        prefix = inflation.decompress(payload, MAX_DECOMPRESSED_PREFIX)
    except zlib.error as exc:
        raise TiffPrefixBlocked("invalid original ZIP DEFLATE prefix") from exc
    # The maximum decompressed prefix can include source data beyond the TIFF
    # header; never print or persist these bytes and do NOT interpret pixels.
    result = tiff_first_ifd(prefix)
    return {
        "scenario": scenario,
        "original_archive_size_bytes": size,
        "original_central_sha256": expected["directory_sha256"],
        "original_member_name": expected["filename"],
        "original_member_compressed_bytes": compressed,
        "original_member_uncompressed_bytes": uncompressed,
        "compressed_member_prefix_bytes_read": len(payload),
        "bounded_decompressed_prefix_bytes_in_memory_only": len(prefix),
        "source_range_requests": 5,
        "source_original_member_bytes_or_raster_cells_persisted": False,
        "any_original_pixel_values_interpreted": False,
        **result,
    }


def probe(*, opener=original._open, clock=lambda: datetime.now(timezone.utc)) -> dict:
    rows = [inspect_one(url, opener) for url in EXPECTED]
    timestamp = clock()
    if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
        raise TiffPrefixBlocked("timestamp lacks timezone")
    return {
        "profile": PROFILE,
        "original_source_checked_utc": timestamp.astimezone(timezone.utc).isoformat(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_scenarios": rows,
        "source_total_bounded_range_requests": 15,
        "complete_zip_or_tiff_downloaded": False,
        "raster_pixel_extraction_or_insurer_loss_computed": False,
        "source_raster_crs_extent_depth_unit_verified": False,
        "second_pilot_raster_coverage_proven": False,
        "cat_model_input_approved": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for reviewed bounded TIFF prefix original requests")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (TiffPrefixBlocked, original.ZipIndexBlocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
