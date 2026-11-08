# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from research_runners.cfdid_hierarchy_preflight_v0 import PreflightError, audit_csv_text

HEADER = (
    "Event level,Event ID,Start year,Start month,Start day,End year,End month,End day,"
    "Direct economic losses (million CNY)\n"
)


def line(level: str, eid: str, amount: str, *,
         year: str | None = None, month: str = "3", day: str = "15",
         end_year: str = "", end_month: str = "", end_day: str = "") -> str:
    year = year if year is not None else eid[:4]
    return f"{level},{eid},{year},{month},{day},{end_year},{end_month},{end_day},{amount}\n"


class CFDIDHierarchyTests(unittest.TestCase):
    def test_parent_aggregation_excludes_children(self) -> None:
        data = (HEADER + line("L1", "2011-043", "100") + line("L2", "2011-043-01", "40") +
                line("L3", "2011-043-01-01", "10") + line("L1", "2011-044", ""))
        output = audit_csv_text(data)
        self.assertEqual(output["by_event_level"], {"L1": 2, "L2": 1, "L3": 1})
        self.assertEqual(output["l1_reported_direct_loss_million_cny"], "100")
        self.assertEqual(output["reported_l1_loss_records"], 1)

    def test_parent_does_not_disappear(self) -> None:
        with self.assertRaisesRegex(PreflightError, "Missing parents"):
            audit_csv_text(HEADER + line("L2", "2011-043-01", "2"))

    def test_duplicate_ids_blocked(self) -> None:
        with self.assertRaisesRegex(PreflightError, "Duplicate"):
            audit_csv_text(HEADER + line("L1", "2011-043", "1") + line("L1", "2011-043", "2"))

    def test_malformed_id_blocked(self) -> None:
        with self.assertRaisesRegex(PreflightError, "hierarchy"):
            audit_csv_text(HEADER + line("L2", "2011-043", "1"))

    def test_negative_or_nonfinite_loss_blocked(self) -> None:
        for invalid in ("-1", "NaN", "Inf", "--"):
            with self.subTest(invalid=invalid), self.assertRaises(PreflightError):
                audit_csv_text(HEADER + line("L1", "2011-043", invalid))

    def test_loss_missing_not_zero_observation(self) -> None:
        out = audit_csv_text(HEADER + line("L1", "2011-043", ""))
        self.assertEqual(out["reported_l1_loss_records"], 0)

    def test_strict_original_counts_do_not_silently_pass_partial_file(self) -> None:
        with self.assertRaisesRegex(PreflightError, "published"):
            audit_csv_text(HEADER + line("L1", "2011-043", "100"), strict_original=True)

    def test_start_year_must_match_event_id(self) -> None:
        with self.assertRaisesRegex(PreflightError, "year differs"):
            audit_csv_text(HEADER + line("L1", "2011-043", "1", year="2010"))

    def test_unknown_start_day_is_counted_not_imputed(self) -> None:
        out = audit_csv_text(HEADER + line("L1", "2011-043", "1", day=""))
        self.assertEqual(out["rows_missing_reported_start_day"], 1)

    def test_invalid_dates_and_partial_end_fields_rejected(self) -> None:
        cases = (
            line("L1", "2011-043", "1", month="2", day="30"),
            line("L1", "2011-043", "1", end_month="3"),
            line("L1", "2011-043", "1", end_day="22"),
            line("L1", "2011-043", "1", end_year="2010"),
        )
        for case in cases:
            with self.subTest(case=case), self.assertRaises(PreflightError):
                audit_csv_text(HEADER + case)

    def test_partial_end_date_allowed_when_valid(self) -> None:
        out = audit_csv_text(HEADER + line("L1", "2011-043", "1", end_year="2011", end_month="6"))
        self.assertEqual(out["rows"], 1)

    def test_required_headings_and_columns(self) -> None:
        for csv_text in ("foo,bar\nL1,1\n", HEADER + line("L1", "2011-043", "1").rstrip("\n") + ",extra\n", HEADER):
            with self.subTest(csv_text=csv_text[:22]), self.assertRaises(PreflightError):
                audit_csv_text(csv_text)


if __name__ == "__main__":
    unittest.main()
