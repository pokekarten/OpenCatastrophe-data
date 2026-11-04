# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic ZIP / shapefile header fixtures, no original GIS bytes."""
import io
import os
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from research_runners.grwl_original_zip_structure_preflight_v0 import (
    OriginalZipError, SOURCE_FILES, _is_safe_entry, inspect_original_zip,
    inspect_zip_structure,
)


def shp_header(*, shape_type=3, length=100, bbox=(-10., -10., 10., 10.), magic=9994):
    b = bytearray(length)
    struct.pack_into('>i', b, 0, magic)
    struct.pack_into('>i', b, 24, length//2)
    struct.pack_into('<i', b, 28, 1000)
    struct.pack_into('<i', b, 32, shape_type)
    struct.pack_into('<4d', b, 36, *bbox)
    return bytes(b)


def dbf(*, count=2, columns=('width_mean', 'lakeflag'), bad_terminator=False, wrong_rows=False):
    header_size = 32 + 32 * len(columns) + 1
    row_size = 13
    content = bytearray(header_size + count * row_size)
    content[0] = 3
    struct.pack_into('<I', content, 4, count + (1 if wrong_rows else 0))
    struct.pack_into('<HH', content, 8, header_size, row_size)
    for idx, field in enumerate(columns):
        raw = field.encode('ascii')
        content[32+32*idx:32+32*idx+len(raw)] = raw
        content[32+32*idx+11] = ord('N')
        content[32+32*idx+16] = 6
    content[header_size-1] = 0 if bad_terminator else 0x0d
    return bytes(content)


def archive_bytes(*, paths=None, shape_type=3, shp_magic=9994, bbox=(-10.,-10.,10.,10.),
                  count=2, columns=('width_mean','lakeflag'), bad_dbf_terminator=False,
                  wrong_dbf_rows=False, prj='GEOGCS["GCS_WGS_1984"]', extra=None):
    paths = paths or ['GRWL.shp','GRWL.shx','GRWL.dbf','GRWL.prj']
    payloads = [
        shp_header(shape_type=shape_type, length=124, bbox=bbox, magic=shp_magic),
        shp_header(shape_type=shape_type, length=116, bbox=bbox),
        dbf(count=count, columns=columns, bad_terminator=bad_dbf_terminator, wrong_rows=wrong_dbf_rows),
        prj.encode(),
    ]
    mem = io.BytesIO()
    with zipfile.ZipFile(mem,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,payload in zip(paths,payloads):
            z.writestr(name,payload)
        if extra:
            z.writestr(*extra)
    return mem.getvalue()


def inspect(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        return inspect_zip_structure(z)


class StructurePreflightTests(unittest.TestCase):
    def test_valid_structure_only(self):
        result = inspect(archive_bytes())
        self.assertEqual(result['shapefile_record_count_from_shx_and_dbf_headers'],2)
        self.assertIn('WIDTH_MEAN',result['shapefile_dbf_columns'])
        self.assertFalse(result['dbf_rows_or_shp_geometry_records_read'])
        self.assertFalse(result['zip_member_payload_crc_verified'])

    def test_real_original_requires_fixed_archive_size(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/SOURCE_FILES['2018'][0]
            p.write_bytes(archive_bytes())
            with self.assertRaises(OriginalZipError):inspect_original_zip(p,'2018')

    def test_real_original_rejects_unknown_release(self):
        with self.assertRaises(OriginalZipError):inspect_original_zip(Path('x.zip'),'1900')

    def test_zipslip_parent_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(paths=['../GRWL.shp','GRWL.shx','GRWL.dbf','GRWL.prj']))

    def test_zipslip_absolute_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(paths=['/tmp/GRWL.shp','GRWL.shx','GRWL.dbf','GRWL.prj']))

    def test_backslash_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(paths=['dir\\GRWL.shp','GRWL.shx','GRWL.dbf','GRWL.prj']))

    def test_duplicates_case_insensitive_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(extra=('grwl.shp',b'BAD')))

    def test_incomplete_sidecars_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(paths=['GRWL.shp','GRWL.shx','GRWL.dbf','README.txt']))

    def test_mismatched_sidecar_stems_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(paths=['GRWL.shp','GRWL.shx','WRONG.dbf','GRWL.prj']))

    def test_non_polyline_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(shape_type=5))

    def test_bad_shp_magic_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(shp_magic=123))

    def test_bad_bbox_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(bbox=(181.,-10.,200.,10.)))

    def test_wrong_dbf_rows_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(wrong_dbf_rows=True))

    def test_missing_width_field_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(columns=('width_min','lakeflag')))

    def test_bad_dbf_terminator_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(bad_dbf_terminator=True))

    def test_unexpected_projection_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(prj='PROJCS["LOCAL"]'))

    def test_projected_wgs84_utm_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(prj='PROJCS["WGS_1984_UTM_Zone_32N",GEOGCS["GCS_WGS_1984"]]'))

    def test_directory_marker_is_permitted(self):
        items=['data/GRWL.shp','data/GRWL.shx','data/GRWL.dbf','data/GRWL.prj']
        self.assertEqual(inspect(archive_bytes(paths=items))['shapefile_record_count_from_shx_and_dbf_headers'],2)

    def test_duplicate_field_names_rejected(self):
        with self.assertRaises(OriginalZipError):inspect(archive_bytes(columns=('width_mean','width_mean','lakeflag')))

    def test_symlink_header_rejected(self):
        info = zipfile.ZipInfo('GRWL.shp')
        info.create_system = 3
        info.external_attr = (0o120777 << 16)
        self.assertFalse(_is_safe_entry(info))

    def test_distinct_zip_checksum_lists_are_frozen(self):
        self.assertEqual(SOURCE_FILES['2026'][1] - SOURCE_FILES['2018'][1], 88699)
        self.assertNotEqual(SOURCE_FILES['2026'][2], SOURCE_FILES['2018'][2])

    def test_extra_unrelated_txt_does_not_affect_structure(self):
        result=inspect(archive_bytes(extra=('readme.txt',b'123')))
        self.assertEqual(result['zip_members'],5)


if __name__=='__main__':
    unittest.main()
