#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fixed-object MRMS MESH gzip/GRIB2 metadata integrity preflight.

No network operations, no original dataset bytes in Git, no raster cell value
decoding, no source admission, no loss modelling. Passing means only that the
selected local compressed file matches a research-observed SHA-256 and the
selected structural metadata constraints. Publisher-original acquisition via
a controlled independent channel still needs separate evidence.

Exit codes: 0 means selected byte/structural checks passed; 2 means blocked.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

# Three fixed historical source objects; earlier two independently verified
# by direct GitHub Actions. Keller 2021 digest is intermediary-only at intake.
# These digests are NOT proof of authentic original direct NOAA acquisition.
SOURCE_OBJECTS = {
    "mesh": {
        "basename": "MRMS_MESH_00.50_20201014-000025.grib2.gz",
        "key": "CONUS/MESH_00.50/20201014/MRMS_MESH_00.50_20201014-000025.grib2.gz",
        "compressed_size": 40186,
        "compressed_sha256": "792b2b7961248f416b593c1fc1d8139f6709829472c1354c80d853417035f5e3",
        "mrms_grib_parameter_number": 28,
    },
    "mesh_max_30min": {
        "basename": "MRMS_MESH_Max_30min_00.50_20201014-000025.grib2.gz",
        "key": "CONUS/MESH_Max_30min_00.50/20201014/MRMS_MESH_Max_30min_00.50_20201014-000025.grib2.gz",
        "compressed_size": 44683,
        "compressed_sha256": "5f139328e25c9b87b8c120a7b67dfb9128717e526c301a0f1b55046d11ca1337",
        "mrms_grib_parameter_number": 29,
    },
    "mesh_keller_2021": {
        # 2.5-inch Keller hail ground report: NOAA NCEI Storm Events 956694,
        # 2021-04-29T01:37Z. Source tile is 21 seconds earlier.
        # Byte hash observed via web intermediary, awaiting independently
        # verified direct NOAA HTTPS retrieval and calibrated value decode.
        "basename": "MRMS_MESH_00.50_20210429-013639.grib2.gz",
        "key": "CONUS/MESH_00.50/20210429/MRMS_MESH_00.50_20210429-013639.grib2.gz",
        "compressed_size": 54463,
        "compressed_sha256": "7d1fc719f0791e25ddd2919cb5dcea1302caa4150712feebc42b6c0cbe84fdf6",
        "mrms_grib_parameter_number": 28,
    },
}
MAX_COMPRESSED_BYTES = 128_000
MAX_DECOMPRESSED_BYTES = 2_000_000
# NOAA/NSSL MRMS operational table: discipline 209, category 3, parameters 28/29
# in mm, https://www.nssl.noaa.gov/projects/mrms/operational/tables.php .
# Version table currently documents v12.2, but THESE objects are from 2020;
# applicability of parameter code and units is checked here, not presumed
# equivalence of MRMS scientific algorithms across versions.
DISCIPLINE = 209
CATEGORY = 3
ORIGIN_CENTER = 161
ORIGIN_SUBCENTER = 0


class MRMSPreflightError(ValueError):
    """Untrusted, incompatible or physically uninterpreted input."""


def inflate_gzip_capped(blob: bytes) -> bytes:
    """Decode one complete gzip member with CRC32 and bounded memory use."""
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_COMPRESSED_BYTES:
        raise MRMSPreflightError("compressed source empty or exceeds byte bound")
    if len(blob) < 18 or blob[:3] != b"\x1f\x8b\x08":
        raise MRMSPreflightError("not a valid gzip/DEFLATE header")
    if blob[3] & 0xE0:
        raise MRMSPreflightError("reserved gzip flag bits")
    try:
        inflater = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
        decoded = inflater.decompress(blob, MAX_DECOMPRESSED_BYTES + 1)
        if len(decoded) > MAX_DECOMPRESSED_BYTES:
            raise MRMSPreflightError("decoded byte bound exceeded")
        if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
            raise MRMSPreflightError("incomplete gzip, trailing bytes or extra member")
        decoded += inflater.flush(MAX_DECOMPRESSED_BYTES + 1 - len(decoded))
        if len(decoded) > MAX_DECOMPRESSED_BYTES:
            raise MRMSPreflightError("decoded byte bound exceeded")
        return decoded
    except (zlib.error, OverflowError) as exc:
        raise MRMSPreflightError("invalid gzip DEFLATE stream or CRC32") from exc


def _grib_signed_magnitude_i32(chunk: bytes) -> int:
    """Decode WMO GRIB2 sign-magnitude 32-bit coordinate, not two's complement."""
    if len(chunk) != 4:
        raise MRMSPreflightError("bad GRIB2 signed-coordinate field length")
    raw = int.from_bytes(chunk, "big")
    if raw == 0xffffffff:
        raise MRMSPreflightError("missing GRIB2 coordinate")
    value = raw & 0x7fffffff
    return -value if raw & 0x80000000 else value


def template0_grid_geography(section3: bytes, expected_points: int) -> dict:
    """Extract only 3.0 regular lat/lon geometry, never hail field values.

    WMO GRIB2 Section 3.0 octet positions from
    https://codes.ecmwf.int/grib/format/grib2/templates/3/0/ .
    Original datasets may use longitude in the 0..360 degree convention.
    """
    if len(section3) != 72 or section3[4] != 3:
        raise MRMSPreflightError("unsupported GRIB2 grid-template-0 section length")
    if int.from_bytes(section3[12:14], "big") != 0:
        raise MRMSPreflightError("not GRIB2 regular latitude/longitude template")
    count = int.from_bytes(section3[6:10], "big")
    ni = int.from_bytes(section3[30:34], "big")
    nj = int.from_bytes(section3[34:38], "big")
    if (count != expected_points or not 0 < ni <= 10000 or
            not 0 < nj <= 10000 or ni * nj != count):
        raise MRMSPreflightError("inconsistent GRIB2 grid dimensions/point count")
    basic_angle = int.from_bytes(section3[38:42], "big")
    subdivisions = int.from_bytes(section3[42:46], "big")
    # WMO Template 3.0 Note 1: a zero or *missing* basic angle and
    # subdivisions mean the recommended 10^-6 degree unit. ecCodes implements
    # missing() for subdivisions as all-one bits (0xffffffff).
    if (basic_angle not in (0, 0xffffffff) or
            subdivisions not in (0, 0xffffffff)):
        raise MRMSPreflightError(
            f"unreviewed GRIB2 angular scale ({basic_angle}, {subdivisions})"
        )
    latitude_first = _grib_signed_magnitude_i32(section3[46:50]) / 1_000_000
    longitude_first = _grib_signed_magnitude_i32(section3[50:54]) / 1_000_000
    latitude_last = _grib_signed_magnitude_i32(section3[55:59]) / 1_000_000
    longitude_last = _grib_signed_magnitude_i32(section3[59:63]) / 1_000_000
    di = int.from_bytes(section3[63:67], "big") / 1_000_000
    dj = int.from_bytes(section3[67:71], "big") / 1_000_000
    scanning = section3[71]
    if (not (-90 <= latitude_first <= 90 and -90 <= latitude_last <= 90) or
            not (0 <= longitude_first <= 360 and 0 <= longitude_last <= 360) or
            not (0 < di < 10 and 0 < dj < 10)):
        raise MRMSPreflightError("GRIB2 latitude/longitude or increments invalid")
    if scanning & 0x3f:
        raise MRMSPreflightError("unreviewed GRIB2 scanning mode low bits")
    # Scan bit 1: 0 means +i (east); 1 means -i.
    # Scan bit 2: 0 means -j (south); 1 means +j.
    eastward = not bool(scanning & 0x80)
    northward = bool(scanning & 0x40)
    end_lon_expected = longitude_first + (ni - 1) * di * (1 if eastward else -1)
    end_lat_expected = latitude_first + (nj - 1) * dj * (1 if northward else -1)
    # 2 microdegrees allow integer-increment and endpoint storage rounding.
    if (abs(end_lon_expected - longitude_last) > 0.000002 or
            abs(end_lat_expected - latitude_last) > 0.000002):
        raise MRMSPreflightError("GRIB2 grid endpoints contradict scan/increments")
    return {
        "geometry_checked": True,
        "template": 0,
        "nx": ni,
        "ny": nj,
        "points": count,
        "latitude_first_deg": latitude_first,
        "longitude_first_east_0_360_deg": longitude_first,
        "latitude_last_deg": latitude_last,
        "longitude_last_east_0_360_deg": longitude_last,
        "latitude_increment_deg": dj,
        "longitude_increment_deg": di,
        "scanning_mode": scanning,
        "i_eastward": eastward,
        "j_northward": northward,
        "coordinate_system": "regular_geographic_latlon_WGS84_assumed_from_GRIB_template_3_0",
        "pixel_values_decoded": False,
    }


def nominal_grid_cell(grid: dict, latitude_deg: float, longitude_deg: float) -> dict:
    """Compute nearest nominal cell index only. Not an observed hail value."""
    if grid.get("geometry_checked") is not True:
        raise MRMSPreflightError("unverified grid geometry")
    if not (-90 <= latitude_deg <= 90 and -180 <= longitude_deg <= 180):
        raise MRMSPreflightError("invalid external observation coordinates")
    lon = longitude_deg + 360 if longitude_deg < 0 else longitude_deg
    x = ((lon - grid["longitude_first_east_0_360_deg"]) /
         (grid["longitude_increment_deg"] * (1 if grid["i_eastward"] else -1)))
    y = ((latitude_deg - grid["latitude_first_deg"]) /
         (grid["latitude_increment_deg"] * (1 if grid["j_northward"] else -1)))
    col, row = round(x), round(y)
    within = 0 <= col < grid["nx"] and 0 <= row < grid["ny"]
    return {
        "external_report_latitude_deg": latitude_deg,
        "external_report_longitude_deg": longitude_deg,
        "nearest_grid_column": col if within else None,
        "nearest_grid_row": row if within else None,
        "within_source_grid_bounds": within,
        "same_location_as_actual_radar_maximum_not_established": True,
        "raster_cell_value_read": False,
    }


def parse_grib2_structure(grib: bytes, expected_parameter: int) -> dict:
    """Inspect strict single-message GRIB2 envelope, not physical grid values.

    The local-definition parameter mapping is source-documented; an external
    ecCodes/wgrib2 decode remains necessary to inspect packing, bitmap, axes,
    nodata sentinels, numeric magnitudes and data-values.
    """
    if not isinstance(grib, bytes) or len(grib) < 16 + 4 + 21 + 14 + 11 + 11 + 6 + 6:
        raise MRMSPreflightError("GRIB2 message too short")
    if grib[:4] != b"GRIB" or grib[4:6] != b"\x00\x00":
        raise MRMSPreflightError("GRIB marker or reserved bytes invalid")
    discipline, edition = grib[6], grib[7]
    if discipline != DISCIPLINE or edition != 2:
        raise MRMSPreflightError("wrong GRIB2 discipline/edition")
    declared_length = int.from_bytes(grib[8:16], "big")
    if declared_length != len(grib) or grib[-4:] != b"7777":
        raise MRMSPreflightError("wrong GRIB2 length/7777 terminator")
    sections: dict[int, bytes] = {}
    section_order = []
    index = 16
    while index < len(grib) - 4:
        if index + 5 > len(grib) - 4:
            raise MRMSPreflightError("truncated GRIB2 section header")
        size = int.from_bytes(grib[index:index + 4], "big")
        number = grib[index + 4]
        if size < 5 or index + size > len(grib) - 4:
            raise MRMSPreflightError("bad GRIB2 section length")
        if number not in (1, 2, 3, 4, 5, 6, 7) or number in sections:
            raise MRMSPreflightError("unknown/duplicated GRIB2 section")
        sections[number] = grib[index:index + size]
        section_order.append(number)
        index += size
    if index != len(grib) - 4:
        raise MRMSPreflightError("unparsed GRIB2 section bytes")
    if section_order not in ([1, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7]):
        raise MRMSPreflightError("wrong single-field GRIB2 section order")
    sec1, sec3, sec4 = sections[1], sections[3], sections[4]
    if len(sec1) < 21 or len(sec3) < 14 or len(sec4) < 11:
        raise MRMSPreflightError("missing mandatory section metadata")
    center, subcenter = struct.unpack(">HH", sec1[5:9])
    if center != ORIGIN_CENTER or subcenter != ORIGIN_SUBCENTER:
        raise MRMSPreflightError("wrong originating GRIB2 center/subcenter")
    try:
        reference_time = datetime(
            int.from_bytes(sec1[12:14], "big"),
            sec1[14], sec1[15], sec1[16], sec1[17], sec1[18],
            tzinfo=timezone.utc,
        ).isoformat()
    except ValueError as exc:
        raise MRMSPreflightError("invalid GRIB2 UTC reference timestamp") from exc
    number_of_points = int.from_bytes(sec3[6:10], "big")
    grid_template = int.from_bytes(sec3[12:14], "big")
    product_template = int.from_bytes(sec4[7:9], "big")
    param_category, param_number = sec4[9], sec4[10]
    if number_of_points <= 0 or number_of_points > 100_000_000:
        raise MRMSPreflightError("invalid GRIB2 grid point count")
    if product_template not in (0, 8):
        raise MRMSPreflightError("unreviewed GRIB2 product template")
    if (param_category, param_number) != (CATEGORY, expected_parameter):
        raise MRMSPreflightError("wrong MESH product category/parameter")
    grid_geography = (
        template0_grid_geography(sec3, number_of_points)
        if grid_template == 0 and len(sec3) >= 72
        else {"geometry_checked": False, "reason": "synthetic_or_unreviewed_section3"}
    )
    return {
        "grid_geography": grid_geography,
        "grib_edition": edition,
        "grib_discipline": discipline,
        "originating_center": center,
        "originating_subcenter": subcenter,
        "reference_utc": reference_time,
        "grid_template_number": grid_template,
        "grid_points_declared": number_of_points,
        "product_template_number": product_template,
        "parameter_category": param_category,
        "parameter_number": param_number,
        "source_parameter_unit_from_noaa_table": "mm",
        "grib_section_sequence": section_order,
        "grib_message_bytes": declared_length,
        "grid_values_decoded": False,
    }


def audit_original(blob: bytes, product: str, filename: str) -> dict:
    if product not in SOURCE_OBJECTS:
        raise MRMSPreflightError("unsupported selected historical MESH object")
    expected = SOURCE_OBJECTS[product]
    if filename != expected["basename"]:
        raise MRMSPreflightError("unexpected original file basename")
    if type(blob) is not bytes or len(blob) != expected["compressed_size"]:
        raise MRMSPreflightError("original compressed byte length mismatch")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected["compressed_sha256"]:
        raise MRMSPreflightError("original compressed SHA256 mismatch")
    decoded = inflate_gzip_capped(blob)  # verifies complete gzip CRC32
    fields = parse_grib2_structure(decoded, expected["mrms_grib_parameter_number"])
    return {
        "audit_version": "noaa-mrms-mesh-original-byte-preflight-v0",
        "selected_product": product,
        "original_object_key": expected["key"],
        "compressed_bytes": len(blob),
        "compressed_sha256": digest,
        "decoded_grib_bytes": len(decoded),
        "gzip_crc32_checked": True,
        **fields,
        "source_bytes_committed_to_git": False,
        "direct_first_party_acquisition_authenticated": False,
        "source_admission_granted": False,
        "scientific_fitness_established": False,
        "model_input_approved": False,
        "insurer_losses_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", required=True, choices=sorted(SOURCE_OBJECTS))
    parser.add_argument("--gzip", required=True, type=Path, help="local file only, not a URL")
    args = parser.parse_args()
    try:
        # Fail before large reads. Opening local file has no network effect.
        if not args.gzip.is_file():
            raise MRMSPreflightError("missing selected local original asset")
        if args.gzip.stat().st_size > MAX_COMPRESSED_BYTES:
            raise MRMSPreflightError("local compressed byte bound exceeded")
        blob = args.gzip.read_bytes()
        result = audit_original(blob, args.product, args.gzip.name)
    except (OSError, MRMSPreflightError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
