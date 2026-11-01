# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: schema classifier and ZIP FileGDB safe extraction."""
import stat
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZipInfo

from research_runners.cems_emns028_filegdb_layer_inventory_v0 import (
    classify_name, extract_gdb_only, gdb_members,
)


class FileGdbMetadataTests(unittest.TestCase):
    def test_aoi04_observed_layer_is_hint_not_proof(self):
        x = classify_name("EMSN028_AOI04_Observed_FloodExtent", ["zone", "area_code"])
        self.assertTrue(x["aoi04_name_hint"])
        self.assertTrue(x["observed_extent_name_hint"])
        self.assertTrue(x["has_aoi_discriminator_field_hint"])
        self.assertFalse(x["observed_aoi04_layer_proven"])

    def test_modeled_maximum_depth_must_not_count_observed(self):
        x = classify_name("AOI_04_observed_maxflood_depth", [])
        self.assertTrue(x["modeled_or_depth_name_hint"])
        self.assertFalse(x["observed_extent_name_hint"])

    def test_safe_single_gdb_extracted_without_other_files(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "test.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("test.gdb/a.gdbtable", b"fixture")
                z.writestr("styles/some.lyr", b"style")
            with ZipFile(archive) as z:
                root = extract_gdb_only(z, Path(td) / "extract")
            self.assertEqual((root / "a.gdbtable").read_bytes(), b"fixture")
            self.assertFalse((Path(td) / "extract/styles/some.lyr").exists())

    def test_reject_zip_slip_before_extraction(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "test.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("../test.gdb/file.gdbtable", b"bad")
            with ZipFile(archive) as z:
                with self.assertRaisesRegex(ValueError, "unsafe"):
                    gdb_members(z)

    def test_reject_symlinks(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "test.zip"
            info = ZipInfo("test.gdb/link.gdbtable")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with ZipFile(archive, "w") as z:
                z.writestr(info, "outside")
            with ZipFile(archive) as z:
                with self.assertRaisesRegex(ValueError, "symlink"):
                    gdb_members(z)

    def test_reject_two_gdb_roots(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "test.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("one.gdb/a.gdbtable", b"fixture")
                z.writestr("two.gdb/a.gdbtable", b"fixture")
            with ZipFile(archive) as z:
                with self.assertRaisesRegex(ValueError, "exactly one"):
                    gdb_members(z)


if __name__ == "__main__":
    unittest.main()
