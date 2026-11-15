# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only time/vintage negative tests; no source payload fixtures."""
import unittest

from scripts.audit_meteoswiss_hail_item_vintage_v0 import (
    COLLECTION_ID, HailVintageError, screen_item_vintage,
)


def row(item="202505-ch", title="CH at 05.2025", time="2025-05-31T04:00:18Z"):
    return {"exact_collection": COLLECTION_ID, "item_id": item,
            "item_title_observed": title, "item_datetime_observed": time}


class HailItemVintageTests(unittest.TestCase):
    def test_equal_id_title_nominal_does_not_admit_any_observations(self):
        got = screen_item_vintage(row())
        self.assertTrue(got["title_matches_item_month"])
        self.assertTrue(got["nominal_datetime_matches_item_month"])
        self.assertTrue(got["item_month_in_hail_season"])
        self.assertIsNone(got["verified_asset_observation_month"])
        self.assertFalse(got["model_input_approved"])

    def test_one_year_nominal_datetime_drift_is_flagged(self):
        got = screen_item_vintage(row(time="2026-05-31T04:00:18.859934Z"))
        self.assertIn("nominal_datetime_item_month_mismatch", got["blockers"])
        self.assertIsNone(got["verified_asset_observation_month"])

    def test_outside_hail_season_not_observed_zero(self):
        got = screen_item_vintage(row("202510-ch", "CH at 10.2025", "2026-10-31T04:00:18Z"))
        self.assertFalse(got["item_month_in_hail_season"])
        self.assertEqual(got["item_year_month"], "2025-10")
        self.assertIn("outside_april_september_hail_computation_season", got["blockers"])
        self.assertIn("nominal_datetime_item_month_mismatch", got["blockers"])
        self.assertFalse(got["independent_hail_observation_verified"])

    def test_item_and_title_disagree(self):
        got = screen_item_vintage(row(title="CH at 06.2025"))
        self.assertIn("title_item_month_mismatch", got["blockers"])

    def test_reject_wrong_source_and_bad_grammar(self):
        examples = [row("202513-ch"), row(title="2025 May"), row("archive-ch"),
                    {**row(), "exact_collection": "different"}, row(time="2025-05-31")]
        for bad in examples:
            with self.subTest(value=bad), self.assertRaises(HailVintageError):
                screen_item_vintage(bad)

    def test_reject_malformed_dates_and_non_utc(self):
        for stamp in ("2025-05-32T04:00:18Z", "2025-05-31T24:00:18Z",
                      "2025-05-31T04:00:18+02:00", "2025-05-31T04:00:18", "not-a-date"):
            with self.subTest(stamp=stamp), self.assertRaises(HailVintageError):
                screen_item_vintage(row(time=stamp))

    def test_reject_wrong_types(self):
        for key,value in (("item_id", None), ("item_title_observed", 123),
                          ("item_datetime_observed", True)):
            bad = row(); bad[key] = value
            with self.subTest(field=key), self.assertRaises(HailVintageError):
                screen_item_vintage(bad)


if __name__ == "__main__":
    unittest.main()
