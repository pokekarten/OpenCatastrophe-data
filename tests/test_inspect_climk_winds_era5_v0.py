# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No provider NetCDF bytes are in the synthetic unit tests."""
import unittest
from unittest.mock import patch

from scripts import inspect_climk_winds_era5_v0 as mod


class CLIMKWindProbeTests(unittest.TestCase):
    def test_exact_sha256_and_native_units_pinned(self):
        self.assertEqual(mod.PINNED_SHA256, "92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102")
        self.assertEqual(mod.EXPECTED_DIMENSIONS, {"storm_number": 50, "latitude": 181, "longitude": 269})
        self.assertEqual(mod.EXPECTED_FIELDS["absolute_maxwindgusts"][1], "m s**-1")
        self.assertEqual(mod.EXPECTED_FIELDS["LI_gridpoint"][1], "none")

    def test_fixed_published_data_receipt(self):
        self.assertEqual(mod.PUBLISHED_SIZE, 6792278)
        self.assertEqual(mod.PUBLISHED_MD5, "887ae3218793c599862f115876c145f9")
        self.assertTrue(mod.SOURCE_URL.startswith("https://zenodo.org/api/records/15305753/files/"))

    def test_rejects_empty_and_size_drift(self):
        for raw in (b"", b"not a NetCDF", b"a" * 100):
            with self.subTest(raw=raw[:12]):
                with self.assertRaises(mod.WindSourceError):
                    mod.verify_source_bytes(raw)

    def test_rejects_wrong_publisher_md5(self):
        with patch.object(mod, "PUBLISHED_SIZE", 3):
            with self.assertRaises(mod.WindSourceError):
                mod.verify_source_bytes(b"abc")

    def test_provisional_sha_gate_fails_closed(self):
        with patch.object(mod, "PUBLISHED_SIZE", 3), patch.object(
            mod, "PUBLISHED_MD5", "900150983cd24fb0d6963f7d28e17f72"
        ), patch.object(mod, "PINNED_SHA256", ""):
            with self.assertRaises(mod.WindSourceError):
                mod.verify_source_bytes(b"abc", require_sha256=True)

    def test_sha_gate_does_not_accept_tampered_content(self):
        with patch.object(mod, "PUBLISHED_SIZE", 3), patch.object(
            mod, "PUBLISHED_MD5", "900150983cd24fb0d6963f7d28e17f72"
        ), patch.object(mod, "PINNED_SHA256", "0" * 64):
            with self.assertRaises(mod.WindSourceError):
                mod.verify_source_bytes(b"abc", require_sha256=True)

    def test_source_provenance_no_insurer_claim(self):
        with patch.object(mod, "PUBLISHED_SIZE", 3), patch.object(
            mod, "PUBLISHED_MD5", "900150983cd24fb0d6963f7d28e17f72"
        ), patch.object(mod, "PINNED_SHA256", ""):
            r = mod.verify_source_bytes(b"abc")
        self.assertFalse(r["sha256_pinned"])
        self.assertEqual(len(r["sha256_observed"]), 64)


if __name__ == "__main__":
    unittest.main()
