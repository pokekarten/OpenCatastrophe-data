#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""OFFLINE verification of a bounded original gzip/TAR/NetCDF4 signature.

DWD RADKLIM RW 2017.002: only corrected 2021 supplement is eligible for
header QA. No HTTP access, original raster values, full-file digest,
scientific calibration, licence promotion, or CAT model admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zlib

SOURCE_ID = "dwd.radklim.rw.v2017.002"
CORRECTED_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/grids_germany/"
    "hourly/radolan/reproc/2017_002/netCDF/supplement/"
    "RW2017.002_2021_netcdf_supplement.tar.gz"
)
UNSAFE_ORIGINAL_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/grids_germany/"
    "hourly/radolan/reproc/2017_002/netCDF/2021/"
    "RW2017.002_2021_netcdf.tar.gz"
)
FROZEN_PREFIX_LENGTH = 2048
# Reviewed original provider bytes=0-2047 from research 2026-11-12;
# this is NOT an archive, TAR-member, or full-NetCDF SHA.
FROZEN_PREFIX_SHA256 = "741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867"
FIRST_MEMBER = "2021/RW_2017.002_202107.nc"
FIRST_MEMBER_BYTES = 91_356_907
NETCDF4_MAGIC = b"\x89HDF\r\n\x1a\n"
REQUIRED_DECOMPRESSED_PREFIX = 512 * 2 + len(NETCDF4_MAGIC)
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class DWD2021PrefixBlocked(ValueError):
    """Exact corrected source identity, archive metadata, or prefix failed."""


def _tar_member(header: bytes) -> tuple[str, int, bytes]:
    if len(header) != 512:
        raise DWD2021PrefixBlocked("incomplete TAR header")
    if header[257:263] not in (b"ustar\x00", b"ustar "):
        raise DWD2021PrefixBlocked("TAR USTAR signature missing")
    try:
        name = header[:100].split(b"\0", 1)[0].decode("ascii")
        size_token = header[124:136].strip(b"\x00 ")
        check_token = header[148:156].strip(b"\x00 ")
        if not size_token or not check_token or any(c not in b"01234567" for c in size_token + check_token):
            raise ValueError("invalid TAR octal header")
        size = int(size_token, 8)
        claimed = int(check_token, 8)
    except (UnicodeError, ValueError) as exc:
        raise DWD2021PrefixBlocked("TAR header values invalid") from exc
    # POSIX TAR calculates checksum with eight ASCII-space checksum bytes.
    actual = sum(header[:148]) + 8 * 32 + sum(header[156:])
    if claimed != actual:
        raise DWD2021PrefixBlocked("TAR header checksum mismatch")
    return name, size, header[156:157]


def inspect_corrected_2021_prefix(
    body: bytes, *, source_url: str, expected_range_sha256: str,
) -> dict:
    """Check exact original *compressed range*, not an entire archive/member.

    The caller supplies externally acquired bytes. The digest here proves only
    that input matches the supplied expected range SHA, not provenance by itself.
    The original-source wrapper additionally pins the previously observed SHA.
    """
    if source_url != CORRECTED_URL:
        raise DWD2021PrefixBlocked("wrong/unreviewed source URL: incorrect 2021 original prohibited")
    if type(body) is not bytes or not 0 < len(body) <= FROZEN_PREFIX_LENGTH:
        raise DWD2021PrefixBlocked("missing or oversized source range")
    if not isinstance(expected_range_sha256, str) or not _SHA.fullmatch(expected_range_sha256):
        raise DWD2021PrefixBlocked("strict expected range SHA-256 required")
    digest = hashlib.sha256(body).hexdigest()
    if digest != expected_range_sha256:
        raise DWD2021PrefixBlocked("original compressed range SHA-256 mismatch")
    if not body.startswith(b"\x1f\x8b\x08"):
        raise DWD2021PrefixBlocked("original compressed bytes are not gzip")
    try:
        stream = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
        # Bounded prefix only: never materialize the 820MB annual TAR or
        # let a short highly-compressible input expand beyond 1,032 bytes.
        decoded = stream.decompress(body, REQUIRED_DECOMPRESSED_PREFIX)
    except zlib.error as exc:
        raise DWD2021PrefixBlocked("invalid gzip compressed range") from exc
    if len(decoded) < REQUIRED_DECOMPRESSED_PREFIX:
        raise DWD2021PrefixBlocked("compressed range lacks two TAR headers and NetCDF signature")
    first_name, first_bytes, first_type = _tar_member(decoded[:512])
    if (first_name != "2021/" or first_bytes != 0 or first_type != b"5"):
        raise DWD2021PrefixBlocked("first TAR directory identity drift")
    member_name, member_bytes, member_type = _tar_member(decoded[512:1024])
    if (member_name != FIRST_MEMBER or member_bytes != FIRST_MEMBER_BYTES
            or member_type not in (b"0", b"\x00")):
        raise DWD2021PrefixBlocked("corrected TAR first NetCDF member identity drift")
    if decoded[1024:1032] != NETCDF4_MAGIC:
        raise DWD2021PrefixBlocked("native NetCDF4/HDF5 magic missing")
    return {
        "source_id": SOURCE_ID,
        "classification": "OFFLINE_CORRECTED_2021_PREFIX_HEADER_ONLY",
        "product_version": "RW2017.002_2021_netcdf_supplement",
        "original_source_request": "Range: bytes=0-2047",
        "original_prefix_bytes": len(body),
        "original_prefix_sha256": digest,
        "first_month_member": FIRST_MEMBER,
        "first_month_member_declared_bytes": FIRST_MEMBER_BYTES,
        "corrected_2021_archive_url_only": True,
        "native_netcdf4_hdf5_signature_verified": True,
        "full_archive_sha256_verified": False,
        "full_month_netcdf_verified": False,
        "precipitation_values_verified": False,
        "all_2021_months_verified": False,
        "model_input_approved": False,
        "source_bytes_exported": False,
        "provider_request_executed": False,
    }


def inspect_frozen_original_prefix(body: bytes) -> dict:
    """Require a whole exact original 2048-byte range and known SHA-256."""
    if type(body) is not bytes or len(body) != FROZEN_PREFIX_LENGTH:
        raise DWD2021PrefixBlocked("frozen original 2048-byte prefix required")
    return inspect_corrected_2021_prefix(
        body, source_url=CORRECTED_URL,
        expected_range_sha256=FROZEN_PREFIX_SHA256,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True,
                        help="Already acquired private original 2048-byte range file; no download")
    args = parser.parse_args(argv)
    try:
        if (args.path.is_symlink() or not args.path.is_file()
                or args.path.stat().st_size != FROZEN_PREFIX_LENGTH):
            raise DWD2021PrefixBlocked("original private prefix file missing/incorrect size")
        result = inspect_frozen_original_prefix(args.path.read_bytes())
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, DWD2021PrefixBlocked):
        print(json.dumps({"status": "BLOCKED", "source_id": SOURCE_ID,
                          "model_input_approved": False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
