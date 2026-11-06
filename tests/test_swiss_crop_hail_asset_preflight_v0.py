# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression checks. No Zenodo assets stored in the test tree."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from research_runners import swiss_crop_hail_asset_preflight_v0 as preflight


class SwissCropHailAssetPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "original.bin"

    def _check(self, content: bytes, kind: str, max_size=100000):
        self.path.write_bytes(content)
        pin = hashlib.md5(content, usedforsecurity=False).hexdigest()
        with patch.dict(preflight.ASSETS, {"local_test": (11064781, pin, kind, max_size)}):
            return preflight.inspect_local("local_test", self.path)

    def _zip(self, entries):
        result = io.BytesIO()
        with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for name, content in entries:
                target.writestr(name, content)
        return result.getvalue()

    def test_pinned_source_asset_records(self):
        self.assertEqual(len(preflight.ASSETS), 8)
        self.assertEqual(set(a[0] for a in preflight.ASSETS.values()), {11064756, 11064767, 11064781, 12784190})
        self.assertEqual(len(preflight.EVENT_DATES), 12)
        self.assertEqual(len(set(preflight.EVENT_DATES)), 12)
        self.assertTrue(all(len(pin) == 32 for _, pin, _, _ in preflight.ASSETS.values()))

    def test_valid_hdf5_signature_returns_sha256_only_as_identity(self):
        content = b"\x89HDF\r\n\x1a\n" + b"0" * 64
        result = self._check(content, "hdf5")
        self.assertEqual(result["sha256"], hashlib.sha256(content).hexdigest())
        self.assertFalse(result["admitted_for_cat_model"])
        self.assertFalse(result["insurer_losses_validated"])

    def test_format_gate_rejects_signature_mismatch_even_with_correct_hash(self):
        with self.assertRaisesRegex(preflight.Blocked, "HDF5"):
            self._check(b"not hdf5 but correct pinned MD5", "hdf5")

    def test_digest_mismatch_and_empty_file_blocked(self):
        self.path.write_bytes(b"wrong")
        with self.assertRaisesRegex(preflight.Blocked, "MD5"):
            preflight.inspect_local("radar_meshs_h5", self.path)
        self.path.write_bytes(b"")
        with self.assertRaisesRegex(preflight.Blocked, "empty"):
            preflight.inspect_local("radar_meshs_h5", self.path)

    def test_bounded_size_and_unrecognized_asset(self):
        with self.assertRaisesRegex(preflight.Blocked, "unrecognized"):
            preflight.inspect_local("unknown", self.path)
        with self.assertRaisesRegex(preflight.Blocked, "size bound"):
            self._check(b"CSV,header", "csv", max_size=2)

    def test_zip_validation_and_no_extraction(self):
        result = self._check(self._zip([("a/b.txt", b"demo")]), "zip")
        self.assertEqual(result["zip_member_count"], 1)
        self.assertFalse((Path(self.tmp.name) / "a").exists())

    def test_zip_path_traversal_and_duplicate_blocked(self):
        for content in [self._zip([("../escape.txt", b"x")]),
                        self._zip([("a", b"x"), ("a", b"y")])]:
            with self.subTest(content_len=len(content)):
                with self.assertRaisesRegex(preflight.Blocked, "unsafe or duplicate"):
                    self._check(content, "zip")

    def test_zip_bomb_ratio_and_empty_archive_blocked(self):
        for content in [self._zip([("a", b"a" * 300_000)]), self._zip([])]:
            with self.assertRaises(preflight.Blocked):
                self._check(content, "zip", max_size=400_000)

    def test_csv_sanity_check(self):
        self.assertTrue(self._check(b"field,value\na,1\n", "csv")["publisher_md5_verified"])
        with self.assertRaisesRegex(preflight.Blocked, "CSV"):
            self._check(b"not a comma separated header", "csv")

    def test_symlinks_are_blocked(self):
        self.path.write_bytes(b"hello")
        link = Path(self.tmp.name) / "alias"
        link.symlink_to(self.path)
        with self.assertRaisesRegex(preflight.Blocked, "non-symlink"):
            preflight.inspect_local("radar_meshs_h5", link)


if __name__ == "__main__":
    unittest.main()
