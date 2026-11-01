# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: never fetch or store any original IGN third-party bytes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
from fr_bdtopo_2016_d077_archive_receipt_v0 import (
    ArchiveReceiptError, MAGIC_7Z, inspect_archive,
)

NAME = "BDTOPO_2-1_TOUSTHEMES_SHP_LAMB93_D077_2016-03-24.7z"


class ArchiveReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / NAME
        self.raw = MAGIC_7Z + b"SYNTHETIC_TEST_ONLY_NOT_A_VALID_7Z_ARCHIVE"
        self.path.write_bytes(self.raw)
        self.meta = {
            "archive_filename": NAME,
            "mirror_listed_size_bytes": len(self.raw),
            "research_only": True,
            "model_input_approved": False,
            "original_sha256": None,
        }

    def test_full_bytes_deterministically_hashed(self):
        r = inspect_archive(self.path, self.meta)
        self.assertTrue(r["7z_file_signature_verified"])
        self.assertEqual(r["full_archive_sha256_local"], hashlib.sha256(self.raw).hexdigest())
        self.assertFalse(r["original_provider_full_archive_sha256_independently_verified"])
        self.assertFalse(r["historical_building_geometry_verified"])
        self.assertFalse(r["model_input_approved"])

    def test_missing_file_fails(self):
        self.path.unlink()
        with self.assertRaises(ArchiveReceiptError):
            inspect_archive(self.path, self.meta)

    def test_truncated_archive_fails(self):
        self.meta["mirror_listed_size_bytes"] += 1
        with self.assertRaisesRegex(ArchiveReceiptError, "size differs"):
            inspect_archive(self.path, self.meta)

    def test_bad_magic_rejected(self):
        self.path.write_bytes(b"X" * len(self.raw))
        with self.assertRaisesRegex(ArchiveReceiptError, "signature"):
            inspect_archive(self.path, self.meta)

    def test_wrong_department_or_release_rejected(self):
        self.meta["archive_filename"] = NAME.replace("D077", "D075")
        with self.assertRaisesRegex(ArchiveReceiptError, "wrong historical"):
            inspect_archive(self.path, self.meta)

    def test_model_admission_not_accepted_as_source_fact(self):
        self.meta["model_input_approved"] = True
        with self.assertRaisesRegex(ArchiveReceiptError, "research-only"):
            inspect_archive(self.path, self.meta)

    def test_invented_provider_sha_rejected(self):
        self.meta["original_sha256"] = "a" * 64
        with self.assertRaisesRegex(ArchiveReceiptError, "provider hash"):
            inspect_archive(self.path, self.meta)

    def test_boolean_size_rejected(self):
        self.meta["mirror_listed_size_bytes"] = True
        with self.assertRaisesRegex(ArchiveReceiptError, "byte size"):
            inspect_archive(self.path, self.meta)

    def test_exact_name_symlink_is_rejected(self):
        real = self.path.parent / "real-archive.7z"
        self.path.rename(real)
        self.path.symlink_to(real)
        with self.assertRaisesRegex(ArchiveReceiptError, "exact-name"):
            inspect_archive(self.path, self.meta)

    def test_wrong_local_filename_rejected(self):
        other = self.path.parent / "other-edition.7z"
        self.path.rename(other)
        with self.assertRaisesRegex(ArchiveReceiptError, "exact-name"):
            inspect_archive(other, self.meta)

    def test_pinned_full_mirror_sha256_match(self):
        self.meta["mirror_full_archive_sha256_verified_in_ci"] = hashlib.sha256(self.raw).hexdigest()
        r = inspect_archive(self.path, self.meta)
        self.assertTrue(r["pinned_mirror_sha256_matched"])

    def test_pinned_full_mirror_sha256_mismatch_blocks(self):
        self.meta["mirror_full_archive_sha256_verified_in_ci"] = "a" * 64
        with self.assertRaisesRegex(ArchiveReceiptError, "differs from pinned"):
            inspect_archive(self.path, self.meta)

    def test_invalid_pinned_hash_blocks(self):
        self.meta["mirror_full_archive_sha256_verified_in_ci"] = "fake-hex"
        with self.assertRaisesRegex(ArchiveReceiptError, "invalid pinned"):
            inspect_archive(self.path, self.meta)

    def test_provenance_descriptor_is_research_only(self):
        meta_path = ROOT / "landscape" / "fr_bdtopo_d077_2016_archive_candidate_v0.json"
        source = json.loads(meta_path.read_text(encoding="utf-8"))
        self.assertEqual(source["mirror_listed_size_bytes"], 110738399)
        self.assertEqual(source["archive_filename"], NAME)
        self.assertFalse(source["model_input_approved"])
        self.assertIsNone(source["original_sha256"])
        self.assertTrue(source["full_archive_downloaded_or_original_bytes_hashed"])
        self.assertEqual(source["mirror_full_archive_sha256_verified_in_ci"], "ab3e1bab127d0e71e372d736572d80e6a8a9578131992475c23a1f0ee1871a06")


if __name__ == "__main__":
    unittest.main()
