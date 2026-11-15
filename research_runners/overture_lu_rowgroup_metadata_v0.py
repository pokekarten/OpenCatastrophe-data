# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original Overture STAC 00226 row-group bbox metadata preflight.

Only reads source STAC and Parquet metadata (<= 2 MiB), not data pages,
building records, insured values or feature geometries. No database writes.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys

from research_runners.overture_luxembourg_stac_receipt_v0 import (
    EXPECTED_BYTES, EXPECTED_ROWS, EXPECTED_ROW_GROUPS_STAC, S3_URL, STAC_URL,
    _source_range, ProbeError,
)
from research_runners.overture_building_original_metadata_probe_v0 import (
    _default_fetch, _request,
)

SCHEMA = "opencatastrophe-lu-overture-original-rowgroup-bbox-preflight-v0"
SCREEN = (6.129, 49.609, 6.131, 49.611)
MAX_FOOTER_BYTES = 2_000_000
EXPECTED_FOOTER_BYTES = 1_461_640
FLOAT_FIELDS = ("bbox.xmin", "bbox.xmax", "bbox.ymin", "bbox.ymax")


class Reader:
    """Strict, bounded Thrift CompactProtocol reader for Parquet metadata."""

    def __init__(self, data):
        if not data or len(data) > MAX_FOOTER_BYTES:
            raise ProbeError("empty or oversized original footer")
        self.data = memoryview(data)
        self.pos = 0

    def byte(self):
        if self.pos >= len(self.data):
            raise ProbeError("truncated original Parquet metadata")
        value = self.data[self.pos]
        self.pos += 1
        return value

    def varint(self):
        number = 0
        for i in range(10):
            b = self.byte()
            number |= (b & 127) << (7 * i)
            if b < 128:
                if number >= 1 << 64:
                    raise ProbeError("oversize Thrift integer")
                return number
        raise ProbeError("invalid Thrift varint")

    def signed(self):
        n = self.varint()
        return (n >> 1) ^ -(n & 1)

    def binary(self):
        n = self.varint()
        if n > 131072 or self.pos + n > len(self.data):
            raise ProbeError("oversized/truncated Thrift binary")
        result = self.data[self.pos:self.pos+n].tobytes()
        self.pos += n
        return result

    def value(self, typ, depth):
        if depth > 25:
            raise ProbeError("excessive Thrift nesting")
        if typ in (1, 2):
            return typ == 1
        if typ == 3:
            return self.byte()
        if typ in (4, 5, 6):
            return self.signed()
        if typ == 7:
            if self.pos + 8 > len(self.data):
                raise ProbeError("truncated Thrift double")
            result = struct.unpack_from("<d", self.data, self.pos)[0]
            self.pos += 8
            return result
        if typ == 8:
            return self.binary()
        if typ in (9, 10):
            head = self.byte()
            count, item_type = head >> 4, head & 15
            if count == 15:
                count = self.varint()
            if count > 4096:
                raise ProbeError("metadata list too long")
            return [self.value(item_type, depth + 1) for _ in range(count)]
        if typ == 11:
            count = self.varint()
            if count > 4096:
                raise ProbeError("metadata map too long")
            if not count:
                return []
            types = self.byte()
            return [(self.value(types >> 4, depth + 1),
                     self.value(types & 15, depth + 1)) for _ in range(count)]
        if typ == 12:
            return self.fields(depth + 1)
        raise ProbeError("unexpected Thrift field type")

    def fields(self, depth=0):
        last = 0
        result = {}
        for _ in range(128):
            head = self.byte()
            if head == 0:
                return result
            delta, typ = head >> 4, head & 15
            field_id = last + delta if delta else self.signed()
            if field_id <= 0 or field_id in result:
                raise ProbeError("invalid/duplicate Thrift field")
            result[field_id] = self.value(typ, depth + 1)
            last = field_id
        raise ProbeError("metadata struct too large")


def read_metadata(footer):
    reader = Reader(footer)
    parsed = reader.fields()
    if reader.pos != len(footer):
        raise ProbeError("unexpected trailing footer bytes")
    schema = parsed.get(2)
    groups = parsed.get(4)
    if (parsed.get(1) != 2 or parsed.get(3) != EXPECTED_ROWS
            or not isinstance(schema, list) or len(schema) != 63
            or not isinstance(groups, list) or len(groups) != EXPECTED_ROW_GROUPS_STAC):
        raise ProbeError("original source file version/schema/rows/groups mismatch")
    if (any(not isinstance(g, dict) or type(g.get(3)) is not int for g in groups)
            or sum(g[3] for g in groups) != EXPECTED_ROWS):
        raise ProbeError("original row-group counts do not conserve file rows")
    return groups


def _float_stat(raw):
    # Parquet primitive Type=5 is DOUBLE (IEEE-754 float64), not FLOAT
    # (Type=4). This exact original Overture file contains 8-byte
    # little-endian statistics for all four bbox columns.
    if not isinstance(raw, bytes) or len(raw) != 8:
        return None
    result = struct.unpack("<d", raw)[0]
    return result if math.isfinite(result) else None


def inspect_group(group):
    if type(group) is not dict or type(group.get(3)) is not int or group[3] <= 0:
        raise ProbeError("invalid original row-group row count")
    cols = group.get(1)
    if type(cols) is not list or not 35 <= len(cols) <= 65:
        raise ProbeError("unrecognized original row-group schema")
    bounds = {}
    for column in cols:
        if type(column) is not dict or type(column.get(3)) is not dict:
            raise ProbeError("bad original column metadata")
        meta = column[3]
        path = meta.get(3)
        if type(path) is not list or any(type(x) is not bytes for x in path):
            raise ProbeError("invalid source column path")
        try:
            name = ".".join(x.decode("utf-8", "strict") for x in path)
        except UnicodeError as exc:
            raise ProbeError("non-UTF8 source column name") from exc
        if name not in FLOAT_FIELDS:
            continue
        if name in bounds or meta.get(1) != 5:
            raise ProbeError("duplicate or non-float original bbox field")
        stats = meta.get(12)
        if type(stats) is not dict:
            bounds[name] = None
            continue
        lower = _float_stat(stats.get(6, stats.get(2)))
        upper = _float_stat(stats.get(5, stats.get(1)))
        bounds[name] = (lower, upper) if (
            lower is not None and upper is not None and lower <= upper) else None
    if any(field not in bounds for field in FLOAT_FIELDS):
        raise ProbeError("missing original bbox column")
    if any(bounds[field] is None for field in FLOAT_FIELDS):
        return "unknown"
    xmin, xmax, ymin, ymax = (bounds[x] for x in FLOAT_FIELDS)
    # Necessary-only screen: candidates still require actual per-row geometry.
    if (xmin[0] > SCREEN[2] or xmax[1] < SCREEN[0]
            or ymin[0] > SCREEN[3] or ymax[1] < SCREEN[1]):
        return "excluded"
    return "candidate"



def _bbox_statistics_diagnostics(group):
    """Only source column metadata flags, never original feature data."""
    out = {}
    for column in group.get(1, []):
        meta = column.get(3, {})
        path = meta.get(3, [])
        if type(path) is not list or any(type(p) is not bytes for p in path):
            continue
        try:
            name = ".".join(p.decode("utf-8", "strict") for p in path)
        except UnicodeError:
            continue
        if name not in FLOAT_FIELDS:
            continue
        stats = meta.get(12)
        if type(stats) is not dict:
            out[name] = {"column_present": True, "stat_struct_present": False}
            continue
        low = stats.get(6, stats.get(2))
        high = stats.get(5, stats.get(1))
        out[name] = {
            "column_present": True,
            "parquet_primitive_type": meta.get(1),
            "stat_struct_present": True,
            "stat_field_ids": sorted(stats.keys()),
            "min_stat_byte_length": len(low) if isinstance(low, bytes) else None,
            "max_stat_byte_length": len(high) if isinstance(high, bytes) else None,
            "min_stat_parses_as_finite_double": _float_stat(low) is not None,
            "max_stat_parses_as_finite_double": _float_stat(high) is not None,
        }
    for name in FLOAT_FIELDS:
        out.setdefault(name, {"column_present": False})
    return out


def screen(groups):
    counts = {"candidate": 0, "excluded": 0, "unknown": 0}
    rows = {"candidate": 0, "excluded": 0, "unknown": 0}
    groups_for_followup = []
    for ordinal, group in enumerate(groups):
        verdict = inspect_group(group)
        counts[verdict] += 1
        rows[verdict] += group[3]
        if verdict != "excluded":
            groups_for_followup.append(ordinal)
    if (sum(counts.values()) != EXPECTED_ROW_GROUPS_STAC
            or sum(rows.values()) != EXPECTED_ROWS):
        raise ProbeError("row-group audit did not conserve original source file")
    return {
        "first_original_rowgroup_bbox_metadata_diagnostics": _bbox_statistics_diagnostics(groups[0]),
        "row_group_count_by_status": counts,
        "file_rows_in_groups_by_status": rows,
        "groups_not_excluded": counts["candidate"] + counts["unknown"],
        "original_zero_based_rowgroup_indices_for_followup": groups_for_followup,
        "no_original_building_data_pages_read": True,
        "country_building_count_measured": False,
        "source_file_full_sha256_verified": False,
        "rights_approved": False,
        "insurance_model_input_approved": False,
        "production_neon_modified": False,
    }


def probe(*, fetch=_default_fetch):
    from research_runners.overture_luxembourg_stac_receipt_v0 import probe as stac_probe
    stac_probe(fetch=fetch)
    # Additional 4-byte identity check pins the ETag of the full-footer transfer
    # to that of the already validated file start and end.
    _, original_etag = _source_range(fetch, 0, 3)
    start = EXPECTED_BYTES - 8 - EXPECTED_FOOTER_BYTES
    request = _request(S3_URL, range_header=f"bytes={start}-{EXPECTED_BYTES-9}")
    status, headers, footer = fetch(request, MAX_FOOTER_BYTES)
    if (status != 206 or len(footer) != EXPECTED_FOOTER_BYTES
            or headers.get("content-range") !=
                f"bytes {start}-{EXPECTED_BYTES-9}/{EXPECTED_BYTES}"
            or headers.get("content-length") != str(EXPECTED_FOOTER_BYTES)
            or not re.fullmatch(r'"[0-9a-f]{32}(?:-\d+)?"',
                                headers.get("etag", ""))
            or headers.get("etag") != original_etag):
        raise ProbeError("original footer changed or unsupported partial response")
    groups = read_metadata(footer)
    return {
        "schema": SCHEMA,
        "original_stac_item": STAC_URL,
        "original_s3_file": S3_URL,
        "source_file_rows_not_luxembourg_rows": EXPECTED_ROWS,
        "source_file_row_groups": EXPECTED_ROW_GROUPS_STAC,
        "source_footer_metadata_bytes_read": len(footer),
        "city_research_bbox_wgs84": SCREEN,
        **screen(groups),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Explicit opt-in to bounded public original-source metadata read")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: explicit --live required", file=sys.stderr)
        return 2
    try:
        result = probe()
    except (ProbeError, OSError, ValueError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
