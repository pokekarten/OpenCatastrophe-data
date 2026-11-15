# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only public ACT2013 archive contract tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

from research_runners.luxembourg_act2013_original_zip_receipt_v0 import (
    ACT2013SourceError, verify_original
)


class ACT2013ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.zip"

    def build(self, entries):
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in entries:
                archive.writestr(name, data)
        return hashlib.sha1(self.path.read_bytes()).hexdigest()

    def test_bounded_original_receipt_and_no_row_output(self):
        original = b"<CityModel><SECRET_PERSON_ID>must-not-output</SECRET_PERSON_ID></CityModel>"
        sha = self.build([("vintage/2013-city.gml", original)])
        receipt = verify_original(self.path, expected_provider_sha1=sha)
        self.assertEqual(receipt["publisher_sha1"], sha)
        self.assertEqual(receipt["original_zip_sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(receipt["member_extensions"], {"gml": 1})
        self.assertTrue(receipt["all_regular_member_crc_checks_passed"])
        self.assertFalse(receipt["model_input_admitted"])
        self.assertFalse(receipt["eubucco_act2013_record_crosswalk_verified"])
        self.assertNotIn("SECRET_PERSON_ID", json.dumps(receipt))
        self.assertEqual(receipt, verify_original(self.path, expected_provider_sha1=sha))

    def test_publisher_sha1_mismatch_blocks(self):
        self.build([("a.gml", b"test")])
        with self.assertRaisesRegex(ACT2013SourceError, "publisher SHA1"):
            verify_original(self.path)

    def test_reject_non_sha1_and_missing_or_symlink(self):
        self.build([("a.gml", b"test")])
        with self.assertRaisesRegex(ACT2013SourceError, "malformed"):
            verify_original(self.path, expected_provider_sha1="wrong")
        alias = Path(self.tmp.name) / "link.zip"
        alias.symlink_to(self.path)
        with self.assertRaisesRegex(ACT2013SourceError, "non-symlink"):
            verify_original(alias, expected_provider_sha1=hashlib.sha1(self.path.read_bytes()).hexdigest())

    def test_traversal_blocks(self):
        sha = self.build([("../outside.gml", b"test")])
        with self.assertRaisesRegex(ACT2013SourceError, "Unsafe"):
            verify_original(self.path, expected_provider_sha1=sha)

    def test_absolute_and_windows_and_duplicate_paths_block(self):
        for entry in ("/root/a.gml", "C:/root/a.gml", "a\\b.gml"):
            sha = self.build([(entry, b"test")])
            with self.subTest(entry=entry), self.assertRaisesRegex(ACT2013SourceError, "Unsafe"):
                verify_original(self.path, expected_provider_sha1=sha)
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr("same.gml", b"one")
            archive.writestr("same.gml", b"two")
        sha = hashlib.sha1(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ACT2013SourceError, "repeated"):
            verify_original(self.path, expected_provider_sha1=sha)

    def test_symlink_member_blocks(self):
        info = zipfile.ZipInfo("link.gml")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr(info, b"target")
        sha = hashlib.sha1(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ACT2013SourceError, "Unsafe"):
            verify_original(self.path, expected_provider_sha1=sha)

    def test_zip_bomb_ratio_blocks(self):
        sha = self.build([("compressed.gml", b"0" * 200000)])
        with self.assertRaisesRegex(ACT2013SourceError, "ratio"):
            verify_original(self.path, expected_provider_sha1=sha)

    def test_tampered_member_crc_blocks(self):
        self.build([("a.gml", b"ORIGINAL_PAYLOAD_1234")])
        original = self.path.read_bytes()
        at = original.index(b"ORIGINAL_PAYLOAD_1234") if b"ORIGINAL_PAYLOAD_1234" in original else -1
        if at == -1:
            with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("a.gml", b"ORIGINAL_PAYLOAD_1234")
            original = self.path.read_bytes()
            at = original.index(b"ORIGINAL_PAYLOAD_1234")
        self.path.write_bytes(original[:at] + b"T" + original[at+1:])
        with self.assertRaisesRegex(ACT2013SourceError, "CRC"):
            verify_original(self.path, expected_provider_sha1=hashlib.sha1(self.path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
