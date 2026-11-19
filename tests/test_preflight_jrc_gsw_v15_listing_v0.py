# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic/offline tests; no external provider bytes are bundled."""

import hashlib
import unittest

from scripts.preflight_jrc_gsw_v15_listing_v0 import (
    GSWListingError,
    MAX_LISTING_BYTES,
    SELECTED_ASSET,
    inspect_original_listing,
)


class OriginalListingPreflightTests(unittest.TestCase):
    def test_exact_v15_selected_once(self):
        original = ("unrelated/other.tif\n" + SELECTED_ASSET + "\n").encode()
        result = inspect_original_listing(original)
        self.assertEqual(result["selected_path"], SELECTED_ASSET)
        self.assertEqual(result["original_listing_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(result["selected_path_occurrences"], 1)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["original_asset_bytes_verified"])

    def test_missing_or_old_v14_rejected(self):
        for value in ("other.tif\n", SELECTED_ASSET.replace("v1_5", "v1_4")):
            with self.subTest(value=value), self.assertRaises(GSWListingError):
                inspect_original_listing(value.encode())

    def test_duplicate_exact_path_rejected(self):
        with self.assertRaisesRegex(GSWListingError, "found 2"):
            inspect_original_listing((SELECTED_ASSET + "\n" + SELECTED_ASSET).encode())

    def test_html_response_and_absolute_url_rejected(self):
        for value in (
            "<html>not listing</html>\n" + SELECTED_ASSET,
            "https://evil.example/file\n" + SELECTED_ASSET,
        ):
            with self.subTest(value=value), self.assertRaises(GSWListingError):
                inspect_original_listing(value.encode())

    def test_binary_non_utf8_rejected(self):
        for payload in (b"", b"\xff\xfe", b"\x00" + SELECTED_ASSET.encode()):
            with self.subTest(payload=payload), self.assertRaises(GSWListingError):
                inspect_original_listing(payload)

    def test_size_bound_enforced(self):
        with self.assertRaises(GSWListingError):
            inspect_original_listing(b"x" * (MAX_LISTING_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
