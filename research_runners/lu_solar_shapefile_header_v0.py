#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed header-only Shapefile/DBF audit for the 2025 Luxembourg solar cadastre.

Input: only tiny, exact official HTTP Range prefixes of SHP/SHX/DBF. No
record bodies, source geometry, actual building identifiers, addresses,
licensed raw source datasets or insurer records are read. Never admits data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys


class HeaderGateError(ValueError):
    """Malformed, oversized, unsupported or inconsistent source header."""


def parse_dbf_header(buf: bytes) -> dict:
    if not isinstance(buf, bytes) or len(buf) < 33:
        raise HeaderGateError("DBF header truncated")
    version = buf[0]
    if version not in (0x03, 0x83, 0x30, 0x31, 0x32, 0xF5):
        raise HeaderGateError("Unsupported DBF version")
    records = int.from_bytes(buf[4:8], "little")
    head_len = int.from_bytes(buf[8:10], "little")
    row_len = int.from_bytes(buf[10:12], "little")
    if not (33 <= head_len <= 8192 and len(buf) >= head_len and row_len >= 1):
        raise HeaderGateError("Invalid DBF header/record lengths or insufficient 8KiB prefix")
    if (head_len - 33) % 32:
        raise HeaderGateError("Malformed DBF field header length")
    if buf[head_len - 1] != 0x0D:
        raise HeaderGateError("DBF field terminator missing")
    fields = []
    physical_width = 1
    for pos in range(32, head_len - 1, 32):
        fd = buf[pos:pos + 32]
        name_bytes = fd[:11].split(b"\x00", 1)[0]
        if not name_bytes or any(v < 33 or v > 126 for v in name_bytes):
            raise HeaderGateError("Invalid ASCII DBF field name")
        name = name_bytes.decode("ascii")
        field_type = chr(fd[11])
        if field_type not in "CNDLFMIBTY@0":
            raise HeaderGateError("Unsupported DBF column type")
        width = fd[16]
        if width == 0:
            raise HeaderGateError("Invalid zero DBF field width")
        physical_width += width
        fields.append({"name": name, "type": field_type, "width": width})
    if physical_width != row_len:
        raise HeaderGateError("DBF physical row size != sum of field lengths")
    names = [f["name"].casefold() for f in fields]
    if len(set(names)) != len(names):
        raise HeaderGateError("Duplicate DBF columns")
    if not (0 < len(fields) <= 230 and 0 <= records <= 50_000_000):
        raise HeaderGateError("Unbounded DBF fields or records")
    return {"record_count": records, "field_count": len(fields), "columns": fields,
            "header_length": head_len, "record_length": row_len,
            "last_update": f"{1900 + buf[1]:04d}-{buf[2]:02d}-{buf[3]:02d}",
            "dbf_version_hex": f"{version:02x}"}


def parse_shp_header(buf: bytes, kind: str) -> dict:
    if len(buf) < 100:
        raise HeaderGateError(f"{kind} header truncated")
    if (struct.unpack_from(">i", buf, 0)[0] != 9994 or
            any(struct.unpack_from(">i", buf, pos)[0] != 0
                for pos in (4, 8, 12, 16, 20))):
        raise HeaderGateError("Invalid Shapefile magic or reserved bytes")
    size_words = struct.unpack_from(">i", buf, 24)[0]
    version = struct.unpack_from("<i", buf, 28)[0]
    shape_type = struct.unpack_from("<i", buf, 32)[0]
    if size_words < 50 or version != 1000 or shape_type not in (5, 15, 25):
        raise HeaderGateError(f"Invalid {kind} header/geometry: only Polygon shapes allowed")
    bbox = struct.unpack_from("<dddd", buf, 36)
    if (not all(-1e9 < x < 1e9 for x in bbox) or
            bbox[0] >= bbox[2] or bbox[1] >= bbox[3]):
        raise HeaderGateError("Invalid SHP declared bbox")
    if kind == "SHX" and ((size_words * 2 - 100) % 8):
        raise HeaderGateError("Invalid SHX record count padding")
    return {"declared_file_bytes": size_words * 2, "shape_type": shape_type,
            "declared_bbox_native_xy": [round(x, 4) for x in bbox],
            **({"index_record_count": (size_words * 2 - 100) // 8}
               if kind == "SHX" else {})}


def inspect(dbf: bytes, shp: bytes, shx: bytes) -> dict:
    d, s, x = parse_dbf_header(dbf), parse_shp_header(shp, "SHP"), parse_shp_header(shx, "SHX")
    if (s["shape_type"] != x["shape_type"] or
            s["declared_bbox_native_xy"] != x["declared_bbox_native_xy"]):
        raise HeaderGateError("SHP/SHX geometry metadata disagree")
    if d["record_count"] != x["index_record_count"]:
        raise HeaderGateError("DBF record count and SHX record count disagree")
    keys = {f["name"].lower() for f in d["columns"]}
    return {
        "schema_version": "lu-solar-2025-shapefile-header-receipt-v0",
        "dataset": "lu.klimaagence.solar-roof-cadastre.2025",
        "shapefile_record_count_unverified_against_bodies": d["record_count"],
        "dbf_header": d, "shp_header": s, "shx_header": x,
        "direct_buildings_shp_field_presence": {
            n: n in keys for n in
            ("hid", "tilt", "aspect", "flat", "area3d", "pv", "solar", "x_2169", "y_2169")
        },
        "documented_crs_not_verified_from_prj": "EPSG:2169",
        "field_values_or_original_polygon_geometries_read": False,
        "provider_rights_reviewed": False, "source_independence_proven": False,
        "model_input_admitted": False,
        "warning": (
            "Original range-prefix header receipt is not source authentication, licence clearance, "
            "geometry verification, nor a proof of roof facets. WMS facets may be separate; "
            "product-local hid is not an ACT or EUBUCCO building ID."
        ),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("dbf", "shp", "shx"):
        p.add_argument("--" + name + "-prefix", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        data = {}
        for name in ("dbf", "shp", "shx"):
            path = getattr(args, name + "_prefix")
            if (not path.is_file() or path.is_symlink()
                    or path.stat().st_size > 8192 or path.stat().st_size < 100):
                raise HeaderGateError("Only 100-8192 byte local original header prefixes accepted")
            data[name] = path.read_bytes()
        print(json.dumps(inspect(data["dbf"], data["shp"], data["shx"]),
                         ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2))
    except (HeaderGateError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
