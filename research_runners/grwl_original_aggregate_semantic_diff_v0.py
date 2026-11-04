# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original, SHA-pinned GRWL DBF/XY *semantic* comparison in ephemeral storage.

The result is aggregate source evidence, not an aligned river-feature change list.
Every real original GET is opt-in, main-only via reviewed workflow. No source
features, raw record content or coordinates are written to stdout or Git.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import struct
import tempfile
import zipfile

from research_runners.grwl_original_zip_structure_preflight_v0 import (
    _safe_members, inspect_original_zip, OriginalZipError, SOURCE_FILES,
)
from research_runners.grwl_trusted_original_byte_proof_v0 import download_fixed

SCHEMA = "opencatastrophe-grwl-original-aggregate-semantics-v0"
PINNED_SOURCE_SHA256 = {
    "2018": "16830e5444d47d6ba74790613533b6a81b4036a15f3ad7a7066241da28f95306",
    "2026": "78aa43a7104d24b1696e9b1547347eec13ba5d660aa990c1e7cea98e7ae70e4a",
}
MAX_DBF_RECORDS = 60_000
MAX_DBF_COLUMNS = 120
MAX_DBF_RECORD_BYTES = 16_384
MAX_SHP_RECORD_BYTES = 2_000_000


def _read_exact(stream, count):
    value = stream.read(count)
    if len(value) != count:
        raise OriginalZipError("truncated original source record")
    return value


def _member(archive: zipfile.ZipFile, suffix: str) -> zipfile.ZipInfo:
    candidates = [x for x in _safe_members(archive)
                  if not x.is_dir() and Path(x.filename).suffix.lower() == suffix]
    if len(candidates) != 1:
        raise OriginalZipError("original expected exactly one " + suffix + " member")
    return candidates[0]


def _normalized(raw: bytes, kind: str) -> bytes:
    if kind in ("N", "F"):
        try:
            txt = raw.strip().decode("ascii")
            if not txt:
                return b"<null>"
            number = Decimal(txt)
            if not number.is_finite():
                raise OriginalZipError("non-finite original numeric DBF value")
            normalized = format(number.normalize(), "f")
            if normalized.startswith("-") and Decimal(normalized) == 0:
                normalized = "0"
            return normalized.encode("ascii")
        except (UnicodeError, InvalidOperation) as exc:
            raise OriginalZipError("invalid original numeric DBF value") from exc
    # Non-numeric fields have source-native bytes; no attempt to decode or
    # interpret the non-numeric owner/site/lineage columns.
    return raw.rstrip(b" ")


def read_dbf_semantics(archive: zipfile.ZipFile):
    info = _member(archive, ".dbf")
    with archive.open(info, "r") as stream:
        head = _read_exact(stream, 32)
        n = struct.unpack_from("<I", head, 4)[0]
        header_len, record_len = struct.unpack_from("<HH", head, 8)
        if (head[0] not in (3, 0x83) or not 1 <= n <= MAX_DBF_RECORDS
                or not 65 <= header_len <= 16384 or (header_len - 33) % 32
                or not 2 <= record_len <= MAX_DBF_RECORD_BYTES
                or header_len + n * record_len > info.file_size):
            raise OriginalZipError("malformed or oversized original DBF")
        field_count = (header_len - 33) // 32
        if not 1 <= field_count <= MAX_DBF_COLUMNS:
            raise OriginalZipError("DBF field count exceeds bound")
        field_header = _read_exact(stream, header_len - 32)
        if field_header[-1] != 0x0d:
            raise OriginalZipError("DBF missing field terminator")
        fields = []
        for index in range(field_count):
            item = field_header[index * 32:(index + 1) * 32]
            try:
                name = item[:11].split(b"\0", 1)[0].decode("ascii").upper()
            except UnicodeError as exc:
                raise OriginalZipError("non-ASCII DBF field name") from exc
            kind = chr(item[11])
            width = item[16]
            if (not name or name in {f[0] for f in fields} or not 1 <= width <= 254
                    or kind not in ("N", "F", "C", "D", "L", "I")):
                raise OriginalZipError("ambiguous or unsupported DBF descriptor")
            fields.append((name, kind, width))
        if sum(field[2] for field in fields) + 1 != record_len:
            raise OriginalZipError("DBF field widths do not match row size")
        if "WIDTH_MEAN" not in {f[0] for f in fields}:
            raise OriginalZipError("GRWL width_mean missing from original DBF")

        values_by_field = {name: Counter() for name, _, _ in fields}
        rows = Counter()
        ordered_rows = []
        for _ in range(n):
            raw_row = _read_exact(stream, record_len)
            if raw_row[:1] != b" ":
                raise OriginalZipError("deleted/invalid DBF records require separate review")
            chunks = []
            offset = 1
            for name, kind, width in fields:
                value = _normalized(raw_row[offset:offset+width], kind)
                values_by_field[name][value] += 1
                chunks.append(struct.pack(">I", len(value)) + value)
                offset += width
            key = hashlib.sha256(b"".join(chunks)).digest()
            rows[key] += 1
            ordered_rows.append(key)
        if stream.read(2) not in (b"", b"\x1a"):
            raise OriginalZipError("unexpected trailing bytes after DBF rows")
    return {"record_count": n, "fields": fields, "values": values_by_field,
            "rows": rows, "ordered_rows": ordered_rows}


def read_shp_xy_sequences(archive: zipfile.ZipFile):
    info = _member(archive, ".shp")
    with archive.open(info, "r") as stream:
        header = _read_exact(stream, 100)
        if struct.unpack_from(">i", header, 0)[0] != 9994:
            raise OriginalZipError("bad original SHP header")
        if struct.unpack_from(">i", header, 24)[0] * 2 != info.file_size:
            raise OriginalZipError("SHP member declared size mismatch")
        expected_type = struct.unpack_from("<i", header, 32)[0]
        if expected_type not in (3, 13, 23):
            raise OriginalZipError("not a GRWL polyline shape file")
        xy_counter = Counter()
        raw_counter = Counter()
        xy_ordered = []
        shape_types = Counter()
        total_points = 0
        i = 0
        consumed = 100
        while consumed < info.file_size:
            rec_header = _read_exact(stream, 8)
            recnum, length_words = struct.unpack(">II", rec_header)
            data_len = length_words * 2
            if (recnum != i + 1 or data_len < 4
                    or data_len > MAX_SHP_RECORD_BYTES
                    or consumed + 8 + data_len > info.file_size):
                raise OriginalZipError("malformed original SHP record numbering/length")
            data = _read_exact(stream, data_len)
            consumed += 8 + data_len
            kind = struct.unpack_from("<i", data, 0)[0]
            if kind == 0:
                xy = b"NULL"
            else:
                if kind != expected_type or data_len < 44:
                    raise OriginalZipError("unexpected original per-record SHP type")
                part_count, point_count = struct.unpack_from("<II", data, 36)
                if not (1 <= part_count <= 10000 and 2 <= point_count <= 100000):
                    raise OriginalZipError("invalid polyline record dimensions")
                min_len = 44 + 4 * part_count + 16 * point_count
                if min_len > data_len:
                    raise OriginalZipError("truncated original XY coordinate payload")
                parts = struct.unpack_from("<" + "I" * part_count, data, 44)
                if parts[0] != 0 or any(a >= b for a, b in zip(parts, parts[1:])) or parts[-1] >= point_count:
                    raise OriginalZipError("invalid polyline part offsets")
                xy_bytes = data[44 + 4 * part_count:min_len]
                # Reject NaN/Inf and out-of-domain WGS84 coordinates; do not
                # publish or return any individual coordinate value.
                for j in range(0, len(xy_bytes), 16):
                    x, y = struct.unpack_from("<dd", xy_bytes, j)
                    if not (math.isfinite(x) and math.isfinite(y)
                            and -180.0001 <= x <= 180.0001
                            and -90.0001 <= y <= 90.0001):
                        raise OriginalZipError("non-finite or non-WGS84 original XY")
                total_points += point_count
                xy = data[36:44] + data[44:44 + 4 * part_count] + xy_bytes
            key = hashlib.sha256(xy).digest()
            xy_counter[key] += 1
            xy_ordered.append(key)
            raw_counter[hashlib.sha256(data).digest()] += 1
            shape_types[str(kind)] += 1
            i += 1
            if i > MAX_DBF_RECORDS:
                raise OriginalZipError("original SHP feature limit")
        if consumed != info.file_size or stream.read(1):
            raise OriginalZipError("SHP record traversal did not exhaust original")
    return {"record_count": i, "total_xy_points": total_points,
            "xy": xy_counter, "raw": raw_counter, "xy_ordered": xy_ordered,
            "shape_types": dict(sorted(shape_types.items()))}


def _unmatched(counter_a, counter_b):
    return sum((counter_a - counter_b).values())


def aggregate_pair(early_dbf, late_dbf, early_shp, late_shp):
    if (early_dbf["record_count"] != early_shp["record_count"] or
            late_dbf["record_count"] != late_shp["record_count"]):
        raise OriginalZipError("SHP/DBF record alignment count mismatch")
    fields_a, fields_b = early_dbf["fields"], late_dbf["fields"]
    equivalent_schema = fields_a == fields_b
    fields = []
    if equivalent_schema:
        for name, kind, width in fields_a:
            a, b = early_dbf["values"][name], late_dbf["values"][name]
            fields.append({
                "field": name,
                "dbf_kind": kind,
                "dbf_field_width": width,
                "value_multiset_equal": a == b,
                "minimum_unmatched_values_each_release": _unmatched(a, b),
                "unique_values_2018": len(a),
                "unique_values_2026": len(b),
                "raw_values_released": False,
            })
    return {
        "schema": SCHEMA,
        "record_count_2018": early_dbf["record_count"],
        "record_count_2026": late_dbf["record_count"],
        "dbf_field_schema_equal": equivalent_schema,
        "dbf_fields": fields,
        "semantic_row_multiset_equal": equivalent_schema and early_dbf["rows"] == late_dbf["rows"],
        "semantic_rows_equal_by_ordinal": equivalent_schema and early_dbf["ordered_rows"] == late_dbf["ordered_rows"],
        "minimum_unmatched_semantic_rows_each_release":
            _unmatched(early_dbf["rows"], late_dbf["rows"]) if equivalent_schema else None,
        "shp_xy_sequence_multiset_equal": early_shp["xy"] == late_shp["xy"],
        "shp_xy_sequences_equal_by_ordinal": early_shp["xy_ordered"] == late_shp["xy_ordered"],
        "minimum_unmatched_xy_sequences_each_release": _unmatched(early_shp["xy"], late_shp["xy"]),
        "shp_raw_record_multiset_equal": early_shp["raw"] == late_shp["raw"],
        "total_xy_points_2018": early_shp["total_xy_points"],
        "total_xy_points_2026": late_shp["total_xy_points"],
        "shape_type_counts_2018": early_shp["shape_types"],
        "shape_type_counts_2026": late_shp["shape_types"],
        "index_is_not_a_stable_river_identity": True,
        "per_river_change_attribution_verified": False,
        "riveratlas_join_validated": False,
        "flood_stage_width_derived": False,
        "model_input_admitted": False,
        "production_database_modified": False,
    }


def original_semantic_diff():
    with tempfile.TemporaryDirectory(prefix="grwl-feature-semantic-") as tmp:
        versions = {}
        zip_evidence = []
        for release in ("2018", "2026"):
            path = Path(tmp) / SOURCE_FILES[release][0]
            downloaded = download_fixed(release, path)
            receipt = inspect_original_zip(path, release)
            exact_sha = PINNED_SOURCE_SHA256[release]
            if (downloaded["independent_original_zip_sha256"] != exact_sha or
                    receipt["independently_computed_original_zip_sha256"] != exact_sha):
                raise OriginalZipError("original ZIP SHA-256 differs from pinned trusted-main evidence")
            zip_evidence.append({"release": release, "source_zip_sha256": exact_sha})
            with zipfile.ZipFile(path, "r") as source:
                versions[release] = (read_dbf_semantics(source), read_shp_xy_sequences(source))
        return {
            "original_zip_sha256": zip_evidence,
            "summary": aggregate_pair(versions["2018"][0], versions["2026"][0],
                                         versions["2018"][1], versions["2026"][1]),
            "source_data_included_in_receipt": False,
            "source_data_admitted": False,
        }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true", help="opt-in trusted-main original Zenodo source download")
    args = p.parse_args(argv)
    if not args.live:
        p.print_help()
        return 2
    try:
        result = original_semantic_diff()
    except OriginalZipError as exc:
        p.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
