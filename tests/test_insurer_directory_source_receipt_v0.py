# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests with independently synthetic source data only."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from insurer_directory_source_receipt_v0 import EXPECTED_VERSION, SOURCE_URL, inspect_bytes


def example():
    return {
        "version": EXPECTED_VERSION,
        "all": SOURCE_URL,
        "licence": "CC BY 4.0 — attribute KAFS North America (synthetic test only)",
        "count": 2,
        "data": [
            {"slug": "test-a", "name": "Synthetic Insurer A", "country": "testland", "classCode": "G", "verification": "verified"},
            {"slug": "test-b", "name": "Synthetic Reinsurer B", "country": "testland", "classCode": "R", "verification": "partial"},
        ],
    }


class DirectoryReceiptTests(unittest.TestCase):
    def convert(self, value):
        return json.dumps(value).encode("utf-8")

    def test_valid_receipt_is_non_admitted(self):
        receipt = inspect_bytes(self.convert(example()))
        self.assertEqual(receipt["rows"], 2)
        self.assertEqual(receipt["country_slugs"], 1)
        self.assertEqual(receipt["classes"], {"G": 1, "R": 1})
        self.assertFalse(receipt["regulator_verified_by_this_audit"])
        self.assertFalse(receipt["model_admitted"])
        self.assertEqual(len(receipt["sha256_of_local_input_bytes"]), 64)

    def test_duplicate_slug_fails_closed(self):
        value = example()
        value["data"][1]["slug"] = "test-a"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            inspect_bytes(self.convert(value))

    def test_wrong_count_fails_closed(self):
        value = example()
        value["count"] = 300
        with self.assertRaisesRegex(ValueError, "count"):
            inspect_bytes(self.convert(value))

    def test_version_change_fails_closed(self):
        value = example()
        value["version"] = "future-unreviewed"
        with self.assertRaisesRegex(ValueError, "version"):
            inspect_bytes(self.convert(value))

    def test_different_licence_fails_closed(self):
        value = example()
        value["licence"] = "all rights reserved"
        with self.assertRaisesRegex(ValueError, "licence"):
            inspect_bytes(self.convert(value))

    def test_missing_row_value_fails_closed(self):
        value = example()
        value["data"][1]["name"] = " "
        with self.assertRaisesRegex(ValueError, "name"):
            inspect_bytes(self.convert(value))

    def test_unknown_verification_fails_closed(self):
        value = example()
        value["data"][0]["verification"] = "officially-certified"
        with self.assertRaisesRegex(ValueError, "verification"):
            inspect_bytes(self.convert(value))


if __name__ == "__main__":
    unittest.main()
