# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from research_runners.cfdid_hierarchy_preflight_v0 import PreflightError, audit_csv_text

HEADER = "Event level,Event ID,Direct economic losses (million CNY)\n"


class CFDIDHierarchyTests(unittest.TestCase):
    def test_parent_aggregation_excludes_children(self) -> None:
        data = (HEADER + "L1,2011-043,100\n" + "L2,2011-043-01,40\n" +
                "L3,2011-043-01-01,10\n" + "L1,2011-044,\n")
        output = audit_csv_text(data)
        self.assertEqual(output["by_event_level"], {"L1": 2, "L2": 1, "L3": 1})
        self.assertEqual(output["l1_reported_direct_loss_million_cny"], "100")
        self.assertEqual(output["reported_l1_loss_records"], 1)

    def test_parent_does_not_disappear(self) -> None:
        with self.assertRaisesRegex(PreflightError, "Missing parents"):
            audit_csv_text(HEADER + "L2,2011-043-01,2\n")

    def test_duplicate_ids_blocked(self) -> None:
        with self.assertRaisesRegex(PreflightError, "Duplicate"):
            audit_csv_text(HEADER + "L1,2011-043,1\nL1,2011-043,2\n")

    def test_malformed_id_blocked(self) -> None:
        with self.assertRaisesRegex(PreflightError, "hierarchy"):
            audit_csv_text(HEADER + "L2,2011-043,1\n")

    def test_negative_or_nonfinite_loss_blocked(self) -> None:
        for invalid in ("-1", "NaN", "Inf", "--"):
            with self.subTest(invalid=invalid), self.assertRaises(PreflightError):
                audit_csv_text(HEADER + f"L1,2011-043,{invalid}\n")

    def test_loss_missing_not_zero_observation(self) -> None:
        out = audit_csv_text(HEADER + "L1,2011-043,\n")
        self.assertEqual(out["reported_l1_loss_records"], 0)

    def test_strict_original_counts_do_not_silently_pass_partial_file(self) -> None:
        with self.assertRaisesRegex(PreflightError, "published"):
            audit_csv_text(HEADER + "L1,2011-043,100\n", strict_original=True)

    def test_required_headings_and_columns(self) -> None:
        for csv_text in ("foo,bar\nL1,1\n", HEADER + "L1,2011-043,1,extra\n", HEADER):
            with self.subTest(csv_text=csv_text[:22]), self.assertRaises(PreflightError):
                audit_csv_text(csv_text)


if __name__ == "__main__":
    unittest.main()
