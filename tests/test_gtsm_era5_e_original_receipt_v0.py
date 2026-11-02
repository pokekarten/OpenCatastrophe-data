# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-only regression tests; no external provider bytes."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.gtsm_era5_e_original_receipt_v0 import (
    GtsmReceiptError, HDF5_MAGIC, _file_receipt, verify_original,
)


class GtsmReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.nc"

    def fixture(self, prefix: bytes = HDF5_MAGIC):
        data = prefix + b"independently invented bytes only" * 7
        self.path.write_bytes(data)
        return data

    def verify_fixture(self, data: bytes):
        return _file_receipt(self.path, expected_size=len(data),
                             expected_md5=hashlib.md5(data, usedforsecurity=False).hexdigest())

    def test_positive_hdf5_synthetic(self):
        data = self.fixture()
        result = self.verify_fixture(data)
        self.assertEqual(result["container_signature"], "netcdf4_hdf5")
        self.assertEqual(result["sha256_observed_not_publisher_pinned"], hashlib.sha256(data).hexdigest())

    def test_positive_classic_synthetic(self):
        data = self.fixture(b"CDF\x02")
        self.assertEqual(self.verify_fixture(data)["container_signature"], "netcdf_classic")

    def test_wrong_publisher_digest_rejected(self):
        data = self.fixture()
        with self.assertRaises(GtsmReceiptError):
            _file_receipt(self.path, expected_size=len(data), expected_md5="0" * 32)

    def test_wrong_length_rejected(self):
        data = self.fixture()
        with self.assertRaises(GtsmReceiptError):
            _file_receipt(self.path, expected_size=len(data) + 1,
                          expected_md5=hashlib.md5(data, usedforsecurity=False).hexdigest())

    def test_malformed_netcdf_signature_rejected_even_if_md5_matches(self):
        data = self.fixture(b"NOTNC123")
        with self.assertRaises(GtsmReceiptError):
            self.verify_fixture(data)

    def test_symlink_rejected(self):
        data = self.fixture()
        link = self.path.with_name("link.nc")
        link.symlink_to(self.path)
        with self.assertRaises(GtsmReceiptError):
            _file_receipt(link, expected_size=len(data),
                          expected_md5=hashlib.md5(data, usedforsecurity=False).hexdigest())

    def test_public_entry_point_never_accepts_synthetic_pin_override(self):
        self.fixture()
        with self.assertRaises(GtsmReceiptError):
            verify_original(self.path)

    def test_no_original_file_rejected(self):
        with self.assertRaises(GtsmReceiptError):
            _file_receipt(self.path, expected_size=10, expected_md5="0" * 32)


if __name__ == "__main__":
    unittest.main()
