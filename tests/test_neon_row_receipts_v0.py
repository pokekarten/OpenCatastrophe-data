# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent row digests against exact 2026-11-01 read-only Neon research branch."""
import unittest
from independent_neon_10k_row_receipts_v0 import ASSETS, EXPECTED, compute_receipts


class NeonRowReceiptsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = compute_receipts()

    def test_all_four_live_neon_receipts_match(self):
        self.assertEqual(self.receipt, EXPECTED)

    def test_rejects_changed_asset_identity_and_value(self):
        modified = list(ASSETS)
        modified[0], modified[1] = (modified[0][0], modified[1][1]), (modified[1][0], modified[0][1])
        self.assertEqual(sum(x[1] for x in modified), sum(x[1] for x in ASSETS))
        with self.assertRaises(ValueError):
            compute_receipts(assets=tuple(modified))

    def test_rejects_nonsynthetic_and_truncated_worlds(self):
        with self.assertRaises(ValueError):
            compute_receipts(synthetic=False)
        with self.assertRaises(ValueError):
            compute_receipts(years=9999)

    def test_all_years_and_events_present(self):
        self.assertEqual(self.receipt['years'], 10000)
        self.assertEqual(self.receipt['events'], 1541)
        self.assertEqual(self.receipt['asset_event_rows'], 18492)


if __name__ == '__main__':
    unittest.main()
