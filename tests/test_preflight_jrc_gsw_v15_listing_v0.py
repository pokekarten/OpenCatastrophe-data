# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic/offline tests; no external provider bytes are bundled."""

import hashlib
import unittest

from scripts.preflight_jrc_gsw_v15_listing_v0 import (
    GSWListingError,
    MAX_LISTING_BYTES,
    SWIFT_DEFAULT_PAGE_LIMIT,
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
        self.assertEqual(result["listing_page_object_count"], 2)
        self.assertEqual(result["listing_scope"], "single_supplied_original_swift_listing_page")
        self.assertFalse(result["complete_original_catalogue_verified"])
        self.assertIsNone(result["original_complete_catalogue_sha256"])
        self.assertTrue(result["additional_swift_pages_not_acquired_by_preflight"])
        self.assertFalse(result["swift_default_page_limit_reached"])
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["original_asset_bytes_verified"])

    def test_missing_or_old_v14_rejected(self):
        for value in ("other.tif\n", SELECTED_ASSET.replace("v1_5", "v1_4")):
            with self.subTest(value=value), self.assertRaises(GSWListingError):
                inspect_original_listing(value.encode())

    def test_duplicate_exact_path_rejected(self):
        with self.assertRaisesRegex(GSWListingError, "found 2"):
            inspect_original_listing((SELECTED_ASSET + "\n" + SELECTED_ASSET).encode())

    def test_swift_ten_thousand_object_page_never_proves_catalogue_complete(self):
        # Source *page* may be accepted as a byte-pinned path observation
        # while the underlying original container has more objects.
        synthetic = [f"other/safe_{i:05d}.tif" for i in range(SWIFT_DEFAULT_PAGE_LIMIT - 1)]
        synthetic.append(SELECTED_ASSET)
        payload = ("\n".join(synthetic) + "\n").encode("utf-8")
        result = inspect_original_listing(payload)
        self.assertEqual(result["listing_page_object_count"], SWIFT_DEFAULT_PAGE_LIMIT)
        self.assertTrue(result["swift_default_page_limit_reached"])
        self.assertFalse(result["complete_original_catalogue_verified"])
        self.assertIsNone(result["original_complete_catalogue_sha256"])
        self.assertEqual(result["selected_path_occurrences"], 1)
        self.assertFalse(result["original_asset_bytes_verified"])

    def test_original_path_whitespace_is_not_normalized_into_false_positive(self):
        # Both selected path and neighbouring source keys must remain
        # byte-exact; provider-side whitespace is not an ignorable typo.
        for payload in (
            (" " + SELECTED_ASSET + "\n").encode(),
            (SELECTED_ASSET + "\n  other/asset.tif\n").encode(),
            (SELECTED_ASSET + "\nother/asset.tif \n").encode(),
            ("\t" + SELECTED_ASSET).encode(),
        ):
            with self.subTest(payload=payload[:60]), self.assertRaises(GSWListingError):
                inspect_original_listing(payload)

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
