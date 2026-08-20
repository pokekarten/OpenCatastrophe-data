# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import run_esrm20_hazard_logic_tree_profile_action as subject


class HazardDirectReceiptBindingTests(unittest.TestCase):
    def test_base_action_binds_exact_trusted_476_receipt_identity(self) -> None:
        self.assertEqual(subject.RECEIPT_ISSUE, 476)
        self.assertEqual(subject.RECEIPT_COMMENT_ID, 5310057117)
        self.assertEqual(subject.GSIM_BYTE_COUNT, 34_018)
        self.assertEqual(
            subject.GSIM_SHA256,
            "f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4",
        )
        self.assertEqual(subject.SOURCE_BYTE_COUNT, 1_964)
        self.assertEqual(
            subject.SOURCE_SHA256,
            "caebf9142da6b4d6d1e970c3c008627d34943da83c977fb1da4d15d1e34d8a12",
        )


if __name__ == "__main__":
    unittest.main()
