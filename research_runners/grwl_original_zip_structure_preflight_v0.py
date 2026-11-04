# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline GRWL summary archive integrity and shapefile structure preflight.

Requires independently downloaded local, version-pinned ZIP archives. Never
extracts members, reads DBF rows or geometry payloads, or emits source bytes.
This is a structural receipt, not a geospatial comparison or admission gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import stat
import struct
import zipfile
from pathlib import Path, PurePosixPath

SCHEMA = 'opencatastrophe-grwl-original-zip-preflight-v0'
MAX_ZIP_ENTRIES = 128
MAX_TOTAL_UNCOMPRESSED = 2_000_000_000
MAX_SINGLE_UNCOMPRESSED = 1_500_000_000
MAX_COMPRESSION_RATIO = 300
MAX_MEMBER_NAME = 255
CHUNK = 1 << 20
SOURCE_FILES = {
    '2018': ('GRWL_summaryStats_V01.01.zip', 43_194_162, 'c37021e144fbff19ae3fc4e701d85d38'),
    '2026': ('GRWL_summaryStats_V01.02.zip', 43_282_861, 'cac403c1a59bce7a74432085d3f5bd3a'),
}
REQUIRED_DBF_FIELDS = frozenset({'WIDTH_MEAN', 'LAKEFLAG'})


class OriginalZipError(ValueError):
    """Archive failed source-integrity or safe-structure checks."""


def _is_safe_entry(item: zipfile.ZipInfo) -> bool:
    name = item.filename
    if (not name or len(name) > MAX_MEMBER_NAME or '\\' in name or '\x00' in name or
            name.startswith('/') or '//' in name or not name.isascii()):
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {'.', '..'} for part in name.split('/')):
        return False
    if item.is_dir() and not name.endswith('/'):
        return False
    if item.create_system == 3 and stat.S_ISLNK(item.external_attr >> 16):
        return False
    return True


def _safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    entries = archive.infolist()
    if not 4 <= len(entries) <= MAX_ZIP_ENTRIES:
        raise OriginalZipError('unexpected ZIP member count')
    seen = set()
    total = 0
    for item in entries:
        if not _is_safe_entry(item):
            raise OriginalZipError('unsafe ZIP entry path or type')
        key = item.filename.casefold()
        if key in seen:
            raise OriginalZipError('duplicate case-insensitive ZIP member name')
        seen.add(key)
        if item.flag_bits & 0x1 or item.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise OriginalZipError('encrypted or unsupported ZIP compression')
        if item.is_dir():
            if item.file_size or item.compress_size:
                raise OriginalZipError('non-empty ZIP directory marker')
            continue
        if item.file_size <= 0 or item.file_size > MAX_SINGLE_UNCOMPRESSED or item.compress_size <= 0:
            raise OriginalZipError('invalid or oversized ZIP member')
        if item.file_size / item.compress_size > MAX_COMPRESSION_RATIO:
            raise OriginalZipError('ZIP compression ratio cap exceeded')
        total += item.file_size
        if total > MAX_TOTAL_UNCOMPRESSED:
            raise OriginalZipError('aggregate ZIP expansion cap exceeded')
    return entries


def _read_header(archive: zipfile.ZipFile, info: zipfile.ZipInfo, max_bytes: int) -> bytes:
    # zipfile can decompress a small fixed buffer to satisfy read(); it does
    # not materialize the original vector or tabular records.
    with archive.open(info, 'r') as handle:
        return handle.read(max_bytes)


def _shapefile_header(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
    data = _read_header(archive, info, 100)
    if len(data) != 100 or info.file_size < 100:
        raise OriginalZipError('truncated shapefile index/geometry header')
    if struct.unpack_from('>i', data, 0)[0] != 9994:
        raise OriginalZipError('invalid ESRI SHP header magic')
    declared_size = struct.unpack_from('>i', data, 24)[0] * 2
    if declared_size != info.file_size:
        raise OriginalZipError('SHP/SHX header length disagrees with ZIP member length')
    if struct.unpack_from('<i', data, 28)[0] != 1000:
        raise OriginalZipError('invalid ESRI shapefile version')
    kind = struct.unpack_from('<i', data, 32)[0]
    if kind not in (3, 13, 23):
        raise OriginalZipError('GRWL should be a polyline shapefile, not point/polygon')
    bbox = struct.unpack_from('<4d', data, 36)
    if not all(math.isfinite(v) for v in bbox) or bbox[0] > bbox[2] or bbox[1] > bbox[3]:
        raise OriginalZipError('invalid shapefile extent')
    if not (-180.0001 <= bbox[0] <= 180.0001 and -180.0001 <= bbox[2] <= 180.0001 and
            -90.0001 <= bbox[1] <= 90.0001 and -90.0001 <= bbox[3] <= 90.0001):
        raise OriginalZipError('GRWL WGS84 geographic extent constraint failed')
    return {'shape_type': kind, 'bounding_box_wgs84_degrees': list(bbox)}


def _dbf_header(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
    header = _read_header(archive, info, 32)
    if len(header) != 32 or info.file_size < 65:
        raise OriginalZipError('truncated DBF header')
    version = header[0]
    if version not in (0x03, 0x83):
        raise OriginalZipError('unexpected DBF version')
    row_count = struct.unpack_from('<I', header, 4)[0]
    header_size, row_size = struct.unpack_from('<HH', header, 8)
    if (row_count == 0 or header_size < 65 or header_size > 16_384 or
            (header_size - 33) % 32 != 0 or row_size <= 1 or
            header_size + row_size * row_count > info.file_size):
        raise OriginalZipError('DBF records and header lengths inconsistent')
    columns_count = (header_size - 33) // 32
    if columns_count < 2 or columns_count > 120:
        raise OriginalZipError('invalid DBF field count')
    fields_raw = _read_header(archive, info, header_size)
    if len(fields_raw) != header_size or fields_raw[-1] != 0x0d:
        raise OriginalZipError('missing DBF field-descriptor terminator')
    fields = []
    for idx in range(columns_count):
        raw = fields_raw[32 + idx * 32:64 + idx * 32]
        name = raw[:11].split(b'\x00', 1)[0].decode('ascii', errors='strict').upper()
        if not re.fullmatch(r'[A-Z][A-Z0-9_]{0,10}', name):
            raise OriginalZipError('invalid DBF field name')
        fields.append(name)
    if len(set(fields)) != len(fields) or not REQUIRED_DBF_FIELDS.issubset(fields):
        raise OriginalZipError('duplicate or missing critical GRWL DBF fields')
    return {'record_count_header': row_count, 'field_names': fields}


def inspect_zip_structure(archive: zipfile.ZipFile) -> dict:
    """Structural metadata only, callable with synthetic BytesIO fixtures."""
    entries = _safe_members(archive)
    by_ext = {}
    for item in entries:
        path = PurePosixPath(item.filename)
        ext = path.suffix.casefold()
        if ext in {'.shp', '.shx', '.dbf', '.prj'}:
            by_ext.setdefault(ext, []).append(item)
    if any(len(by_ext.get(ext, [])) != 1 for ext in ('.shp', '.shx', '.dbf', '.prj')):
        raise OriginalZipError('expected one complete shapefile: shp/shx/dbf/prj')
    stems = {PurePosixPath(by_ext[ext][0].filename).with_suffix('').as_posix().casefold()
             for ext in ('.shp', '.shx', '.dbf', '.prj')}
    if len(stems) != 1:
        raise OriginalZipError('shapefile sidecars do not share a stem')
    shp = _shapefile_header(archive, by_ext['.shp'][0])
    shx = _shapefile_header(archive, by_ext['.shx'][0])
    if shp != shx or (by_ext['.shx'][0].file_size - 100) % 8 != 0:
        raise OriginalZipError('SHP and SHX headers disagree')
    indexed_records = (by_ext['.shx'][0].file_size - 100) // 8
    if by_ext['.shp'][0].file_size < 100 + indexed_records * 12:
        raise OriginalZipError('SHP too short for SHX-declared number of records')
    dbf = _dbf_header(archive, by_ext['.dbf'][0])
    if indexed_records != dbf['record_count_header']:
        raise OriginalZipError('SHX index and DBF record count disagree')
    prj_info = by_ext['.prj'][0]
    if prj_info.file_size > 16_384:
        raise OriginalZipError('unexpectedly large PRJ metadata')
    prj = _read_header(archive, prj_info, 16384).decode('utf-8-sig', errors='strict')
    if (not re.search(r'GEOGCS\s*\[|GEOGCRS\s*\[', prj, re.IGNORECASE) or
        re.search(r'PROJCS\s*\[|PROJCRS\s*\[', prj, re.IGNORECASE) or
        not re.search(r'WGS[_ ]?1984|WGS[_ ]?84|EPSG["\s,:]+4326', prj, re.IGNORECASE)):
        raise OriginalZipError('cannot verify geographic WGS84 from original PRJ text')
    return {
        'zip_members': len(entries),
        'zip_total_uncompressed_bytes_claimed': sum(i.file_size for i in entries),
        'shapefile_record_count_from_shx_and_dbf_headers': indexed_records,
        'shapefile_dbf_columns': dbf['field_names'],
        'geometry_shape_type': shp['shape_type'],
        'geometry_bbox_provider_wgs84_degrees': shp['bounding_box_wgs84_degrees'],
        'shapefile_header_and_sidecars_checked': True,
        'zip_member_payload_crc_verified': False,
        'dbf_rows_or_shp_geometry_records_read': False,
    }


def inspect_original_zip(path: Path, release: str) -> dict:
    """Verify original ZIP length and MD5, independently compute SHA256 and read headers."""
    if release not in SOURCE_FILES:
        raise OriginalZipError('unknown GRWL source release')
    filename, expected_size, expected_md5 = SOURCE_FILES[release]
    if path.name != filename or not path.is_file() or path.is_symlink() or path.stat().st_size != expected_size:
        raise OriginalZipError('local archive identity, size or type differs from original provider metadata')
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    try:
        with path.open('rb') as stream:
            while block := stream.read(CHUNK):
                md5.update(block)
                sha256.update(block)
            if md5.hexdigest() != expected_md5:
                raise OriginalZipError('original source ZIP MD5 does not match Zenodo-listed bytes')
            stream.seek(0)  # reuse the same original file descriptor, no path swap
            with zipfile.ZipFile(stream) as archive:
                structure = inspect_zip_structure(archive)
    except (zipfile.BadZipFile, UnicodeError, OSError) as exc:
        raise OriginalZipError('ZIP structure invalid or unreadable') from exc
    return {
        'release': release,
        'provider_archive_name': filename,
        'provider_archive_bytes': expected_size,
        'independently_verified_original_zip_md5': md5.hexdigest(),
        'independently_computed_original_zip_sha256': sha256.hexdigest(),
        'structural_metadata': structure,
        'source_data_admitted': False,
        'scientific_comparison_completed': False,
        'geospatial_records_loaded_or_compared': False,
        'model_input_approved': False,
        'production_database_modified': False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--2018-zip', type=Path, required=True)
    p.add_argument('--2026-zip', type=Path, required=True)
    args = p.parse_args(argv)
    try:
        early = inspect_original_zip(args.__dict__['2018_zip'], '2018')
        late = inspect_original_zip(args.__dict__['2026_zip'], '2026')
    except (OriginalZipError, OSError) as exc:
        p.error(str(exc))
    a, b = early['structural_metadata'], late['structural_metadata']
    result = {
        'schema': SCHEMA,
        'receipts': [early, late],
        'provider_simplified_archive_size_difference_bytes': SOURCE_FILES['2026'][1] - SOURCE_FILES['2018'][1],
        'shapefile_record_count_difference_from_headers': b['shapefile_record_count_from_shx_and_dbf_headers'] - a['shapefile_record_count_from_shx_and_dbf_headers'],
        'shapefile_fields_equal': a['shapefile_dbf_columns'] == b['shapefile_dbf_columns'],
        'geographic_bbox_equal_in_headers': a['geometry_bbox_provider_wgs84_degrees'] == b['geometry_bbox_provider_wgs84_degrees'],
        'row_values_and_geometry_changes_unknown': True,
        'source_data_admitted': False,
        'real_world_geometry_compared': False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
