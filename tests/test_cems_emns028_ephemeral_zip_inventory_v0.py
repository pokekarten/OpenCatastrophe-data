# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully synthetic archive tests; never download provider data."""
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from scripts.cems_emns028_ephemeral_zip_inventory_v0 import inspect_local


class InventoryTests(unittest.TestCase):
    def test_synthetic_gdb_inventory_legal_and_model_flags_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.zip"
            with ZipFile(path, "w") as zf:
                zf.writestr("example.gdb/a.gdbtable", b"fictional")
                zf.writestr("example.gdb/a.gdbtablx", b"fictional")
                zf.writestr("AOI04_observed_context.txt", b"not real flood data")
            res = inspect_local(path)
            self.assertEqual(res["archive_member_count"], 3)
            self.assertEqual(res["gdb_directory_count"], 1)
            self.assertEqual(res["aoi04_filename_hint_count"], 1)
            self.assertEqual(len(res["archive_sha256_from_this_download"]), 64)
            self.assertFalse(res["aoi04_observed_extent_layer_verified"])
            self.assertFalse(res["activation_specific_reuse_rights_cleared"])
            self.assertFalse(res["cat_model_admitted"])

    def test_reject_invalid_zip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "fake.zip"
            path.write_bytes(b"not a zip")
            with self.assertRaisesRegex(ValueError, "not a ZIP"):
                inspect_local(path)

    def test_reject_zip_slip_member_even_without_extract(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "fake.zip"
            with ZipFile(path, "w") as zf:
                zf.writestr("../escape.txt", b"fictional")
            with self.assertRaisesRegex(ValueError, "unsafe"):
                inspect_local(path)


if __name__ == "__main__":
    unittest.main()
