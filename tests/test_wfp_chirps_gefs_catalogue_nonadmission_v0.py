# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed catalogue semantics for WFP CHIRPS3-GEFS forecast variants.

An internally consistent synthetic issue/lead receipt is not evidence that
WFP retained the historical issue, nor an observed rainfall or CAT loss.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "landscape/sources-wfp-chirps-gefs-forecast-20261103.json"
DAILY = "wfp.hdc.chirps3-gefs-daily-forecast.v3"
DEKAD = "wfp.hdc.chirps3-gefs-dekad-forecast.v3"


class WfpForecastCatalogueBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entries = json.loads(CATALOGUE.read_text(encoding="utf-8"))["entries"]
        cls.entries = entries
        cls.by_id = {item["candidate_id"]: item for item in entries}

    def test_distinct_products_but_one_shared_forecast_lineage(self):
        self.assertEqual(set(self.by_id), {DAILY, DEKAD})
        self.assertEqual(len(self.entries), 2)
        for item in self.entries:
            self.assertIn("forecast", item["categories"])
            self.assertIn("GEFSv12", item["note"])
            self.assertIn("CHIRPS3", item["note"])

    def test_rolling_daily_issues_cannot_be_called_asof_historical_proof(self):
        daily = self.by_id[DAILY]
        note = daily["note"].lower()
        self.assertIn("overwrite", note)
        self.assertIn("lead-0", note)
        self.assertIn("retrospective", note)
        self.assertIn("not an observed", note)

    def test_dekadal_not_independent_forecast_ensemble(self):
        dekad = self.by_id[DEKAD]
        self.assertIn("same parent forecast lineage", dekad["note"])
        self.assertIn("never treat them as statistically independent", dekad["note"])

    def test_all_products_remain_not_admitted(self):
        for item in self.entries:
            with self.subTest(candidate_id=item["candidate_id"]):
                self.assertEqual(item["admission_status"], "not_admitted")
                self.assertEqual(item["rights_review_status"], "not_reviewed")
                self.assertEqual(item["scientific_review_status"], "not_reviewed")


if __name__ == "__main__":
    unittest.main()
