# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only offline tests, no original archived data."""

import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners.nyc_building_archive_receipt_v0 import (
    ArchiveGateError, _csv_header, inspect, parse_version_date, sha256_file,
)

HEADER = (
    'the_geom,BIN,DOITT_ID,BASE_BBL,Map Pluto BBL,Feature Code,'
    'Construction Year,LAST_EDITED_DATE,Other\n'
)


class ArchiveReceiptTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.dir = Path(self.folder.name)

    def file(self, name="source.csv", content=None):
        p = self.dir / name
        p.write_bytes((HEADER + '"MULTIPOLYGON (dummy)",1000001,22,1000000001,1000000001,2100,1960,2024-01-01,abc\n').encode() if content is None else content)
        return p

    @staticmethod
    def h(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_local_csv_hash_and_header_only_verified(self):
        file = self.file()
        result = inspect(str(file), self.h(file), "2024-12-30")
        self.assertEqual(result['source_view_id'], '5zhs-2jue')
        self.assertEqual(result['required_header_fields_found'], 8)
        self.assertEqual(result['header_column_count'], 9)
        self.assertTrue(result['entire_container_sha256_matches_expected'])
        for key in ('full_csv_record_count_verified', 'official_snapshot_release_authenticity_verified', 'historic_inventory_year_2024_admitted', 'source_license_rights_approved', 'insured_tiv_or_losses_calculated', 'raw_source_rows_identifiers_geometry_or_file_path_printed'):
            self.assertFalse(result[key])
        self.assertNotIn(str(file), str(result))
        self.assertNotIn('MULTIPOLYGON', str(result))
        self.assertNotIn('1000001', str(result))

    def test_zip_with_one_csv_is_supported_without_extraction(self):
        p = self.dir / 'source.zip'
        with ZipFile(p, 'w', ZIP_DEFLATED) as z:
            z.writestr('folder/original.csv', HEADER + 'test,1,2,3,4,5,6,7,z\n')
        r = inspect(str(p), self.h(p), '2024-11-13')
        self.assertEqual(r['container_format'], 'single_csv_zip')
        self.assertFalse(r['official_snapshot_release_authenticity_verified'])
        self.assertFalse((self.dir / 'folder/original.csv').exists())

    def test_hash_mismatch_and_non_2024_date_are_blocked(self):
        p = self.file()
        with self.assertRaises(ArchiveGateError):
            inspect(str(p), '0' * 64, '2024-12-31')
        for dt in ('2025-01-01', '2024-02-30', '2024-13-01', '2024-01-01T01:00:00', '2023-12-31'):
            with self.subTest(dt=dt), self.assertRaises(ArchiveGateError):
                inspect(str(p), self.h(p), dt)
        with self.assertRaises(ArchiveGateError):
            inspect(str(p), self.h(p), '2024-12-31', source_view='ipkp-snf6')

    def test_missing_column_never_admitted(self):
        p = self.file(content=(HEADER.replace('Map Pluto BBL,', '') + 'dummy\n').encode())
        with self.assertRaisesRegex(ArchiveGateError, 'mappluto_bbl'):
            inspect(str(p), self.h(p), '2024-12-31')

    def test_bad_duplicate_and_binary_csv_headers(self):
        for text in ('bin,bin\n', 'a,b,c\n', 'bin,\x00name\n', 'x' * 40000 + '\n', 'bin,bin'):
            p = self.file(content=text.encode())
            with self.subTest(text=text[:9]), self.assertRaises(ArchiveGateError):
                inspect(str(p), self.h(p), '2024-12-31')

    def test_reject_multiple_zip_members_or_traversal(self):
        for entries in ([('sample.csv', HEADER), ('bad.csv', HEADER)], [('../outside.csv', HEADER)], [('/abs.csv', HEADER)]):
            p = self.dir / 'source.zip'
            with ZipFile(p, 'w', ZIP_DEFLATED) as z:
                for name, value in entries:
                    z.writestr(name, value)
            with self.subTest(entries=entries[0][0]), self.assertRaises(ArchiveGateError):
                inspect(str(p), self.h(p), '2024-12-31')

    def test_reject_symlink_and_wrong_extension(self):
        p = self.file()
        link = self.dir / 'a.csv'
        link.symlink_to(p)
        with self.assertRaises(ArchiveGateError):
            inspect(str(link), self.h(p), '2024-12-31')
        wrong = self.file(name='source.txt')
        with self.assertRaises(ArchiveGateError):
            inspect(str(wrong), self.h(wrong), '2024-12-31')

    def test_source_data_never_returned_in_report(self):
        p = self.file(content=(HEADER + 'OWNER_NAME: SECRET,OWNER_VALUE,111,222,333,444,555,666,777\n').encode())
        result = inspect(str(p), self.h(p), '2024-12-31')
        self.assertNotIn('SECRET', str(result))
        self.assertFalse(result['historic_inventory_year_2024_admitted'])


if __name__ == '__main__':
    unittest.main()
