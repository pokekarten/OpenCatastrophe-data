# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic HDF5-signature fixtures only; no genuine Zenodo asset."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from zenodo_hail330_lux_hdf5_receipt_v0 import (  # noqa: E402
    AssetError, MAGIC, audit_file,
)


class TestLuxHailHdf5Identity(unittest.TestCase):
    def test_synthetic_hdf5_magic_and_matching_hash_receipt_only(self):
        data = MAGIC + b"synthetic-placeholder-not-real-h5" + b"z" * 64
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "hail_LUX_ref.h5"
            path.write_bytes(data)
            result = audit_file(path, filename=path.name, md5=hashlib.md5(data).hexdigest())
            self.assertEqual(result["sha256_local"], hashlib.sha256(data).hexdigest())
            self.assertFalse(result["hdf5_datasets_and_units_checked"])

    def test_corrupted_file_signature_rejected_even_if_digest_matches(self):
        data = b"NOT-HDF5" + b"x" * 64
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "hail_LUX_ref.h5"
            path.write_bytes(data)
            with self.assertRaisesRegex(AssetError, "signature"):
                audit_file(path, filename=path.name, md5=hashlib.md5(data).hexdigest())

    def test_nonmatching_publisher_checksum_rejected(self):
        data = MAGIC + b"x" * 64
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "hail_LUX_PGW.h5"
            path.write_bytes(data)
            with self.assertRaisesRegex(AssetError, "MD5"):
                audit_file(path, filename=path.name, md5="0" * 32)

    def test_wrong_name_and_symlink_rejected(self):
        data = MAGIC + b"x" * 64
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "hail_LUX_ref.h5"
            path.write_bytes(data)
            target = Path(td) / "hail_LUX_PGW.h5"
            target.symlink_to(path)
            for choice, filename in ((path, "hail_LUX_PGW.h5"), (target, target.name)):
                with self.subTest(choice=choice), self.assertRaises(AssetError):
                    audit_file(choice, filename=filename, md5=hashlib.md5(data).hexdigest())

    def test_signature_only_cannot_prove_source_identity(self):
        data = MAGIC
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "hail_LUX_ref.h5"
            path.write_bytes(data)
            with self.assertRaisesRegex(AssetError, "MD5"):
                audit_file(path, filename=path.name, md5="f" * 32)


if __name__ == "__main__":
    unittest.main()
