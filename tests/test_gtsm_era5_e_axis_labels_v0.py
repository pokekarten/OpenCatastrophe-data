# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic statistical axis metadata only; no provider measurements."""
from __future__ import annotations

import unittest

from scripts.gtsm_era5_e_axis_labels_v0 import (
    NativeAxesBlocked, inspect_level_labels,
    PAPER_RETURN_YEARS,
)


class GtsmAxisLabelTests(unittest.TestCase):
    def test_seven_native_vs_nine_paper_percentiles_explicitly_flagged(self):
        result = inspect_level_labels([.01, .05, .10, .25, .50, .75, .95], list(PAPER_RETURN_YEARS))
        self.assertEqual(result["native_quantile_count"], 7)
        self.assertEqual(result["paper_quantile_count"], 9)
        self.assertEqual(result["candidate_missing_paper_percentiles"], [90, 99])
        self.assertFalse(result["quantile_semantics_reviewed"])

    def test_one_to_one_return_years(self):
        r = inspect_level_labels([1, 5, 10, 25, 50, 75, 95], list(PAPER_RETURN_YEARS))
        self.assertEqual(r["observed_return_period_years"], list(PAPER_RETURN_YEARS))
        self.assertEqual(r["quantile_encoding_hypothesis"], "percentage_candidate")

    def test_reject_nonfinite_quantile(self):
        q = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, float("nan")]
        with self.assertRaises(NativeAxesBlocked):
            inspect_level_labels(q, list(PAPER_RETURN_YEARS))

    def test_reject_nonascending_quantile(self):
        with self.assertRaises(NativeAxesBlocked):
            inspect_level_labels([0.01, .05, .1, .5, .25, .75, .95], list(PAPER_RETURN_YEARS))

    def test_reject_wrong_return_periods(self):
        with self.assertRaises(NativeAxesBlocked):
            inspect_level_labels([.01, .05, .1, .25, .5, .75, .95], [1,2,5,10,20,50,75,100])

    def test_reject_wrong_axis_lengths(self):
        with self.assertRaises(NativeAxesBlocked):
            inspect_level_labels([.01, .05], list(PAPER_RETURN_YEARS))

    def test_reject_bool_integer_year(self):
        with self.assertRaises(NativeAxesBlocked):
            inspect_level_labels([.01, .05, .1, .25, .5, .75, .95], [True,2,5,10,25,50,75,100])

    def test_no_raw_hazard_source_data_in_receipt(self):
        r = inspect_level_labels([.01,.05,.1,.25,.5,.75,.95], list(PAPER_RETURN_YEARS))
        self.assertFalse(r["raw_hazard_grids_read"])
        self.assertFalse(r["cat_model_admitted"])


if __name__ == "__main__":
    unittest.main()
