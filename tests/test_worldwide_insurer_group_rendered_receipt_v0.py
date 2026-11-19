# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic offline regression: no live source rows or external fetches."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.worldwide_insurer_group_rendered_receipt_v0 import (
    GroupRegisterError, _parse_iais, _parse_naic, audit_rendered_text,
)


IAIS = (
    "Register of Internationally Active Insurance Groups\n"
    "As of 14 October 2026, 61 IAIGs have been identified by relevant GWSs from 19 jurisdictions.\n"
    "| 1 | Synthetic Group Alpha | Regulator A | Place A |\n"
    "| 2 | Synthetic Group Beta | Regulator B | Place B |\n"
)
NAIC = (
    "Insurance Group Lead State Report 2026 - Quarter 2\n"
    "| Group Name | Group Code | Lead State |\n"
    "| Synthetic Coastal Grp | 123 | CA |\n"
    "| Synthetic Mountain Grp | 456 | PR |\n"
)


class RenderedGroupReceiptTests(unittest.TestCase):
    def test_iais_synthetic_profile(self):
        rows = _parse_iais(IAIS, count=2, jurisdictions=2)
        self.assertEqual([r[0] for r in rows], ["1", "2"])

    def test_naic_synthetic_profile(self):
        rows = _parse_naic(NAIC, count=2, jurisdictions=2)
        self.assertEqual([r[1] for r in rows], ["123", "456"])

    def test_iais_missing_row_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "incomplete"):
            _parse_iais(IAIS.replace("| 2 | Synthetic Group Beta | Regulator B | Place B |\n", ""), count=2, jurisdictions=2)

    def test_iais_duplicate_or_wrong_rank_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "incomplete"):
            _parse_iais(IAIS.replace("| 2 |", "| 1 |"), count=2, jurisdictions=2)

    def test_iais_casefold_duplicate_names_block(self):
        with self.assertRaisesRegex(GroupRegisterError, "duplicate"):
            _parse_iais(IAIS.replace("Synthetic Group Beta", "SYNTHETIC group alpha"), count=2, jurisdictions=2)

    def test_iais_incorrect_header_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "header"):
            _parse_iais(IAIS.replace("14 October 2026", "13 October 2026"), count=2, jurisdictions=2)

    def test_naic_duplicate_code_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "repeated"):
            _parse_naic(NAIC.replace("456", "123"), count=2, jurisdictions=2)

    def test_naic_bad_state_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "jurisdiction"):
            _parse_naic(NAIC.replace("456 | PR", "456 | Germany"), count=2, jurisdictions=2)

    def test_naic_wrong_quarter_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "header"):
            _parse_naic(NAIC.replace("Quarter 2", "Quarter 3"), count=2, jurisdictions=2)

    def test_naic_truncated_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "missing"):
            _parse_naic(NAIC.replace("| Synthetic Mountain Grp | 456 | PR |\n", ""), count=2, jurisdictions=2)

    def test_reserved_separator_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "reserved"):
            audit_rendered_text(b"test\x1e", "iais")

    def test_bounded_source_blocks(self):
        with self.assertRaisesRegex(GroupRegisterError, "oversized"):
            audit_rendered_text(b"x" * (1024 * 1024 + 1), "naic")

    def test_report_not_reclassify_any_group_as_insurer(self):
        # Profiles are intentionally pinned to actual public source counts:
        # a valid synthetic two-row example must not look like a full census.
        with self.assertRaisesRegex(GroupRegisterError, "incomplete"):
            audit_rendered_text(IAIS.encode("utf-8"), "iais")
        with self.assertRaisesRegex(GroupRegisterError, "missing"):
            audit_rendered_text(NAIC.encode("utf-8"), "naic")

    def test_non_network_default(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network used")):
            with self.assertRaises(GroupRegisterError):
                audit_rendered_text(b"not a register", "iais")


if __name__ == "__main__":
    unittest.main()
