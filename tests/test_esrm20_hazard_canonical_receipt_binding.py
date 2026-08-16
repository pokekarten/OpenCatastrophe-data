# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import run_esrm20_hazard_logic_tree_profile_action as original
from scripts import run_esrm20_hazard_logic_tree_profile_action_receipt_fix as subject


class HazardCanonicalReceiptBindingTests(unittest.TestCase):
    def test_adapter_binds_exact_trusted_476_receipt_identity(self) -> None:
        subject.assert_canonical_receipt_binding()
        self.assertEqual(
            subject.GSIM_SHA256,
            "f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4",
        )
        self.assertEqual(
            subject.SOURCE_SHA256,
            "caebf9142da6b4d6d1e970c3c008627d34943da83c977fb1da4d15d1e34d8a12",
        )
        self.assertEqual(subject.RECEIPT_COMMENT_ID, 5310057117)
        self.assertEqual(original.GSIM_SHA256, subject.GSIM_SHA256)
        self.assertEqual(original.SOURCE_SHA256, subject.SOURCE_SHA256)
        self.assertEqual(original.RECEIPT_COMMENT_ID, subject.RECEIPT_COMMENT_ID)

    def test_parser_and_action_contract_are_not_replaced(self) -> None:
        self.assertIs(subject.validate_request, original.validate_request)
        self.assertIs(subject.run_profile, original.run_profile)
        self.assertIs(subject._validate_profile, original._validate_profile)
        self.assertEqual(subject.ACTION, original.ACTION)
        self.assertEqual(subject.REQUEST_MARKER, original.REQUEST_MARKER)
        self.assertEqual(subject.RESULT_MARKER, original.RESULT_MARKER)


if __name__ == "__main__":
    unittest.main()
