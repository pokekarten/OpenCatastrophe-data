# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only PSMSL Cuxhaven 2 RLR monthly preflight checks."""

import hashlib
import unittest

from scripts.psmsl_rlr_monthly_qc_v0 import MAX_ORIGINAL_BYTES, screen_original_bytes


VALID = b"2025.0417; 6909; 0; 000\n2025.1250; 6940; 0; 001\n2025.2083; -99999; 99; 010\n"


class PsmslRlrMonthlyQcTests(unittest.TestCase):
    def test_preserves_original_byte_hash_and_explicit_non_admission(self):
        result = screen_original_bytes(VALID)
        self.assertEqual(result["original_sha256"], hashlib.sha256(VALID).hexdigest())
        self.assertEqual(result["original_bytes"], len(VALID))
        self.assertEqual(result["rows"], 3)
        self.assertEqual(result["first_month"], "2025-01")
        self.assertEqual(result["last_month"], "2025-03")
        self.assertEqual(result["missing_months"], 1)
        self.assertEqual(result["interpolated_months"], 1)
        self.assertEqual(result["flagged_months"], 2)
        self.assertEqual(result["cat_model_admission"], "not_admitted")
        self.assertEqual(result["neon_storage"], "storage_not_verified")

    def test_no_mutation_of_original(self):
        original = bytearray(VALID)
        before = bytes(original)
        screen_original_bytes(original)
        self.assertEqual(bytes(original), before)

    def test_rejects_html_error_page(self):
        self.assertRaises(ValueError, screen_original_bytes, b"<html>temporarily unavailable</html>")

    def test_rejects_empty_or_oversized(self):
        for original in (b"", b"x" * (MAX_ORIGINAL_BYTES + 1)):
            with self.subTest(length=len(original)):
                self.assertRaises(ValueError, screen_original_bytes, original)

    def test_rejects_duplicate_and_gap(self):
        for original in (
            b"2025.0417; 6909; 0; 000\n2025.0417; 6940; 0; 000\n",
            b"2025.0417; 6909; 0; 000\n2025.2083; 6940; 0; 000\n",
            b"2025.1250; 6909; 0; 000\n2025.0417; 6940; 0; 000\n",
        ):
            with self.subTest(original=original):
                self.assertRaises(ValueError, screen_original_bytes, original)

    def test_rejects_invalid_decimal_time(self):
        for field in ("2025.0000", "2025.0410", "2025.9999", "2025.5", "NaN"):
            with self.subTest(field=field):
                self.assertRaises(ValueError, screen_original_bytes, f"{field}; 6909; 0; 000\n".encode())

    def test_rejects_invalid_missing_days_and_flags(self):
        for row in (b"2025.2917; 6909; 31; 000\n", b"2025.0417; 6909; -1; 000\n", b"2025.0417; 6909; 0; 099\n"):
            with self.subTest(row=row):
                self.assertRaises(ValueError, screen_original_bytes, row)

    def test_rejects_malformed_lines_and_encoding(self):
        for row in (b"2025.0417,6909,0,000\n", b"2025.0417; 6909; 0; 000; extra\n", b"\xff\n", b"2025.0417; 6909; 0; 000\n\n2025.1250; 6940; 0; 000\n"):
            with self.subTest(row=row):
                self.assertRaises(ValueError, screen_original_bytes, row)


if __name__ == "__main__":
    unittest.main()
