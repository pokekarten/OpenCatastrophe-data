# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original GDW v1 GDB ZIP safety and source identity checks."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

from research_runners import gdw_v1_original_filegdb_quality_v0 as q

def archive(additional=None):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("GDW_v1_0/GDW_v1_0.gdb/a00000001.gdbtable", b"synthetic-gdb-member")
        z.writestr("GDW_v1_0/GDW_v1_0.gdb/a00000001.gdbtablx", b"synthetic-index")
        z.writestr("GDW_v1_0/GDW_TechDoc_v1_0.pdf", b"synthetic-manual")
        if additional is not None:
            name, value = additional
            z.writestr(name, value)
    return out.getvalue()


class GDWFileGDBSourceSafetyTests(unittest.TestCase):
    def test_synthetic_archive_path_and_bounded_streaming(self):
        b = archive()
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            members, folder = q.safe_members(z)
            self.assertEqual(folder, "GDW_v1_0/GDW_v1_0.gdb")
            self.assertEqual(len(members), 3)
            with tempfile.TemporaryDirectory() as temp:
                q.extract_members(z, members, Path(temp))
                self.assertTrue((Path(temp)/folder/"a00000001.gdbtable").is_file())

    def test_reject_traversal_duplicate_symlink_and_second_gdb_root(self):
        candidates = (
            ("../../private.txt", b"unsafe"),
            ("GDW_v1_0/GDW_v1_0.gdb/A00000001.GDBTABLE", b"casefold duplicate"),
            ("Other.gdb/a00000001.gdbtable", b"second root"),
        )
        for item in candidates:
            with self.subTest(item=item[0]):
                with zipfile.ZipFile(io.BytesIO(archive(item))) as z:
                    with self.assertRaises(q.GDWFileGDBError):
                        q.safe_members(z)
        with io.BytesIO() as target:
            with zipfile.ZipFile(target, "w") as z:
                z.writestr("s.gdb/a.gdbtable", b"x")
                info=zipfile.ZipInfo("s.gdb/link")
                info.create_system=3
                info.external_attr=stat.S_IFLNK<<16
                z.writestr(info,b"etc/passwd")
            with zipfile.ZipFile(io.BytesIO(target.getvalue())) as z:
                with self.assertRaises(q.GDWFileGDBError):
                    q.safe_members(z)

    def test_wrong_original_provider_digest_and_file_size_block(self):
        b=archive()
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"original.zip"
            p.write_bytes(b)
            md5=hashlib.md5(b, usedforsecurity=False).hexdigest()
            sha=hashlib.sha256(b).hexdigest()
            result=q.original_file_identity(p, expected_size=len(b),
                                            expected_md5=md5, expected_sha256=sha)
            self.assertTrue(result["separately_pinned_sha256_compared"])
            self.assertEqual(result["original_sha256"],sha)
            with self.assertRaisesRegex(q.GDWFileGDBError,"MD5 mismatch"):
                q.original_file_identity(p, expected_size=len(b),
                                         expected_md5="0"*32)
            with self.assertRaisesRegex(q.GDWFileGDBError,"mismatch"):
                q.original_file_identity(p, expected_size=len(b)+1,
                                         expected_md5=md5)
            with self.assertRaisesRegex(q.GDWFileGDBError,"SHA256 mismatch"):
                q.original_file_identity(p, expected_size=len(b),
                                         expected_md5=md5, expected_sha256="0"*64)

    def test_geodatabase_role_and_gdw_id_contract(self):
        self.assertEqual(q.layer_role("GDW_barriers_v1_0"),"GDW_barriers_v1_0")
        self.assertEqual(q.layer_role("GDW-reservoirs-v1-0"),"GDW_reservoirs_v1_0")
        self.assertIsNone(q.layer_role("unreviewed_hazard_table"))
        self.assertEqual(q._gdw_id(123),123)
        self.assertEqual(q._gdw_id(123.0),123)
        for value in ("123",0,-99,1.25,float("nan"),float("inf")):
            with self.subTest(value=str(value)),self.assertRaises(q.GDWFileGDBError):
                q._gdw_id(value)

    def test_original_source_metadata_and_nonadmission(self):
        self.assertEqual(q.GDW_FILE_ID,47913742)
        self.assertEqual(q.PROVIDER_BYTES,57476758)
        self.assertEqual(q.PROVIDER_MD5,"410d1ed16312ac613975fd092c193c65")
        self.assertEqual(q.EXPECTED_POINTS,41145)
        self.assertEqual(q.EXPECTED_POLYGONS,35295)
        self.assertEqual(q.EXPECTED_POINT_ONLY,5850)


if __name__=="__main__":
    unittest.main()
