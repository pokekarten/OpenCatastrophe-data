# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ZIP and GPKG header security/identity tests."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from research_runners.luxembourg_bati3d_zip_preflight_v0 import inspect_original_zip, ArchivePreflightError


class TestLuxembourgZip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "source.zip"

    def write(self, entries):
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as out:
            for name, data in entries:
                out.writestr(name, data)
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def good(self):
        return self.write([("act2023v2.gpkg", b"SQLite format 3\0" + b"a" * 128)])

    def test_complete_bounded_signature_crc_and_receipt(self):
        h = self.good()
        result = inspect_original_zip(self.path, expected_sha256=h)
        self.assertEqual(result["original_zip_sha256"], h)
        self.assertTrue(result["zip_crc_verified_for_gpkg"])
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["gpkg_schema_and_crs_verified"])
        self.assertEqual(result, inspect_original_zip(self.path, expected_sha256=h))

    def test_wrong_digest_blocks(self):
        self.good()
        with self.assertRaisesRegex(ArchivePreflightError, "mismatches"):
            inspect_original_zip(self.path, expected_sha256="0" * 64)

    def test_unpinned_digest_blocks(self):
        self.good()
        with self.assertRaisesRegex(ArchivePreflightError, "predeclared"):
            inspect_original_zip(self.path, expected_sha256="unknown")

    def test_path_traversal_blocks(self):
        h = self.write([("../bad.gpkg", b"SQLite format 3\0" + b"a" * 64)])
        with self.assertRaisesRegex(ArchivePreflightError, "unsafe member"):
            inspect_original_zip(self.path, expected_sha256=h)

    def test_bad_header_blocks(self):
        h = self.write([("a.gpkg", b"pretend-this-is-a-database" * 4)])
        with self.assertRaisesRegex(ArchivePreflightError, "header"):
            inspect_original_zip(self.path, expected_sha256=h)

    def test_two_gpkg_members_block(self):
        h = self.write([("a.gpkg", b"SQLite format 3\0"+b"a"*64), ("b.gpkg", b"SQLite format 3\0"+b"b"*64)])
        with self.assertRaisesRegex(ArchivePreflightError, "exactly one"):
            inspect_original_zip(self.path, expected_sha256=h)

    def test_archive_symlink_blocks(self):
        h = self.good()
        link = Path(self.tmp.name) / "alias.zip"
        link.symlink_to(self.path)
        with self.assertRaisesRegex(ArchivePreflightError, "non-symlink"):
            inspect_original_zip(link, expected_sha256=h)

    def test_zip_member_symlink_blocks(self):
        info = zipfile.ZipInfo("a.gpkg")
        info.create_system = 3
        info.external_attr = (0o120777 << 16)
        with zipfile.ZipFile(self.path, "w") as out:
            out.writestr(info, b"SQLite format 3\0"+b"a"*64)
        h = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ArchivePreflightError, "symlink"):
            inspect_original_zip(self.path, expected_sha256=h)

    def test_excessive_expansion_blocks(self):
        h = self.write([("a.gpkg", b"SQLite format 3\0" + b"0" * 100000)])
        with self.assertRaisesRegex(ArchivePreflightError, "compression ratio"):
            inspect_original_zip(self.path, expected_sha256=h)


if __name__ == "__main__":
    unittest.main()
