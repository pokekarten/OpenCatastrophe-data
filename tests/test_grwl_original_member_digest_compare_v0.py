# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only member-byte/CRC/size comparison tests; no original GRWL ZIPs."""
import io
import zipfile
import unittest

from research_runners.grwl_original_member_digest_compare_v0 import (
    SCHEMA, OriginalZipError, compare_digest_inventories, member_digests,
)

CORE = {'GRWL.shp':b'GEOMETRY-ORIGINAL', 'GRWL.shx':b'INDEX-ORIGINAL',
        'GRWL.dbf':b'ATTRIBUTES-ORIGINAL', 'GRWL.prj':b'WGS84'}


def synthetic_zip(contents=None, compression=zipfile.ZIP_DEFLATED):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',compression=compression) as z:
        for key,payload in (contents or CORE).items():
            z.writestr(key,payload)
    return b.getvalue()


def digest(b):
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        return member_digests(z)


class OriginalMemberDigestTests(unittest.TestCase):
    def test_identical_member_bytes_different_zip_compression(self):
        x = digest(synthetic_zip(compression=zipfile.ZIP_STORED))
        y = digest(synthetic_zip(compression=zipfile.ZIP_DEFLATED))
        r = compare_digest_inventories(x,y)
        self.assertEqual(r['schema'], SCHEMA)
        self.assertTrue(r['identical_uncompressed_member_payloads'])
        self.assertTrue(r['core_shapefile_bytes_identical'])
        self.assertTrue(r['shp_geometry_member_bytes_identical'])
        self.assertTrue(r['dbf_attribute_member_bytes_identical'])
        for key in ('any_real_width_change_verified','any_real_geometry_change_interpreted',
                    'flood_hazard_calibrated','source_data_admitted','production_database_modified'):
            self.assertIs(r[key],False)

    def test_xml_metadata_only_change_core_identical(self):
        a={**CORE,'GRWL.shp.xml':b'old'}
        b={**CORE,'GRWL.shp.xml':b'new XML'}
        r=compare_digest_inventories(digest(synthetic_zip(a)),digest(synthetic_zip(b)))
        self.assertFalse(r['identical_uncompressed_member_payloads'])
        self.assertTrue(r['core_shapefile_bytes_identical'])
        self.assertEqual(r['member_files_changed'],['grwl.shp.xml'])

    def test_shp_byte_change_is_not_interpreted_as_width_change(self):
        newer={**CORE,'GRWL.shp':b'GEOMETRY-V02'}
        r=compare_digest_inventories(digest(synthetic_zip()),digest(synthetic_zip(newer)))
        self.assertFalse(r['shp_geometry_member_bytes_identical'])
        self.assertTrue(r['dbf_attribute_member_bytes_identical'])
        self.assertFalse(r['any_real_width_change_verified'])

    def test_dbf_byte_change_is_not_interpreted_as_width_change(self):
        newer={**CORE,'GRWL.dbf':b'ATTRIBUTES-NEW'}
        r=compare_digest_inventories(digest(synthetic_zip()),digest(synthetic_zip(newer)))
        self.assertFalse(r['dbf_attribute_member_bytes_identical'])
        self.assertTrue(r['shp_geometry_member_bytes_identical'])
        self.assertFalse(r['any_real_width_change_verified'])

    def test_index_change_makes_core_unequal(self):
        newer={**CORE,'GRWL.shx':b'NEW-INDEX'}
        r=compare_digest_inventories(digest(synthetic_zip()),digest(synthetic_zip(newer)))
        self.assertFalse(r['core_shapefile_bytes_identical'])
        self.assertTrue(r['shp_geometry_member_bytes_identical'])

    def test_file_addition_and_removal_reported(self):
        a={**CORE,'GRWL.sbn':b'INDEX1'}
        b={**CORE,'GRWL.sbx':b'INDEX2'}
        r=compare_digest_inventories(digest(synthetic_zip(a)),digest(synthetic_zip(b)))
        self.assertEqual(r['member_files_only_2018'],['grwl.sbn'])
        self.assertEqual(r['member_files_only_2026'],['grwl.sbx'])
        self.assertTrue(r['core_shapefile_bytes_identical'])

    def test_missing_prj_flags_core_not_complete(self):
        a=digest(synthetic_zip()); b={k:v for k,v in a.items() if k!='grwl.prj'}
        r=compare_digest_inventories(a,b)
        self.assertFalse(r['core_shapefile_bytes_identical'])

    def test_deterministic_sorted_names(self):
        z={k:CORE[k] for k in reversed(list(CORE))}
        result=digest(synthetic_zip(z))
        self.assertEqual(list(result),sorted(result))

    def test_malformed_zip_member_crc_rejected(self):
        original=synthetic_zip(compression=zipfile.ZIP_STORED)
        needle=b'GEOMETRY-ORIGINAL'
        self.assertIn(needle,original)
        corrupted=original.replace(needle,b'GEOMETRY-CORRUPT!',1)
        self.assertEqual(len(original),len(corrupted))
        with self.assertRaises(OriginalZipError):digest(corrupted)

    def test_duplicate_casefold_names_rejected(self):
        z={**CORE,'grwl.shp':b'extra'}
        with self.assertRaises(OriginalZipError):digest(synthetic_zip(z))

    def test_path_traversal_rejected(self):
        z={**CORE,'../evil.txt':b'x'}
        with self.assertRaises(OriginalZipError):digest(synthetic_zip(z))

    def test_empty_member_rejected(self):
        z={**CORE,'GRWL.shp.xml':b''}
        with self.assertRaises(OriginalZipError):digest(synthetic_zip(z))

    def test_digest_count_and_sha256_are_member_only(self):
        rec=digest(synthetic_zip())
        self.assertEqual(rec['grwl.shp']['uncompressed_bytes'],len(CORE['GRWL.shp']))
        self.assertEqual(len(rec['grwl.shp']['sha256_of_uncompressed_member_bytes']),64)
        self.assertNotIn('raw',rec['grwl.shp'])
        self.assertNotIn('contents',rec['grwl.shp'])


if __name__ == '__main__':
    unittest.main()
