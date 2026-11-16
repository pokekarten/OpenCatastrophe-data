# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only offline LANDFIRE LF2025 FBFM40 CONUS ZIP/GeoTIFF preflight.

Requires a caller-provided, separately authorized local original ZIP with
independently recorded external MD5/SHA256 pins. No remote download, provider
rights approval, pixel reading, public source byte publishing or model admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import zipfile

SOURCE_ID = "us.landfire.fuel-vegetation.2025"
ARCHIVE_NAME = "LF2025_FBFM40_CONUS.zip"
MAX_ARCHIVE_BYTES = 6 * 1024**3
MAX_MEMBER_BYTES = 8 * 1024**3
MAX_MEMBERS = 1024
READ_CHUNK = 1024 * 1024
MD5_HEX = re.compile(r"[a-f0-9]{32}\Z")
SHA256_HEX = re.compile(r"[a-f0-9]{64}\Z")
ROOT = Path(__file__).resolve().parents[1]


class LandfireArchiveError(ValueError):
    """Archive original identity, safety or native science-header gate failed."""


def _file_identity(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)


def _finite_number(v, field):
    if type(v) not in (float, int):
        raise LandfireArchiveError("non-numeric native " + field)
    try:
        n = float(v)
    except (OverflowError, ValueError) as exc:
        raise LandfireArchiveError("unrepresentable native " + field) from exc
    if not math.isfinite(n):
        raise LandfireArchiveError("nonfinite native " + field)
    return n


def screen_native_raster_profile(profile: object) -> dict:
    """Validate only a GDAL-observed TIFF header, never pixel content."""
    keys = {
        "driver", "bands", "dtype", "crs_epsg", "crs_unit_metres", "width", "height",
        "nodata", "a", "b", "c", "d", "e", "f",
    }
    if type(profile) is not dict or set(profile) != keys:
        raise LandfireArchiveError("missing or extra native raster header fields")
    if profile["driver"] != "GTiff" or type(profile["bands"]) is not int or profile["bands"] != 1:
        raise LandfireArchiveError("expected one-band GeoTIFF")
    # -9999 cannot be represented in unsigned 8-bit or 16-bit class rasters.
    if profile["dtype"] not in ("int16", "int32"):
        raise LandfireArchiveError("expected signed integer categorical fuel raster")
    if type(profile["crs_epsg"]) is not int or profile["crs_epsg"] != 5070:
        raise LandfireArchiveError("expected NAD83 / CONUS Albers EPSG:5070")
    if _finite_number(profile["crs_unit_metres"], "CRS unit") != 1.0:
        raise LandfireArchiveError("native raster map unit is not one metre")
    for k in ("width", "height"):
        if type(profile[k]) is not int or not 2 <= profile[k] <= 100_000:
            raise LandfireArchiveError("invalid raster dimension: " + k)
    for k, expected in (("nodata", -9999), ("a", 30), ("e", -30), ("b", 0), ("d", 0)):
        if _finite_number(profile[k], k) != expected:
            raise LandfireArchiveError("native raster nodata/spacing/rotation mismatch: " + k)
    for k in ("c", "f"):
        if abs(_finite_number(profile[k], k)) > 50_000_000:
            raise LandfireArchiveError("implausible native raster projected origin: " + k)
    return {
        "native_header_profile_matches_expected_albers_30m": True,
        "observed_header_epsg": 5070,
        "observed_header_pixel_size_m": 30,
        "observed_header_nodata": -9999,
        "observed_header_width": profile["width"],
        "observed_header_height": profile["height"],
        "observed_header_dtype": profile["dtype"],
        "geographic_extent_within_conus_verified": False,
        "class_values_and_statistics_verified": False,
        "geospatial_published_grid_alignment_verified": False,
        "native_raster_pixel_values_read": False,
        "raster_suitable_for_individual_buildings": False,
    }


def _safe_member_names(zf: zipfile.ZipFile) -> zipfile.ZipInfo:
    members = zf.infolist()
    if not 1 <= len(members) <= MAX_MEMBERS:
        raise LandfireArchiveError("invalid archive entry count")
    seen = set()
    tiffs = []
    total_uncompressed = 0
    for member in members:
        name = member.filename
        if (not isinstance(name, str) or not name or "\\" in name or "\x00" in name or
                name.startswith("/") or ":" in name or any(p in ("", ".", "..") for p in name.rstrip("/").split("/"))):
            raise LandfireArchiveError("unsafe ZIP member pathname")
        identity = name.rstrip("/").lower()
        if identity in seen:
            raise LandfireArchiveError("duplicate ZIP member identity")
        seen.add(identity)
        mode = stat.S_IFMT((member.external_attr >> 16) & 0xFFFF)
        if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise LandfireArchiveError("non-regular or symlinked ZIP member")
        if member.flag_bits & 1 or member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise LandfireArchiveError("encrypted or unsupported ZIP compression")
        if not 0 <= member.file_size <= MAX_MEMBER_BYTES:
            raise LandfireArchiveError("unbounded ZIP member")
        total_uncompressed += member.file_size
        if total_uncompressed > MAX_MEMBER_BYTES:
            raise LandfireArchiveError("unbounded archive expansion")
        if not member.is_dir() and name.lower().endswith((".tif", ".tiff")):
            tiffs.append(member)
    if len(tiffs) != 1 or "fbfm40" not in PurePosixPath(tiffs[0].filename).name.lower():
        raise LandfireArchiveError("expected one unambiguous FBFM40 TIFF in original ZIP")
    if not 8 <= tiffs[0].file_size <= MAX_MEMBER_BYTES:
        raise LandfireArchiveError("empty or unbounded source TIFF")
    return tiffs[0]


def inspect_local_original_zip(path: Path, *, publisher_md5: str,
                               expected_sha256: str, expected_archive_bytes: int) -> dict:
    """Stream and pin exact caller-supplied ZIP before parsing one TIFF header."""
    if (type(publisher_md5) is not str or not MD5_HEX.fullmatch(publisher_md5) or
            type(expected_sha256) is not str or not SHA256_HEX.fullmatch(expected_sha256)):
        raise LandfireArchiveError("both external checksum pins require lowercase exact hex")
    if (type(expected_archive_bytes) is not int or
            not 100 <= expected_archive_bytes <= MAX_ARCHIVE_BYTES):
        raise LandfireArchiveError("invalid bounded expected original ZIP byte size")
    if path.name != ARCHIVE_NAME or path.resolve().is_relative_to(ROOT):
        raise LandfireArchiveError("unexpected original ZIP name or repository-local provider bytes")
    if not hasattr(os, "O_NOFOLLOW"):
        raise LandfireArchiveError("platform lacks safe original-byte nofollow open")
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size != expected_archive_bytes:
            raise LandfireArchiveError("original ZIP is not a bounded regular file of the pinned length")
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        with os.fdopen(os.open(path, flags), "rb") as reader:
            opened = os.fstat(reader.fileno())
            if _file_identity(opened) != _file_identity(before):
                raise LandfireArchiveError("original ZIP identity changed on open")
            md5 = hashlib.md5(usedforsecurity=False)
            sha = hashlib.sha256()
            count = 0
            while True:
                block = reader.read(READ_CHUNK)
                if not block:
                    break
                count += len(block)
                if count > expected_archive_bytes:
                    raise LandfireArchiveError("original ZIP size expanded during hash")
                md5.update(block)
                sha.update(block)
            if (count != expected_archive_bytes or md5.hexdigest() != publisher_md5 or
                    sha.hexdigest() != expected_sha256):
                raise LandfireArchiveError("original ZIP size/MD5/SHA256 do not match supplied pins")
            if _file_identity(os.fstat(reader.fileno())) != _file_identity(before):
                raise LandfireArchiveError("original ZIP was modified during byte verification")
            reader.seek(0)
            with zipfile.ZipFile(reader) as zf:
                member = _safe_member_names(zf)
                tif_sha = hashlib.sha256()
                copied = 0
                with tempfile.TemporaryDirectory(prefix="lf-fbfm40-header-") as scratch:
                    local_tif = Path(scratch) / "source-fbfm40.tif"
                    with zf.open(member, "r") as source, local_tif.open("xb") as sink:
                        while True:
                            data = source.read(READ_CHUNK)
                            if not data:
                                break
                            copied += len(data)
                            if copied > member.file_size or copied > MAX_MEMBER_BYTES:
                                raise LandfireArchiveError("ZIP TIFF uncompressed length exceeded")
                            tif_sha.update(data)
                            sink.write(data)
                    if copied != member.file_size:
                        raise LandfireArchiveError("ZIP TIFF extracted byte count mismatch")
                    try:
                        import rasterio
                    except ImportError as exc:
                        raise LandfireArchiveError("pinned Rasterio/GDAL needed for native TIFF header") from exc
                    try:
                        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="YES", PROJ_NETWORK="OFF"):
                            with rasterio.open(local_tif, "r") as src:
                                crs = src.crs
                                affine = src.transform
                                profile = {
                                    "driver": src.driver, "bands": src.count,
                                    "dtype": src.dtypes[0] if src.count == 1 else None,
                                    "crs_epsg": crs.to_epsg() if crs else None,
                                    "crs_unit_metres": crs.linear_units_factor[1] if crs else None,
                                    "width": src.width, "height": src.height,
                                    "nodata": src.nodata,
                                    "a": affine.a, "b": affine.b, "c": affine.c,
                                    "d": affine.d, "e": affine.e, "f": affine.f,
                                }
                                header = screen_native_raster_profile(profile)
                    except (ValueError, TypeError, RuntimeError, OSError, IndexError, AttributeError) as exc:
                        if isinstance(exc, LandfireArchiveError):
                            raise
                        raise LandfireArchiveError("invalid or unreviewed native TIFF header") from exc
            if (_file_identity(os.fstat(reader.fileno())) != _file_identity(before) or
                    _file_identity(path.lstat()) != _file_identity(before)):
                raise LandfireArchiveError("source ZIP changed during ZIP/TIFF inspection")
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, EOFError) as exc:
        raise LandfireArchiveError("cannot safely read caller-supplied original ZIP") from exc
    return {
        "source_id": SOURCE_ID,
        "product_identity": "LF2025:FBFM40:CONUS:annual_nonseasonal",
        "original_zip_filename": ARCHIVE_NAME,
        "original_zip_bytes": count,
        "original_zip_md5_matches_operator_supplied_provider_pin": True,
        "original_zip_sha256_matches_operator_supplied_pin": True,
        "original_zip_md5": md5.hexdigest(),
        "original_zip_sha256": sha.hexdigest(),
        "tiff_zip_member_name": member.filename,
        "tiff_uncompressed_bytes": copied,
        "tiff_uncompressed_sha256": tif_sha.hexdigest(),
        **header,
        "provider_pins_independently_authenticated_by_tool": False,
        "original_archive_was_acquired_by_this_tool": False,
        "archive_source_commercial_rights_verified": False,
        "native_raster_qualified_for_cat_model": False,
        "neon_database_written": False,
        "external_bytes_written_to_git": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original-zip", type=Path, required=True)
    ap.add_argument("--publisher-md5", required=True)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--expected-bytes", type=int, required=True)
    args = ap.parse_args(argv)
    try:
        result = inspect_local_original_zip(args.original_zip,
                                            publisher_md5=args.publisher_md5,
                                            expected_sha256=args.expected_sha256,
                                            expected_archive_bytes=args.expected_bytes)
    except LandfireArchiveError as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
