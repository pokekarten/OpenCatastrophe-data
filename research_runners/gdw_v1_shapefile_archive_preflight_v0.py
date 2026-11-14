# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, read-only original GDW v1.0 Shapefile ZIP structural preflight.

No network, extraction, provider records, geometry, IDs or database output.
Provider MD5 is weak and proves only correspondence with Figshare metadata;
optional independently pinned SHA256 is a separate identity check.
Passing does NOT approve source rights, science, topology, or CAT model use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import stat
import struct
import sys
import zipfile

PROVIDER_BYTES = 69_745_749
PROVIDER_MD5 = "5064cf2315ef6159d9133b03596e761a"
EXPECTED_COUNTS = {"GDW_barriers_v1_0": (1, 41_145), "GDW_reservoirs_v1_0": (5, 35_295)}
MAX_UNPACKED_BYTES = 512 * 1024 * 1024
MAX_MEMBERS = 100
MAX_MEMBER_BYTES = 256 * 1024 * 1024
MAX_NAME_BYTES = 256
CHUNK = 65536
PROFILE = "oc-gdw-v1-original-shapefile-zip-structure-v0"


class GDWArchiveError(ValueError):
    """Invalid original file, ZIP stream or declared shapefile structure."""


def _hash_file(path: Path) -> tuple[int, str, str]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > PROVIDER_BYTES:
        raise GDWArchiveError("expected regular, bounded, non-symlink local archive")
    sha, md5 = hashlib.sha256(), hashlib.md5(usedforsecurity=False)
    n = 0
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            n += len(block)
            if n > PROVIDER_BYTES:
                raise GDWArchiveError("archive exceeds original byte bound")
            sha.update(block)
            md5.update(block)
    return n, sha.hexdigest(), md5.hexdigest()


def _consume(f, n: int) -> None:
    if n < 0:
        raise GDWArchiveError("negative shapefile record length")
    while n:
        chunk = f.read(min(n, CHUNK))
        if not chunk:
            raise GDWArchiveError("truncated shape record")
        n -= len(chunk)


def _header(f, size: int, expected_type: int) -> None:
    head = f.read(100)
    if len(head) != 100 or size < 100:
        raise GDWArchiveError("truncated SHP/SHX header")
    if (struct.unpack_from(">I", head, 0)[0] != 9994
            or struct.unpack_from("<I", head, 28)[0] != 1000
            or struct.unpack_from("<I", head, 32)[0] != expected_type
            or struct.unpack_from(">I", head, 24)[0] * 2 != size):
        raise GDWArchiveError("SHP/SHX identity, geometry type or length mismatch")


def _members(z: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    infos = z.infolist()
    if not 1 <= len(infos) <= MAX_MEMBERS:
        raise GDWArchiveError("unexpected ZIP member count")
    total = 0
    seen = set()
    members = {}
    for i in infos:
        name = i.filename
        # Prevent archive path traversal, casefold collisions and non-regular entries.
        if (not isinstance(name, str) or not name.isascii() or len(name) > MAX_NAME_BYTES
                or not re.fullmatch(r"[A-Za-z0-9._/-]+", name)
                or name.startswith("/") or "//" in name or
                any(p in ("", ".", "..") for p in name.rstrip("/").split("/"))):
            raise GDWArchiveError("unsafe original archive member path")
        key = name.casefold()
        if key in seen:
            raise GDWArchiveError("duplicate archive path")
        seen.add(key)
        unix_type = (i.external_attr >> 16) & 0o170000
        if unix_type not in (0, stat.S_IFDIR if i.is_dir() else stat.S_IFREG):
            raise GDWArchiveError("non-regular or symlink archive member")
        if i.flag_bits & 1 or i.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise GDWArchiveError("encrypted or unsupported compression")
        if i.file_size > MAX_MEMBER_BYTES or i.file_size < 0:
            raise GDWArchiveError("oversized archive member")
        total += i.file_size
        if total > MAX_UNPACKED_BYTES:
            raise GDWArchiveError("unpacked ZIP exceeds memory/work bound")
        if not i.is_dir():
            members[name.lower()] = i
    return members


def _find(members: dict, stem: str, ext: str) -> zipfile.ZipInfo:
    ending = (stem + ext).lower()
    options = [info for key, info in members.items() if key.split("/")[-1] == ending]
    if len(options) != 1:
        raise GDWArchiveError("missing or ambiguous required shapefile sidecar")
    return options[0]


def _geo_point(raw: bytes) -> tuple[float, float]:
    if len(raw) != 16:
        raise GDWArchiveError("truncated original coordinate pair")
    lon, lat = struct.unpack("<dd", raw)
    if not all(map(math.isfinite, (lon, lat))) or not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise GDWArchiveError("out-of-bounds/nonfinite WGS84 coordinate")
    return lon, lat


def _polygon_record(f, n: int) -> None:
    if n < 40:
        raise GDWArchiveError("short polygon content")
    header = f.read(40)
    if len(header) != 40:
        raise GDWArchiveError("truncated polygon header")
    xmin, ymin, xmax, ymax, part_count, point_count = struct.unpack("<ddddII", header)
    if (not all(map(math.isfinite, (xmin, ymin, xmax, ymax)))
            or not (-180 <= xmin <= xmax <= 180 and -90 <= ymin <= ymax <= 90)
            or not 1 <= part_count <= 100_000 or not 4 <= point_count <= 5_000_000
            or part_count * 4 + point_count * 16 != n - 40):
        raise GDWArchiveError("invalid polygon bounds/ring table size")
    raw_parts = f.read(4 * part_count)
    if len(raw_parts) != 4 * part_count:
        raise GDWArchiveError("truncated polygon ring offsets")
    parts = struct.unpack("<" + "I" * part_count, raw_parts)
    if parts[0] != 0 or any((b - a) < 4 for a, b in zip(parts, (*parts[1:], point_count))):
        raise GDWArchiveError("invalid polygon ring starts or too-short rings")
    # Read bounded coordinate pairs, without materialising rings, IDs or geometries.
    next_index, first, last = 0, None, None
    for idx in range(point_count):
        if next_index < part_count and idx == parts[next_index]:
            if next_index and first != last:
                raise GDWArchiveError("polygon ring not exactly closed")
            first = None
            next_index += 1
        pt = _geo_point(f.read(16))
        if not (xmin - 1e-8 <= pt[0] <= xmax + 1e-8 and
                ymin - 1e-8 <= pt[1] <= ymax + 1e-8):
            raise GDWArchiveError("polygon record bounds exclude coordinate")
        if first is None:
            first = pt
        last = pt
    if first != last:
        raise GDWArchiveError("final polygon ring not exactly closed")


def _shape_records(z: zipfile.ZipFile, shp: zipfile.ZipInfo, shx: zipfile.ZipInfo,
                   shape_type: int, expected_count: int) -> int:
    if shx.file_size != 100 + expected_count * 8:
        raise GDWArchiveError("SHX index row count mismatch")
    count, offset_words = 0, 50
    with z.open(shp) as f, z.open(shx) as index:
        _header(f, shp.file_size, shape_type)
        _header(index, shx.file_size, shape_type)
        while count < expected_count:
            entry = index.read(8)
            rec = f.read(8)
            if len(entry) != 8 or len(rec) != 8:
                raise GDWArchiveError("truncated SHP or SHX record")
            index_offset, index_length = struct.unpack(">II", entry)
            record_number, record_words = struct.unpack(">II", rec)
            if (index_offset != offset_words or index_length != record_words
                    or record_number != count + 1 or record_words < 2
                    or record_words * 2 > MAX_MEMBER_BYTES):
                raise GDWArchiveError("SHP/SHX offset, record number or byte-length mismatch")
            geom_type = f.read(4)
            if len(geom_type) != 4 or struct.unpack("<I", geom_type)[0] != shape_type:
                raise GDWArchiveError("unexpected/null shapefile record geometry type")
            if shape_type == 1:
                if record_words != 10:
                    raise GDWArchiveError("unexpected point content length")
                _geo_point(f.read(16))
            elif shape_type == 5:
                _polygon_record(f, record_words * 2 - 4)
            else:
                raise GDWArchiveError("unsupported geometry type in source check")
            offset_words += 4 + record_words
            count += 1
        if f.read(1) or index.read(1) or offset_words * 2 != shp.file_size:
            raise GDWArchiveError("unindexed shape bytes or trailing index data")
    return count


def _dbf_ids(z: zipfile.ZipFile, entry: zipfile.ZipInfo, expected: int) -> set[int]:
    """Check GDW_ID uniqueness without emitting or retaining provider rows after return."""
    with z.open(entry) as f:
        hdr = f.read(32)
        if len(hdr) != 32 or hdr[0] not in (3, 0x83):
            raise GDWArchiveError("unsupported/truncated DBF format")
        rows = struct.unpack_from("<I", hdr, 4)[0]
        header_size = struct.unpack_from("<H", hdr, 8)[0]
        row_size = struct.unpack_from("<H", hdr, 10)[0]
        if rows != expected or not 65 <= header_size <= 65535 or row_size < 2:
            raise GDWArchiveError("DBF header row count or layout mismatch")
        if (header_size - 33) % 32:
            raise GDWArchiveError("invalid DBF field descriptor table")
        if not (header_size + rows * row_size <= entry.file_size <= header_size + rows * row_size + 1):
            raise GDWArchiveError("DBF declared rows do not match byte size")
        defs = f.read(header_size - 32)
        if len(defs) != header_size - 32 or defs[-1] != 0x0d:
            raise GDWArchiveError("truncated/unterminated DBF field descriptors")
        offset, id_field = 1, None
        field_names = set()
        for pos in range(0, len(defs) - 1, 32):
            field = defs[pos:pos + 32]
            try:
                name = field[:11].split(b"\0", 1)[0].decode("ascii").upper()
            except UnicodeError as exc:
                raise GDWArchiveError("non-ASCII DBF field names") from exc
            width = field[16]
            if not name or name in field_names or width < 1:
                raise GDWArchiveError("invalid/duplicate DBF column descriptor")
            field_names.add(name)
            if name == "GDW_ID":
                if field[11:12] != b"N" or field[17] != 0:
                    raise GDWArchiveError("GDW_ID must be an integer DBF field")
                id_field = (offset, offset + width)
            offset += width
        if offset != row_size or id_field is None:
            raise GDWArchiveError("DBF row layout or GDW_ID column missing")
        ids = set()
        for _ in range(rows):
            row = f.read(row_size)
            if len(row) != row_size or row[0:1] != b" ":
                raise GDWArchiveError("truncated/deleted DBF source row")
            token = row[id_field[0]:id_field[1]].strip()
            if not re.fullmatch(rb"[0-9]{1,18}", token):
                raise GDWArchiveError("missing or invalid numeric GDW_ID")
            key = int(token)
            if key <= 0 or key in ids:
                raise GDWArchiveError("duplicate or zero GDW_ID")
            ids.add(key)
        rest = f.read(2)
        if rest not in (b"", b"\x1a"):
            raise GDWArchiveError("unexpected DBF trailer")
        return ids


def inspect(path: Path, *, expected_sha256: str | None = None,
            original_size: int = PROVIDER_BYTES,
            publisher_md5: str = PROVIDER_MD5,
            counts: dict[str, tuple[int, int]] | None = None) -> dict:
    """Inspect already-downloaded ZIP. Overrides are for synthetic unit tests only."""
    if expected_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise GDWArchiveError("lowercase pinned SHA256 required")
    size, digest, weak = _hash_file(path)
    if size != original_size or weak != publisher_md5:
        raise GDWArchiveError("original ZIP size or provider-declared MD5 mismatch")
    if expected_sha256 is not None and digest != expected_sha256:
        raise GDWArchiveError("independently pinned original SHA256 mismatch")
    targets = EXPECTED_COUNTS if counts is None else counts
    try:
        with zipfile.ZipFile(path) as z:
            members = _members(z)
            layer_counts = {}
            layer_ids = {}
            used = set()
            for name, (shape_type, expected) in targets.items():
                shp, shx, dbf, prj = (_find(members, name, e) for e in (".shp", ".shx", ".dbf", ".prj"))
                used.update((shp.filename, shx.filename, dbf.filename, prj.filename))
                with z.open(prj) as f:
                    if not 10 <= prj.file_size <= 4096:
                        raise GDWArchiveError("invalid projection sidecar length")
                    wkt = f.read(4097).decode("ascii", errors="strict").upper()
                    if ("GEOGCS" not in wkt or "WGS" not in wkt or
                            "PROJCS" in wkt or "PROJCRS" in wkt):
                        raise GDWArchiveError("projection not declared WGS84 geographic")
                n = _shape_records(z, shp, shx, shape_type, expected)
                layer_ids[name] = _dbf_ids(z, dbf, expected)
                layer_counts[name] = n
            points, polygons = layer_ids["GDW_barriers_v1_0"], layer_ids["GDW_reservoirs_v1_0"]
            unmatched = len(points - polygons)
            if not polygons.issubset(points) or unmatched != (
                    targets["GDW_barriers_v1_0"][1] - targets["GDW_reservoirs_v1_0"][1]):
                raise GDWArchiveError("GDW_ID source link relationship does not match v1 inventory")
            # Validate every remaining member CRC without extracting file bytes.
            for info in members.values():
                if info.filename in used:
                    continue
                with z.open(info) as f:
                    _consume(f, info.file_size)
            return {
                "profile": PROFILE, "source_id": "globaldamwatch.gdw.v1.0",
                "original_file": "GDW_v1_0_shp.zip", "original_bytes": size,
                "original_sha256": digest, "provider_declared_md5_matches": True,
                "caller_supplied_sha256_matches": expected_sha256 is not None,
                "member_count": len(members),
                "layer_record_counts": layer_counts,
                "shp_shx_dbf_row_counts_agree": True,
                "coordinate_bounds_and_polygon_ring_closure_checked": True,
                "zip_streams_crc_checked": True,
                "declared_geographic_wgs84": True,
                "dbf_gdw_id_subset_verified": True,
                "dbf_point_only_id_count": unmatched,
                "point_polygon_spatial_join_verified": False,
                "record_coordinates_or_ids_exported": False,
                "topology_validated": False,
                "missing_value_sentinels_applied": False,
                "model_input_admitted": False,
                "provider_bytes_committed": False,
            }
    except (OSError, zipfile.BadZipFile, EOFError, UnicodeError, struct.error, OverflowError) as exc:
        raise GDWArchiveError("invalid ZIP or source member structure") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", required=True, type=Path)
    parser.add_argument("--expected-sha256", help="independently frozen lowercase SHA256; do not derive from same input")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect(args.original_zip, expected_sha256=args.expected_sha256),
                         sort_keys=True, indent=2, allow_nan=False))
    except GDWArchiveError as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
